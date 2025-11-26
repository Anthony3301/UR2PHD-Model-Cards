
"""
Generate a filled card evaluation from a URL using OpenAI's API.

Usage:
  python src/generate_eval.py \
      --url https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct \
      --template templates/card_review_template.md \
      --outdir evaluations \
      --model gpt-4o

Env:
  OPENAI_API_KEY must be set.
"""

import os
import re
import sys
import time
import argparse
import pathlib
import textwrap
from typing import Optional

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), override=False)  


try:
    import requests
except ImportError as e:
    print("Please `pip install requests`", file=sys.stderr)
    raise

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except Exception:
    HAS_BS4 = False


try:
    from openai import OpenAI
except ImportError:
    print("Please `pip install openai` (official OpenAI Python SDK).", file=sys.stderr)
    raise


MAX_INPUT_CHARS = 150_000 
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


def fetch_url_text(url: str) -> str:
    """Fetch URL and return lightly cleaned text (HTML stripped if bs4 present)."""
    headers = {
        "User-Agent": "card-review-bot/1.0 (+https://github.com/your-org)"
    }
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()

    content_type = resp.headers.get("Content-Type", "").lower()
    text = resp.text

    if "html" in content_type and HAS_BS4:
        soup = BeautifulSoup(text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
        text = "\n".join(line.strip() for line in text.splitlines() if line.strip())

        if len(text) > MAX_INPUT_CHARS:
            text = text[:MAX_INPUT_CHARS] + "\n...[truncated]..."

    # focus on the model card section if possible
    # text = focus_on_model_card(text)

    return text


def load_template(path: str) -> str:
    p = pathlib.Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Template not found: {path}")
    return p.read_text(encoding="utf-8")


def sanitize_filename(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"https?://", "", s)
    s = re.sub(r"[^a-z0-9._/-]+", "-", s)
    s = s.strip("-")
    s = s.replace("/", "_")
    if not s:
        s = "card"
    return s[:120]


def build_prompt(template_md: str, url: str, page_text: str) -> dict:
    system = (
        "You are an AI transparency reviewer evaluating model cards on Hugging Face.\n"
        "You MUST obey all of the following rules:\n"
        "1. Fill the provided Markdown template EXACTLY AS-IS.\n"
        "   - Do not add, remove, or rename any sections, headings, or tables.\n"
        "   - Keep the same ordering and formatting of headings and table columns.\n"
        "2. You may ONLY use information that comes from the provided PAGE TEXT or the URL.\n"
        "   - Do NOT use outside knowledge, training data, or assumptions.\n"
        "   - If something is not clearly supported by PAGE TEXT, treat it as unknown.\n"
        "3. If a field is unknown or not specified in PAGE TEXT:\n"
        "   - Leave it blank, or write a very short note like 'N/A – not specified in model card text'.\n"
        "   - Do NOT guess, infer, or hallucinate plausible details.\n"
        "4. For the scoring table:\n"
        "   - Each category score MUST be an integer 0, 1, 2, or 3.\n"
        "   - The 'Total (/30)' MUST equal the sum of all category scores.\n"
        "5. For the standards comparison table:\n"
        "   - Use only '✓', '~', or '✗' as statuses.\n"
        "6. Do not output anything outside the template boundaries."
    )

    user = textwrap.dedent(f"""
    TEMPLATE (fill exactly, keep headings/format identical):
    ---
    {template_md}
    ---

    CONTEXT (URL + scraped text):
    URL: {url}

    IMPORTANT: All facts MUST be supported by the PAGE TEXT below.
    If unsure, leave fields blank or mark them as 'N/A – not specified in model card text'.

    PAGE TEXT (possibly truncated):
    """) + page_text

    return {"system": system, "user": user}


def call_openai_with_fallback(
    client: OpenAI, model: str, system: str, user: str, retries: int = 3
) -> str:
    last_err: Optional[Exception] = None
    for attempt in range(retries):
        try:
            # Primary path: Responses API
            resp = client.responses.create(
                model=model,
                instructions=system,
                input=user,
                temperature=0.0,  # fully deterministic
            )
            return resp.output_text
        except Exception as e:
            last_err = e
            # Fallback: Chat Completions
            try:
                chat = client.chat.completions.create(
                    model=model,
                    temperature=0.0,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                )
                return chat.choices[0].message.content
            except Exception as e2:
                last_err = e2
                time.sleep(1.5 * (attempt + 1))
                continue

    raise RuntimeError(f"OpenAI call failed after {retries} attempts: {last_err}")

def write_output(outdir: str, url: str, md_text: str) -> str:
    pathlib.Path(outdir).mkdir(parents=True, exist_ok=True)
    fname = f"{sanitize_filename(url)}.md"
    outpath = pathlib.Path(outdir) / fname
    outpath.write_text(md_text, encoding="utf-8")
    return str(outpath)

def focus_on_model_card(text: str) -> str:
    """
    Try to focus the context on the 'Model card' section of a Hugging Face page.
    If we don't find such a marker, return the original text.
    """
    lowered = text.lower()
    markers = ["model card", "modelcard", "model description"]  # tweak as needed

    idx = -1
    for marker in markers:
        idx = lowered.find(marker)
        if idx != -1:
            break

    if idx == -1:
        return text  # fallback: can't find a clear marker

    # Keep some context before and after the marker
    start = max(0, idx - 3000)
    end = min(len(text), idx + 50_000)
    return text[start:end]

def main():
    parser = argparse.ArgumentParser(description="Fill AI card template from a URL.")
    parser.add_argument("--url", required=True, help="URL of the model/dataset card")
    parser.add_argument("--template", default="templates/card_review_template.md",
                        help="Path to the Markdown template")
    parser.add_argument("--outdir", default="evaluations", help="Output folder")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="OpenAI model (e.g., gpt-4o)")
    parser.add_argument("--no-fetch", action="store_true",
                        help="Do not fetch page text; only send URL + template")
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY is not set.", file=sys.stderr)
        sys.exit(1)

    template_md = load_template(args.template)
    page_text = ""
    if not args.no_fetch:
        try:
            page_text = fetch_url_text(args.url)
        except Exception as e:
            print(f"Warning: failed to fetch URL text ({e}). Continuing with URL only.", file=sys.stderr)
            page_text = ""

    prompt = build_prompt(template_md, args.url, page_text)
    client = OpenAI(api_key=api_key)

    filled_md = call_openai_with_fallback(
        client=client,
        model=args.model,
        system=prompt["system"],
        user=prompt["user"],
    )

    outpath = write_output(args.outdir, args.url, filled_md)
    print(f"✔ Wrote: {outpath}")

if __name__ == "__main__":
    main()
