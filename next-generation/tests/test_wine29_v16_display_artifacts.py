"""Source-only immutable provenance checks for the current isolated Wine29 v26 display test."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = (ROOT / ".github/workflows/charoite-next.yml").read_text(encoding="utf-8")
PROBE = (ROOT / "next-generation/CharoiteWine29V28FocusedInfProbe.java").read_text(
    encoding="utf-8"
)
HOST = (ROOT / "next-generation/WineActivity.java").read_text(encoding="utf-8")


class V16DisplayArtifacts(unittest.TestCase):
    def test_exact_verified_native_host_and_explorer_zip_digests(self):
        # GitHub Actions source-only provider run 45934599681; artifact digests
        # are published by GitHub and checked again when staging the APK.
        self.assertIn("actions/artifacts/15169674395/zip", WORKFLOW)
        self.assertIn(
            "583b8886046a3f2dc9abcc7e42a6ffe968f653122199bb5d9f566af310798f87",
            WORKFLOW
        )
        self.assertIn("actions/artifacts/15170283267/zip", WORKFLOW)
        self.assertIn(
            "45f2fcb790cf629389540841e6bb49fbaf2349a8d88b29d09e56594129dd5ddf",
            WORKFLOW
        )
        self.assertIn('(cd "$assets" && sha256sum -c SHA256SUMS)', WORKFLOW)
        self.assertIn('(cd "$assets" && sha256sum -c explorer.sha256)', WORKFLOW)
        for old in ("actions/artifacts/14756623119/zip", "actions/artifacts/14736472448/zip"):
            self.assertNotIn(old, WORKFLOW)

    def test_strict_purple_fixture_and_fresh_prefix_survive(self):
        self.assertIn("charoite-next-wine29-x64-window-v26", PROBE)
        self.assertIn("if (!newScratch.mkdir())", PROBE)
        self.assertIn("for (int version = 26; version >= 1; version--)", HOST)
        self.assertIn("wine29-x64-window.zip", WORKFLOW)
        self.assertIn("x64-window.sha256", WORKFLOW)
        self.assertIn('if (pixel != paint_color || client_pixel != paint_color || !IsWindowVisible(window))',
                      (ROOT / "next-generation/charoite-wine/fixtures/x64-window.c")
                      .read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
