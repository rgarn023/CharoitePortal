"""Guarantee the native Charoite Wine build is isolated and verifiable."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = (ROOT / "next-generation/charoite-wine/build-android-arm64.sh").read_text()
STABLE = (ROOT / ".github/workflows/runtime-preview.yml").read_text()
NEXT = (ROOT / ".github/workflows/charoite-next.yml").read_text()
WINE = (ROOT / ".github/workflows/charoite-wine-source.yml").read_text()


class NativeBuildContract(unittest.TestCase):
    def test_source_must_be_prepared_and_new_build_dirs(self):
        self.assertIn("charoite-source-validation.txt", SCRIPT)
        self.assertIn("Refusing to overwrite existing Wine build", SCRIPT)
        self.assertIn("charoite-host-tools", SCRIPT)
        self.assertIn("charoite-arm64-android", SCRIPT)

    def test_cross_compilation_is_for_android_arm64(self):
        self.assertIn("aarch64-linux-android35-clang", SCRIPT)
        self.assertIn("--host=aarch64-linux-android35", SCRIPT)
        self.assertIn("--with-wine-tools=../charoite-host-tools", SCRIPT)
        self.assertIn("ANDROID_SUPPORT_FLEXIBLE_PAGE_SIZES", SCRIPT)

    def test_requires_true_16_kib_native_elf(self):
        self.assertIn("max-page-size=16384", SCRIPT)
        self.assertIn("readelf", SCRIPT)
        self.assertIn("a<16384", SCRIPT)
        self.assertIn('alignments.append(int(match.group(1),16))', SCRIPT)

    def test_native_engine_output_does_not_install_in_apps(self):
        for forbidden in ("rm -rf", "adb install", "com.charoite/files",
                          "deleteRecursively", "setenforce", "su -c"):
            self.assertNotIn(forbidden, SCRIPT)
        self.assertIn("com.charoitx/files/", SCRIPT)
        self.assertIn("NOT yet integrated", SCRIPT)

    def test_wine_workflow_is_not_apk_workflow(self):
        self.assertIn("android-arm64-wineserver", WINE)
        self.assertIn("Charoite-Wine-Android-ARM64-Experimental", WINE)
        self.assertIn("Charoite-Portal-Android-APK", STABLE)
        self.assertIn("Charoite-Core-Next-Android-APK", NEXT)
        self.assertNotIn("Charoite-Wine-Android-ARM64-Experimental", STABLE)
        self.assertNotIn("Charoite-Wine-Android-ARM64-Experimental", NEXT)


if __name__ == "__main__":
    unittest.main()
