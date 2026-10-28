"""Safety and ABI contract checks for Charoite Wine ARM64EC ntdll build."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = (ROOT / "next-generation/charoite-wine/build-arm64ec-ntdll.sh").read_text()
WORKFLOW = (ROOT / ".github/workflows/charoite-wine-source.yml").read_text()


class Arm64ecBuildContract(unittest.TestCase):
    def test_arm64ec_is_not_plain_aarch64(self):
        self.assertIn("--target=arm64ec-w64-windows-gnu", SCRIPT)
        self.assertIn("charoite-arm64ec-probe.obj", SCRIPT)
        self.assertIn("IMAGE_FILE_MACHINE_ARM64EC", SCRIPT)
        self.assertIn("--enable-archs=arm64ec,aarch64", SCRIPT)
        self.assertIn("--with-mingw=yes", SCRIPT)

    def test_native_ntdll_is_not_wineserver(self):
        self.assertIn("dlls/ntdll/aarch64-windows/ntdll.dll", SCRIPT)
        self.assertIn("dlls/ntdll/ntdll.so", SCRIPT)
        self.assertIn("AArch64", SCRIPT)
        self.assertIn("16384", SCRIPT)

    def test_build_is_read_only_to_installed_runtimes(self):
        self.assertIn("charoite-source-validation.txt", SCRIPT)
        self.assertIn("Refusing to replace existing ARM64EC build output", SCRIPT)
        for forbidden in ("rm -rf", "adb install", "su -c", "com.charoite/files",
                          "setenforce", "chmod 777", "curl "):
            self.assertNotIn(forbidden, SCRIPT)
        self.assertIn("NOT installed in either Charoite edition", SCRIPT)

    def test_pe_toolchain_is_hash_pinned(self):
        self.assertIn("llvm-mingw-20261020-ucrt-ubuntu-22.04-x86_64.tar.xz", WORKFLOW)
        self.assertIn("55064b60b991a1e1e8090b8c2f84e82b22cfe5903d12c159d65064cf5e8ae335", WORKFLOW)
        self.assertIn("sha256sum --check", WORKFLOW)

    def test_not_mislabeled_as_complete_runner(self):
        self.assertIn("Charoite-Wine-ARM64EC-NTDLL-Experimental", WORKFLOW)
        self.assertNotIn("assembleDebug", WORKFLOW)
        self.assertIn("NOT an executable Android runner", SCRIPT)


if __name__ == "__main__":
    unittest.main()
