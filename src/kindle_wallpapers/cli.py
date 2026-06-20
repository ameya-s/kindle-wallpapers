import re
import sys
import json
import shutil
import subprocess
from pathlib import Path

from .parser import parse_clippings
from .renderer import make_wallpaper
from .readwise import save_token, load_token, fetch_highlights

KINDLE_VOLUME   = Path("/Volumes/Kindle")
KINDLE_CLIPS    = KINDLE_VOLUME / "documents" / "My Clippings.txt"
DATA_DIR        = Path.home() / ".kindle-wallpapers"
CLIPPINGS_LOCAL = DATA_DIR / "My Clippings.txt"
HIGHLIGHTS_DB   = DATA_DIR / "highlights.json"
OUTPUT_DIR      = Path.home() / "Pictures" / "KindleWallpapers"


def _sync_clippings() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if KINDLE_VOLUME.exists() and KINDLE_CLIPS.exists():
        shutil.copy2(KINDLE_CLIPS, CLIPPINGS_LOCAL)
        print("✓ Synced clippings from Kindle")
    elif CLIPPINGS_LOCAL.exists():
        print("Kindle not connected — using last synced clippings")
    else:
        print("No Kindle connected and no local clippings found.")
        print(f"  Connect your Kindle, or copy My Clippings.txt to {DATA_DIR}")
        sys.exit(1)


def _load_db() -> dict:
    if HIGHLIGHTS_DB.exists():
        return json.loads(HIGHLIGHTS_DB.read_text())
    return {}


def _save_db(db: dict) -> None:
    HIGHLIGHTS_DB.write_text(json.dumps(db, indent=2, ensure_ascii=False))


def _ask_token_via_dialog() -> str | None:
    script = '''
    tell application "System Events"
        display dialog "Paste your Readwise API token:" \
            default answer "" with hidden answer \
            buttons {"Cancel", "Save"} default button "Save"
        return text returned of result
    end tell
    '''
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _setup():
    token = _ask_token_via_dialog()
    if not token:
        print("Cancelled.")
        return
    save_token(token)
    print("✓ Token saved to macOS Keychain")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        _setup()
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Kindle clippings
    _sync_clippings()
    all_highlights = parse_clippings(CLIPPINGS_LOCAL)

    # Readwise (if token is set)
    if load_token():
        print("Fetching Readwise highlights ...")
        rw = fetch_highlights()
        all_highlights.update(rw)
        print(f"  {len(rw)} highlights from Readwise")
    else:
        print("No Readwise token — run 'kindle-wallpapers setup' to add one")

    db = _load_db()
    new = {h: v for h, v in all_highlights.items() if h not in db}

    print(f"  {len(all_highlights)} total highlights  ·  {len(new)} new")

    if not new:
        print("Already up to date — no new wallpapers to generate.")
        return

    for i, (h, entry) in enumerate(new.items(), 1):
        slug = re.sub(r"[^\w]+", "_", entry["title"][:40]).strip("_").lower()
        fname = f"{h}_{slug}.png"
        print(f"  [{i}/{len(new)}] {entry['title'][:50]}")
        make_wallpaper(entry["quote"], entry["title"], entry["author"], OUTPUT_DIR / fname)
        db[h] = entry

    _save_db(db)

    print(f"\n✓ {len(new)} wallpapers saved to {OUTPUT_DIR}")
    if len(db) == len(new):
        print("\nFirst time setup:")
        print("  System Settings → Wallpaper → Add Folder → ~/Pictures/KindleWallpapers")
        print("  Enable shuffle and set your preferred rotation interval")
