"""Add verified report-section links without rewriting the surrounding HTML."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from html import escape, unescape
from html.parser import HTMLParser
import re
from typing import Iterable, Mapping, Sequence


_CODE = r"(?:\d+(?:-[A-Z][A-Z0-9]*)?|[A-Z](?:-[A-Z0-9]+)?)"
_HEADING = re.compile(rf"^\s*(Chapter|Appendix)\s+({_CODE})(?=\s|:|[—–])")
_TOKEN_END = r"(?![A-Za-z0-9]|-(?!\d))"
_REFERENCE = re.compile(rf"\b(Chapter|Chapters|Appendix|Appendices)(\s+)({_CODE}){_TOKEN_END}")
_CONTINUATION = re.compile(
    rf"(?P<separator>\s*(?:,\s*(?:and\s+)?|and\s+|through\s+|to\s+|[-—–]\s*))"
    rf"(?P<explicit>(?:(?:Chapter|Appendix)\s+)?)"
    rf"(?P<code>{_CODE}){_TOKEN_END}"
)
_SKIP_TAGS = frozenset({"a", "h1", "h2", "h3", "h4", "h5", "h6", "script", "style", "pre", "code"})
_BLOCK_TAGS = frozenset({
    "address", "article", "aside", "blockquote", "body", "caption", "dd", "div", "dl", "dt",
    "fieldset", "figcaption", "figure", "footer", "form", "header", "li", "main", "nav", "ol",
    "p", "section", "table", "tbody", "td", "tfoot", "th", "thead", "tr", "ul",
})


@dataclass(frozen=True)
class ReferenceOccurrence:
    """One named reference encountered in eligible visible text."""

    label: str
    heading_id: str | None = None
    href: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class ReferenceInventory:
    """Resolved and unresolved references, in document order."""

    resolved: tuple[ReferenceOccurrence, ...]
    unresolved: tuple[ReferenceOccurrence, ...]


def _reference_key(kind: str, code: str) -> tuple[str, str]:
    singular = "Appendix" if kind.lower().startswith("append") else "Chapter"
    return singular, code.upper()


def _display_label(key: tuple[str, str]) -> str:
    return f"{key[0]} {key[1]}"


def _toc_rows(toc: Sequence[tuple[str, str, str]] | Mapping[str, str]):
    if isinstance(toc, Mapping):
        for title, heading_id in toc.items():
            yield str(heading_id), str(title)
        return
    for row in toc:
        if len(row) != 3:
            raise ValueError("TOC rows must be (tag, heading_id, visible_heading_text)")
        _tag, heading_id, title = row
        yield str(heading_id), str(title)


def _build_targets(toc, aliases):
    label_ids: dict[tuple[str, str], list[str]] = defaultdict(list)
    title_ids: dict[str, list[str]] = defaultdict(list)
    all_ids: set[str] = set()
    for heading_id, title in _toc_rows(toc):
        all_ids.add(heading_id)
        title_ids[title].append(heading_id)
        match = _HEADING.match(title)
        if match:
            label_ids[_reference_key(match.group(1), match.group(2))].append(heading_id)

    targets: dict[tuple[str, str], str | None] = {
        key: ids[0] if len(set(ids)) == 1 else None for key, ids in label_ids.items()
    }
    for source_label, destination in (aliases or {}).items():
        match = _REFERENCE.fullmatch(source_label.strip())
        if not match or match.group(1) in {"Chapters", "Appendices"}:
            raise ValueError(f"alias key must be one singular named reference: {source_label!r}")
        key = _reference_key(match.group(1), match.group(3))
        if destination in all_ids:
            heading_id = destination
        else:
            ids = title_ids.get(destination, [])
            heading_id = ids[0] if len(set(ids)) == 1 else None
        if key in targets and targets[key] not in {None, heading_id}:
            raise ValueError(f"alias conflicts with TOC heading for {source_label!r}")
        targets[key] = heading_id
    return targets


class _ReferenceLinker(HTMLParser):
    def __init__(self, source: str, targets, href_prefix: str):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.targets = targets
        self.href_prefix = href_prefix
        self.output: list[str] = []
        self.stack: list[str] = []
        self.resolved: list[ReferenceOccurrence] = []
        self.unresolved: list[ReferenceOccurrence] = []
        self._visible_parts: list[str] = []
        self._visible_owners: list[int] = []
        self._text_node = 0
        starts = [0]
        starts.extend(match.end() for match in re.finditer("\n", source))
        self._line_starts = starts

    @property
    def excluded(self) -> bool:
        return any(tag in _SKIP_TAGS for tag in self.stack)

    def _source_offset(self) -> int:
        line, column = self.getpos()
        return self._line_starts[line - 1] + column

    def _raw_through(self, ending: str) -> str:
        start = self._source_offset()
        end = self.source.find(ending, start)
        if end < 0:
            return self.source[start:]
        return self.source[start : end + len(ending)]

    def handle_starttag(self, tag, attrs):
        lowered = tag.lower()
        if lowered in _BLOCK_TAGS or lowered in _SKIP_TAGS:
            self._flush_visible_run()
        self.output.append(self.get_starttag_text())
        self.stack.append(lowered)

    def handle_startendtag(self, tag, attrs):
        self.output.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        lowered = tag.lower()
        if lowered in _BLOCK_TAGS or lowered in _SKIP_TAGS:
            self._flush_visible_run()
        self.output.append(self._raw_through(">"))
        if self.stack and self.stack[-1] == lowered:
            self.stack.pop()
        elif lowered in self.stack:
            index = len(self.stack) - 1 - self.stack[::-1].index(lowered)
            del self.stack[index:]

    def handle_data(self, data):
        if not self.excluded:
            self._append_visible(data)
        self.output.append(data if self.excluded else self._link_text(data))

    def handle_entityref(self, name):
        if not self.excluded:
            self._append_visible(unescape(f"&{name};"))
        self.output.append(f"&{name};")

    def handle_charref(self, name):
        if not self.excluded:
            self._append_visible(unescape(f"&#{name};"))
        self.output.append(f"&#{name};")

    def handle_comment(self, data):
        self.output.append(self._raw_through("-->"))

    def handle_decl(self, decl):
        self.output.append(self._raw_through(">"))

    def handle_pi(self, data):
        self.output.append(self._raw_through(">"))

    def unknown_decl(self, data):
        self.output.append(self._raw_through(">"))

    def _append_visible(self, text: str):
        self._visible_parts.append(text)
        self._visible_owners.extend([self._text_node] * len(text))
        self._text_node += 1

    def _flush_visible_run(self):
        if not self._visible_parts:
            return
        text = "".join(self._visible_parts)
        owners = self._visible_owners
        cursor = 0
        while True:
            match = _REFERENCE.search(text, cursor)
            if not match:
                break
            word, _whitespace, code = match.groups()
            kind = "Appendix" if word.startswith("Append") else "Chapter"
            if len(set(owners[match.start() : match.end()])) > 1:
                key = _reference_key(kind, code)
                self.unresolved.append(ReferenceOccurrence(label=_display_label(key), reason="split_markup"))
            cursor = match.end()
            if word not in {"Chapters", "Appendices"}:
                continue
            while True:
                continuation = _CONTINUATION.match(text, cursor)
                if not continuation:
                    break
                if len(set(owners[cursor : continuation.end()])) > 1:
                    explicit = continuation.group("explicit")
                    next_kind = explicit.strip().split()[0] if explicit else kind
                    key = _reference_key(next_kind, continuation.group("code"))
                    self.unresolved.append(ReferenceOccurrence(label=_display_label(key), reason="split_markup"))
                cursor = continuation.end()
        self._visible_parts = []
        self._visible_owners = []

    def _linked(self, raw_text: str, key: tuple[str, str]) -> str:
        label = _display_label(key)
        if key not in self.targets:
            self.unresolved.append(ReferenceOccurrence(label=label, reason="unknown"))
            return raw_text
        heading_id = self.targets[key]
        if heading_id is None:
            self.unresolved.append(ReferenceOccurrence(label=label, reason="ambiguous"))
            return raw_text
        href = f"{self.href_prefix}{heading_id}"
        self.resolved.append(ReferenceOccurrence(label=label, heading_id=heading_id, href=href))
        return f'<a href="{escape(href, quote=True)}">{raw_text}</a>'

    def _link_text(self, data: str) -> str:
        output: list[str] = []
        cursor = 0
        while True:
            match = _REFERENCE.search(data, cursor)
            if not match:
                output.append(data[cursor:])
                return "".join(output)
            output.append(data[cursor : match.start()])
            word, whitespace, code = match.groups()
            plural = word in {"Chapters", "Appendices"}
            kind = "Appendix" if word.startswith("Append") else "Chapter"
            key = _reference_key(kind, code)
            if plural:
                output.append(word + whitespace)
                output.append(self._linked(code, key))
            else:
                output.append(self._linked(match.group(0), key))
            cursor = match.end()

            if not plural:
                continue
            while True:
                continuation = _CONTINUATION.match(data, cursor)
                if not continuation:
                    break
                explicit = continuation.group("explicit")
                next_code = continuation.group("code")
                next_kind = explicit.strip().split()[0] if explicit else kind
                next_key = _reference_key(next_kind, next_code)
                output.append(continuation.group("separator"))
                raw_reference = explicit + next_code
                output.append(self._linked(raw_reference, next_key))
                cursor = continuation.end()


def link_report_references(
    html_text: str,
    toc: Sequence[tuple[str, str, str]] | Mapping[str, str],
    *,
    aliases: Mapping[str, str] | None = None,
    href_prefix: str = "/#",
) -> tuple[str, ReferenceInventory]:
    """Link named report references that resolve to caller-supplied heading IDs.

    Unknown or ambiguous labels remain byte-for-byte unchanged and are returned in
    the inventory. Existing links, headings, scripts, styles, preformatted text,
    and code are never inspected for references.
    """

    targets = _build_targets(toc, aliases)
    parser = _ReferenceLinker(html_text, targets, href_prefix)
    parser.feed(html_text)
    parser.close()
    parser._flush_visible_run()
    return "".join(parser.output), ReferenceInventory(
        resolved=tuple(parser.resolved), unresolved=tuple(parser.unresolved)
    )
