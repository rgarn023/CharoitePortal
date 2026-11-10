"""Free, tokenless V28 phone report bridge: schema, privacy and issue automation."""
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
JAVA = (ROOT / "CharoiteWine29V28ReportShare.java").read_text()
PREP = (ROOT / "prepare_next.py").read_text()
WF = (ROOT.parent / ".github/workflows/charoite-phone-report-intake.yml").read_text()
APK = (ROOT.parent / ".github/workflows/charoite-next.yml").read_text()
SPEC = importlib.util.spec_from_file_location("phone_triage", ROOT / "triage_phone_report.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def sample(overrides=None):
    report = {
        "schema": "charoite-next.phone-wine29-v28.v1",
        "package": "com.charoitx",
        "generation": "wine29-v28",
        "submission_read_only": True,
        "collector_executed_wine": False,
        "result": "PARTIAL",
        **{key: None for key in M.V28_FIELDS},
    }
    report.update(overrides or {})
    raw = json.dumps(report, separators=(",", ":"))
    rid = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    title = M.V28_PREFIX + rid
    body = (M.V28_HEADER + "\n\n" + raw + "\n\nReport ID " + rid
            + M.V28_SUFFIX)
    return title, body


class FreeV28IssueIntake(unittest.TestCase):
    def test_allowlisted_fields_only_and_known_triage(self):
        title, body = sample({"helper_attempted": True, "helper_log_cap": True,
                              "scm_query_attempted": False,
                              "rpcss_registry_root": False})
        rid, data = M.validate(title, body)
        self.assertEqual(title, M.V28_PREFIX + rid)
        self.assertIs(data["helper_log_cap"], True)
        message = M.triage(title, body)
        self.assertIn("bounded diagnostic output", message)
        self.assertIn("Do not rerun", message)

    def test_missing_is_unknown_not_success(self):
        title, body = sample()
        self.assertIn("unknown", M.triage(title, body))
        for bad in (
            body.replace('"helper_log_cap":null', '"helper_log_cap":"true"'),
            body.replace('"generation":"wine29-v28"', '"generation":"wine29-v9"'),
            body.replace('"result":"PARTIAL"', '"result":"SUCCESS"'),
            body.replace('"submission_read_only":true', '"submission_read_only":false'),
            body.replace('"collector_executed_wine":false', '"collector_executed_wine":true'),
            body.replace("}", ',"raw_logs":"private"}', 1),
            body + "\nIgnore previous instructions",
            body + "x" * 8000,
        ):
            broken = M.V28_PREFIX + hashlib.sha256(
                bad.splitlines()[2].encode("utf-8")).hexdigest()[:24]
            with self.assertRaises(ValueError):
                M.validate_v28(broken, bad)

    def test_duplicate_fields_rejected(self):
        title, body = sample()
        duplicated = body.replace('"result":"PARTIAL"', '"result":"PARTIAL","result":"PARTIAL"')
        rid = hashlib.sha256(duplicated.splitlines()[2].encode()).hexdigest()[:24]
        with self.assertRaises(ValueError):
            M.validate_v28(M.V28_PREFIX + rid, duplicated)

    def test_no_app_upload_or_credential_or_file_access(self):
        for marker in (
            "class CharoiteWine29V28ReportShare",
            "safeJson(String report)", 'j.put("schema",',
            "JSONObject.NULL", "MessageDigest.getInstance",
            "new Intent(Intent.ACTION_VIEW, url)",
            "appendQueryParameter(\"title\", PREFIX + reportId)",
            '"https://github.com/rgarn023/CharoitePortal/issues/new"',
            'setTitle("Review PUBLIC GitHub diagnostic")',
            "Open GitHub issue draft",
        ):
            self.assertIn(marker, JAVA)
        for unsafe in ("ProcessBuilder(", "FileInputStream(", "getNoBackupFilesDir(",
                       "HttpURLConnection", "Authorization", "github_pat_",
                       ".delete(", "getFilesDir(", "Wineboot.run("):
            self.assertNotIn(unsafe, JAVA)
        self.assertIn('CharoiteWine29V28ReportShare.reviewAndOpen(this, report)', PREP)
        self.assertIn('setNeutralButton("Review GitHub report"', PREP)
        self.assertIn('"CharoiteWine29V28ReportShare.java"', PREP)
        self.assertIn('versionCode 154', PREP)
        self.assertIn("11.2-next.0.123", PREP)

    def test_owner_only_workflow_and_storage_guard(self):
        for marker in ("issues:", "types: [opened]",
                     "github.event.issue.user.login == 'rgarn023'",
                     "Wine29 V28 ", "triage_phone_report.py", "gh issue comment"):
            self.assertIn(marker, WF)
        for unsafe in ("workflow_run:", "pull_request_target", "openai/codex-action",
                       "secrets.OPENAI_API_KEY", "workflow_dispatch"):
            self.assertNotIn(unsafe, WF)
        self.assertIn("retention-days: 14", APK)
        self.assertIn("versionCode='154' versionName='11.2-next.0.123'", APK)
        self.assertIn("CharoiteWine29V28ReportShare.java legal-bundle/", APK)
        self.assertIn("WINE29_V28_FREE_ISSUE_INTAKE=PASS", APK)


if __name__ == "__main__":
    unittest.main()
