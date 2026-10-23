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
        self.assertIn('.touhou-japanese-helpers-v5', SUPPORT)
        self.assertIn('FileUtils.writeString(helperVersion, "v5\\n")', SUPPORT)
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
        self.assertIn("font_has_japanese(item->hwndItem,selected)", HOOK)

    def test_x86_callback_export_matches_real_pe_dll(self):
        # v4's 32-bit DLL exports TouhouDrawHook@12; v4 looked up a
        # leading-underscore name and failed silently.
        self.assertIn('const char *drawExport="TouhouDrawHook@12"', HELPER)
        self.assertIn('const char *drawExport="TouhouDrawHook"', HELPER)
        self.assertIn("WH_CALLWNDPROCRET", HELPER)
        self.assertIn("post-draw hook attach failed win32_error=", HELPER)


if __name__ == "__main__":
    unittest.main()
