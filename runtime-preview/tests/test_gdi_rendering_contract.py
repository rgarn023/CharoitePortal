"""Contracts for read-only, shared Charoite Core rendering diagnostics."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXE = (ROOT / "charoite-core/rendering/charoite_gdi_probe.c").read_text()
OWNER = (ROOT / "charoite-core/rendering/charoite_ownerdraw_probe.c").read_text()
CORE = (ROOT / "charoite-core/CharoiteRenderingDiagnostics.java").read_text()
PORTAL = (ROOT / "TouhouEntryActivity.java").read_text()
OVERLAY = (ROOT / "overlay.py").read_text()
WORKFLOW = (ROOT.parent / ".github/workflows/runtime-preview.yml").read_text()
DIAGNOSTICS = (ROOT / "charoite-core/CharoiteDiagnostics.java").read_text()

class GdiBaseline(unittest.TestCase):
    def test_real_gdi_unicode_and_cp932_paths(self):
        for expr in ("DrawTextW(dc,jp", "DrawTextA(dc,cp932",
                     "WideCharToMultiByte(932", "GetGlyphIndicesW",
                     "GetTextFaceW", "CreateFontIndirectW"):
            self.assertIn(expr, EXE)
        self.assertIn("Charoite Core GDI read-only diagnostic v1", EXE)

    def test_owner_draw_differential_gdi_methods(self):
        for expr in ("LBS_OWNERDRAWFIXED", "LBS_HASSTRINGS",
                     "WM_DRAWITEM", "DrawTextW(dc,jp",
                     "DrawTextA(dc,ansi", "ExtTextOutW(dc",
                     "ExtTextOutA(dc", "TextOutW(dc",
                     "LB_GETTEXT", "original_unicode_intact"):
            self.assertIn(expr, OWNER)
        for expr in ("SetWindowsHookEx", "RegSetValue",
                     "WriteProcessMemory", "DeleteFileW"):
            self.assertNotIn(expr, OWNER)

    def test_no_auto_launch_or_mutation(self):
        for expr in ("SetWindowTextW(", "RegSetValue", "DeleteFileW(",
                     "WriteProcessMemory", "SetWindowsHookEx"):
            self.assertNotIn(expr, EXE)
        self.assertIn("Only copies a core-owned diagnostic program on explicit request", CORE)
        self.assertIn("rendering/charoite_gdi_probe32.exe", CORE)
        self.assertIn("CharoiteRenderingDiagnostics.prepare(this, containerId)", PORTAL)
        self.assertIn("RUN WINDOWS TEXT RENDERING TEST", PORTAL)
        self.assertIn("RUN OWNER-DRAW TEXT RENDERING TEST", PORTAL)
        self.assertIn("CharoiteRenderingDiagnostics.prepareOwnerDraw(this, containerId)", PORTAL)
        self.assertIn("rendering/charoite_ownerdraw_probe32.exe", CORE)

    def test_report_local_and_scoped(self):
        self.assertIn("CharoiteRenderingDiagnostics.report(context)", DIAGNOSTICS)
        self.assertIn("clearReportForAnotherLaunch(context, executable)", DIAGNOSTICS)
        self.assertIn("PreferenceManager.getDefaultSharedPreferences(host)", CORE)

    def test_wine_rootfs_not_rebuilt_or_changed(self):
        self.assertIn("charoite_gdi_probe32.exe", OVERLAY)
        self.assertIn("charoite_gdi_probe32.exe", WORKFLOW)
        self.assertIn("charoite_ownerdraw_probe32.exe", OVERLAY)
        self.assertIn("charoite_ownerdraw_probe32.exe", WORKFLOW)
        self.assertNotIn("Wine DLL replacement", CORE)

if __name__ == "__main__":
    unittest.main()
