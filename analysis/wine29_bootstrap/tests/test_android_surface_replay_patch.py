"""Fail-closed native window-surface replay contract; does not create fake pixels."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
PATCHER = ROOT / "analysis/wine29_bootstrap/patch_android_surface_replay.py"
WORKFLOW = ROOT / ".github/workflows/wine29-first-provider-crossbuild.yml"
spec = spec_from_file_location("native_replay", PATCHER)
mod = module_from_spec(spec)
spec.loader.exec_module(mod)

def sample_source():
    # Exact post-v19 surface-refresh and post-error-gate fragments.
    return ("static void android_surface_flush(void) {\n"
            + mod.POST_ANCHOR + "\n}\n"
            + mod.DISPATCH + "\n{\n"
            + mod.HANDLER + "\n}\n")

class NativeGdiReplayContract(unittest.TestCase):
    def test_only_actual_window_bitmap_is_marked_dirty_and_flushed(self):
        patched = mod.patch_source(sample_source())
        self.assertIn("struct window_surface *surface = window_surface_get( hwnd );", patched)
        self.assertIn("surface->funcs != &android_surface_funcs", patched)
        self.assertIn("full = surface->rect;", patched)
        self.assertIn("OffsetRect( &full, -full.left, -full.top );", patched)
        self.assertIn("if (!IsRectEmpty( &full ))", patched)
        self.assertIn("window_surface_lock( surface );", patched)
        self.assertIn("surface->bounds = full;", patched)
        self.assertIn("window_surface_unlock( surface );", patched)
        self.assertIn("window_surface_flush( surface );", patched)
        self.assertIn("window_surface_release( surface );", patched)
        self.assertIn("replay_registered_android_surface( hwnd );", patched)
        self.assertIn("NtUserRedrawWindow( hwnd, NULL, 0, RDW_INVALIDATE | RDW_UPDATENOW )", patched)
        self.assertIn("Wine29 native GDI buffer posted", patched)

    def test_no_android_buffer_injection_or_false_success(self):
        patched = mod.patch_source(sample_source())
        for prohibited in ("ANativeWindow_lock", "memset( buffer.bits", "ExitProcess(42)",
                           "PaintAndroidPixels", "wine_surface_changed("):
            self.assertNotIn(prohibited, patched)
        self.assertEqual(patched.count("replay_registered_android_surface( hwnd );"), 1)
        self.assertEqual(patched.count("window_surface_flush( surface );"), 1)

    def test_fail_closed_on_double_patch_or_changed_vendor_layout(self):
        patched = mod.patch_source(sample_source())
        with self.assertRaises(ValueError):
            mod.patch_source(patched)
        for broken in (
            sample_source().replace("RDW_UPDATENOW", "RDW_ERASE"),
            sample_source().replace("NATIVE_WINDOW_UNLOCK_AND_POST", "UNKNOWN_POST"),
            sample_source().replace("ANDROID_WindowMessage", "BROKEN_WindowMessage"),
            sample_source() + mod.HANDLER,
        ):
            with self.assertRaises(ValueError):
                mod.patch_source(broken)

    def test_provider_isolation_and_ordering(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("test_android_surface_replay_patch.py", workflow)
        self.assertIn("patch_android_surface_replay.py", workflow)
        self.assertLess(workflow.index("python3 analysis/wine29_bootstrap/patch_android_surface_flush.py"),
                        workflow.index("python3 analysis/wine29_bootstrap/patch_android_refresh_redraw.py"))
        self.assertLess(workflow.index("python3 analysis/wine29_bootstrap/patch_android_refresh_redraw.py"),
                        workflow.index("python3 analysis/wine29_bootstrap/patch_android_surface_replay.py"))
        self.assertNotIn("adb install", workflow)

if __name__ == "__main__":
    unittest.main()
