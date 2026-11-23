"""Fail-closed signed experimental APK v23 native artifact provenance contract.

Static only: never runs Wine, changes phone storage, or installs an APK.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github/workflows/charoite-next.yml"


class V23NativeCohortContract(unittest.TestCase):
    def setUp(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        start = source.index("      - name: Stage verified Wine29 Java host assets")
        end = source.index("      - name: Apply the allocated Android version", start)
        self.stage = source[start:end]

    def test_immutable_artifacts_share_exact_provider_source(self):
        for expected in (
            "actions/runs/45220173185/artifacts?per_page=100",
            "b4642f08600302197e55023fc7502d77f6b80b69",
            'origin["id"] == 45220173185',
            'origin["head_sha"]',
            'assert not artifact["expired"]',
            "WINE29_V23_PROVIDER_COHORT=SOURCE_MATCH",
            "14841775498",
            "14840920851",
            "14840820839",
            "1486897e9bb6607549cba2391f407548bb544568f5d5b446776fc3740b67b8a3",
            "92835ef588f0b87cee9274cd44b72de7445a0039a1a2a7e8d9d4e2e1e0f7fa34",
            "4fbb46191fc0c7833c0cf68d3e16e1d82c7191e014533afdbf445fd7d50dd182",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, self.stage)

    def test_archive_and_native_binary_gates_remain_strict(self):
        self.assertEqual(self.stage.count("sha256sum -c -"), 4)
        self.assertIn("(cd \"$assets\" && sha256sum -c SHA256SUMS)", self.stage)
        self.assertIn("(cd \"$assets\" && sha256sum -c explorer.sha256)", self.stage)
        self.assertIn('unzip -p \"$display\" \"$file\" | cmp - \"$assets/$file\"', self.stage)
        self.assertIn("WINE29_V23_NATIVE_HOST_DISPLAY_COHORT=MATCH", self.stage)
        self.assertLess(self.stage.index("WINE29_V23_PROVIDER_COHORT=SOURCE_MATCH"),
                        self.stage.index('gh api \"repos/$GITHUB_REPOSITORY/actions/artifacts/14841775498/zip\"'))
        for old in ("14786954701", "14787417115", "14786854846",
                    "WINE29_V19_NATIVE_HOST_DISPLAY_COHORT"):
            self.assertNotIn(old, self.stage)

    def test_only_explicit_experimental_builds_stage_new_assets(self):
        self.assertIn("contains(github.event.head_commit.message, '[wine29-display]')",
                      self.stage)
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("contains(github.event.head_commit.message, '[next-apk]')",
                      source)
        self.assertNotIn("adb install", self.stage)
        self.assertNotIn("rm -rf", self.stage)


if __name__ == "__main__":
    unittest.main()
