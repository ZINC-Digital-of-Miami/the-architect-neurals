#!/usr/bin/env python3
"""Destructive counterexamples and scheduling/release failure tests; no network/writes outside tempdirs."""
import copy
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import preservation as p
import check_artifact as artifact
import release
import weekly_run as w

ROOT = Path(__file__).resolve().parents[1]


class PreservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base = json.loads((ROOT / "preservation/baseline.json").read_text())
        for name in [*self.base["immutable_files"], "src/update_part2.html", "src/map_source.json"]:
            out = self.root / name
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, out)

    def errors(self):
        return p.validate(self.root, self.base)

    def test_original_is_preserved(self):
        self.assertEqual(self.errors(), [])

    def test_each_immutable_file_rejects_even_an_append(self):
        for name in self.base["immutable_files"]:
            with self.subTest(name=name):
                path = self.root / name
                raw = path.read_bytes()
                path.write_bytes(raw + b"\nunauthorized revision\n")
                self.assertTrue(self.errors())
                path.write_bytes(raw)

    def test_reworded_correction_rejected(self):
        path = self.root / "src/update_part2.html"
        path.write_text(path.read_text().replace("Never seated.", "Seated.", 1))
        self.assertTrue(self.errors())

    def test_removed_correction_rejected(self):
        path = self.root / "src/update_part2.html"
        path.write_text(path.read_text().replace(self.base["corrections"][0], "", 1))
        self.assertTrue(self.errors())

    def test_dated_context_sibling_append_passes(self):
        path = self.root / "src/update_part2.html"
        before = len(p.corrections(self.root))
        path.write_text(path.read_text().replace('  <h4 id="u-silence"',
            '<div class="correction"><div>2026-09-06 · C-001 · context added</div><p>New record.</p></div>\n  <h4 id="u-silence"'))
        self.assertEqual(len(p.corrections(self.root)), before + 1)
        self.assertEqual(self.errors(), [])

    def test_undated_context_rejected(self):
        path = self.root / "src/update_part2.html"
        path.write_text(path.read_text().replace('  <h4 id="u-silence"',
            '<div class="correction">C-001 revised</div>\n  <h4 id="u-silence"'))
        self.assertTrue(self.errors())

    def test_duplicate_correction_cannot_pose_as_new_finding(self):
        path = self.root / "src/update_part2.html"
        path.write_text(path.read_text().replace('  <h4 id="u-silence"',
            '<div class="correction">2026-09-06 · C-001<p>Different finding.</p></div>\n  <h4 id="u-silence"'))
        self.assertTrue(self.errors())

    def test_removed_node_or_edge_or_changed_grade_rejected(self):
        path = self.root / "src/map_source.json"
        original = json.loads(path.read_text())
        for mutation in ("node", "edge", "grade", "label"):
            with self.subTest(mutation=mutation):
                value = copy.deepcopy(original)
                if mutation == "node":
                    del value["nodes"][next(iter(self.base["map"]["nodes"]))]
                elif mutation == "edge":
                    value["edges"].remove(self.base["map"]["edges"][0])
                elif mutation == "grade":
                    index = value["edges"].index(self.base["map"]["edges"][0])
                    value["edges"][index][2] = "O" if value["edges"][index][2] != "O" else "A"
                else:
                    index = value["edges"].index(self.base["map"]["edges"][0])
                    value["edges"][index][3] = "unsupported rewrite"
                path.write_text(json.dumps(value))
                self.assertTrue(self.errors())

    def test_new_map_record_passes_without_rewriting_old_edges(self):
        path = self.root / "src/map_source.json"
        value = json.loads(path.read_text())
        value["nodes"]["TEST_NEW_ENTITY"] = {"name": "New entity"}
        value["edges"].append(["TRUMP", "TEST_NEW_ENTITY", "O", "research lead only"])
        path.write_text(json.dumps(value))
        self.assertEqual(self.errors(), [])

    def test_new_brief_allowed_then_frozen_in_next_run(self):
        new = self.root / "src/briefs/2026-09-06.html"
        new.write_text("A new brief source")
        self.assertEqual(self.errors(), [])
        next_baseline = p.snapshot(self.root, "a" * 40, verify_git=False)
        new.write_text("Silently rewritten")
        self.assertTrue(p.validate(self.root, next_baseline))


class RunTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.private = self.root / ".architecture"
        self.private.mkdir()
        self.pub = {"current_through": "2026-08-30", "source_commit": "a" * 40}
        w.save(self.private / "publication.json", self.pub)

    def test_sunday_boundary_and_late_dispatch(self):
        self.assertEqual(str(w.latest_due(dt.datetime.fromisoformat("2026-09-06T11:59:59+00:00"))), "2026-08-30")
        self.assertEqual(str(w.latest_due(dt.datetime.fromisoformat("2026-09-06T12:00:00+00:00"))), "2026-09-06")
        self.assertEqual(str(w.latest_due(dt.datetime.fromisoformat("2026-09-08T12:00:00+00:00"))), "2026-09-06")

    def test_dst_is_chicago_not_fixed_utc(self):
        self.assertEqual(str(w.latest_due(dt.datetime.fromisoformat("2026-03-08T11:59:59+00:00"))), "2026-03-01")
        self.assertEqual(str(w.latest_due(dt.datetime.fromisoformat("2026-03-08T12:00:00+00:00"))), "2026-03-08")
        self.assertEqual(str(w.latest_due(dt.datetime.fromisoformat("2026-11-01T12:59:59+00:00"))), "2026-10-25")
        self.assertEqual(str(w.latest_due(dt.datetime.fromisoformat("2026-11-01T13:00:00+00:00"))), "2026-11-01")

    def test_catchup_lists_oldest_missing_week_first(self):
        now = dt.datetime.fromisoformat("2026-09-22T12:00:00+00:00")
        self.assertEqual(w.pending("2026-08-30", now), ["2026-09-06", "2026-09-13", "2026-09-20"])

    def test_bootstrap_coverage_cannot_be_a_future_sunday(self):
        (self.private / "publication.json").unlink()
        receipt = {"current_through": "2026-09-13", "source_commit": "a" * 40}
        args = ["weekly_run.py", "bootstrap", "--root", str(self.root), "--receipt", str(self.private / "receipt.json")]
        with patch.object(w, "latest_due", return_value=dt.date(2026, 9, 6)), \
             patch.object(w, "check_receipt", return_value=receipt), patch.object(sys, "argv", args):
            with self.assertRaisesRegex(ValueError, "after the latest due Sunday"):
                w.main()
        self.assertFalse((self.private / "publication.json").exists())

    def test_overlap_refused_without_stealing_lock(self):
        w.save(self.private / "active.json", {"token": "owner"})
        with self.assertRaisesRegex(ValueError, "exclusive writer"):
            w.start(self.root)
        self.assertEqual(w.read(self.private / "active.json"), {"token": "owner"})

    def test_transaction_lock_excludes_a_second_process(self):
        code = "import fcntl,sys; f=open(sys.argv[1],'a'); fcntl.flock(f,fcntl.LOCK_EX); print('locked',flush=True); sys.stdin.read()"
        process = subprocess.Popen([sys.executable, "-c", code, str(self.private / "transaction.lock")],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(process.stdout.readline().strip(), "locked")
            with self.assertRaises(BlockingIOError):
                with w.transaction(self.root):
                    self.fail("two processes acquired the transaction lock")
        finally:
            process.communicate("", timeout=5)

    def test_other_token_cannot_abandon_run(self):
        w.save(self.private / "active.json", {"token": "owner"})
        with self.assertRaisesRegex(ValueError, "token mismatch"):
            w.mutate(self.root, "fail", "other", "stop")

    def test_acquisition_failure_keeps_coverage_and_receipt(self):
        with patch.object(w, "pending", return_value=["2026-09-06"]), patch.object(w, "git", return_value=""), \
             patch.object(w, "pull", side_effect=ValueError("source unavailable")):
            with self.assertRaisesRegex(ValueError, "source unavailable"):
                w.start(self.root)
        self.assertEqual(w.read(self.private / "publication.json"), self.pub)
        self.assertFalse((self.private / "active.json").exists())
        receipts = list((self.private / "runs").rglob("run.json"))
        self.assertEqual(len(receipts), 1)
        self.assertEqual(w.read(receipts[0])["status"], "failed")

    def test_dispatch_never_advances_watermark_and_retry_preserves_attempt(self):
        with patch.object(w, "pending", return_value=["2026-09-06"]), patch.object(w, "git", return_value=""), \
             patch.object(w, "pull", return_value="a" * 40):
            first = w.start(self.root)
            self.assertEqual(w.read(self.private / "publication.json"), self.pub)
            w.mutate(self.root, "fail", first["token"], "retrieval failed")
            second = w.start(self.root)
        self.assertNotEqual(first["attempt"], second["attempt"])
        self.assertEqual(first["week_ending"], second["week_ending"])
        self.assertTrue((Path(first["attempt"]) / "run.json").exists())

    def test_unverified_or_preview_receipt_cannot_advance_coverage(self):
        receipt = self.private / "receipt.json"
        for status, production in [("failed", True), ("verified", False)]:
            w.save(receipt, {"status": status, "production": production})
            with self.assertRaisesRegex(ValueError, "verified production"):
                w.check_receipt(self.root, receipt)

    def test_stale_main_receipt_rejected(self):
        receipt = self.private / "receipt.json"
        w.save(receipt, {"status": "verified", "production": True, "source_commit": "a" * 40})
        with patch.object(w, "live_main", return_value="b" * 40):
            with self.assertRaisesRegex(ValueError, "not current live main"):
                w.check_receipt(self.root, receipt)

    def test_success_is_recorded_once_and_completion_retry_is_idempotent(self):
        token = "c" * 32
        attempt = self.private / "runs/2026-09-06" / token
        data = {"token": token, "attempt": str(attempt), "candidate": str(attempt / "candidate"),
                "status": "ready_for_review", "staged_files": {"index.html": "hash"},
                "window_after": "2026-08-30", "week_ending": "2026-09-06", "events": []}
        w.save(self.private / "active.json", data)
        receipt = {"current_through": "2026-09-06", "source_commit": "d" * 40}
        with patch.object(w, "check_receipt", return_value=receipt):
            completed = w.mutate(self.root, "complete", token, receipt_path=self.private / "receipt.json")
        self.assertEqual(completed["status"], "published")
        self.assertFalse((self.private / "active.json").exists())
        self.assertEqual(w.read(self.private / "publication.json")["current_through"], "2026-09-06")
        with patch.object(w, "check_receipt", return_value=receipt) as verify_again:
            replay = w.mutate(self.root, "complete", token, receipt_path=self.private / "receipt.json")
            verify_again.assert_called_once()
        self.assertTrue(replay["idempotent_replay"])
        self.assertEqual(w.read(self.private / "publication.json")["current_through"], "2026-09-06")

    def ready_fixture(self):
        token = "e" * 32
        attempt = self.private / "runs/2026-09-06" / token
        data = {"token": token, "attempt": str(attempt), "candidate": str(attempt / "candidate"),
                "status": "ready_for_review", "staged_files": {"index.html": "hash"},
                "window_after": "2026-08-30", "week_ending": "2026-09-06", "events": []}
        w.save(self.private / "active.json", data)
        w.save(attempt / "run.json", data)
        return data, {"current_through": "2026-09-06", "source_commit": "d" * 40}

    def test_interruption_after_watermark_is_recoverable_with_same_verified_receipt(self):
        data, receipt = self.ready_fixture()
        real_save = w.save
        def interrupted_save(path, value):
            if path == Path(data["attempt"]) / "run.json":
                raise OSError("interrupted after publication write")
            real_save(path, value)
        with patch.object(w, "check_receipt", return_value=receipt), patch.object(w, "save", side_effect=interrupted_save):
            with self.assertRaisesRegex(OSError, "after publication"):
                w.mutate(self.root, "complete", data["token"], receipt_path=self.private / "receipt.json")
        self.assertEqual(w.read(self.private / "publication.json")["current_through"], "2026-09-06")
        self.assertEqual(w.read(self.private / "active.json")["status"], "completing")
        self.assertEqual(w.read(Path(data["attempt"]) / "run.json")["status"], "ready_for_review")
        self.assertTrue(list((Path(data["attempt"]) / "completion-errors").glob("*.json")))
        with patch.object(w, "check_receipt", return_value=receipt) as reverify:
            result = w.mutate(self.root, "complete", data["token"], receipt_path=self.private / "receipt.json")
            reverify.assert_called_once()
        self.assertEqual(result["status"], "published")
        self.assertFalse((self.private / "active.json").exists())

    def test_interruption_before_active_cleanup_is_recoverable(self):
        data, receipt = self.ready_fixture()
        with patch.object(w, "check_receipt", return_value=receipt), patch.object(w, "remove_active", side_effect=OSError("interrupted before unlink")):
            with self.assertRaisesRegex(OSError, "before unlink"):
                w.mutate(self.root, "complete", data["token"], receipt_path=self.private / "receipt.json")
        self.assertEqual(w.read(Path(data["attempt"]) / "run.json")["status"], "published")
        with patch.object(w, "check_receipt", return_value=receipt):
            w.mutate(self.root, "complete", data["token"], receipt_path=self.private / "receipt.json")
        self.assertFalse((self.private / "active.json").exists())

    def test_recovery_rejects_changed_receipt_and_cannot_be_abandoned(self):
        data, receipt = self.ready_fixture()
        with patch.object(w, "check_receipt", return_value=receipt), patch.object(w, "remove_active", side_effect=OSError("interrupted")):
            with self.assertRaises(OSError):
                w.mutate(self.root, "complete", data["token"], receipt_path=self.private / "receipt.json")
        before = (self.private / "publication.json").read_bytes()
        with patch.object(w, "check_receipt", return_value={**receipt, "source_commit": "f" * 40}):
            with self.assertRaisesRegex(ValueError, "exact receipt"):
                w.mutate(self.root, "complete", data["token"], receipt_path=self.private / "receipt.json")
        with self.assertRaisesRegex(ValueError, "pending verified completion"):
            w.mutate(self.root, "fail", data["token"], "abandon")
        self.assertEqual((self.private / "publication.json").read_bytes(), before)
        self.assertTrue((self.private / "active.json").exists())

    def test_interruption_before_watermark_retries_without_skipping_interval(self):
        data, receipt = self.ready_fixture()
        real_save = w.save
        def interrupted_save(path, value):
            if path == self.private / "publication.json":
                raise OSError("interrupted before watermark")
            real_save(path, value)
        with patch.object(w, "check_receipt", return_value=receipt), patch.object(w, "save", side_effect=interrupted_save):
            with self.assertRaises(OSError):
                w.mutate(self.root, "complete", data["token"], receipt_path=self.private / "receipt.json")
        self.assertEqual(w.read(self.private / "publication.json"), self.pub)
        with patch.object(w, "check_receipt", return_value=receipt):
            w.mutate(self.root, "complete", data["token"], receipt_path=self.private / "receipt.json")
        self.assertEqual(w.read(self.private / "publication.json")["current_through"], "2026-09-06")

    def test_main_change_during_served_byte_reads_rejects_receipt(self):
        sha = "a" * 40
        bodies = {"index.html": b"report", "src/MANIFEST.json": json.dumps({"current_through": "2026-09-06"}).encode(),
                  "release.json": json.dumps({"source_commit": sha}).encode()}
        path = self.private / "receipt.json"
        w.save(path, {"status": "verified", "production": True, "source_commit": sha,
                     "current_through": "2026-09-06", "files": {k: p.digest(v) for k, v in bodies.items()}})
        current = [sha]
        def fetch(url):
            current[0] = "b" * 40
            key = url.removeprefix(w.LIVE).lstrip("/") or "index.html"
            return bodies[key]
        with patch.object(w, "live_main", side_effect=lambda root: current[0]) as remote, patch.object(w, "public_bytes", side_effect=fetch):
            with self.assertRaisesRegex(ValueError, "changed during"):
                w.check_receipt(self.root, path)
            self.assertEqual(remote.call_count, 2)

    def test_candidate_mismatch_fails_before_network_publication_check(self):
        path = self.private / "receipt.json"
        w.save(path, {"status": "verified", "production": True, "source_commit": "a" * 40,
                     "files": {"index.html": "different", "src/MANIFEST.json": "m", "release.json": "r"}})
        with patch.object(w, "live_main", return_value="a" * 40), patch.object(w, "public_bytes") as fetch:
            with self.assertRaisesRegex(ValueError, "differs from the reviewed"):
                w.check_receipt(self.root, path, {"index.html": "reviewed"})
            fetch.assert_not_called()


class ArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.base_temp.cleanup)
        cls.base = Path(cls.base_temp.name)
        for name, raw in artifact.source_inputs(ROOT).items():
            path = cls.base / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        shutil.copytree(ROOT / "scripts", cls.base / "scripts", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copytree(ROOT / "preservation", cls.base / "preservation")
        env = os.environ.copy()
        env.pop("ARCH_SITE_URL", None)
        env.update({"ARCH_ROOT": str(cls.base / "src"), "ARCH_DIST": str(cls.base / "site"), "PYTHONDONTWRITEBYTECODE": "1"})
        for command in (["node", "src/build_neural_map.js"], [sys.executable, "src/build_site3.py"]):
            result = subprocess.run(command, cwd=cls.base, env=env, capture_output=True, text=True)
            if result.returncode:
                raise AssertionError(result.stderr)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "fixture"
        shutil.copytree(self.base, self.root)

    def test_clean_build_passes_without_changing_inputs_or_outputs(self):
        inputs = artifact.source_inputs(self.root)
        output = artifact.artifact_hashes(self.root / "site")
        self.assertEqual(artifact.check(self.root), [])
        self.assertEqual(artifact.source_inputs(self.root), inputs)
        self.assertEqual(artifact.artifact_hashes(self.root / "site"), output)

    def test_full_gate_rejects_changed_rendered_chapter_and_disabled_site_js(self):
        clean = subprocess.run(["bash", "check.sh"], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(clean.returncode, 0, clean.stdout + clean.stderr)
        page = self.root / "site/index.html"
        revised, count = re.subn(r'(<h3\b[^>]*id="chapter-0[^\"]*"[^>]*>).*?(</h3>)',
                                r'\1UNAUTHORIZED REWRITTEN CHAPTER\2', page.read_text(), count=1, flags=re.S)
        self.assertEqual(count, 1)
        page.write_text(revised)
        (self.root / "site/site-ui.js").write_text("// disabled interaction implementation\n")
        rejected = subprocess.run(["bash", "check.sh"], cwd=self.root, capture_output=True, text=True)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("current source rebuild: index.html", rejected.stdout + rejected.stderr)
        self.assertIn("current source rebuild: site-ui.js", rejected.stdout + rejected.stderr)

    def test_all_generated_asset_types_are_compared(self):
        paths = ["sources.html", "site-ui.js", "research-ui.js", "styles.css", "research/data.json", "map/svg.frag"]
        for name in paths:
            path = self.root / "site" / name
            path.write_bytes(path.read_bytes() + b"\nUNAUTHORIZED CHANGE")
        errors = artifact.check_rebuild(self.root)
        for name in paths:
            self.assertIn(f"generated artifact differs from current source rebuild: {name}", errors)

    def test_missing_and_extra_files_are_rejected(self):
        (self.root / "site/site-ui.js").unlink()
        (self.root / "site/unreviewed.html").write_text("extra publication")
        errors = artifact.check_rebuild(self.root)
        self.assertIn("generated artifact missing: site-ui.js", errors)
        self.assertIn("unexpected generated artifact: unreviewed.html", errors)

    def test_unexpected_vercel_routing_configuration_is_rejected(self):
        (self.root / "site/vercel.json").write_text('{"rewrites":[{"source":"/(.*)","destination":"https://example.com"}]}')
        self.assertIn("unexpected generated artifact: vercel.json", artifact.check_rebuild(self.root))

    def test_only_exact_cli_metadata_is_excluded_from_public_inventory(self):
        site = self.root / "site"
        (site / ".vercel").mkdir()
        (site / ".vercel/project.json").write_text('{"projectId":"local-metadata"}')
        (site / ".gitignore").write_text(".vercel\n")
        self.assertEqual(artifact.check_rebuild(self.root), [])
        self.assertNotIn(".gitignore", release.file_hashes(site))
        self.assertNotIn(".vercel/project.json", release.file_hashes(site))
        (site / ".gitignore").write_text(".vercel\nindex.html\n")
        with self.assertRaisesRegex(ValueError, "may contain only"):
            artifact.check_rebuild(self.root)


class ReleaseTests(unittest.TestCase):
    def test_weekly_upload_is_bound_to_reviewed_bytes_before_external_mutation(self):
        for mutation in ("changed", "unstaged", "wrong_interval"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                site = root / "site"
                (site / "src").mkdir(parents=True)
                (site / "index.html").write_text("preserved report")
                (site / "styles.css").write_text("reviewed styles")
                (site / "src/MANIFEST.json").write_text(json.dumps({"current_through": "2026-09-06"}))
                owned = {"token": "owner", "status": "ready_for_review", "week_ending": "2026-09-06",
                         "staged_files": release.file_hashes(site)}
                if mutation == "changed":
                    (site / "styles.css").write_text("unreviewed change after staging")
                elif mutation == "unstaged":
                    owned["status"] = "researching"
                else:
                    owned["week_ending"] = "2026-09-13"
                w.save(root / ".architecture/active.json", owned)
                def archive(_root, _sha, destination, _prefix):
                    shutil.copytree(site, destination / "site")
                with patch.object(release, "validate_main", return_value="a" * 40), \
                     patch.object(release, "extract_archive", side_effect=archive), \
                     patch.object(release, "vc", return_value=b"zincdigitalofmiami") as vc:
                    with self.assertRaisesRegex(ValueError, "candidate|interval"):
                        release.publish(root, True, "owner")
                    self.assertEqual([call.args[0] for call in vc.call_args_list], [["whoami"]])

    def test_matching_staged_weekly_artifact_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            site = Path(temp)
            (site / "src").mkdir()
            (site / "index.html").write_text("reviewed report")
            (site / "src/MANIFEST.json").write_text(json.dumps({"current_through": "2026-09-06"}))
            release.validate_reviewed_artifact(site, {"status": "ready_for_review", "week_ending": "2026-09-06",
                "staged_files": release.file_hashes(site)})

    def test_changed_live_byte_fails_verification(self):
        with tempfile.TemporaryDirectory() as temp:
            site = Path(temp)
            (site / "index.html").write_text("preserved report")
            with patch.object(release, "public_bytes", return_value=b"old or modified report"):
                with self.assertRaisesRegex(ValueError, "served bytes differ"):
                    release.verify_files(site)

    def test_non_main_head_cannot_deploy(self):
        with patch.object(release, "live_main", return_value="a" * 40), patch.object(release, "git", return_value="b" * 40):
            with self.assertRaisesRegex(ValueError, "HEAD is not live"):
                release.validate_main(ROOT)

    def test_dirty_tree_cannot_deploy(self):
        with patch.object(release, "live_main", return_value="a" * 40), patch.object(release, "git", side_effect=["a" * 40, " M src/master_report.md"]):
            with self.assertRaisesRegex(ValueError, "uncommitted"):
                release.validate_main(ROOT)


if __name__ == "__main__":
    unittest.main(verbosity=2)
