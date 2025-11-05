
"""
Generate a filled card evaluation from a URL using OpenAI's API.

Usage:
  python src/generate_card_review.py \
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
        "You are an expert AI transparency reviewer. "
        "Fill the provided Markdown template EXACTLY AS-IS: "
        "do not add, remove, or rename any sections or headings; "
        "only insert content where there are blanks. "
        "Do not include any prose outside the template. "
        "If a field is unknown from the provided content, leave it blank or write a short 'N/A' note. "
        "Keep links as Markdown links when possible."
    )
    user = textwrap.dedent(f"""
    TEMPLATE (fill exactly, keep headings/format identical):
    ---
    {template_md}
    ---

    CONTEXT (URL + scraped text):
    URL: {url}

    PAGE TEXT (possibly truncated):
    """
    ) + page_text

    return {"system": system, "user": user}


def call_openai_with_fallback(
    client: OpenAI, model: str, system: str, user: str, retries: int = 3
) -> str:
    last_err: Optional[Exception] = None
    for attempt in range(retries):
        try:
            resp = client.responses.create(
                model=model,
                instructions=system,
                input=user,
                temperature=0.2,
            )
            return resp.output_text
        except Exception as e:
            last_err = e
            try:
                chat = client.chat.completions.create(
                    model=model,
                    temperature=0.2,
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
