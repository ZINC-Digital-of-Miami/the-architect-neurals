"""The midterms route must survive generation, navigation and source export."""
from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class MidtermsPublicationTests(unittest.TestCase):
    def test_route_uses_shared_navigation_and_dated_record(self):
        page = (ROOT / "site/midterms.html").read_text()
        navigation = page.split('<nav class="navlinks"', 1)[1].split('</nav>', 1)[0]
        self.assertLess(navigation.index('Weekly record'), navigation.index('Mid Terms'))
        self.assertLess(navigation.index('Mid Terms'), navigation.index('Topics'))
        self.assertIn('href="/midterms.html" aria-current="page">Mid Terms</a>', navigation)
        self.assertIn('<body class="research-page">', page)
        self.assertIn('2026-11-04', page)
        self.assertIn('CT', page)
        self.assertIn('certification', page.lower())
        ids = set(re.findall(r'\bid="([^"]+)"', page))
        for target in re.findall(r'href="#([^"]+)"', page):
            self.assertIn(target, ids)

    def test_route_and_authored_source_are_exported(self):
        self.assertIn('/midterms.html', (ROOT / 'site/sitemap.xml').read_text())
        self.assertEqual((ROOT / 'src/midterms.html').read_bytes(),
                         (ROOT / 'site/src/midterms.html').read_bytes())
        manifest = json.loads((ROOT / 'site/src/MANIFEST.json').read_text())
        self.assertIn('midterms.html', {row['path'] for row in manifest['files']})
        self.assertEqual(manifest['current_through'],
                         max(p.stem for p in (ROOT / 'src/briefs').glob('2*.html')))


if __name__ == '__main__':
    unittest.main()
