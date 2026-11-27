"""Fail-closed signed experimental APK v26 native artifact provenance contract.

Static only: never runs Wine, changes phone storage, or installs an APK.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github/workflows/charoite-next.yml"


class V26NativeCohortContract(unittest.TestCase):
    def setUp(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        start = source.index("      - name: Stage verified Wine29 Java host assets")
        end = source.index("      - name: Apply the allocated Android version", start)
        self.stage = source[start:end]

    def test_immutable_artifacts_share_exact_provider_source(self):
        for expected in (
            "actions/runs/45934599681/artifacts?per_page=100",
            "764c62f6057c4f67bc0ecb61bfd945d8ed34c0b6",
            'origin["id"] == 45934599681',
            'origin["head_sha"]',
            'assert not artifact["expired"]',
            "WINE29_V26_PROVIDER_COHORT=SOURCE_MATCH",
            "15169674395",
            "15169729236",
            "15170283267",
            "583b8886046a3f2dc9abcc7e42a6ffe968f653122199bb5d9f566af310798f87",
            "94ccf44a8d605c5c9139b4b694aed08f40d0155e6b53acc3ecdc90da9b73caaa",
            "45f2fcb790cf629389540841e6bb49fbaf2349a8d88b29d09e56594129dd5ddf",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, self.stage)

    def test_archive_and_native_binary_gates_remain_strict(self):
        self.assertEqual(self.stage.count("sha256sum -c -"), 4)
        self.assertIn("(cd \"$assets\" && sha256sum -c SHA256SUMS)", self.stage)
        self.assertIn("(cd \"$assets\" && sha256sum -c explorer.sha256)", self.stage)
        self.assertIn('unzip -p \"$display\" \"$file\" | cmp - \"$assets/$file\"', self.stage)
        self.assertIn("WINE29_V26_NATIVE_HOST_DISPLAY_COHORT=MATCH", self.stage)
        self.assertLess(self.stage.index("WINE29_V26_PROVIDER_COHORT=SOURCE_MATCH"),
                        self.stage.index('gh api \"repos/$GITHUB_REPOSITORY/actions/artifacts/15169674395/zip\"'))
        for old in ("14786954701", "14787417115", "14786854846",
                    "WINE29_V19_NATIVE_HOST_DISPLAY_COHORT",
                    "14965418391", "14965018928", "14965827499"):
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
