"""Offline safety regression for the isolated, auto-triggered first-provider build.

This test does not execute Wine, the compiler, Android, or any workflow.
"""
from pathlib import Path
import re
import unittest

WORKFLOW = Path(__file__).resolve().parents[2] / ".github/workflows/wine29-first-provider-crossbuild.yml"


class FirstProviderWorkflowContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = WORKFLOW.read_text(encoding="utf-8")

    def test_scoped_auto_trigger_no_apk_or_secrets(self):
        source = self.source
        self.assertRegex(source, r"(?m)^on:\s*\n\s+workflow_dispatch:\s*$")
        self.assertRegex(source, r"(?m)^  push:\s*$")
        self.assertIn("branches: [main]", source)
        self.assertIn("\'.github/workflows/wine29-first-provider-crossbuild.yml\'", source)
        self.assertNotRegex(source, r"(?m)^  (?:pull_request|workflow_run):")
        self.assertNotRegex(source, r"(?m)^  schedule:")
        self.assertIn("contents: read", source)
        self.assertIn("persist-credentials: false", source)
        self.assertNotIn("secrets.", source)
        self.assertNotIn("gradlew", source)
        self.assertIn("timeout-minutes: 58", source)
        self.assertIn("retention-days: 7", source)
        self.assertIn("concurrency:", source)
        self.assertIn("  group: wine29-first-provider-crossbuild-v3", source)
        # Preserve already-running cross-build evidence during subsequent pushes.
        self.assertIn("  cancel-in-progress: false", source)

    def test_lightweight_ci_covers_provider_workflow_edits(self):
        # Editing an expensive workflow must still run the cheap offline
        # regression on both pushes and pull requests.
        static = (WORKFLOW.parent / "charoite-agent-pr-check.yml").read_text(encoding="utf-8")
        for event in ("push", "pull_request"):
            match = re.search(
                rf"(?ms)^  {event}:\n(?P<body>.*?)(?=^  (?:push|pull_request|workflow_dispatch):|^concurrency:)",
                static,
            )
            self.assertIsNotNone(match, f"Missing {event} static CI trigger")
            self.assertIn(
                "'.github/workflows/wine29-first-provider-crossbuild.yml'",
                match.group("body"),
                f"{event} must check provider workflow edits",
            )
        self.assertIn("python3 -m unittest discover -s next-generation/tests", static)
        self.assertNotIn("gradlew", static)

    def test_github_completion_request_is_safe_and_nonrecursive(self):
        notice = (WORKFLOW.parent / "charoite-continue-notifications.yml").read_text(encoding="utf-8")
        static = (WORKFLOW.parent / "charoite-agent-pr-check.yml").read_text(encoding="utf-8")
        self.assertIn("types: [requested, in_progress, completed]", notice)
        self.assertIn("charoite-continue-request:v1 run_id=", notice)
        self.assertIn("run.head_branch === 'main'", notice)
        self.assertIn("['success', 'failure'].includes(run.conclusion)", notice)
        self.assertIn("run.head_repository?.full_name === context.repo.owner", notice)
        self.assertIn("does not directly wake ChatGPT", notice)
        self.assertIn("issue_number: 8", notice)
        self.assertNotIn("workflow_dispatch", notice)
        self.assertNotIn("repository_dispatch", notice)
        self.assertNotIn("secrets.OPENAI", notice)
        self.assertIn("'.github/workflows/charoite-continue-notifications.yml'", static)

    def test_genuine_pinned_provider_build_not_stub(self):
        source = self.source
        self.assertIn("c74acb09d51b447f5d5ac56c87608d3ec565a767", source)
        self.assertIn("ndk;27.3.13750724", source)
        self.assertIn("55064b60b991a1e1e8090b8c2f84e82b22cfe5903d12c159d65064cf5e8ae335", source)
        self.assertIn("prepare-source.sh", source)
        self.assertIn("build-arm64ec-ntdll.sh", source)
        self.assertIn("dlls/mouhid.sys/aarch64-windows/mouhid.sys", source)
        self.assertIn('machine == 0xAA64', source)
        self.assertIn("module.pe_imports(raw)", source)
        self.assertIn("sha256", source)
        self.assertIn("Wine29-HID-XInput-Five-ARM64-PE-NOT-APK", source)

    def test_ntoskrnl_import_summary_remains_diagnostic_only(self):
        source = self.source
        self.assertIn("NTOSKRNL_IMPORT_INSPECTION=PASS", source)
        self.assertIn("NTOSKRNL_IMPORT_SUMMARY=", source)
        self.assertIn("ntoskrnl.exe-import-summary.json", source)
        self.assertIn("'import_symbols':{k:sorted(set(v))", source)
        self.assertIn("raw_symbol.rsplit(' (',1)", source)
        self.assertIn("raw_symbol.rsplit(' (',1)[-1][:-1].isdigit()", source)
        self.assertIn("'runtime_dependency_closure_verified':False", source)
        self.assertIn("assert counts, 'No import DLL names found'", source)
        self.assertIn("NTOSKRNL_PE_BUILD_PROBE=", source)
        self.assertIn("PROVIDER_DEPENDENCY_CLOSURE=UNVERIFIED", source)

    def test_dependency_export_probes_remain_read_only_and_non_runtime(self):
        source = self.source
        self.assertIn("NTOSKRNL_DEPENDENCY_EXPORT_PROBES=", source)
        self.assertIn("ntoskrnl-dependency-export-probes.json", source)
        self.assertIn("'--coff-exports'", source)
        self.assertIn("'symbol_resolution_verified':False", source)
        self.assertIn("'runtime_dependency_closure_verified':False", source)
        self.assertIn("timeout=15", source)

    def test_ntoskrnl_static_export_comparison_is_bounded_and_not_runtime(self):
        source = self.source
        self.assertIn("required=set(imports.get('import_symbols',{}).get(dll,[]))", source)
        self.assertIn("entry['missing_export_symbol_count']", source)
        self.assertIn("sorted(required-exports)[:100]", source)
        self.assertIn("entry['static_export_match']", source)
        self.assertIn("static_export_match_is_not_runtime_verification", source)
        self.assertIn("'symbol_resolution_verified':False", source)
        self.assertIn("'runtime_dependency_closure_verified':False", source)

    def test_evidence_does_not_claim_runtime_closure(self):
        source = self.source
        for key in (
            "provider_import_closure_verified", "native_companion_closure_verified",
            "runtime_compatibility_verified", "wine_executed", "phone_tested",
            "historical_scratch_accessed",
        ):
            self.assertRegex(source, rf'"{key}"\s*:\s*False')
        self.assertIn('"package":"com.charoitx"', source)
        self.assertNotIn('"package":"com.charoite"', source)


if __name__ == "__main__":
    unittest.main()
