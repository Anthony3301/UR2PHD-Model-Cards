# server.py
import os
import re
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from dotenv import load_dotenv, find_dotenv

# Load .env so OPENAI_API_KEY and OPENAI_MODEL work like in generate_eval.py
load_dotenv(find_dotenv(), override=False)

# Import existing helpers
from src.generate_eval import (
    fetch_url_text,
    load_template,
    build_prompt,
    call_openai_with_fallback,
    DEFAULT_MODEL,
)
from openai import OpenAI

TEMPLATE_PATH = "templates/card_review_template.md"
MODEL_NAME = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)

app = FastAPI()

# Allow your Chrome extension to call us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can restrict later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------
# Pydantic models for a richer response
# --------------------------------------------------------------------
class BasicInfo(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    type: Optional[str] = None
    version: Optional[str] = None
    owner: Optional[str] = None


class CategoryScore(BaseModel):
    name: str
    score: Optional[float] = None  # 0–3


class StandardsSummary(BaseModel):
    present: int = 0
    partial: int = 0
    missing: int = 0
    total_items: int = 0
    missing_items: List[str] = []
    partial_items: List[str] = []


class GapSummary(BaseModel):
    missing: Optional[str] = None
    inconsistent: Optional[str] = None
    ambiguous: Optional[str] = None


class GradeRequest(BaseModel):
    url: str


class GradeResponse(BaseModel):
    # Normalized overall score (0–100)
    score: Optional[float] = None
    # Raw total from /30, if parsed
    raw_total: Optional[float] = None
    max_total: Optional[float] = 30.0

    label: Optional[str] = None
    details: Optional[str] = None

    basic_info: Optional[BasicInfo] = None
    category_scores: Optional[List[CategoryScore]] = None
    standards_summary: Optional[StandardsSummary] = None
    gaps: Optional[GapSummary] = None

    filled_markdown: Optional[str] = None


# --------------------------------------------------------------------
# LLM call
# --------------------------------------------------------------------
def run_card_evaluation(url: str) -> str:
    """Use your existing pipeline to produce the filled evaluation markdown."""
    template_md = load_template(TEMPLATE_PATH)
    page_text = fetch_url_text(url)

    prompt = build_prompt(template_md, url, page_text)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=api_key)

    filled_md = call_openai_with_fallback(
        client=client,
        model=MODEL_NAME,
        system=prompt["system"],
        user=prompt["user"],
    )

    return filled_md


# --------------------------------------------------------------------
# Parsing helpers
# --------------------------------------------------------------------
def parse_basic_info(filled_md: str) -> BasicInfo:
    """
    Extracts Basic Info section assuming lines like:
    - **Card Title / URL:**
      some title
      https://...
    - **Type:** Model
    - **Version / Date:** ...
    - **Owner / Contact:** ...
    """
    lines = filled_md.splitlines()
    title = url = card_type = version = owner = None

    def get_block_after(idx: int) -> str:
        """Return the next non-empty line after idx, or empty string."""
        for j in range(idx + 1, len(lines)):
            txt = lines[j].strip()
            if txt:
                return txt
        return ""

    for i, line in enumerate(lines):
        stripped = line.strip()
        if "**Card Title / URL:**" in stripped:
            # next lines often contain title and/or url
            next_line = get_block_after(i)
            # If next_line looks like URL, maybe title is on the same line
            if "http://" in next_line or "https://" in next_line:
                url = next_line.strip()
            else:
                title = next_line.strip()
                # try a second line for url
                second = get_block_after(i + 1)
                if "http://" in second or "https://" in second:
                    url = second.strip()
        elif "**Type:**" in stripped:
            # e.g. "- **Type:** Model"
            m = re.search(r"\*\*Type:\*\*\s*(.+)", stripped)
            if m:
                card_type = m.group(1).strip()
            else:
                card_type = get_block_after(i)
        elif "**Version / Date:**" in stripped:
            m = re.search(r"\*\*Version / Date:\*\*\s*(.+)", stripped)
            if m:
                version = m.group(1).strip()
            else:
                version = get_block_after(i)
        elif "**Owner / Contact:**" in stripped:
            m = re.search(r"\*\*Owner / Contact:\*\*\s*(.+)", stripped)
            if m:
                owner = m.group(1).strip()
            else:
                owner = get_block_after(i)

    return BasicInfo(
        title=title,
        url=url,
        type=card_type,
        version=version,
        owner=owner,
    )


def parse_scoring_table(filled_md: str) -> tuple[list[CategoryScore], Optional[float]]:
    """
    Parse section '## 4 Scoring (0–3 per category)'
    and return a list of CategoryScore plus the Total(/30).
    """
    lines = filled_md.splitlines()
    in_section = False
    category_scores: list[CategoryScore] = []
    raw_total: Optional[float] = None

    for i, line in enumerate(lines):
        if line.strip().startswith("## 4 Scoring"):
            in_section = True
            continue
        if in_section:
            # End when we hit another section or horizontal rule
            if line.strip().startswith("## ") or line.strip().startswith("---"):
                break
            if not line.strip().startswith("|"):
                continue

            # Split markdown table row
            parts = [p.strip() for p in line.strip().split("|")]
            if len(parts) < 3:
                continue

            name = parts[1]
            score_cell = parts[2]

            # Skip header row
            if name.lower().startswith("category"):
                continue

            # Extract first number in score cell (if any)
            m = re.search(r"([0-9]+)", score_cell)
            if not m:
                continue

            try:
                value = float(m.group(1))
            except ValueError:
                continue

            if "total" in name.lower():
                raw_total = value
            else:
                clean_name = re.sub(r"\*+", "", name).strip()
                category_scores.append(CategoryScore(name=clean_name, score=value))

    return category_scores, raw_total


def parse_standards_table(filled_md: str) -> StandardsSummary:
    """
    Parse '## 2 Standards Comparison' table to count ✓ / ~ / ✗.
    """
    lines = filled_md.splitlines()
    in_section = False
    in_table = False
    present = partial = missing = 0
    missing_items: list[str] = []
    partial_items: list[str] = []
    total_items = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("## 2 Standards Comparison"):
            in_section = True
            continue
        if in_section:
            if stripped.startswith("---") or stripped.startswith("## "):
                break
            if stripped.startswith("| Standard Item"):
                in_table = True
                continue
            if in_table:
                if not stripped.startswith("|"):
                    continue
                parts = [p.strip() for p in stripped.split("|")]
                if len(parts) < 4:
                    continue
                # parts: ["", "Standard Item", "Status", "Notes", ""]
                name = parts[1]
                status = parts[2]
                if not name or name.lower().startswith("standard item"):
                    continue

                total_items += 1
                if "✓" in status:
                    present += 1
                elif "~" in status:
                    partial += 1
                    partial_items.append(name)
                elif "✗" in status or "x" == status.lower():
                    missing += 1
                    missing_items.append(name)

    return StandardsSummary(
        present=present,
        partial=partial,
        missing=missing,
        total_items=total_items,
        missing_items=missing_items,
        partial_items=partial_items,
    )


def parse_gaps(filled_md: str) -> GapSummary:
    """
    Parse '## 3 Gaps & Inconsistencies' bullets:
    - **Missing:**
    - **Inconsistent / conflicting:**
    - **Ambiguous:**
    """
    lines = filled_md.splitlines()
    in_section = False
    current_key = None
    buckets = {"missing": [], "inconsistent": [], "ambiguous": []}

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## 3 Gaps & Inconsistencies"):
            in_section = True
            continue
        if in_section:
            if stripped.startswith("## ") or stripped.startswith("---"):
                break

            # Headings
            if stripped.startswith("- **Missing:**"):
                current_key = "missing"
                # capture text on the same line (after the heading)
                extra = stripped.replace("- **Missing:**", "").strip(" -")
                if extra:
                    buckets["missing"].append(extra)
                continue
            if stripped.startswith("- **Inconsistent / conflicting:**"):
                current_key = "inconsistent"
                extra = stripped.replace("- **Inconsistent / conflicting:**", "").strip(" -")
                if extra:
                    buckets["inconsistent"].append(extra)
                continue
            if stripped.startswith("- **Ambiguous:**"):
                current_key = "ambiguous"
                extra = stripped.replace("- **Ambiguous:**", "").strip(" -")
                if extra:
                    buckets["ambiguous"].append(extra)
                continue

            # Bullet lines under the current key
            if current_key and stripped.startswith("- "):
                text = stripped[2:].strip()
                buckets[current_key].append(text)

    def join_or_none(lst: list[str]) -> Optional[str]:
        if not lst:
            return None
        return " ".join(lst)

    return GapSummary(
        missing=join_or_none(buckets["missing"]),
        inconsistent=join_or_none(buckets["inconsistent"]),
        ambiguous=join_or_none(buckets["ambiguous"]),
    )


def compute_score_from_total(raw_total: Optional[float], max_total: float = 30.0) -> Optional[float]:
    if raw_total is None:
        return None
    try:
        pct = (raw_total / max_total) * 100.0
        pct = max(0.0, min(100.0, pct))
        return pct
    except ZeroDivisionError:
        return None


def score_label(score: Optional[float]) -> Optional[str]:
    if score is None:
        return None
    if score >= 85:
        return "Excellent"
    if score >= 70:
        return "Good"
    if score >= 50:
        return "Fair"
    return "Poor"


# --------------------------------------------------------------------
# Route
# --------------------------------------------------------------------
@app.post("/grade", response_model=GradeResponse)
def grade(req: GradeRequest):
    if "huggingface.co" not in req.url:
        raise HTTPException(status_code=400, detail="Only Hugging Face URLs are supported")

    try:
        filled_md = run_card_evaluation(req.url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to evaluate model card: {e}")

    # Parse structured info
    basic_info = parse_basic_info(filled_md)
    category_scores, raw_total = parse_scoring_table(filled_md)
    standards_summary = parse_standards_table(filled_md)
    gaps = parse_gaps(filled_md)

    score = compute_score_from_total(raw_total, max_total=30.0)
    label = score_label(score)

    details = None
    if score is not None and raw_total is not None:
        details = f"Score parsed from scoring table: {raw_total:.0f}/30."
    else:
        details = "Could not parse score from scoring table."

    return GradeResponse(
        score=score,
        raw_total=raw_total,
        max_total=30.0,
        label=label,
        details=details,
        basic_info=basic_info,
        category_scores=category_scores or None,
        standards_summary=standards_summary,
        gaps=gaps,
        filled_markdown=filled_md,  # extension can show full audit
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("CARD_GRADER_PORT", "8000"))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
