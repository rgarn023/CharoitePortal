"""v23 native GDI creation gate: visible-only, source-pinned, fail-closed."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
WF = ROOT / ".github/workflows/wine29-first-provider-crossbuild.yml"
LIGHT = ROOT / ".github/workflows/charoite-agent-pr-check.yml"

def load(name, filename):
    spec = spec_from_file_location(name, ROOT / "analysis/wine29_bootstrap" / filename)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

v20 = load("v23_replay", "patch_android_surface_replay.py")
v21 = load("v23_rearm", "patch_android_surface_rearm.py")
v22 = load("v23_scaled", "patch_android_scaled_surface_target.py")
v23 = load("v23_create", "patch_android_visible_surface_create.py")

def native_window():
    initial = ("static void android_surface_flush(void) {\n" +
               v20.POST_ANCHOR + "\n}\n" + v20.DISPATCH +
               "\n{\n" + v20.HANDLER + "\n}\n" + v23.ANDROID_ANCHOR + "\n")
    return v22.patch_sources(v21.patch_source(v20.patch_source(initial)),
                             v22.DCE_ANCHOR.replace("window_surface_get", "window_surface_get"),
                             v22.HEADER_ANCHOR)[0]

class VisibleGdiNativeGate(unittest.TestCase):
    def setUp(self):
        self.window = native_window()
        self.win32u = "void example(void) {\n" + v23.WIN32U_ANCHOR + "\n}\n"

    def test_visible_only_native_creation_and_no_fake_frame(self):
        native, w32 = v23.patch_sources(self.window, self.win32u)
        self.assertIn("if (!NtUserIsWindowVisible( hwnd ))", native)
        self.assertIn("SWP_NOACTIVATE | SWP_FRAMECHANGED | SWP_SHOWWINDOW", native)
        self.assertIn("Win32u GDI allocation gate", w32)
        self.assertIn("Wine29 v23 Win32u calling native CreateWindowSurface", w32)
        self.assertIn("Wine29 v23 native Android CreateWindowSurface request", native)
        self.assertIn("Wine29 v23 created real Android GDI surface", native)
        self.assertIn("Wine29 v23 Android window data missing", native)
        self.assertIn("Wine29 v23 Android GDI DIB allocation failed", native)
        self.assertIn("wine29_has_android_surface_target( hwnd, surface )", native)
        self.assertIn("window_surface_flush( surface );", native)
        self.assertIn("return TRUE; /* retain original fail-closed default behavior */", native)
        self.assertEqual(native.count("SWP_SHOWWINDOW"), 1)
        self.assertEqual(native.count("NtUserSetWindowPos( hwnd, NULL"), 1)
        for forbidden in ("ExitProcess(42)", "ANativeWindow_lock", "memset( buffer.bits",
                          "SWP_HIDEWINDOW", "SWP_NOREDRAW", "Sleep("):
            self.assertNotIn(forbidden, v23.REARM_NEW + v23.ANDROID_NEW)

    def test_exact_source_drift_and_reapply_fail_closed(self):
        orig = (self.window, self.win32u)
        patched = v23.patch_sources(*orig)
        cases = (
            patched,
            (self.window.replace("SWP_NOACTIVATE | SWP_FRAMECHANGED", "SWP_NOACTIVATE", 1), self.win32u),
            (self.window.replace("Wine29 v21 rearming", "unrelated native refresh"), self.win32u),
            (self.window, self.win32u.replace("else if (needs_surface)", "else if (FALSE)")),
            (self.window.replace("wine29_has_android_surface_target( hwnd, surface )", "1"), self.win32u),
        )
        for bad in cases:
            with self.subTest(source=bad[0][:30]):
                with self.assertRaises(ValueError):
                    v23.patch_sources(*bad)

    def test_real_provider_and_lightweight_ci_include_v23(self):
        workflow = WF.read_text(encoding="utf-8")
        self.assertIn("test_android_visible_surface_create_patch.py", workflow)
        self.assertIn("patch_android_visible_surface_create.py", workflow)
        self.assertLess(workflow.index("python3 analysis/wine29_bootstrap/patch_android_scaled_surface_target.py"),
                        workflow.index("python3 analysis/wine29_bootstrap/patch_android_visible_surface_create.py"))
        self.assertIn('"$build/../dlls/win32u/window.c"', workflow)
        self.assertIn('"$build/../dlls/wineandroid.drv/window.c"', workflow)
        self.assertIn("test_android_visible_surface_create_patch.py", LIGHT.read_text(encoding="utf-8"))
        self.assertNotIn("adb install", workflow)

if __name__ == "__main__":
    unittest.main()
