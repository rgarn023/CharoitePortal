"""Native-only, user-initiated Wine --version smoke guardrails for Next v0.5."""
import importlib.util
from pathlib import Path
import struct
import unittest

ROOT=Path(__file__).resolve().parents[1]
STAGER=(ROOT/"stage_native_wine_loader.py").read_text(encoding="utf-8")
JAVA=(ROOT/"CharoiteWineNativeProbe.java").read_text(encoding="utf-8")
SERVER_JAVA=(ROOT/"CharoiteWineServerProbe.java").read_text(encoding="utf-8")
PREP=(ROOT/"prepare_next.py").read_text(encoding="utf-8")
WORKFLOW=(ROOT.parent/".github/workflows/charoite-next.yml").read_text(encoding="utf-8")
spec=importlib.util.spec_from_file_location("native_wine_stage",ROOT/"stage_native_wine_loader.py")
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

def elf(kind=3,machine=183):
    data=bytearray(128)
    data[:6]=b"\x7fELF\x02\x01"
    struct.pack_into("<H",data,16,kind)
    struct.pack_into("<H",data,18,machine)
    return bytes(data)

class NativeVersionProbeTest(unittest.TestCase):
    def test_elf64_pie_arm64_only(self):
        self.assertTrue(mod.validate_loader(elf()))
        for bad in (b"MZ"+bytes(120),elf(machine=62),elf(kind=2),bytes(128)):
            with self.assertRaises(ValueError):mod.validate_loader(bad)
    def test_pin_source_artifact_and_manifest(self):
        for value in ("40898982875","12908731604",
                      "5d07e29fdba6552033d5f1a1a50ff1cc2fffe420",
                      "verify-bootstrap-bundle.py",
                      "wine10-arm64ec-bootstrap.0.4",
                      "component_count","nls_count", "22","76",
                      "Refusing to overwrite existing native smoke payload",
                      "libcharoite_wine_ntdll.so","ntdll_sha256","ntdll_size",
                      "CHAROITE_NTDLL_NATIVE_DIR"):
            self.assertIn(value,STAGER)
        for value in ("40898982875","Charoite-Wine-Coherent-Bootstrap-22-Experimental",
                      "stage_native_wine_loader.py","libcharoite_wine_loader.so",
                      "CHAROITE_NEXT_WINE_NATIVE_APK_LOADER_VERIFIED=PASS",
                      "CHAROITE_NEXT_WINE_APK_NTDLL_VERIFIED=PASS"):
            self.assertIn(value,WORKFLOW)
    def test_device_isolation_and_non_destructive_execution(self):
        for value in ('PACKAGE = "com.charoitx"',
                      'NATIVE_FILE = "libcharoite_wine_loader.so"',
                      'new ProcessBuilder(loader.getAbsolutePath(), "--version")',
                      "nativeLibraryDir", "sha256(loader)",
                      "sha256(ntdll)", "CHAROITE_NTDLL_NATIVE_DIR",
                      "env.clear()", "TIMEOUT_SECONDS = 7L",
                      "WINEPREFIX", "NO prefix"[:2], "source_run"):
            self.assertIn(value,JAVA)
        self.assertNotIn('"wineboot.exe"',JAVA)
        for bad in ("deleteRecursively","Runtime.getRuntime().exec","su -c",
                    "clearApplicationUserData","ProcessBuilder(\"sh\"",
                    "new File(context.getFilesDir(),"):
            self.assertNotIn(bad,JAVA)
        for bad in ("adb install","rm -rf","WINEPREFIX=","/data/data/com.charoite/files"):
            self.assertNotIn(bad,STAGER)
    def test_verified_native_wineserver_probe_is_version_only(self):
        for value in ("wineserver_native_library_filename", "wineserver_sha256",
                      "wineserver_size", "wineserver_needed",
                      "libcharoite_wineserver.so",
                      'tar.extractfile("runtime/bin/wineserver")',
                      'SERVER_LIB', "validate_loader(server_raw)",
                      'doNotStrip "**/libcharoite_wineserver.so"'):
            self.assertIn(value, STAGER)
        for value in ("libcharoite_wineserver.so", "source_code_sha",
                      "sha256", "hash(server)",
                      'new ProcessBuilder(server.getAbsolutePath(), "--version")',
                      "env.clear()", "waitFor(7, TimeUnit.SECONDS)",
                      "Existing game/save/prefix data: NOT ACCESSED",
                      "Wineserver session: NOT STARTED"):
            self.assertIn(value, SERVER_JAVA)
        for danger in ('"wineboot.exe"', 'new File(context.getFilesDir()',
                       "clearApplicationUserData", "deleteRecursively",
                       '"WINEPREFIX"', '"HOME"', "Runtime.getRuntime().exec"):
            self.assertNotIn(danger, SERVER_JAVA)
        self.assertIn("CharoiteWineServerProbe.java",PREP)
        self.assertIn("Test source-built wineserver --version",PREP)


        for value in ('versionCode 61','11.2-next.0.30',
                      "CharoiteWineNativeProbe.java",
                      "Test source-built Wine --version","Run Core Next device diagnostics",
                      "new Thread(() ->"):
            self.assertIn(value,PREP)
        self.assertIn("launch_ready",STAGER)
        self.assertIn("installable_as_runtime",STAGER)
        self.assertNotIn("WINEPREFIX=",PREP)

if __name__=="__main__":unittest.main()
