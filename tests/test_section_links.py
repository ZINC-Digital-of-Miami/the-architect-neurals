import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("section_links", Path(__file__).resolve().parents[1] / "scripts/check_section_links.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class SectionLinksTests(unittest.TestCase):
    def check_pages(self, pages):
        with tempfile.TemporaryDirectory() as directory:
            site = Path(directory)
            for name, markup in pages.items():
                path = site / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(markup)
            return checker.validate(site)

    def test_cross_page_and_encoded_section_links(self):
        errors, pages, links = self.check_pages({
            "index.html": '<h2 id="a-b">Chapter</h2><a href="topics/a.html#record">Record</a>',
            "topics/a.html": '<p id="record">Record</p><a href="../#a%2Db">Chapter</a>'})
        self.assertEqual((errors, pages, links), ([], 2, 2))

    def test_missing_page_and_missing_section_fail(self):
        errors, _, _ = self.check_pages({"index.html": '<a href="missing.html">Missing</a><a href="#lost">Lost</a>'})
        self.assertEqual(len(errors), 2)
        self.assertTrue(any("missing route" in error for error in errors))
        self.assertTrue(any("missing section" in error for error in errors))

    def test_duplicate_destinations_fail(self):
        errors, _, _ = self.check_pages({"index.html": '<h2 id="same">A</h2><h2 id="same">B</h2>'})
        self.assertEqual(len(errors), 1)
        self.assertIn("duplicate IDs", errors[0])
