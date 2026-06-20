import re
import hashlib
from pathlib import Path

MIN_WORDS = 6


def _hash(text: str) -> str:
    return hashlib.sha256(text.strip().encode()).hexdigest()[:16]


def parse_clippings(path: Path) -> dict[str, dict]:
    """Parse My Clippings.txt → {hash: {quote, title, author, hash}}."""
    text = path.read_text(encoding="utf-8-sig")
    result = {}

    for entry in text.split("=========="):
        lines = [l.strip() for l in entry.strip().splitlines() if l.strip()]
        if len(lines) < 3:
            continue

        meta_idx = next(
            (i for i, l in enumerate(lines) if l.startswith("- Your Highlight")),
            None,
        )
        if meta_idx is None:
            continue

        raw_title = lines[0].lstrip("﻿").strip()
        quote = " ".join(lines[meta_idx + 1:]).strip()

        if len(quote.split()) <= MIN_WORDS:
            continue

        m = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", raw_title)
        if m:
            title = m.group(1).strip().strip(",")
            author = m.group(2).strip()
            parts = [p.strip() for p in author.split(",")]
            author = f"{parts[1]} {parts[0]}" if len(parts) == 2 else author
        else:
            title, author = raw_title, ""

        h = _hash(quote)
        result[h] = {"hash": h, "quote": quote, "title": title, "author": author}

    return result
