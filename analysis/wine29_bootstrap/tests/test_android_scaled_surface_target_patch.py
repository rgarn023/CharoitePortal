"""V22 scaled-Win32u real Android target gate, source-only and fail-closed."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
WF = ROOT / ".github/workflows/wine29-first-provider-crossbuild.yml"
PR = ROOT / ".github/workflows/charoite-agent-pr-check.yml"

def load(name, path):
    spec = spec_from_file_location(name, ROOT / "analysis/wine29_bootstrap" / path)
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

v20 = load("v22_v20_replay", "patch_android_surface_replay.py")
v21 = load("v22_v21_rearm", "patch_android_surface_rearm.py")
v22 = load("v22_scaled_driver", "patch_android_scaled_surface_target.py")

def example_v21():
    source = ("static void android_surface_flush(void) {\n" + v20.POST_ANCHOR +
              "\n}\n" + v20.DISPATCH + "\n{\n" + v20.HANDLER + "\n}\n")
    return v21.patch_source(v20.patch_source(source))

def example_dce():
    return (
        "struct scaled_surface { struct window_surface header; struct window_surface *target_surface; };\n"
        "static const struct window_surface_funcs scaled_surface_funcs = {0};\n"
        "static struct scaled_surface *get_scaled_surface( struct window_surface *surface ) { return (void *)surface; }\n"
        + v22.DCE_ANCHOR + "\n"
    )

class V22ScaledSurfaceContract(unittest.TestCase):
    def test_underlying_android_target_not_outer_scaled_callback(self):
        window, dce, header = v22.patch_sources(
            example_v21(), example_dce(), v22.HEADER_ANCHOR)
        self.assertIn("window_surface_get_driver( hwnd )", window)
        self.assertIn("target && target->funcs == &android_surface_funcs", window)
        self.assertIn("target != surface", window)
        self.assertIn("Wine29 v22 real Android driver behind Win32u scaled surface", window)
        self.assertEqual(window.count("!wine29_has_android_surface_target( hwnd, surface )"), 2)
        self.assertEqual(window.count("if (surface->funcs != &android_surface_funcs)"), 0)
        self.assertIn("window_surface_flush( surface );", window)
        self.assertEqual(window.count("window_surface_flush( surface );"), 1)
        self.assertIn("W32KAPI struct window_surface *window_surface_get_driver( HWND hwnd )", header)
        self.assertIn("W32KAPI struct window_surface *window_surface_get_driver( HWND hwnd )", dce)

    def test_scaled_driver_handle_has_independent_ref_and_preserves_original(self):
        _, dce, _ = v22.patch_sources(example_v21(), example_dce(), v22.HEADER_ANCHOR)
        self.assertIn("surface->funcs == &scaled_surface_funcs", dce)
        self.assertIn("get_scaled_surface( surface )->target_surface", dce)
        self.assertIn("if (target) window_surface_add_ref( target );", dce)
        self.assertIn("window_surface_release( surface );", dce)
        self.assertIn("return target;", dce)
        self.assertIn("return surface;", dce)
        self.assertEqual(dce.count(v22.DCE_ANCHOR), 1)
        self.assertIn("struct window_surface *surface = window_surface_get( hwnd );", dce)

    def test_real_native_backend_still_required_and_original_rearm_retained(self):
        window, _, _ = v22.patch_sources(example_v21(), example_dce(), v22.HEADER_ANCHOR)
        self.assertIn("return valid;", window)
        self.assertIn("if (target) window_surface_release( target );", window)
        self.assertIn("NtUserSetWindowPos( hwnd, NULL, 0, 0, 0, 0,", window)
        self.assertIn("SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER |", window)
        self.assertIn("SWP_NOACTIVATE | SWP_FRAMECHANGED", window)
        for invalid in ("ExitProcess(42)", "ANativeWindow_lock", "memset( buffer.bits",
                        "PaintAndroidPixels", "Sleep(", "SWP_SHOWWINDOW"):
            self.assertNotIn(invalid, v22.REPLAY_HELPER)
        self.assertIn("wine29_has_android_surface_target( hwnd, surface )", window)

    def test_double_patching_and_drift_fail_closed(self):
        src = (example_v21(), example_dce(), v22.HEADER_ANCHOR)
        patched = v22.patch_sources(*src)
        for broken in (
            patched,
            (src[0].replace("surface->funcs != &android_surface_funcs", "surface->funcs == NULL", 1), src[1], src[2]),
            (src[0], src[1].replace("scaled_surface_funcs", "bad_surface_funcs"), src[2]),
            (src[0], src[1], src[2].replace("window_surface_get", "unsupported_window_surface_get")),
        ):
            with self.subTest(source=broken[0][:30]):
                with self.assertRaises(ValueError):
                    v22.patch_sources(*broken)

    def test_provider_compiles_modified_win32u_and_native_window(self):
        wf = WF.read_text(encoding="utf-8")
        self.assertIn("test_android_scaled_surface_target_patch.py", wf)
        self.assertIn("patch_android_scaled_surface_target.py", wf)
        self.assertLess(
            wf.index("python3 analysis/wine29_bootstrap/patch_android_surface_rearm.py"),
            wf.index("python3 analysis/wine29_bootstrap/patch_android_scaled_surface_target.py"))
        self.assertIn('"$build/../dlls/win32u/dce.c"', wf)
        self.assertIn('"$build/../include/wine/gdi_driver.h"', wf)
        self.assertIn("dlls/wineandroid.drv/wineandroid.so", wf)
        self.assertIn("dlls/win32u/win32u.so", wf)
        self.assertNotIn("adb install", wf)
        self.assertIn("test_android_scaled_surface_target_patch.py", PR.read_text(encoding="utf-8"))

if __name__ == "__main__":
    unittest.main()
