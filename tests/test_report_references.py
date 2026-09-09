"""Regression tests for source-preserving report reference links."""

from html.parser import HTMLParser
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from report_references import link_report_references


TOC = [
    ("h3", "chapter-12", "Chapter 12: Purging Dissent"),
    ("h3", "chapter-13", "Chapter 13: Emergency Powers"),
    ("h3", "chapter-14", "Chapter 14: Enforcement"),
    ("h3", "chapter-21-b", "Chapter 21-B: The War"),
    ("h3", "chapter-c-2", "Chapter C-2: The Crypto Apparatus"),
    ("h2", "budget", "The Budget Architecture — Priorities Revealed"),
    ("h2", "appendix-a", "Appendix A — Method"),
    ("h2", "appendix-b", "Appendix B — Provenance"),
]
ALIASES = {"Chapter 21": "The Budget Architecture — Priorities Revealed"}


class TextCollector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def visible_text(markup):
    parser = TextCollector()
    parser.feed(markup)
    return "".join(parser.parts)


class ReportReferenceTests(unittest.TestCase):
    def test_links_known_reference_and_explicit_alias_without_changing_visible_text(self):
        source = '<p class="lede">See Chapter 12 and Chapter 21.</p>'
        linked, inventory = link_report_references(source, TOC, aliases=ALIASES)
        self.assertEqual(
            linked,
            '<p class="lede">See <a href="/#chapter-12">Chapter 12</a> and '
            '<a href="/#budget">Chapter 21</a>.</p>',
        )
        self.assertEqual(visible_text(linked), visible_text(source))
        self.assertEqual([item.label for item in inventory.resolved], ["Chapter 12", "Chapter 21"])
        self.assertEqual(inventory.unresolved, ())

    def test_links_compound_lists_ranges_and_mixed_chapter_codes(self):
        source = (
            "<p>Chapters 12, 13, and 21-B; Chapters 12–14; "
            "Chapter C-2 through Chapter 21-B.</p>"
        )
        linked, inventory = link_report_references(source, TOC)
        self.assertEqual(
            linked,
            '<p>Chapters <a href="/#chapter-12">12</a>, '
            '<a href="/#chapter-13">13</a>, and <a href="/#chapter-21-b">21-B</a>; '
            'Chapters <a href="/#chapter-12">12</a>–<a href="/#chapter-14">14</a>; '
            '<a href="/#chapter-c-2">Chapter C-2</a> through '
            '<a href="/#chapter-21-b">Chapter 21-B</a>.</p>',
        )
        self.assertEqual(visible_text(linked), visible_text(source))
        self.assertEqual(len(inventory.resolved), 7)

    def test_distinguishes_ascii_range_from_mixed_chapter_codes(self):
        source = "<p>Chapters 12-14, beside Chapter 21-B and Chapter C-2.</p>"
        linked, inventory = link_report_references(source, TOC)
        self.assertEqual(
            linked,
            '<p>Chapters <a href="/#chapter-12">12</a>-<a href="/#chapter-14">14</a>, '
            'beside <a href="/#chapter-21-b">Chapter 21-B</a> and '
            '<a href="/#chapter-c-2">Chapter C-2</a>.</p>',
        )
        self.assertEqual(visible_text(linked), visible_text(source))
        self.assertEqual(inventory.unresolved, ())

    def test_links_appendix_list_and_preserves_punctuation(self):
        source = "<p>See Appendices A and B; Appendix A, then Appendix B.</p>"
        linked, inventory = link_report_references(source, TOC)
        self.assertEqual(
            linked,
            '<p>See Appendices <a href="/#appendix-a">A</a> and '
            '<a href="/#appendix-b">B</a>; <a href="/#appendix-a">Appendix A</a>, '
            'then <a href="/#appendix-b">Appendix B</a>.</p>',
        )
        self.assertEqual(visible_text(linked), visible_text(source))
        self.assertEqual(len(inventory.resolved), 4)

    def test_preserves_raw_markup_entities_and_links_inside_inline_strong(self):
        source = (
            '<X-Card DATA-note="A&amp;B"><p>Read <strong>Chapter 12</strong> '
            '&amp; Appendix A.</p></X-Card>'
        )
        linked, _ = link_report_references(source, TOC)
        self.assertEqual(
            linked,
            '<X-Card DATA-note="A&amp;B"><p>Read <strong><a href="/#chapter-12">'
            'Chapter 12</a></strong> &amp; <a href="/#appendix-a">Appendix A</a>.'
            '</p></X-Card>',
        )
        self.assertEqual(visible_text(linked), visible_text(source))

    def test_skips_existing_links_headings_and_literal_code_contexts(self):
        source = (
            '<h3>Chapter 12: Purging Dissent</h3>'
            '<p><a href="/old">Chapter 12</a> <code>Chapter 12</code> '
            '<pre>Appendix A</pre><script>"Chapter 12"</script>'
            '<style>/* Appendix A */</style></p>'
        )
        linked, inventory = link_report_references(source, TOC)
        self.assertEqual(linked, source)
        self.assertEqual(inventory.resolved, ())
        self.assertEqual(inventory.unresolved, ())

    def test_leaves_unknown_and_ambiguous_named_references_unchanged_and_reports_them(self):
        duplicate_toc = TOC + [("h3", "other-12", "Chapter 12: A duplicate")]
        source = "<p>Chapter 12 and Chapter 999 remain named references.</p>"
        linked, inventory = link_report_references(source, duplicate_toc)
        self.assertEqual(linked, source)
        self.assertEqual(inventory.resolved, ())
        self.assertEqual([item.label for item in inventory.unresolved], ["Chapter 12", "Chapter 999"])

    def test_does_not_link_generic_uses_of_the_word_chapter(self):
        source = "<p>This chapter explains the result; the next chapter gives context.</p>"
        linked, inventory = link_report_references(source, TOC)
        self.assertEqual(linked, source)
        self.assertEqual(inventory.resolved, ())
        self.assertEqual(inventory.unresolved, ())

    def test_does_not_link_valid_prefixes_inside_longer_tokens(self):
        source = "<p>Chapter 12abc and Appendix ABC are not named section references.</p>"
        linked, inventory = link_report_references(source, TOC)
        self.assertEqual(linked, source)
        self.assertEqual(inventory.resolved, ())
        self.assertEqual(inventory.unresolved, ())

    def test_inventories_cross_inline_references_without_rewriting_markup(self):
        source = (
            "<p>Chapter <strong>12</strong>; Chapters 12 and <em>13</em>; "
            "Appendix <span>A</span>.</p>"
        )
        linked, inventory = link_report_references(source, TOC)
        self.assertEqual(
            linked,
            '<p>Chapter <strong>12</strong>; Chapters <a href="/#chapter-12">12</a> '
            'and <em>13</em>; Appendix <span>A</span>.</p>',
        )
        self.assertEqual(visible_text(linked), visible_text(source))
        self.assertEqual([item.label for item in inventory.resolved], ["Chapter 12"])
        self.assertEqual(
            [(item.label, item.reason) for item in inventory.unresolved],
            [("Chapter 12", "split_markup"), ("Chapter 13", "split_markup"),
             ("Appendix A", "split_markup")],
        )


if __name__ == "__main__":
    unittest.main()
