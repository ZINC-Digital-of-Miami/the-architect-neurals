"""Apply reviewed navigation corrections without editing authored research."""
import html
import re


def repair_directional_references(markup, source):
    """Correct four obsolete layout directions; preserve the original source files."""
    if source == "update_part2.html":
        for code in ("C-010", "C-011", "C-012"):
            pattern = r'<div class="correction">(?=<div class="mono">[^<]*\b' + code + r'\b)'
            markup, count = re.subn(pattern, f'<div class="correction" id="correction-{code.lower()}">', markup)
            if count != 1:
                raise ValueError(f"Correction anchor needs review: {code}")
    replacements = {
        "briefs/2026-08-23.html": (
            ("Both are logged as corrections below.",
             'Both are logged in the permanent Corrections Log: <a href="/#correction-c-010">C-010</a> and <a href="/#correction-c-011">C-011</a>.'),
            ("Correction C-010 below carries the precise form.",
             '<a href="/#correction-c-010">Correction C-010 in the permanent Corrections Log</a> carries the precise form.'),
            ("both are corrected below.",
             'both are corrected in <a href="/#correction-c-012">C-012 in the permanent Corrections Log</a>.'),
        ),
        "sources_manifest.md": (("Chapter 21-C below", "Chapter 21-C in the main report"),),
    }
    for old, new in replacements.get(source, ()):
        if markup.count(old) != 1:
            raise ValueError(f"Archived navigation wording needs review: {source}: {old}")
        markup = markup.replace(old, new, 1)
    return markup


def link_silence_clocks(markup, targets, report_ids):
    seen = set()
    inventory = []

    def replace(match):
        opening, old_href, body = match.groups()
        visible = html.unescape(re.sub(r"<[^>]+>", "", body))
        matches = [key for key in targets if key in visible]
        if not matches:
            return match.group(0)
        if len(matches) != 1 or matches[0] in seen:
            raise ValueError("Silence-clock identity is ambiguous or repeated")
        key = matches[0]
        seen.add(key)
        target = targets[key]
        if old_href != target["currentHref"]:
            raise ValueError(f"Silence-clock source changed: {key}")
        status, href = target["status"], target["canonicalHref"]
        inventory.append({"identity": key, "status": status, "href": href})
        if status == "unresolved":
            if href is not None:
                raise ValueError(f"Unresolved clock has a destination: {key}")
            return ('<div class="clock" data-reference-status="unresolved">' + body
                    + '<p class="clock-reference-note">Supporting section not linked</p></div>')
        if status not in {"resolved", "keep_existing"} or not href or not href.startswith("/#"):
            raise ValueError(f"Invalid clock destination: {key}")
        if href[2:] not in report_ids:
            raise ValueError(f"Missing clock destination: {href}")
        return opening.replace('href="' + old_href + '"', 'href="' + html.escape(href, quote=True) + '"') + body + '</a>'

    result = re.sub(r'(<a class="clock" href="([^"]+)">)(.*?)</a>', replace, markup, flags=re.S)
    if seen != set(targets):
        raise ValueError("Reviewed silence-clock identities disappeared: " + ", ".join(sorted(set(targets) - seen)))
    return result, inventory
