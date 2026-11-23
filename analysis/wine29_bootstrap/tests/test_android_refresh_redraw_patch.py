"""Source-only GDI repaint recovery contract for the pinned WineAndroid handler."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
PATCHER = ROOT / "analysis/wine29_bootstrap/patch_android_refresh_redraw.py"
WORKFLOW = ROOT / ".github/workflows/wine29-first-provider-crossbuild.yml"
spec = spec_from_file_location("android_refresh_redraw", PATCHER)
mod = module_from_spec(spec)
spec.loader.exec_module(mod)

# Exact upstream Wine29 event hook retained, including its GL-only path.
BASELINE = """LRESULT ANDROID_WindowMessage( HWND hwnd, UINT msg, WPARAM wp, LPARAM lp )
{
    switch (msg)
    {
    case WM_ANDROID_REFRESH:
        if (wp)  /* opengl client window */
        {
            update_gl_drawable( hwnd );
        }
        else
        {
            NtUserExposeWindowSurface( hwnd, 0, NULL, 0 );
        }
        return 0;
    default:
        return 0;
    }
}"""


class RefreshRedraw(unittest.TestCase):
    def test_invalidate_only_after_registration_and_for_visible_cpu_window(self):
        updated = mod.patch_source(BASELINE)
        self.assertEqual(updated.count("NtUserExposeWindowSurface( hwnd, 0, NULL, 0 );"), 1)
        self.assertIn("if (NtUserIsWindowVisible( hwnd ))", updated)
        self.assertIn("NtUserRedrawWindow( hwnd, NULL, 0, RDW_INVALIDATE | RDW_UPDATENOW )", updated)
        self.assertIn("Could not redraw newly registered Android HWND", updated)
        self.assertLess(updated.index("NtUserExposeWindowSurface("), updated.index("NtUserRedrawWindow("))
        self.assertEqual(updated.count("update_gl_drawable( hwnd );"), 1)
        self.assertIn("if (wp)  /* opengl client window */", updated)
        self.assertNotIn("ANativeWindow_lock", updated)
        self.assertNotIn("FillRect(", updated)
        self.assertNotIn("ExitProcess(", updated)

    def test_no_double_apply_or_unrecognized_source(self):
        with self.assertRaises(ValueError):
            mod.patch_source(mod.patch_source(BASELINE))
        for changed in (
            BASELINE.replace("NtUserExposeWindowSurface", "NtUserExposeWindowSurfaceBROKEN"),
            BASELINE.replace("if (wp)", "if (unknown)"),
            BASELINE + BASELINE,
        ):
            with self.assertRaises(ValueError):
                mod.patch_source(changed)

    def test_native_provider_crossbuild_runs_source_test_and_applies_patch(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("test_android_refresh_redraw_patch.py", workflow)
        self.assertIn("patch_android_refresh_redraw.py", workflow)
        self.assertIn("patch_android_surface_flush.py", workflow)
        self.assertLess(workflow.index("patch_android_surface_flush.py \\"), workflow.index("patch_android_refresh_redraw.py \\"))
        self.assertLess(workflow.index("patch_android_refresh_redraw.py \\"), workflow.index("make -j2 \\"))
        self.assertIn("branches: [main]", workflow)
        self.assertNotIn("adb install", workflow)


if __name__ == "__main__":
    unittest.main()
