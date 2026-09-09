import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from report_navigation import link_silence_clocks, repair_directional_references


class NavigationTests(unittest.TestCase):
    def setUp(self):
        self.source = (ROOT / "src/update_part2.html").read_text()
        self.targets = json.loads((ROOT / "src/report_reference_targets.json").read_text())["targets"]
        self.ids = {value["canonicalHref"][2:] for value in self.targets.values() if value["canonicalHref"]}

    def test_reviewed_destinations_and_all_authored_clock_bodies_preserved(self):
        result, inventory = link_silence_clocks(self.source, self.targets, self.ids)
        bodies = re.findall(r'<a class="clock"[^>]*>(.*?)</a>', self.source, re.S)
        self.assertEqual(len(bodies), 12)
        self.assertTrue(all(body in result for body in bodies))
        self.assertEqual(result.count('class="clock"'), 12)
        self.assertEqual(len(inventory), 11)
        self.assertEqual(result.count('data-reference-status="unresolved"'), 5)
        for row in inventory:
            if row["href"]:
                self.assertIn('href="' + row["href"] + '"', result)

    def test_missing_destination_fails(self):
        with self.assertRaisesRegex(ValueError, "Missing clock destination"):
            link_silence_clocks(self.source, self.targets, set())

    def test_source_drift_fails(self):
        with self.assertRaisesRegex(ValueError, "identities disappeared"):
            link_silence_clocks("", self.targets, self.ids)

    def test_archived_directions_link_to_correct_permanent_records(self):
        source = (ROOT / "src/briefs/2026-08-23.html").read_text()
        repaired = repair_directional_references(source, "briefs/2026-08-23.html")
        anchored = repair_directional_references(self.source, "update_part2.html")
        for code in ("C-010", "C-011", "C-012"):
            self.assertIn(f'href="/#correction-{code.lower()}"', repaired)
            self.assertEqual(anchored.count(f'id="correction-{code.lower()}"'), 1)
        self.assertNotIn("corrections below", repaired)
        self.assertNotIn("C-010 below", repaired)
        self.assertNotIn("corrected below", repaired)
        # Removing only the new IDs recovers the entire authored correction HTML.
        self.assertEqual(re.sub(r' id="correction-c-01[012]"', '', anchored), self.source)

    def test_source_archive_direction_and_source_drift(self):
        source = (ROOT / "src/sources_manifest.md").read_text()
        fixed = repair_directional_references(source, "sources_manifest.md")
        self.assertEqual(fixed.replace("Chapter 21-C in the main report", "Chapter 21-C below"), source)
        with self.assertRaisesRegex(ValueError, "needs review"):
            repair_directional_references("", "briefs/2026-08-23.html")


if __name__ == "__main__":
    unittest.main()
