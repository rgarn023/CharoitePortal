"""Fail-closed signed experimental APK v23 native artifact provenance contract.

Static only: never runs Wine, changes phone storage, or installs an APK.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github/workflows/charoite-next.yml"


class V24NativeCohortContract(unittest.TestCase):
    def setUp(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        start = source.index("      - name: Stage verified Wine29 Java host assets")
        end = source.index("      - name: Apply the allocated Android version", start)
        self.stage = source[start:end]

    def test_immutable_artifacts_share_exact_provider_source(self):
        for expected in (
            "actions/runs/45489493053/artifacts?per_page=100",
            "2e5de0b7ef6d2a8de2c3d9ddf35e7235cac39876",
            'origin["id"] == 45489493053',
            'origin["head_sha"]',
            'assert not artifact["expired"]',
            "WINE29_V24_PROVIDER_COHORT=SOURCE_MATCH",
            "14965418391",
            "14965018928",
            "14965827499",
            "8be85d8443655c1428f6003ef9c7cc73352cd1e89147d732cab3ce22bfa470f0",
            "741f218746a17730d450761737a1eea625bfc400dae49ae7cebd6c7a3a2a870d",
            "6bbf702751b55e09be20bce38a769e42539a2abf28c265e144eaaa0d683a5acb",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, self.stage)

    def test_archive_and_native_binary_gates_remain_strict(self):
        self.assertEqual(self.stage.count("sha256sum -c -"), 4)
        self.assertIn("(cd \"$assets\" && sha256sum -c SHA256SUMS)", self.stage)
        self.assertIn("(cd \"$assets\" && sha256sum -c explorer.sha256)", self.stage)
        self.assertIn('unzip -p \"$display\" \"$file\" | cmp - \"$assets/$file\"', self.stage)
        self.assertIn("WINE29_V24_NATIVE_HOST_DISPLAY_COHORT=MATCH", self.stage)
        self.assertLess(self.stage.index("WINE29_V24_PROVIDER_COHORT=SOURCE_MATCH"),
                        self.stage.index('gh api \"repos/$GITHUB_REPOSITORY/actions/artifacts/14965418391/zip\"'))
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
