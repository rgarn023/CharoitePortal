"""Wine29 same-source six-DLL candidates: safe CI-only build contracts."""
import importlib.util
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "wine29-deps/build-wine29-deps.sh"
CHECKER = ROOT / "wine29-deps/verify-wine29-deps.py"
CI = ROOT.parent / ".github/workflows/wine29-07-dependency-candidates.yml"
SRC = BUILDER.read_text(encoding="utf-8")
VERIFY = CHECKER.read_text(encoding="utf-8")
spec = importlib.util.spec_from_file_location("wine29_deps_test", CHECKER)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def header(machine):
    data = bytearray(160)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 0x3c, 0x80)
    data[0x80:0x84] = b"PE\x00\x00"
    struct.pack_into("<H", data, 0x84, machine)
    return bytes(data)


class Wine29DependencyCandidateContracts(unittest.TestCase):
    def test_only_pinned_six_modules_are_candidates(self):
        self.assertEqual(mod.MODULES,
                         ("coml2", "imm32", "oleacc", "oleaut32", "shcore", "newdev"))
        self.assertEqual(mod.PHONE_DIRECT, mod.MODULES[:5] if False else
                         ("coml2.dll","imm32.dll","oleacc.dll","oleaut32.dll","shcore.dll"))
        self.assertEqual(mod.GENERATION,
                         "wine10-arm64ec-dependencies.0.8-candidate")
        self.assertEqual(mod.SOURCE_COMMIT,
                         "c74acb09d51b447f5d5ac56c87608d3ec565a767")
        self.assertEqual(len(mod.BASELINE), 64)
        for module in mod.MODULES:
            self.assertIn("coml2 imm32 oleacc oleaut32 shcore newdev", SRC)
        self.assertIn("dlls/$name/aarch64-windows/$name.dll", SRC)
        self.assertIn("dlls/$name/Makefile.in", SRC)

    def test_hybrid_raw_machine_accepts_only_pinned_arm_classes(self):
        self.assertEqual(mod.raw_coff_machine(header(0xAA64)), 0xAA64)
        self.assertEqual(mod.raw_coff_machine(header(0xA641)), 0xA641)
        with self.assertRaises(ValueError):
            mod.raw_coff_machine(header(0x8664))
        with self.assertRaises(ValueError):
            mod.raw_coff_machine(b"MZ")
        bad = bytearray(header(0xAA64))
        bad[0x80] = ord("X")
        with self.assertRaises(ValueError):
            mod.raw_coff_machine(bytes(bad))

    def test_fresh_runner_only_build_prohibits_phone_execution(self):
        for required in (
            "verify-bootstrap-bundle.py", "66068032bd2203c8e53fddc92ce46b84086eb293306b2bd12bb741bf9a5e035e",
            "charoite-wine29-native-source-validation.json",
            "charoite-wine29-native-source-delta.patch",
            "git","rev-parse","HEAD",
            "make -j2", "Machine: IMAGE_FILE_MACHINE_ARM64EC (0xA641)",
            "WINE29_07_DEPENDENCY_CANDIDATES=NOT_INSTALLED_OR_EXECUTED",
            "verify-wine29-deps.py",
        ):
            self.assertIn(required, SRC)
        for forbidden in ("wineboot -i", "WINEPREFIX=", "adb ", "rm -rf ",
                          "shutil.rmtree", "os.system", "prefix_created = True"):
            self.assertNotIn(forbidden, SRC + VERIFY)
        for scope in ("/data/data/", "/data/user/", "/storage/emulated/", "/sdcard/"):
            self.assertIn(scope, SRC)
            self.assertIn(scope, VERIFY)

    def test_candidate_verifier_rejects_executable_claims_and_unsafe_files(self):
        for s in ("launch_ready", "wineboot_executed", "windows_exe_executed",
                  "device_tested", "installed", "prefix_created"):
            self.assertIn('"'+s+'": False', VERIFY)
        for term in ("info.st_size > MAX_FILE", "path.is_symlink()",
                     "baseline_source_archive_sha256", "header_log_sha256",
                     "import_log_sha256", "arm64ec_view", "raw_arm64x_carrier",
                     "candidate_imports_not_in_candidate_set",
                     "Unexpected files in sealed candidate artifact"):
            self.assertIn(term, VERIFY)
        self.assertIn("no Wine", SRC)

    def test_only_separate_ci_workflow_is_allowed_to_produce_source_artifact(self):
        self.assertTrue(CI.exists())
        workflow = CI.read_text(encoding="utf-8")
        self.assertIn("next-generation/wine29-deps/", workflow)
        self.assertIn("build-wine29-complete.sh", workflow)
        self.assertIn("verify-wine29-native-compile.py", workflow)
        self.assertIn("build-wine29-deps.sh", workflow)
        self.assertIn("Wine29-07-Source-Built-Six-PE-Dependency-Candidates", workflow)
        self.assertIn("wine29-07-six-candidates.json", workflow)
        self.assertIn("No Android APK or Wineboot", workflow)


if __name__ == "__main__":
    unittest.main()
