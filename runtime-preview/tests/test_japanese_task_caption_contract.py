"""Guardrails for scoped Win32 Japanese task-label display repair.

These tests cover the repair's source contract and a representative
reversible CP1252/Shift-JIS caption. Wine behavior still needs device testing.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HOOK = (ROOT / "charoite-core/japanese/touhou_font_hook.c").read_text(encoding="utf-8")
HELPER = (ROOT / "charoite-core/japanese/touhou_font_helper.c").read_text(encoding="utf-8")
SUPPORT = (ROOT / "charoite-core/CharoiteJapaneseSupport.java").read_text(encoding="utf-8")


class JapaneseTaskCaptionContract(unittest.TestCase):
    def test_known_cp932_mojibake_can_be_reversed_without_guessing(self):
        japanese = "追加アイコン"
        original_bytes = japanese.encode("cp932")
        corrupted_caption = original_bytes.decode("cp1252")
        self.assertNotEqual(corrupted_caption, japanese)
        self.assertEqual(corrupted_caption.encode("cp1252").decode("cp932"), japanese)
        # Fixed strings need not be hard-coded in the DLL: users can install
        # other Japanese games with completely different checklist labels.
        self.assertNotIn(japanese, HOOK)

    def test_recovery_is_lossless_or_leaves_existing_text_alone(self):
        for fragment in (
            "contains_japanese(wrong)",
            "WC_NO_BEST_FIT_CHARS",
            "MB_ERR_INVALID_CHARS",
            "if (japanese<2) return FALSE;",
            "memcmp(source,roundtrip,source_len)==0",
        ):
            self.assertIn(fragment, HOOK)
        self.assertIn("GetWindowLongPtrW(hwnd,GWL_STYLE)&LBS_HASSTRINGS", HOOK)

    def test_listbox_data_and_check_states_are_never_rewritten(self):
        for fragment in (
            "WH_CALLWNDPROCRET",
            "UnhookWindowsHookEx(drawHook)",
        ):
            self.assertIn(fragment, HELPER)
        for fragment in (
            "WM_DRAWITEM",
            "item->CtlType!=ODT_LISTBOX",
            "installer_task_list(item->hwndItem)",
            "draw_recovered_task",
        ):
            self.assertIn(fragment, HOOK)
        for destructive_operation in (
            "SendMessageW(hwnd,LB_DELETESTRING",
            "SendMessageW(hwnd,LB_INSERTSTRING",
            "SendMessageW(hwnd,LB_SETITEMDATA",
        ):
            self.assertNotIn(destructive_operation, HOOK)

    def test_existing_prefix_receives_updated_helpers_without_reset(self):
        self.assertIn('.touhou-japanese-helpers-v10', SUPPORT)
        self.assertIn('FileUtils.writeString(helperVersion, "v10\\n")', SUPPORT)
        self.assertNotIn("deleteRecursively", SUPPORT)
        self.assertNotIn("formatPrefix", SUPPORT)

    def test_original_unicode_japanese_is_redrawn_without_decoding(self):
        # Real v4 phone diagnostics show already-correct Japanese LB_GETTEXT.
        for codepoints, expected in (
            ([0x30A2,0x30A4,0x30B3,0x30F3,0x3092,0x8FFD,0x52A0,0x3059,0x308B,0x003A], "アイコンを追加する:"),
            ([0x30C7,0x30B9,0x30AF,0x30C8,0x30C3,0x30D7,0x306B,0x30A2,0x30A4,0x30B3,0x30F3,0x3092,0x4F5C,0x6210], "デスクトップにアイコンを作成"),
            ([0x30B9,0x30BF,0x30FC,0x30C8,0x30E1,0x30CB,0x30E5,0x30FC,0x306B,0x767B,0x9332], "スタートメニューに登録"),
        ):
            self.assertEqual("".join(map(chr,codepoints)),expected)
        self.assertIn("originally_japanese=contains_japanese(original)", HOOK)
        self.assertIn("const wchar_t *label=original", HOOK)
        self.assertIn("DrawTextW(dc,label,-1", HOOK)
        self.assertIn("validated_japanese_font_for_row(item->hwndItem,selected)", HOOK)
        self.assertIn("return font_has_japanese(hwnd,font);", HOOK)

    def test_x86_callback_export_matches_real_pe_dll(self):
        # v4's 32-bit DLL exports TouhouDrawHook@12; v4 looked up a
        # leading-underscore name and failed silently.
        self.assertIn('const char *drawExport="TouhouDrawHook@12"', HELPER)
        self.assertIn('const char *drawExport="TouhouDrawHook"', HELPER)
        self.assertIn("WH_CALLWNDPROCRET", HELPER)
        self.assertIn("post-draw hook attach failed win32_error=", HELPER)

    def test_real_installer_charset_audit_is_read_only_and_bounded(self):
        # Thread-scoped pre/post owner-draw snapshots must never be mistaken
        # for an interception of Delphi's transient DrawTextA font selection.
        self.assertIn('const char *auditExport="TouhouAuditHook@12"', HELPER)
        self.assertIn('const char *auditExport="TouhouAuditHook"', HELPER)
        self.assertIn("WH_CALLWNDPROC", HELPER)
        self.assertIn("UnhookWindowsHookEx(auditHook)", HELPER)
        for fragment in (
            "TouhouAuditHook(", "paint_audit_seen[2][2]",
            "audit_installer_paint(item,0)", "audit_installer_paint(item,1)",
            "GetCurrentObject(item->hDC,OBJ_FONT)", "GetTextCharset(item->hDC)",
            "GetTextFaceW(item->hDC", "GetObjectW(listFont",
            "installer_task_list(item->hwndItem)",
            "GetWindowThreadProcessId(item->hwndItem,NULL)!=GetCurrentThreadId()",
            "caption_present=%d japanese_utf16=%d",
            "paint boundary snapshots cannot prove a transient GDI font",
        ):
            self.assertIn(fragment, HOOK)
        for destructive in ("SendMessageW(item->hwndItem,LB_DELETESTRING",
                            "SendMessageW(item->hwndItem,LB_SETITEMDATA"):
            self.assertNotIn(destructive, HOOK)


    def test_prepaint_compatibility_is_scoped_and_restored(self):
        # Row 1 in the real installer began with DC charset 0, whereas the
        # synthetic CP932 ANSI text test worked with SHIFTJIS_CHARSET 128.
        for fragment in (
            "static void select_japanese_before_installer_draw(",
            "static void restore_installer_prepaint(",
            "GetACP()!=932",
            "installer_task_list(item->hwndItem)",
            "GetWindowThreadProcessId(item->hwndItem,NULL)!=GetCurrentThreadId()",
            "read_task_caption(item->hwndItem,item->itemID,text,512)",
            "contains_japanese(text)",
            "SaveDC(item->hDC)", "SelectObject(item->hDC,replacement)",
            "RestoreDC(item->hDC,entry->saved)",
            "select_japanese_before_installer_draw(item);",
            "restore_installer_prepaint(item);",
            "hook-v10 prepaint restored original DC",
            "draw_recovered_task",
        ):
            self.assertIn(fragment, HOOK)
        # A post-draw hook must be available before installing the
        # pre-draw hook, otherwise GDI state might not be restored.
        self.assertLess(HELPER.index("HHOOK drawHook=NULL"),
                        HELPER.index("HHOOK auditHook=NULL"))
        self.assertIn("if(drawHook && auditCallback)", HELPER)
        for destructive in (
            "SendMessageW(hwnd,LB_SETITEMDATA",
            "SendMessageW(hwnd,LB_DELETESTRING",
            "SendMessageW(hwnd,LB_INSERTSTRING",
            "DeleteFileW(",
        ):
            self.assertNotIn(destructive, HOOK)

    def test_repeat_paint_avoids_unneeded_font_and_caption_probes(self):
        self.assertIn("validated_japanese_font_for_row(HWND hwnd, HFONT font)", HOOK)
        self.assertIn("patched_windows[i]==hwnd && patched_fonts[i]==font", HOOK)
        self.assertIn("return font_has_japanese(hwnd,font);", HOOK)
        self.assertIn("validated_japanese_font_for_row(item->hwndItem,selected)", HOOK)
        self.assertIn("if(oldCharset==SHIFTJIS_CHARSET)", HOOK)
        self.assertLess(HOOK.index("if(oldCharset==SHIFTJIS_CHARSET)"),
                        HOOK.index("read_task_caption(item->hwndItem,item->itemID,text,512)"))
        self.assertIn("hook-v10 UI-scan slowest_ms=", HOOK)
        self.assertIn("hook-v10 Unicode fallback slowest_ms=", HOOK)
        self.assertIn("RestoreDC(item->hDC,entry->saved)", HOOK)
        self.assertIn("draw_recovered_task", HOOK)


    def test_summary_page_display_queues_urgent_font_scan(self):
        # Summary-page memos can appear between 300 ms scans. Use deferred,
        # coalesced urgent scans after the VCL page/control event completes.
        for needle in (
            "static void queue_visible_page_scan(",
            "inside_installer_wizard(event->hwnd)",
            "WM_SHOWWINDOW", "WM_WINDOWPOSCHANGED",
            "WM_PARENTNOTIFY", "WM_SETTEXT",
            "SWP_SHOWWINDOW",
            "PostMessageW(event->hwnd,WM_NULL,0,0)",
            "page_rescan_requested=TRUE",
            "now-last_scan_tick>=15",
            "hook-v10 page-event fast-scan kind=",
            "hook-v10 summary-memo Japanese font applied",
            "request_to_scan_ms=%lu",
        ):
            self.assertIn(needle, HOOK)
        self.assertIn("GetWindowThreadProcessId(hwnd,NULL)!=GetCurrentThreadId()", HOOK)
        self.assertIn("BOOL urgent=page_rescan_requested", HOOK)
        self.assertLess(HOOK.index("page_rescan_requested=FALSE;\n            scan_started=TRUE"),
                        HOOK.index("EnumThreadWindows(GetCurrentThreadId(),wizard_callback,0);"))
        self.assertIn("draw_recovered_task", HOOK)
        self.assertIn("RestoreDC(item->hDC,entry->saved)", HOOK)
        self.assertNotIn("SendMessageW(hwnd,LB_DELETESTRING", HOOK)

    def test_header_repaint_removes_prefix_without_touching_checkbox_gutter(self):
        # Phone screenshot shows erroneous '|A|C|' before the correct
        # Unicode section heading. It is not part of LB_GETTEXT.
        self.assertIn('BOOL section_header=(item->itemID==0', HOOK)
        self.assertIn("!(item->itemState & ODS_SELECTED)", HOOK)
        self.assertIn("label[label_len-1]==L':'", HOOK)
        self.assertIn("region.left+=section_header ? 2 : GetSystemMetrics(SM_CXMENUCHECK)+14;", HOOK)
        self.assertIn("complete unselected section heading repainted", HOOK)
        self.assertNotIn("SendMessageW(hwnd,LB_SETITEMDATA", HOOK)

    def test_faster_scoped_repair_setup(self):
        probe = (ROOT / "charoite-core/japanese/touhou_probe.c").read_text(encoding="utf-8")
        overlay = (ROOT / "overlay.py").read_text(encoding="utf-8")
        self.assertIn("Thread.sleep(100)", overlay)
        self.assertIn("Sleep(pass < 120 ? 150 : 500);", probe)
        self.assertIn("interval=(diagnosed_count[0]>0 ? 300 : 100)", HOOK)
        self.assertIn("Sleep(200);", HELPER)


if __name__ == "__main__":
    unittest.main()
