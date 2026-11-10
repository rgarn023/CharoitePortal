"""Static safety gate for source-only provider queue CI publication.

Never runs Wine/Android, accesses a prefix, or creates a release.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github/workflows/wine29-v28-copyqueue-source-audit.yml"


class ProviderArtifactPublication(unittest.TestCase):
    def test_workflow_refuses_unverified_provider_binary_claims(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        for key in (
            '"provider_pe_binaries_verified": False',
            '"provider_native_companions_verified": False',
            '"provider_import_closure_verified": False',
            '"runtime_correction_verified": False',
            '"wine_executed": False',
            '"v28_reused": False',
            '"provider_crossbuild_work_queue_only": True',
            '"provider_source_build_order_only": True',
            'UNVERIFIED_PROVIDER_BUILD_QUEUE_CONTRACT=PASS',
            'PINNED_ARM64_PE_BUILD_AND_IMPORT_TABLE',
            'entry.get("blockers") != blockers',
            'row.get("crossbuild_verified") is not False',
        ):
            self.assertIn(key, text)
        self.assertLess(
            text.index("UNVERIFIED_PROVIDER_BUILD_QUEUE_CONTRACT=PASS"),
            text.index("Publish SOURCE-ONLY coverage report"))

    def test_no_executable_or_heavy_build_in_source_audit(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        for forbidden in (
            "wineboot", "wineserver", "adb shell", "gradle assemble",
            "OPENAI_API_KEY", "secrets.", "gh release create",
            "charoite-next-vc", "com.charoite/files",
        ):
            self.assertNotIn(forbidden, text)
        self.assertIn("retention-days: 30", text)


if __name__ == "__main__":
    unittest.main()
