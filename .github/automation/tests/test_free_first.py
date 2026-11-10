"""Offline no-cost automation contract tests. No secrets/network/Wine/device."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCRIPT = ROOT / ".github/automation/known_test_drift.py"
spec = importlib.util.spec_from_file_location("known_test_drift", SCRIPT)
known = importlib.util.module_from_spec(spec)
spec.loader.exec_module(known)


def fixture(root: Path, code=157, name="11.2-next.0.126", gate_code=None):
    gate_code = gate_code if gate_code is not None else code
    prep = root / "next-generation/prepare_next.py"
    flow = root / ".github/workflows/charoite-next.yml"
    prep.parent.mkdir(parents=True, exist_ok=True)
    flow.parent.mkdir(parents=True, exist_ok=True)
    prep.write_text(
        'text = text.replace(\'versionName "11.2"\', \'versionName "' +
        name + '"\')\ntext = text.replace("versionCode 33", "versionCode ' +
        str(code) + '")\n', encoding="utf-8")
    flow.write_text(
        """grep -F "package: name='com.charoitx' versionCode='""" +
        str(gate_code) + "' versionName='" + name + """'"\n""" +
        "TAG=charoite-next-vc" + str(code) + "\n", encoding="utf-8")
    for path in known.TARGETS:
        f = root / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("assert 'versionCode 156' and \"11.2-next.0.125\"\n",
                     encoding="utf-8")


class KnownFix(unittest.TestCase):
    def test_rewrites_previous_version_only_with_no_disk_writes(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            fixture(root)
            f = root / known.TARGETS[0]
            before = f.read_bytes()
            changes = known.plan(root)
            self.assertEqual(len(changes), len(known.TARGETS))
            self.assertIn("versionCode 157", changes[known.TARGETS[0]])
            self.assertIn("11.2-next.0.126", changes[known.TARGETS[0]])
            self.assertEqual(f.read_bytes(), before)
            self.assertNotIn("next-generation/prepare_next.py", changes)

    def test_no_change_on_current_version_or_older_than_one_build(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            fixture(root)
            for path in known.TARGETS:
                (root / path).write_text("versionCode 157 11.2-next.0.126")
            self.assertEqual(known.plan(root), {})
            (root / known.TARGETS[0]).write_text("versionCode 155 11.2-next.0.124")
            self.assertEqual(known.plan(root), {})

    def test_disagreeing_release_metadata_refuses_changes(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            fixture(root, gate_code=156)
            with self.assertRaises(known.UnsafeVersionDrift):
                known.plan(root)
            self.assertIn("versionCode 156",
                          (root / known.TARGETS[0]).read_text())

    def test_only_explicitly_allowlisted_tests(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            fixture(root)
            extra = root / "next-generation/CharoiteWine29V28ScopedTriage.java"
            extra.write_text("versionCode 156", encoding="utf-8")
            self.assertTrue(known.plan(root))
            self.assertEqual(extra.read_text(), "versionCode 156")

    def test_symlinks_fail_closed(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            fixture(root)
            f = root / known.TARGETS[0]
            f.unlink()
            f.symlink_to(root / known.TARGETS[1])
            with self.assertRaises(known.UnsafeVersionDrift):
                known.plan(root)


class WorkflowPolicy(unittest.TestCase):
    def test_cost_free_workflows_never_run_paid_ai_or_phone(self):
        files = (
            ".github/workflows/charoite-free-known-fix.yml",
            ".github/workflows/charoite-free-status.yml",
        )
        for name in files:
            body = (ROOT / name).read_text(encoding="utf-8")
            for bad in ("openai/codex-action", "secrets.OPENAI_API_KEY",
                        "gh pr merge", "gh release create",
                        "wineboot", "wineserver", "adb shell"):
                self.assertNotIn(bad, body, name)
        fix = (ROOT / files[0]).read_text(encoding="utf-8")
        self.assertIn("workflow_run:", fix)
        self.assertIn("head_branch == 'main'", fix)
        self.assertIn("head_repository.full_name == github.repository", fix)
        self.assertIn("gh pr create --draft", fix)
        self.assertNotIn("push:\n", fix)
        status = (ROOT / files[1]).read_text(encoding="utf-8")
        self.assertIn("schedule:", status)
        self.assertIn("workflow_dispatch:", status)
        self.assertIn("issues: write", status)
        self.assertNotIn("gh workflow run", status)

    def test_paid_agent_remains_manual_only(self):
        paid = (ROOT / ".github/workflows/charoite-controlled-codex.yml").read_text()
        self.assertNotIn("  schedule:", paid)
        self.assertIn("paid_api_consent:", paid)
        self.assertIn("vars.CHAROITE_AGENT_ENABLED == 'true'", paid)


if __name__ == "__main__":
    unittest.main()
