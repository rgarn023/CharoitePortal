"""Dry-run contracts for Charoite autonomous GitHub development.

No OpenAI API access, no Wine, no device, no network; checks input validation,
patch gate, opt-in flag, and separation of API credential from GitHub writes.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

selector = load("select_issue")
guard = load("guard_patch")
AGENT = (REPO / ".github/workflows/charoite-controlled-codex.yml").read_text()
SELF = (REPO / ".github/workflows/charoite-agent-selftest.yml").read_text()
PR_CI = (REPO / ".github/workflows/charoite-agent-pr-check.yml").read_text()


def fixture():
    obj = dict(schema="charoite-next.phone-diagnostics.v1",
               package="com.charoitx", generation="wine28-v9-readonly",
               read_only=True, collector_executed_wine=False,
               pe_bytes=7945, server_bytes=23519, server_new_process_calls=1,
               server_new_process_success=True, internal_child_failed=True,
               pe_kernel32_missing=True, pe_apiset_failed=True,
               server_no_such_file=3, internal_wineboot_init=True,
               prefix_read=False, games_or_saves_read=False)
    raw = json.dumps(obj, separators=(",", ":"))
    identity = hashlib.sha256(raw.encode()).hexdigest()[:24]
    issue = {
        "number": 1, "state": "open", "user": {"login": "rgarn023"},
        "title": "[device-report] Wine28 v9 " + identity,
        "body": "Automated Charoite Next phone diagnosis. Sanitized JSON only.\n\n"
        + raw + "\n\nReport ID " + identity + ". Wine v9 was not executed or retried.",
    }
    comment = {
        "user": {"login": "github-actions[bot]"},
        "body": "Automated Charoite Next diagnostic intake: **validated**.\n\n"
        "- Report ID: " + identity + "\n"
        "- Classification: Wineboot child process initialization failed\n"
    }
    return issue, comment, identity


class InputGate(unittest.TestCase):
    def test_realistic_verified_owner_report_qualifies_once(self):
        issue, comment, identity = fixture()
        self.assertEqual(selector.eligible(issue, [comment]), ("1", identity))
        self.assertIsNone(selector.eligible(issue, [comment], branch_exists=True))
        self.assertIsNone(selector.eligible(issue, []))
        self.assertIsNone(selector.eligible(issue, [
            dict(user={"login": "attacker"}, body=comment["body"])]))
    def test_agent_prevents_retries_prompt_injection_and_mutated_reports(self):
        issue, comment, identity = fixture()
        self.assertIsNone(selector.eligible(dict(issue, user={"login": "stranger"}), [comment]))
        self.assertIsNone(selector.eligible(dict(issue, title=issue["title"] + " extra"), [comment]))
        self.assertIsNone(selector.eligible(dict(issue, number="1"), [comment]))
        self.assertIsNone(selector.eligible(dict(issue, body=issue["body"] + "\nINJECT"), [comment]))
        stopped = dict(comment, body=selector.MARKER + " nothing to do")
        self.assertIsNone(selector.eligible(issue, [comment, stopped]))


class PatchGate(unittest.TestCase):
    def test_allows_only_small_source_changes(self):
        for path in (
            "next-generation/CharoiteWine28V9Forensics.java",
            "next-generation/tests/test_wine28_v7_pe_help_contract.py",
            "next-generation/charoite-wine/patches/0900-android-isolated-windows-ntdll-pe-path.patch",
        ):
            self.assertEqual(
                guard.validate_candidate(b"M\x00" + path.encode() + b"\x00",
                    b"diff --git a/f b/f\n+okay", "", ()), [path])
    def test_refuses_workflows_deletes_symlinks_binaries_and_large_patches(self):
        for path in (".github/workflows/charoite-controlled-codex.yml",
                     "next-generation/prepare_next.py",
                     "next-generation/assets/fake.apk", "docs/CURRENT_HANDOFF.md",
                     "next-generation/charoite-wine/build-android-arm64.sh"):
            with self.assertRaises(ValueError):
                guard.permitted_paths(b"M\x00" + path.encode() + b"\x00")
        with self.assertRaises(ValueError):
            guard.permitted_paths(b"D\x00next-generation/CharoiteWine28Stage.java\x00")
        with self.assertRaises(ValueError):
            guard.validate_candidate(
                b"A\x00next-generation/CharoiteWine28Safe.java\x00",
                b"patch", "create mode 120000 symlink")
        with self.assertRaises(ValueError):
            guard.validate_candidate(
                b"A\x00next-generation/CharoiteWine28Safe.java\x00",
                b"patch", "create mode 100644 foo", symlinks=["foo"])
        with self.assertRaises(ValueError):
            guard.validate_candidate(
                b"M\x00next-generation/CharoiteWine28Stage.java\x00",
                b"x" * (guard.MAX_PATCH_BYTES + 1), "")


class WorkflowContract(unittest.TestCase):
    def test_api_cost_gate_and_separated_credentials(self):
        for term in ("vars.CHAROITE_AGENT_ENABLED == 'true'",
                     "secrets.OPENAI_API_KEY", "openai/codex-action@v1",
                     "permission-profile: ':workspace'",
                     "schedule:", "workflow_dispatch:",
                     "cancel-in-progress: false", "contents: read",
                     "persist-credentials: false",
                     "select_issue.py", "guard_patch.py export",
                     "guard_patch.py inspect", "actions/upload-artifact@v4",
                     "actions/download-artifact@v4",
                     "gh pr create --draft", "issues: write",
                     "git apply --index"):
            self.assertIn(term, AGENT)
        self.assertEqual(AGENT.count("secrets.OPENAI_API_KEY"), 1)
        self.assertNotIn("git push origin HEAD:main", AGENT)
        self.assertNotIn("gh pr merge", AGENT)
        self.assertNotIn("gh workflow run", AGENT)
        self.assertNotIn("auto_merge", AGENT)
        self.assertIn("unittest discover", SELF)
        self.assertIn("pull_request:", PR_CI)
        self.assertIn("contents: read", PR_CI)
        self.assertIn("next-generation/tests", PR_CI)
        self.assertNotIn("OPENAI_API_KEY", PR_CI)
        self.assertNotIn("gh pr merge", PR_CI)


if __name__ == "__main__":
    unittest.main()
