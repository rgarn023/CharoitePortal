"""Fail-closed WineAndroid v21 recovery for a real surface, never fake pixels."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github/workflows/wine29-first-provider-crossbuild.yml"

def load(name, path):
    spec = spec_from_file_location(name, ROOT / path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

v20 = load("v20_native_replay", "analysis/wine29_bootstrap/patch_android_surface_replay.py")
v21 = load("v21_native_rearm", "analysis/wine29_bootstrap/patch_android_surface_rearm.py")

def v20_source():
    source = ("static void android_surface_flush(void) {\n" + v20.POST_ANCHOR +
              "\n}\n" + v20.DISPATCH + "\n{\n" + v20.HANDLER + "\n}\n")
    return v20.patch_source(source)


class NativeGdiV21Rearm(unittest.TestCase):
    def test_real_driver_surface_required_and_recreated_via_native_win32u(self):
        output = v21.patch_source(v20_source())
        for fragment in (
            "NtUserSetWindowPos( hwnd, NULL, 0, 0, 0, 0,",
            "SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER |",
            "SWP_NOACTIVATE | SWP_FRAMECHANGED",
            "surface = window_surface_get( hwnd );",
            "if (!surface)",
            "surface->funcs != &android_surface_funcs",
            "Wine29 v21 real Android GDI surface attached",
            "Wine29 v21 HWND %p still lacks Android GDI surface after rearm",
            "NtUserRedrawWindow( hwnd, NULL, 0, RDW_INVALIDATE | RDW_UPDATENOW )",
            "window_surface_flush( surface );",
            "window_surface_release( surface );",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, output)
        self.assertEqual(output.count("NtUserSetWindowPos( hwnd, NULL"), 1)
        self.assertEqual(output.count("window_surface_flush( surface );"), 1)
        self.assertEqual(output.count("replay_registered_android_surface( hwnd );"), 1)

    def test_missing_or_non_android_surface_remains_failure_not_success(self):
        output = v21.patch_source(v20_source())
        self.assertLess(output.index("NtUserSetWindowPos( hwnd, NULL"),
                        output.index("Wine29 v21 real Android GDI surface attached"))
        self.assertLess(output.index("Wine29 v21 real Android GDI surface attached"),
                        output.index("window_surface_flush( surface );"))
        for forbidden in (
            "ANativeWindow_lock", "memset( buffer.bits", "ExitProcess(42)",
            "PaintAndroidPixels", "SWP_SHOWWINDOW", "SWP_HIDEWINDOW",
            "SWP_NOREDRAW", "Sleep(", "usleep(",
        ):
            self.assertNotIn(forbidden, v21.NEW)
        self.assertIn('return;', v21.NEW)
        self.assertIn("Wine29 v21 surface still absent after rearm", output)

    def test_fails_closed_on_repeated_or_mismatched_source(self):
        orig = v20_source()
        patched = v21.patch_source(orig)
        for broken in (patched, orig.replace("no Android GDI surface", "unknown GDI backend"),
                       orig.replace("window_surface_flush( surface );", "/* absent */"),
                       orig.replace("replay_registered_android_surface( hwnd );", "/* absent */")):
            with self.subTest(broken=broken[:75]):
                with self.assertRaises(ValueError):
                    v21.patch_source(broken)

    def test_provider_applies_after_v20_only_in_fresh_source(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("test_android_surface_rearm_patch.py", text)
        self.assertIn("patch_android_surface_rearm.py", text)
        self.assertLess(
            text.index("python3 analysis/wine29_bootstrap/patch_android_surface_replay.py"),
            text.index("python3 analysis/wine29_bootstrap/patch_android_surface_rearm.py"))
        self.assertNotIn("adb install", text)
        self.assertIn("wine29-first-provider-candidate", text)


if __name__ == "__main__":
    unittest.main()
