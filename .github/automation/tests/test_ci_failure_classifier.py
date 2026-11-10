"""Free CI failure watcher contracts; no network, Wine, phone or paid APIs."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "classify_next_ci.py"
spec = importlib.util.spec_from_file_location("classify_next_ci", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Classifier(unittest.TestCase):
    def test_known_static_test_failure(self):
        jobs = [{"conclusion":"failure", "steps":[
            {"name":"Checkout", "conclusion":"success"},
            {"name":"Verify Next multi-engine isolation tests","conclusion":"failure"}]}]
        category, count = module.classify(jobs)
        self.assertEqual((category,count),("NEXT_STATIC_REGRESSION",1))
        report = module.render(jobs,"42749010430","a"*40,"rgarn023/CharoitePortal")
        self.assertIn("NEXT_STATIC_REGRESSION",report)
        self.assertIn("/actions/runs/42749010430",report)

    def test_unknown_does_not_leak_untrusted_step_names(self):
        secret = "ENV_SECRET=should-never-appear"
        jobs=[{"conclusion":"failure","steps":[{"name":secret,"conclusion":"failure"}]}]
        report=module.render(jobs,"4","b"*40,"rgarn023/CharoitePortal")
        self.assertIn("OTHER_CI_STEP",report)
        self.assertNotIn(secret,report)

    def test_multiple_stages_and_no_failure(self):
        jobs=[{"conclusion":"failure","steps":[
            {"name":"Verify Next multi-engine isolation tests","conclusion":"failure"},
            {"name":"Install build dependencies","conclusion":"failure"}]}]
        self.assertEqual(module.classify(jobs),("MULTIPLE_CI_FAILURE_STAGES",2))
        self.assertEqual(module.classify([]),("NO_FAILED_JOB_IN_PAYLOAD",0))

    def test_blocks_forged_ids_wrong_repository_and_massive_payloads(self):
        for run in ("", "0", "42; echo nope", "1"*40):
            with self.assertRaises(ValueError):
                module.render([],run,"c"*40,"rgarn023/CharoitePortal")
        with self.assertRaises(ValueError):
            module.render([],"1","bad","rgarn023/CharoitePortal")
        with self.assertRaises(ValueError):
            module.render([],"1","c"*40,"stranger/other")
        with self.assertRaises(ValueError):
            module.classify([{}]*101)
        with self.assertRaises(ValueError):
            module.classify([{"conclusion":"failure","steps":{}}])

    def test_workflow_has_only_trusted_main_run_and_no_log_fetch(self):
        src=(SCRIPT.parents[2] / ".github/workflows/charoite-free-ci-watch.yml").read_text()
        for required in ("workflow_run:","conclusion == 'failure'",
                         "head_branch == 'main'","head_repository.full_name == github.repository",
                         "issues: write","classify_next_ci.py","--run-id","--commit"):
            self.assertIn(required,src)
        for forbidden in ("jobs/$", "/logs", "gh pr merge", "OPENAI_API_KEY",
                          "wineserver", "wineboot", "adb shell", "gh release"):
            self.assertNotIn(forbidden,src)


if __name__ == "__main__":
    unittest.main()
