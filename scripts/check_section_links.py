#!/usr/bin/env python3
"""Check every published HTML route and its local navigation destinations."""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://the-architecture-neurals.vercel.app"


class Links(HTMLParser):
    def __init__(self, markup):
        super().__init__()
        self.ids, self.links = [], []
        self.feed(markup)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])


def validate(site):
    pages = {path.relative_to(site).as_posix(): Links(path.read_text())
             for path in site.rglob("*.html") if "src" not in path.relative_to(site).parts}
    errors, checked = [], 0
    for name, page in pages.items():
        duplicates = [key for key, count in Counter(page.ids).items() if count > 1]
        if duplicates:
            errors.append(f"{name}: duplicate IDs {duplicates}")
        for href in page.links:
            url = urlsplit(urljoin(ORIGIN + "/" + name, href))
            if url.scheme not in {"http", "https"} or url.netloc != urlsplit(ORIGIN).netloc:
                continue
            checked += 1
            destination = unquote(url.path).lstrip("/") or "index.html"
            if destination.endswith("/"):
                destination += "index.html"
            if not (site / destination).is_file():
                errors.append(f"{name}: missing route {href}")
            elif url.fragment and destination in pages and unquote(url.fragment) not in pages[destination].ids:
                errors.append(f"{name}: missing section {href}")
    return errors, len(pages), checked


if __name__ == "__main__":
    errors, pages, links = validate(ROOT / "site")
    if errors:
        raise SystemExit("SECTION LINKS FAILED:\n" + "\n".join(errors))
    print(f"SECTION LINKS: {pages} pages; {links} local links; zero duplicate IDs or missing destinations")
