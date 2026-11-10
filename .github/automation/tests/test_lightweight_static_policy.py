"""Source-only regression: Next test changes never start a heavyweight APK build.

Checks fixed workflow YAML contracts; does NOT execute Wine/Android or read
secrets, user prefixes, files on a device, or any historical scratch.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
HEAVY = ROOT / ".github/workflows/charoite-next.yml"
LIGHT = ROOT / ".github/workflows/charoite-agent-pr-check.yml"


def triggers(path: Path) -> str:
    # The on: block is entirely before top-level permissions/concurrency.
    # Keep this test dependency-free (avoid PyYAML YAML 1.1 'on' coercion).
    text = path.read_text(encoding="utf-8")
    self_contained = text.partition("\non:\n")
    if not self_contained[1]:
        raise AssertionError(f"Missing GitHub on: trigger: {path}")
    after = self_contained[2]
    stop = [i for delimiter in ("\npermissions:", "\nconcurrency:", "\njobs:")
            if (i := after.find(delimiter)) >= 0]
    if not stop:
        raise AssertionError(f"Cannot bound triggers: {path}")
    return after[:min(stop)]


class LightweightBuildSplit(unittest.TestCase):
    def test_test_only_edit_never_launches_heavy_apk(self):
        block = triggers(HEAVY)
        self.assertIn("  push:\n", block)
        self.assertIn("      - 'next-generation/**'", block)
        self.assertIn("      - '!next-generation/tests/**'", block)
        self.assertIn("      - '!next-generation/charoite-wine/**'", block)
        self.assertNotIn("      - '.github/workflows/charoite-next.yml'", block)
        self.assertLess(block.index("'next-generation/**'"),
                        block.index("'!next-generation/tests/**'"))
        # No schedule / timer should launch a 465 MB APK build.
        self.assertNotIn("  schedule:", block)

    def test_lightweight_trigger_covers_test_and_workflow_changes(self):
        block = triggers(LIGHT)
        self.assertIn("  push:\n", block)
        for required in (
            "'next-generation/tests/**'",
            "'.github/workflows/charoite-agent-pr-check.yml'",
            "'.github/workflows/charoite-next.yml'",
            "  pull_request:",
            "  workflow_dispatch:",
        ):
            self.assertIn(required, block)
        self.assertNotIn("  schedule:", block)

    def test_lightweight_has_no_phone_secrets_or_artifact_publication(self):
        text = LIGHT.read_text(encoding="utf-8")
        self.assertIn("permissions:\n  contents: read", text)
        self.assertIn("unittest discover -s next-generation/tests", text)
        self.assertIn("persist-credentials: false", text)
        for forbidden in (
            "OPENAI_API_KEY", "secrets.", "gh release", "upload-artifact",
            "gh pr merge", "adb ", "wineboot", "wineserver",
            "gradle assemble", "create-release",
        ):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
