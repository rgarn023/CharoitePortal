"""Fail-closed signed experimental APK v22 native artifact provenance contract.

Static only: never runs Wine, changes phone storage, or installs an APK.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github/workflows/charoite-next.yml"


class V22NativeCohortContract(unittest.TestCase):
    def setUp(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        start = source.index("      - name: Stage verified Wine29 Java host assets")
        end = source.index("      - name: Apply the allocated Android version", start)
        self.stage = source[start:end]

    def test_immutable_artifacts_share_exact_provider_source(self):
        for expected in (
            "actions/runs/45211800904/artifacts?per_page=100",
            "495af7a054be51118d6794789fe3b33e06a14843",
            'origin["id"] == 45211800904',
            'origin["head_sha"]',
            'assert not artifact["expired"]',
            "WINE29_V22_PROVIDER_COHORT=SOURCE_MATCH",
            "14838255023",
            "14836507866",
            "14836598137",
            "7d871248c53a610ba27fbc9e252a3af25d5877febbc5d4878db798ba16f7ba00",
            "0912eaf81f3c6e574b5f5bb0a0d1c9783956dc7dab3b14c00dae563bca88717b",
            "e41ef0bb37b32f2b89c66f7ae0d8fe732fc0568b9c5b390a17e4c4883ff0bf57",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, self.stage)

    def test_archive_and_native_binary_gates_remain_strict(self):
        self.assertEqual(self.stage.count("sha256sum -c -"), 4)
        self.assertIn("(cd \"$assets\" && sha256sum -c SHA256SUMS)", self.stage)
        self.assertIn("(cd \"$assets\" && sha256sum -c explorer.sha256)", self.stage)
        self.assertIn('unzip -p \"$display\" \"$file\" | cmp - \"$assets/$file\"', self.stage)
        self.assertIn("WINE29_V22_NATIVE_HOST_DISPLAY_COHORT=MATCH", self.stage)
        self.assertLess(self.stage.index("WINE29_V22_PROVIDER_COHORT=SOURCE_MATCH"),
                        self.stage.index('gh api \"repos/$GITHUB_REPOSITORY/actions/artifacts/14838255023/zip\"'))
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
