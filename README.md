# kindle-wallpapers

You have a lot of good stuff highlighted on your Kindle. You never go back to read it.

This turns every highlight into a desktop wallpaper. macOS rotates through them. Good ideas show up on their own.

![example wallpaper](docs/example.png)

---

## install

```bash
pip install kindle-wallpapers
```

## run

1. Connect your Kindle to your Mac via USB
2. Wait for it to appear in Finder (shows up as "Kindle" under Locations)
3. Run:

```bash
kindle-wallpapers
```

That's it. First run generates a wallpaper for every highlight (>5 words). Subsequent runs only process new ones.

Wallpapers land in `~/Pictures/KindleWallpapers/`.

## set up rotation (macOS)

System Settings → Wallpaper → Add Folder → select `~/Pictures/KindleWallpapers`

Turn on shuffle. Set whatever interval you like.

---

**No Kindle connected?** The script falls back to the last synced clippings file, so it still works.

Data lives in `~/.kindle-wallpapers/` — highlights database and a local copy of your clippings.
