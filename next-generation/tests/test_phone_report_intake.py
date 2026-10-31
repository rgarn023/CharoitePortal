"""Static and dynamic contract of public issue intake."""
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("phone_triage", ROOT/"triage_phone_report.py")
M=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
WF=(ROOT.parent/".github/workflows/charoite-phone-report-intake.yml").read_text()

def fixture():
    obj = dict(schema="charoite-next.phone-diagnostics.v1", package="com.charoitx",
               generation="wine28-v9-readonly", read_only=True,
               collector_executed_wine=False, pe_bytes=7945, server_bytes=23519,
               server_new_process_calls=1, server_new_process_success=True,
               internal_child_failed=True, pe_kernel32_missing=True,
               pe_apiset_failed=True, server_no_such_file=3,
               internal_wineboot_init=True, prefix_read=False,
               games_or_saves_read=False)
    raw=json.dumps(obj,separators=(",",":"))
    digest=hashlib.sha256(raw.encode()).hexdigest()[:24]
    return (M.PREFIX+digest,
            "Automated Charoite Next phone diagnosis. Sanitized JSON only.\n\n"
            +raw+"\n\nReport ID "+digest+". Wine v9 was not executed or retried.")

class IntakeTests(unittest.TestCase):
    def test_valid_report_classifies_child_failure(self):
        title,body=fixture()
        result=M.triage(title,body)
        self.assertIn("validated",result)
        self.assertIn("Wineboot child process initialization failed",result)
        self.assertIn("do not rerun v9",result)
    def test_rejects_mutations_and_unexpected_fields(self):
        title,body=fixture()
        bad=[body.replace('"pe_bytes":7945','"pe_bytes":7944'),
             body.replace('"prefix_read":false','"prefix_read":true'),
             body.replace('"generation":"wine28-v9-readonly"','"generation":"other"'),
             body.replace('}',',"extra":"secret"}',1),
             body + "\n" + "x" * 9000]
        for row in bad:
            with self.assertRaises(ValueError):
                M.validate(title,row)
    def test_workflow_only_handles_owners_device_reports(self):
        for marker in ("issues:", "types: [opened]",
                       "github.event.issue.user.login == 'rgarn023'",
                       "issues: write", "triage_phone_report.py",
                       "gh issue comment", "ISSUE_BODY:"):
            self.assertIn(marker,WF)
        for unsafe in ("pull_request_target", "workflow_run:", "subprocess", "eval("):
            self.assertNotIn(unsafe,WF)

if __name__=="__main__":
    unittest.main()
