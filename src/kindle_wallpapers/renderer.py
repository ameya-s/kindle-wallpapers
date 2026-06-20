import re
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def _detect_screen() -> tuple[int, int]:
    try:
        out = subprocess.check_output(
            ["system_profiler", "SPDisplaysDataType"],
            stderr=subprocess.DEVNULL, text=True
        )
        matches = re.findall(r"Resolution:\s*(\d+)\s*x\s*(\d+)", out)
        if matches:
            return max((int(w), int(h)) for w, h in matches)
    except Exception:
        pass
    return 2560, 1600  # sensible fallback


WIDTH, HEIGHT = _detect_screen()

BG_COLOR       = "#FDFAF5"
TEXT_COLOR     = "#1C1C1C"
ATTR_COLOR     = "#888880"
RULE_COLOR     = "#D4CFCA"
MARK_COLOR     = "#C8C0B8"

PADDING        = 320
MAX_TEXT_WIDTH = WIDTH - PADDING * 2
LINE_GAP       = 28
QUOTE_SIZE     = 82
ATTR_SIZE      = 52
MARK_SIZE      = 260

_FONT_SEARCH_DIRS = [
    "/System/Library/Fonts/Supplemental",
    "/Library/Fonts",
    str(Path.home() / "Library/Fonts"),
]


def _find_font(*names: str) -> str | None:
    for name in names:
        for d in _FONT_SEARCH_DIRS:
            p = Path(d) / name
            if p.exists():
                return str(p)
    return None


def _get_fonts():
    italic = _find_font("Georgia Italic.ttf", "Georgia.ttf", "DejaVuSerif-Italic.ttf")
    regular = _find_font("Georgia.ttf", "DejaVuSerif.ttf")
    decorative = regular
    return italic, regular, decorative


def _wrap(text: str, font: ImageFont.FreeTypeFont) -> list[str]:
    dummy = Image.new("RGB", (1, 1))
    d = ImageDraw.Draw(dummy)
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
    italic_path, regular_path, _ = _get_fonts()

    q_font = ImageFont.truetype(italic_path, QUOTE_SIZE) if italic_path else ImageFont.load_default()
    a_font = ImageFont.truetype(regular_path, ATTR_SIZE) if regular_path else ImageFont.load_default()
    m_font = ImageFont.truetype(regular_path, MARK_SIZE) if regular_path else ImageFont.load_default()

    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    q_lines = _wrap(quote, q_font)
    qlh = q_font.getbbox("Ag")[3] - q_font.getbbox("Ag")[1]
    q_height = qlh * len(q_lines) + LINE_GAP * (len(q_lines) - 1)

    attr_parts = [p for p in [title, author] if p]
    attr_text = f"— {' · '.join(attr_parts)}" if attr_parts else ""
    alh = a_font.getbbox("Ag")[3] - a_font.getbbox("Ag")[1]

    RULE_GAP = 60
    ATTR_GAP = 40
    total_h = q_height + RULE_GAP + 2 + ATTR_GAP + alh
    y = (HEIGHT - total_h) // 2

    mark_h = m_font.getbbox(""")[3] - m_font.getbbox(""")[1]
    draw.text((PADDING - 20, y - mark_h // 2 - 10), "“", font=m_font, fill=MARK_COLOR)

    for line in q_lines:
        lw = draw.textlength(line, font=q_font)
        draw.text(((WIDTH - lw) // 2, y), line, font=q_font, fill=TEXT_COLOR)
        y += qlh + LINE_GAP

    y += RULE_GAP - LINE_GAP
    draw.line([(PADDING + 120, y), (WIDTH - PADDING - 120, y)], fill=RULE_COLOR, width=2)
    y += 2 + ATTR_GAP

    if attr_text:
        aw = draw.textlength(attr_text, font=a_font)
        draw.text(((WIDTH - aw) // 2, y), attr_text, font=a_font, fill=ATTR_COLOR)

    img.save(out_path, "PNG", optimize=True)
