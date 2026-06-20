import urllib.request
import urllib.error
import json
import subprocess

KEYCHAIN_SERVICE = "kindle-wallpapers"
KEYCHAIN_ACCOUNT = "readwise-token"
HIGHLIGHTS_URL = "https://readwise.io/api/v2/highlights/"
BOOKS_URL      = "https://readwise.io/api/v2/books/"


def save_token(token: str) -> None:
    """Store token in Keychain. macOS will prompt for confirmation on every read."""
    # Delete existing entry if present (ignore errors)
    subprocess.run(
        ["security", "delete-generic-password",
         "-s", KEYCHAIN_SERVICE, "-a", KEYCHAIN_ACCOUNT],
        capture_output=True,
    )
    subprocess.run(
        ["security", "add-generic-password",
         "-s", KEYCHAIN_SERVICE,
         "-a", KEYCHAIN_ACCOUNT,
         "-w", token.strip()],
        check=True,
    )


def load_token() -> str | None:
    """Read token from Keychain — triggers native macOS confirmation popup."""
    result = subprocess.run(
        ["security", "find-generic-password",
         "-s", KEYCHAIN_SERVICE,
         "-a", KEYCHAIN_ACCOUNT,
         "-w"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _paginate(url: str, token: str) -> list[dict]:
    results = []
    while url:
        req = urllib.request.Request(url, headers={"Authorization": f"Token {token}"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
        results.extend(data["results"])
        url = data.get("next")
    return results


def fetch_highlights() -> dict[str, dict]:
    """Fetch all highlights with book metadata, return in standard {hash: entry} format."""
    import hashlib

    token = load_token()
    if not token:
        return {}

    print("  fetching books ...")
    books_raw = _paginate(BOOKS_URL, token)
    books = {b["id"]: {"title": b.get("title", ""), "author": b.get("author", "")} for b in books_raw}

    print("  fetching highlights ...")
    highlights_raw = _paginate(HIGHLIGHTS_URL, token)

    result = {}
    for h in highlights_raw:
        text = (h.get("text") or "").strip()
        if not text or len(text.split()) <= 6:
            continue

        book   = books.get(h.get("book_id"), {})
        if "readwise" in book.get("title", "").lower():
            continue
        hash_  = hashlib.sha256(text.encode()).hexdigest()[:16]

        result[hash_] = {
            "hash":   hash_,
            "quote":  text,
            "title":  book.get("title", ""),
            "author": book.get("author", ""),
            "source": "readwise",
        }

    return result
