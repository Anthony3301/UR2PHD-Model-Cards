# server.py
import os
import re
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from dotenv import load_dotenv, find_dotenv

# Load .env so OPENAI_API_KEY and OPENAI_MODEL work like in generate_eval.py
load_dotenv(find_dotenv(), override=False)

# Import your existing helpers
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

# Try to extract a numeric score from the filled markdown.
# Adjust this pattern to match your actual template.
SCORE_REGEX = re.compile(
    r"overall\s*score[^0-9]*([0-9]{1,3})",
    re.IGNORECASE,
)

app = FastAPI()

# Allow your Chrome extension to call us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can restrict later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GradeRequest(BaseModel):
    url: str


class GradeResponse(BaseModel):
    score: Optional[float] = None
    label: Optional[str] = None
    details: Optional[str] = None
    filled_markdown: Optional[str] = None


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


def extract_score(filled_md: str) -> Optional[float]:
    """Pull a numeric score out of the evaluation markdown."""
    m = SCORE_REGEX.search(filled_md)
    if not m:
        return None
    try:
        score = float(m.group(1))
        # clamp to 0–100 just in case
        score = max(0.0, min(100.0, score))
        return score
    except ValueError:
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


@app.post("/grade", response_model=GradeResponse)
def grade(req: GradeRequest):
    if "huggingface.co" not in req.url:
        raise HTTPException(status_code=400, detail="Only Hugging Face URLs are supported")

    try:
        filled_md = run_card_evaluation(req.url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to evaluate model card: {e}")

    score = extract_score(filled_md)
    label = score_label(score)

    # You can trim filled_md if you don't want to send everything
    return GradeResponse(
        score=score,
        label=label,
        details="Score parsed from evaluation template." if score is not None else "Could not parse score.",
        filled_markdown=None,  # set to filled_md if you want full content in the response
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("CARD_GRADER_PORT", "8000"))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)