"""Offline safety regression for the expensive, manually dispatched first-provider build.

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

    def test_manual_only_no_apk_or_secrets(self):
        source = self.source
        self.assertRegex(source, r"(?m)^on:\s*\n\s+workflow_dispatch:\s*$")
        self.assertNotRegex(source, r"(?m)^\s+(?:push|pull_request|schedule|workflow_run):")
        self.assertIn("contents: read", source)
        self.assertIn("persist-credentials: false", source)
        self.assertNotIn("secrets.", source)
        self.assertNotIn("gradlew", source)
        self.assertIn("timeout-minutes: 58", source)
        self.assertIn("retention-days: 7", source)
        self.assertRegex(source, r"(?m)^concurrency:\s*\n\s+group: wine29-first-provider-crossbuild\s*\n\s+cancel-in-progress: false\s*$")

    def test_lightweight_ci_covers_provider_workflow_edits(self):
        # Editing a manual expensive workflow must still run the cheap offline
        # regression on both pushes and pull requests.
        static = (WORKFLOW.parent / "charoite-agent-pr-check.yml").read_text(encoding="utf-8")
        for event in ("push", "pull_request"):
            match = re.search(
                rf"(?ms)^  {event}:\\n(?P<body>.*?)(?=^  (?:push|pull_request|workflow_dispatch):|^concurrency:)",
                static,
            )
            self.assertIsNotNone(match, f"Missing {event} static CI trigger")
            self.assertIn(
                "' .github/workflows/wine29-first-provider-crossbuild.yml'".replace("' ", "'"),
                match.group("body"),
                f"{event} must check provider workflow edits",
            )
        self.assertIn("python3 -m unittest discover -s next-generation/tests", static)
        self.assertNotIn("gradlew", static)

    def test_genuine_pinned_provider_build_not_stub(self):
        source = self.source
        self.assertIn("c74acb09d51b447f5d5ac56c87608d3ec565a767", source)
        self.assertIn("ndk;27.3.13750724", source)
        self.assertIn("55064b60b991a1e1e8090b8c2f84e82b22cfe5903d12c159d65064cf5e8ae335", source)
        self.assertIn("prepare-source.sh", source)
        self.assertIn("build-arm64ec-ntdll.sh", source)
        self.assertIn("make -j2 dlls/mouhid.sys/aarch64-windows/mouhid.sys", source)
        self.assertIn('machine == 0xAA64', source)
        self.assertIn("module.pe_imports(raw)", source)
        self.assertIn("sha256", source)
        self.assertIn("Wine29-Mouhid-ARM64-Source-Built-PE-NOT-APK", source)

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
