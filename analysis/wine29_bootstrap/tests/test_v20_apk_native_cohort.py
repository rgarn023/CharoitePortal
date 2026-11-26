"""Fail-closed signed experimental APK v25 native artifact provenance contract.

Static only: never runs Wine, changes phone storage, or installs an APK.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github/workflows/charoite-next.yml"


class V25NativeCohortContract(unittest.TestCase):
    def setUp(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        start = source.index("      - name: Stage verified Wine29 Java host assets")
        end = source.index("      - name: Apply the allocated Android version", start)
        self.stage = source[start:end]

    def test_immutable_artifacts_share_exact_provider_source(self):
        for expected in (
            "actions/runs/45908407139/artifacts?per_page=100",
            "3f780149052dddd9dce4f7ff441f738f37321c86",
            'origin["id"] == 45908407139',
            'origin["head_sha"]',
            'assert not artifact["expired"]',
            "WINE29_V25_PROVIDER_COHORT=SOURCE_MATCH",
            "15158469428",
            "15158479554",
            "15158738277",
            "98a6a29c598e318dda3e75fe6475dd3a1c20dbb4c1cae44dcb3491193f8aa26a",
            "f3f35165476cd56ff2759b5d79c42c4c00a025d9aad34f4849fa4d00e9be83a5",
            "6bddb288448c9e197e7faf6edca415a02c6a0cf6832fb225f0f762719b22687e",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, self.stage)

    def test_archive_and_native_binary_gates_remain_strict(self):
        self.assertEqual(self.stage.count("sha256sum -c -"), 4)
        self.assertIn("(cd \"$assets\" && sha256sum -c SHA256SUMS)", self.stage)
        self.assertIn("(cd \"$assets\" && sha256sum -c explorer.sha256)", self.stage)
        self.assertIn('unzip -p \"$display\" \"$file\" | cmp - \"$assets/$file\"', self.stage)
        self.assertIn("WINE29_V25_NATIVE_HOST_DISPLAY_COHORT=MATCH", self.stage)
        self.assertLess(self.stage.index("WINE29_V25_PROVIDER_COHORT=SOURCE_MATCH"),
                        self.stage.index('gh api \"repos/$GITHUB_REPOSITORY/actions/artifacts/15158469428/zip\"'))
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
