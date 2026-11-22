"""Fast, source-only tests for the pinned WineAndroid CPU flush failure gate."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
PATCHER = ROOT / "analysis/wine29_bootstrap/patch_android_surface_flush.py"
WORKFLOW = ROOT / ".github/workflows/wine29-first-provider-crossbuild.yml"

spec = spec_from_file_location("android_surface_flush_gate", PATCHER)
module = module_from_spec(spec)
spec.loader.exec_module(module)

# Exact pinned Wine source anchors, with a representative shortened loop body.
PINNED = r'''static BOOL android_surface_flush( struct window_surface *window_surface, const RECT *rect, const RECT *dirty,
                                   const BITMAPINFO *color_info, const void *color_bits, BOOL shape_changed,
                                   const BITMAPINFO *shape_info, const void *shape_bits )
{
    struct android_window_surface *surface = get_android_surface( window_surface );
    ANativeWindow_Buffer buffer;
    ARect rc;

    rc.left = dirty->left;
    if (!surface->window->perform( surface->window, NATIVE_WINDOW_LOCK, &buffer, &rc ))
    {
        /* source uses the CPU copy loop here */
        surface->window->perform( surface->window, NATIVE_WINDOW_UNLOCK_AND_POST );
    }
    else TRACE( "Unable to lock surface %p window %p buffer %p\n",
                surface, window_surface->hwnd, surface->window );

    return TRUE;
}'''


class FlushGate(unittest.TestCase):
    def test_missing_window_lock_error_and_post_error_fail_closed(self):
        updated = module.patch_source(PINNED)
        self.assertIn('if (!surface->window)', updated)
        self.assertIn('int status;', updated)
        self.assertIn('status = surface->window->perform( surface->window, NATIVE_WINDOW_LOCK', updated)
        self.assertIn('status = surface->window->perform( surface->window, NATIVE_WINDOW_UNLOCK_AND_POST', updated)
        self.assertEqual(updated.count('return FALSE;'), 3)
        self.assertIn('Unable to post Android surface', updated)
        self.assertIn('Unable to lock Android surface', updated)
        self.assertIn('return TRUE;', updated)  # Only reached after both operations succeed.

    def test_unexpected_source_fails_instead_of_guessing(self):
        for edited in (
            PINNED.replace('NATIVE_WINDOW_LOCK', 'NATIVE_WINDOW_FAKE'),
            PINNED.replace('NATIVE_WINDOW_UNLOCK_AND_POST', 'NATIVE_WINDOW_UNKNOWN'),
            PINNED + PINNED,
        ):
            with self.assertRaises(ValueError):
                module.patch_source(edited)

    def test_workflow_checks_patch_before_crossbuilding(self):
        workflow = WORKFLOW.read_text(encoding='utf-8')
        self.assertIn('analysis/wine29_bootstrap/patch_android_surface_flush.py', workflow)
        self.assertIn('test_android_surface_flush_patch.py', workflow)
        self.assertNotIn('adb install', workflow)


if __name__ == '__main__':
    unittest.main()
