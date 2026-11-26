"""Source-only checks for the v25 tray-independent real display publication."""
from pathlib import Path
from importlib.util import module_from_spec, spec_from_file_location
import unittest

ROOT = Path(__file__).resolve().parents[3]
spec = spec_from_file_location("v25_monitor", ROOT / "analysis/wine29_bootstrap/patch_android_monitor_publish.py")
patch = module_from_spec(spec)
spec.loader.exec_module(patch)

def fixture():
    return ("void init_monitors( int width, int height )\n{\n"
            "    virtual_screen_rect.right = width;\n"
            "    virtual_screen_rect.bottom = height;\n"
            "    monitor_rc_work = virtual_screen_rect;\n"
            + patch.ANCHOR + "\n}\nUINT ANDROID_UpdateDisplayDevices(")

class MonitorPublish(unittest.TestCase):
    def test_notification_outside_optional_tray(self):
        result = patch.patch_source(fixture())
        self.assertIn("if (hwnd && NtUserIsWindowVisible( hwnd ) &&", result)
        self.assertIn("if (*p_java_vm && width > 0 && height > 0)", result)
        self.assertEqual(result.count("NtUserCallNoParam( NtUserCallNoParam_DisplayModeChanged );"), 1)
        self.assertNotIn("return;", patch.NEW)
        self.assertIn("monitor_rc_work.bottom = rect.top;", result)
        self.assertIn("monitor_rc_work.top = rect.bottom;", result)
        self.assertLess(result.index("monitor_rc_work = virtual_screen_rect;"),
                        result.index("Wine29 v25 publishing Android display mode"))
    def test_fail_closed(self):
        for source in (fixture() + patch.ANCHOR, patch.patch_source(fixture()),
                       fixture().replace("virtual_screen_rect.right = width;", ""),
                       fixture().replace("if (!hwnd", "if (hwnd")):
            with self.assertRaises(ValueError):
                patch.patch_source(source)
    def test_workflows(self):
        provider = (ROOT / ".github/workflows/wine29-first-provider-crossbuild.yml").read_text()
        light = (ROOT / ".github/workflows/charoite-agent-pr-check.yml").read_text()
        self.assertIn("patch_android_monitor_publish.py", provider)
        self.assertIn('"$build/../dlls/wineandroid.drv/init.c"', provider)
        self.assertIn("test_android_monitor_publish.py", provider)
        self.assertIn("test_android_monitor_publish.py", light)

if __name__ == "__main__":
    unittest.main()
