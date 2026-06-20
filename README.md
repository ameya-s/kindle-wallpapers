# kindle-wallpapers

You have a lot of good stuff highlighted on your Kindle. You never go back to read it.

This turns every highlight into a desktop wallpaper. macOS rotates through them. Good ideas show up on their own.

![example wallpaper](docs/example.png)

---

## install

Not on PyPI yet — install directly from GitHub:

```bash
pip install git+https://github.com/ameya-s/kindle-wallpapers.git
```

## setup

First, connect your Readwise account — this pulls all your highlights across every device (Kindle, phone, tablet, Mac app):

```bash
kindle-wallpapers setup
```

Paste your API token from [readwise.io/access_token](https://readwise.io/access_token) when prompted. Stored in macOS Keychain, not in any file.

## run

```bash
kindle-wallpapers
```

First run generates a wallpaper for every highlight (>5 words). Subsequent runs only process new ones.

Optionally, plug in your Kindle before running — the script will also sync `My Clippings.txt` directly off the device and merge any highlights not already in Readwise.

Wallpapers land in `~/Pictures/KindleWallpapers/`.

## set up rotation (macOS)

System Settings → Wallpaper → Add Folder → select `~/Pictures/KindleWallpapers`

Turn on shuffle. Set whatever interval you like.

---

## how it works

The script pulls highlights from two sources:

**Readwise** — fetches all your highlights via the Readwise API, with book titles and authors resolved automatically. This covers highlights made on any device.

**My Clippings.txt** — if a Kindle is connected via USB, the script copies this file off the device and parses it as a secondary source. Useful for highlights that haven't synced to Readwise yet.

Both sources are merged. Every highlight gets hashed and tracked in `~/.kindle-wallpapers/highlights.json` — so on subsequent runs, only new highlights get rendered.

For each new highlight, it generates a PNG at your display's native resolution — quote in Georgia Italic, book title and author as attribution below a thin rule, ghost quotation mark in the corner. Warm off-white background, near-black text.

Those PNGs go into `~/Pictures/KindleWallpapers/`. macOS wallpaper rotation does the rest.
