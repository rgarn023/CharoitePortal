"""v24 real GDI allocation: preserve an explicit visible/dummy SHOWWINDOW gate only."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "analysis/wine29_bootstrap/patch_android_visible_dummy_swp_gate.py"
WF = ROOT / ".github/workflows/wine29-first-provider-crossbuild.yml"
LIGHT = ROOT / ".github/workflows/charoite-agent-pr-check.yml"

spec = spec_from_file_location("v24_dummy_gate", SCRIPT)
v24 = module_from_spec(spec)
spec.loader.exec_module(v24)


def make_pinned_window():
    return (
        "static BOOL fixup_swp_flags( WINDOWPOS *winpos, const RECT *old_window_rect, int parent_x, int parent_y )\n"
        "{\n" + v24.ANCHOR + "\n}\n"
        "static void example(void) {\n"
        "surface = get_window_surface( winpos->hwnd, winpos->flags, FALSE, &new_rects, &surface_rect );\n"
        "else if (swp_flags & SWP_SHOWWINDOW) needs_surface = TRUE;\n"
        "TRACE( \"Wine29 v23 Win32u calling native CreateWindowSurface HWND %p\\n\", hwnd );\n"
        "}\n"
    )

class VisibleDummySurfaceRearm(unittest.TestCase):
    def test_safely_retains_exact_gate_for_one_dummy_top_level_rearm(self):
        result = v24.patch_source(make_pinned_window())
        for required in (
            "win->surface == &dummy_surface",
            "!(win->dwStyle & WS_CHILD)",
            "const UINT rearm = SWP_SHOWWINDOW | SWP_FRAMECHANGED",
            "SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER",
            "SWP_NOACTIVATE",
            "if ((winpos->flags & rearm) == rearm",
            "else winpos->flags &= ~SWP_SHOWWINDOW;",
            "Wine29 v24 preserving SHOWWINDOW for dummy GDI HWND",
            "if (swp_flags & SWP_SHOWWINDOW) needs_surface = TRUE;",
        ):
            with self.subTest(required=required):
                self.assertIn(required, result)
        self.assertEqual(result.count("Wine29 v24 preserving SHOWWINDOW"), 1)
        self.assertEqual(result.count("surface = get_window_surface("), 1)
        self.assertEqual(result.count("winpos->flags &= ~SWP_SHOWWINDOW;"), 1)

    def test_no_forced_success_or_general_window_policy_change(self):
        for forbidden in (
            "ExitProcess(42)", "ANativeWindow_lock", "memset( buffer.bits",
            "SWP_HIDEWINDOW | SWP_SHOWWINDOW", "SWP_NOREDRAW |",
            "NtUserSetWindowLong", "NtUserShowWindow", "Sleep(",
            "isWindowVisible = TRUE",
        ):
            self.assertNotIn(forbidden, v24.NEW)
        self.assertIn("if (win->dwStyle & WS_VISIBLE)", v24.NEW)
        self.assertIn("else\n    {\n        winpos->flags &= ~SWP_HIDEWINDOW;", v24.NEW)
        self.assertNotIn("win->surface = ", v24.NEW)

    def test_double_patch_and_incompatible_source_fail_closed(self):
        original = make_pinned_window()
        cases = (
            v24.patch_source(original),
            original.replace("win->dwStyle & WS_VISIBLE", "win->dwStyle & WS_CHILD"),
            original.replace("if (swp_flags & SWP_SHOWWINDOW)", "if (FALSE)"),
            original.replace("Wine29 v23 Win32u calling", "unsupported driver"),
            original.replace("surface = get_window_surface(", "surface = NULL; //"),
            original + v24.ANCHOR,
        )
        for text in cases:
            with self.subTest(case=text[:90]):
                with self.assertRaises(ValueError):
                    v24.patch_source(text)

    def test_provider_source_order_and_lightweight_contract(self):
        workflow = WF.read_text(encoding="utf-8")
        self.assertIn("patch_android_visible_dummy_swp_gate.py", workflow)
        self.assertIn("test_android_visible_dummy_swp_gate.py", workflow)
        self.assertLess(
            workflow.index("python3 analysis/wine29_bootstrap/patch_android_visible_surface_create.py"),
            workflow.index("python3 analysis/wine29_bootstrap/patch_android_visible_dummy_swp_gate.py"))
        self.assertIn('"$build/../dlls/win32u/window.c"', workflow)
        self.assertIn("test_android_visible_dummy_swp_gate.py", LIGHT.read_text(encoding="utf-8"))
        self.assertNotIn("adb install", workflow)


if __name__ == "__main__":
    unittest.main()
