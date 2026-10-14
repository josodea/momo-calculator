#!/usr/bin/env python3
"""Strip the Word/MIME wrapper from the exported HTML and save a clean HTML file.

Usage:
    python clean_word_html.py

This safely leaves the original index.html untouched and writes a cleaned version to
index.cleaned.html.
"""

from __future__ import annotations

import re
from email import policy
from email.parser import BytesParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "index.html"
OUT = ROOT / "index.cleaned.html"


def decode_part(part) -> str:
    payload = part.get_payload(decode=True)
    if payload is None:
        payload = part.get_payload() or ""

    if isinstance(payload, bytes):
        charset = part.get_content_charset() or "utf-8"
        try:
            return payload.decode(charset, errors="replace")
        except (LookupError, UnicodeDecodeError):
            return payload.decode("utf-8", errors="replace")

    return str(payload)


def extract_html(raw: str) -> str:
    # Prefer the actual HTML document if the file is a multipart MIME export.
    match = re.search(r"<html[\s\S]*?</html>", raw, flags=re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(0)

    # Fallback: if no explicit root tag exists, return the cleaned content as-is.
    return raw


def main() -> None:
    if not SRC.exists():
        raise FileNotFoundError(f"Source file not found: {SRC}")

    raw = SRC.read_bytes()
    msg = BytesParser(policy=policy.default).parsebytes(raw)

    html_parts: list[str] = []
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            text = decode_part(part)
            if "<html" in text.lower():
                html_parts.append(extract_html(text))

    if not html_parts:
        text = raw.decode("utf-8", errors="replace")
        html_parts.append(extract_html(text))

    final_html = html_parts[0] if html_parts else "<html><body></body></html>"

    # Light cleanup: remove Word-export comments and collapse excess whitespace.
    final_html = re.sub(r"<!\-\-.*?\-\->", "", final_html, flags=re.DOTALL)
    final_html = re.sub(r">\s+<", "><", final_html)
    final_html = re.sub(r"\s{2,}", " ", final_html)

    OUT.write_text(final_html, encoding="utf-8")
    print(f"Saved cleaned HTML to {OUT}")


if __name__ == "__main__":
    main()
