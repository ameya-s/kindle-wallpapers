#!/usr/bin/env python3
"""
Kindle Wallpaper Generator

First run  : parses all highlights >5 words, builds highlights.json, generates all wallpapers.
Subsequent : syncs clippings from Kindle if connected, merges new highlights, generates only new wallpapers.
"""

import re
import sys
import json
import shutil
import hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR        = Path(__file__).parent
CLIPPINGS_LOCAL = BASE_DIR / "My Clippings.txt"
HIGHLIGHTS_DB   = BASE_DIR / "highlights.json"
OUTPUT_DIR      = Path.home() / "Pictures" / "KindleWallpapers"
KINDLE_VOLUME   = Path("/Volumes/Kindle")
KINDLE_CLIPS    = KINDLE_VOLUME / "documents" / "My Clippings.txt"

# ── Canvas ───────────────────────────────────────────────────────────────────
WIDTH, HEIGHT   = 3456, 2234

# ── Palette ──────────────────────────────────────────────────────────────────
BG_COLOR        = "#FDFAF5"
TEXT_COLOR      = "#1C1C1C"
ATTR_COLOR      = "#888880"
RULE_COLOR      = "#D4CFCA"
MARK_COLOR      = "#C8C0B8"

# ── Layout ───────────────────────────────────────────────────────────────────
PADDING         = 320
MAX_TEXT_WIDTH  = WIDTH - PADDING * 2

# ── Fonts ────────────────────────────────────────────────────────────────────
GEORGIA         = "/System/Library/Fonts/Supplemental/Georgia.ttf"
GEORGIA_ITALIC  = "/System/Library/Fonts/Supplemental/Georgia Italic.ttf"

QUOTE_SIZE      = 82
ATTR_SIZE       = 52
MARK_SIZE       = 260
LINE_GAP        = 28

MIN_WORDS       = 6


# ── Kindle sync ──────────────────────────────────────────────────────────────

def sync_clippings() -> bool:
    """Copy clippings from Kindle if connected. Returns True if synced."""
    if KINDLE_VOLUME.exists() and KINDLE_CLIPS.exists():
        shutil.copy2(KINDLE_CLIPS, CLIPPINGS_LOCAL)
        print(f"Synced clippings from Kindle → {CLIPPINGS_LOCAL}")
        return True
    if not CLIPPINGS_LOCAL.exists():
        print("No Kindle connected and no local clippings file found.")
        print(f"  Connect your Kindle, or place My Clippings.txt in {BASE_DIR}")
        sys.exit(1)
    print("Kindle not connected — using local clippings file.")
    return False


# ── Parsing ──────────────────────────────────────────────────────────────────

def _hash(text: str) -> str:
    return hashlib.sha256(text.strip().encode()).hexdigest()[:16]


def parse_clippings(path: Path) -> dict[str, dict]:
    """Parse clippings file → {hash: {quote, title, author, hash}}."""
    text   = path.read_text(encoding="utf-8-sig")
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

        raw_title  = lines[0].lstrip("﻿").strip()
        quote      = " ".join(lines[meta_idx + 1:]).strip()

        if len(quote.split()) <= MIN_WORDS:
            continue

        m = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", raw_title)
        if m:
            title  = m.group(1).strip().strip(",")
            author = m.group(2).strip()
            parts  = [p.strip() for p in author.split(",")]
            author = f"{parts[1]} {parts[0]}" if len(parts) == 2 else author
        else:
            title, author = raw_title, ""

        h = _hash(quote)
        result[h] = {"hash": h, "quote": quote, "title": title, "author": author}

    return result


# ── JSON database ─────────────────────────────────────────────────────────────

def load_db() -> dict:
    if HIGHLIGHTS_DB.exists():
        return json.loads(HIGHLIGHTS_DB.read_text())
    return {}


def save_db(db: dict) -> None:
    HIGHLIGHTS_DB.write_text(json.dumps(db, indent=2, ensure_ascii=False))


# ── Image generation ──────────────────────────────────────────────────────────

def _wrap(text: str, font: ImageFont.FreeTypeFont) -> list[str]:
    dummy = Image.new("RGB", (1, 1))
    d     = ImageDraw.Draw(dummy)
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = f"{current} {word}".strip()
        if d.textlength(test, font=font) <= MAX_TEXT_WIDTH:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def make_wallpaper(quote: str, title: str, author: str, out_path: Path) -> None:
    img  = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    q_font = ImageFont.truetype(GEORGIA_ITALIC, QUOTE_SIZE)
    a_font = ImageFont.truetype(GEORGIA, ATTR_SIZE)
    m_font = ImageFont.truetype(GEORGIA, MARK_SIZE)

    q_lines  = _wrap(quote, q_font)
    qlh      = q_font.getbbox("Ag")[3] - q_font.getbbox("Ag")[1]
    q_height = qlh * len(q_lines) + LINE_GAP * (len(q_lines) - 1)

    attr_parts = [p for p in [title, author] if p]
    attr_text  = f"— {' · '.join(attr_parts)}" if attr_parts else ""
    alh        = a_font.getbbox("Ag")[3] - a_font.getbbox("Ag")[1]

    RULE_GAP = 60
    ATTR_GAP = 40
    total_h  = q_height + RULE_GAP + 2 + ATTR_GAP + alh
    y        = (HEIGHT - total_h) // 2

    # ghost opening-quote mark
    mark_h = m_font.getbbox(""")[3] - m_font.getbbox(""")[1]
    draw.text((PADDING - 20, y - mark_h // 2 - 10), "“", font=m_font, fill=MARK_COLOR)

    # quote lines
    for line in q_lines:
        lw = draw.textlength(line, font=q_font)
        draw.text(((WIDTH - lw) // 2, y), line, font=q_font, fill=TEXT_COLOR)
        y += qlh + LINE_GAP

    # rule
    y += RULE_GAP - LINE_GAP
    draw.line([(PADDING + 120, y), (WIDTH - PADDING - 120, y)], fill=RULE_COLOR, width=2)
    y += 2 + ATTR_GAP

    # attribution
    if attr_text:
        aw = draw.textlength(attr_text, font=a_font)
        draw.text(((WIDTH - aw) // 2, y), attr_text, font=a_font, fill=ATTR_COLOR)

    img.save(out_path, "PNG", optimize=True)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    sync_clippings()

    print(f"Parsing {CLIPPINGS_LOCAL} ...")
    all_highlights = parse_clippings(CLIPPINGS_LOCAL)
    print(f"  {len(all_highlights)} highlights with >{MIN_WORDS - 1} words")

    db  = load_db()
    new = {h: v for h, v in all_highlights.items() if h not in db}

    if not new:
        print("No new highlights — wallpapers are up to date.")
        return

    print(f"  {len(new)} new highlights to render")

    for i, (h, entry) in enumerate(new.items(), 1):
        slug  = re.sub(r"[^\w]+", "_", entry["title"][:40]).strip("_").lower()
        fname = f"{h}_{slug}.png"
        out   = OUTPUT_DIR / fname
        print(f"  [{i}/{len(new)}] {fname}")
        make_wallpaper(entry["quote"], entry["title"], entry["author"], out)
        db[h] = entry

    save_db(db)
    print(f"\nDone. {len(new)} new wallpapers → {OUTPUT_DIR}")
    print(f"Database: {len(db)} total highlights tracked in {HIGHLIGHTS_DB.name}")


if __name__ == "__main__":
    main()
