# Wine Notepad Japanese README compatibility

Observed on Galaxy S26 Ultra with TPDP original setup.exe: the installer
wizard correctly displays Japanese using Core's CP932/IPA font repair,
but the post-setup ReadMe.txt launches in Wine Notepad with Japanese
characters appearing as empty boxes. Japanese Notepad menus and its title
are localized, proving that the editor's document font is a separate path.

Wine's built-in Notepad initializes its text Edit control with the
`System` font and `DEFAULT_CHARSET`. It reads `lfFaceName` and
`lfCharSet` from HKCU\\Software\\Microsoft\\Notepad. The original
README's bytes are decoded using the process ANSI code page (CP_ACP)
when it is not BOM-marked Unicode.

Charoite Core's Japanese opt-in already bundles true `IPAGothic`
and `IPAPGothic` fonts, and TPDP's setup.exe proves ACP=932.
The new narrowly scoped compatibility default:
- sets Notepad's `lfFaceName` to `IPAGothic` only when absent or `System`;
- sets `lfCharSet` to 128 (SHIFTJIS_CHARSET) only when missing,
  DEFAULT_CHARSET (1) or ANSI_CHARSET (0);
- leaves a custom Notepad face or nondefault charset untouched;
- applies even on existing Japanese font-v5 prefixes, without resetting them;
- never reads or modifies the ReadMe.txt content, installed game, saves,
  or unrelated program/editor fonts.

This is a **font correction**, not a file recoding operation. If boxes
remain after the new APK and reopening the ReadMe, capture another screenshot.
The original file's byte encoding or Wine's edit-control glyph fallback would
then need further inspection. Do not claim success until device-confirmed.

Wine upstream references:
- https://github.com/wine-mirror/wine/blob/master/programs/notepad/main.c
- https://github.com/wine-mirror/wine/blob/master/programs/notepad/dialog.c
