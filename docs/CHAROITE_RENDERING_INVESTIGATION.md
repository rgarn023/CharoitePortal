# Charoite Core: Windows text rendering investigation

This is the start of a **general** rendering compatibility investigation,
not a claim that the present Wine/Delphi owner-draw issue is fixed.

## What the Touhou installer proved

The v4 device logs showed Japanese ACP=932 and correct LB_GETTEXT Unicode
task labels, while the Delphi TNewCheckListBox rendered them incorrectly.
The v5-v6 scoped helper repaints those controls after the application's
original draw. That is a workaround, not a Wine GDI patch.

## Phase 1 - repeatable, non-destructive baseline

Charoite Core ships a small Win32 GDI test executable, launched manually from
the Portal's System page in any environment. It shows the same Japanese string
through **DrawTextW** and **DrawTextA (CP932)** under four logical font names,
records ACP/OEMCP, resolved font faces, and glyph coverage, and writes a local
report. Nothing is transmitted. No game files, Wine registries, or Windows
DLLs are changed. User closes the test like any Windows window.

Interpretation:
- W and A both correct: investigate the affected application's owner-draw
  canvas/selected font or a specific GDI call path, not generic decoding.
- W correct but A corrupt: investigate Wine's ANSI conversion and ACP path.
- Both corrupt or missing: investigate actual selected font, Fontconfig,
  FreeType and GDI32/WIN32U font rendering.
- Different results across environments: inspect environment-specific
  locale, font mapping and prefix registry configuration.

Neither this synthetic test nor CI alone establishes real-device correctness.

## When to modify Wine

Only after reproducing a specific defect in Wine's GDI path, preserve the
unmodified runtime, pin the matching Wine source release/build configuration,
create an independently testable patch against the actual affected layer,
and build the changed Wine DLLs/binaries for the same architecture and ABI.
Current Portal packages **prebuilt Wine** within the upstream rootfs archive;
there is no Wine-from-source build stage today.

Do not install a different Wine runtime, erase a prefix, or modify a user's
installed game without a separate, reversible migration and passing tests.

## Phase 2

Add opt-in per-application GDI API tracing if the baseline test passes;
target the actual owner's DrawText/ExtTextOutW calls, DC font and charset
rather than doing a delayed visual overwrite. Limit logs to test strings
or metadata and obtain user approval before capturing other game text.

## Phase 3

If a Wine bug is isolated, build a pinned patched Wine variant as an optional
side-by-side compatibility profile. Keep upstream attribution and licensing.


## Phase 2a - differential owner-draw baseline (implemented)

The user's actual GDI test on Galaxy S26 Ultra showed all four font
faces produce correct Japanese characters through both DrawTextW and DrawTextA.
ACP/OEMCP was 932 and glyph coverage was complete. This excludes a broad,
always-failing GDI Japanese rendering issue under those test conditions.

The new **Run Owner-Draw Text Rendering Test** uses an isolated native Win32
LBS_OWNERDRAWFIXED | LBS_HASSTRINGS control, placing the same known Japanese
text into each list row and drawing it with DrawTextW, DrawTextA, ExtTextOutW,
ExtTextOutA, and TextOutW respectively. It records original LB_GETTEXT
fidelity, resolved font, charset and GDI success codes. Compare the visible
rows and copy the local diagnostic report.

This is not a full simulation of Delphi TNewCheckListBox's drawing code.
If the native owner-drawn rows also pass, focus further efforts on the
Delphi/VCL control font/charset selection and drawing-path behavior. If a
specific GDI operation fails, reproduce that operation under stock Wine
before considering a Wine patch.

Do not call this a universal fix or remove the existing scoped workaround.

## Phase 2b - font charset differential (implemented)

The first owner-draw test passed on Galaxy S26 Ultra for all five GDI APIs
using a font explicitly requested with SHIFTJIS_CHARSET (128). This makes
core Wine rendering failures less likely under that known-good configuration.

The next owner-draw test (v2) retains the five original rows and adds six
font-character-set cases using DEFAULT_CHARSET (1) and ANSI_CHARSET (0).
The face requested remains IPAPGothic. It records the requested charset,
GetTextCharset as actually selected, and the mapped face for each draw.
Rows below the first five require scrolling inside the test list.

If DEFAULT/ANSI rows reproduce the installer-like corruption, investigate
font-charset propagation in Delphi/VCL and the selected GDI device context.
If all rows pass, we must instrument the actual Inno TNewCheckListBox at
draw-time before deciding any general Wine or Core behavior change.

No Wine binaries, registry settings or user saves are modified by this test.


## Phase 2c - phone-safe paging (implemented)

On a Galaxy S26 Ultra, the v2 Win32 owner-draw test could not be scrolled
using touch. A user does not need a touchscreen-to-mouse wheel workaround.
The v3 test uses visible FIRST 5 TESTS / LAST 6 TESTS Win32 buttons near
the top of the window, with 64-pixel test rows fitting the test viewport.
Clicking the second button redraws the synthetic list with test indices 5..10,
records each drawing result and font mapping, and logs the page transition.
No other process or persistent game data is modified.

## Phase 2d - original Inno checklist draw-boundary font audit (implemented)

The Galaxy owner-draw v3 results reproduce Japanese corruption only for the
two ANSI A calls where an IPAPGothic font is selected with ANSI_CHARSET
0 (Western-1252). SHIFTJIS_CHARSET 128 and DEFAULT_CHARSET 1 (resolved to
128) work for the same CP932 bytes. All Unicode W calls work.

The original TPDP installer still requires a real call-path diagnosis:
Charoite's opt-in installer helper now installs a read-only pre-draw
WH_CALLWNDPROC audit alongside the existing post-draw
WH_CALLWNDPROCRET repaint fallback, strictly in the already-identified
TWizardForm GUI thread. For the first two TNewCheckListBox rows it records
the font charset selected into the DRAWITEMSTRUCT HDC, the font charset
exposed through the list's WM_GETFONT, font face, and whether original
Unicode LB_GETTEXT data is intact. Logs appear as "hook-v7 paint-audit"
in System -> View Last Launch Diagnostics when the installer reaches the
Additional Tasks page. The helper and Java diagnostics log paths are
unchanged; the helper binary is refreshed once per existing Wine prefix
through its new version marker, without reset or migration.

These are boundary snapshots, not instrumentation of the actual
Delphi calls inside WM_DRAWITEM. If the app selects and restores a different
font during the owner-draw callback, the snapshots alone cannot prove it.
The existing Unicode repaint stays as fallback while we collect evidence.
No global CP1252->CP932 redirect has been introduced because that would
break legitimate Western ANSI applications.

To gather evidence, keep "Japanese text support" and opt-in "Installer
font repair" enabled, run the original TPDP setup.exe, navigate to its
Select Additional Tasks checklist, and copy View Last Launch Diagnostics.
Look for paired "paint-audit phase=before" and "phase=after" records.

## Phase 2e - v8 bounded pre-draw SHIFTJIS font trial

The real TPDP installer v7 log confirms a task row sometimes begins
WM_DRAWITEM with GDI charset 0, DC face MS Sans Serif and original Unicode
LB_GETTEXT intact. A later sample already begins with IPAPGothic / charset 128.
The owner-draw synthetic reproducer showed CP932 ANSI bytes rendered as
mojibake under ANSI_CHARSET 0, while SHIFTJIS_CHARSET 128 is correct.

The v8 installer helper retains its opt-in and FocasLens / TWizardForm /
Japanese-font-repair scope. For owner-drawn checklist rows 0..2 with correct
Japanese source text and ACP=932 only, it now tentatively selects an
IPAPGothic SHIFTJIS_CHARSET font into the WM_DRAWITEM HDC BEFORE the Delphi
WndProc executes **only if that HDC does not already use charset 128**.
It uses SaveDC / RestoreDC in paired pre/post callbacks so all previous
GDI state returns; no ListBox items, user files, checkbox data, registry,
Wine binaries, or saved games change. The pre-hook is NEVER installed unless
the existing post-hook is available for paired restoration. The original
v5-v7 Unicode post-draw rendering correction remains in place as fallback.

New log entries: "hook-v8 prepaint selected SHIFTJIS font before Delphi draw"
and "hook-v8 prepaint restored original DC", with prior and restored charset.
A "prepaint ... already-shiftjis=128" entry means no action was needed.

IMPORTANT: Even a successful preselect cannot prove the font remained
selected throughout Delphi's original drawing; Delphi/VCL may select its
own font mid-handler, or use text APIs that are unaffected by the selected
context. The retained post-draw fallback also means a correct screenshot
does not prove native paint is corrected. We must test visual timing and
new pre/post log records before changing the fallback or modifying Wine.


## Phase 2f - v9 diagnostic performance pass

In v8, device testing established a verified prepaint transition from
ANSI charset 0 to SHIFTJIS charset 128 and a successful SaveDC/RestoreDC.
Both the Additional Tasks checklist and the Ready to Install scrollable
summary showed Japanese text correctly. The user also reported a delay
on the final scroll-box page. The screenshots do not prove whether that
delay was due to Charoite's compatibility hooks or normal Inno/Wine
page-transition and layout processing.

v9 keeps the original correctness/fallback model and makes small,
non-destructive performance improvements:

- Avoid sending LB_GETTEXTLEN/LB_GETTEXT during repeated owner-drawn
  checklist paints when the HDC already reports SHIFTJIS_CHARSET.
- Reuse a Japanese font's already-verified glyph coverage only for the
  exact HWND/HFONT pair created and validated by this helper. Any unknown
  font is rechecked through the original GDI font validation.
- Log only expensive >39ms UI control scans and fallback Unicode
  repaints (slowest observed values) as "hook-v9 UI-scan slowest_ms=..."
  and "hook-v9 Unicode fallback slowest_ms=..." to find costly
  operations on the actual device without flooding the filesystem.

This changes neither Wine DLLs nor game prefixes, saved games, installer
strings or checkbox selections. The post-draw Unicode repaint remains
enabled, because a correct v8 screenshot alone does not prove that the
original Delphi paint is always correct. Absence of slow timing entries
means no operation crossed the reporting threshold; it does NOT establish
that the whole page transition was fast.

To compare performance, on the same device navigate to Additional
Tasks, Next (scrollable Ready to Install summary), Back, and Next again.
Record whether any delay repeats, how long it lasts approximately, and
copy the diagnostics with their hook-v9 timing entries (if any).


## Phase 2g - v10 event-driven UI scan on installer page transitions

The user's v9 screen still showed the Ready-to-Install scrollable summary
after a delay even though Japanese characters ultimately were correct.
There were no slowest_ms entries (40 ms threshold), so individual scans
or Unicode repaints were not proven slow. The delay may involve the schedule
for discovering or initially painting a newly shown/updated memo.

v10 keeps the working pre-draw Shift-JIS correction and post-draw Unicode
fallback. In the already attached installer GUI thread, the existing
post-message hook now listens only for specific events in TWizardForm:
WM_SHOWWINDOW on a page/list/memo, WM_WINDOWPOSCHANGED showing a memo,
WM_SETTEXT updating memo contents, and WM_PARENTNOTIFY child creation.

Each burst requests an urgent font scan and posts WM_NULL to the relevant
window. The existing WH_GETMESSAGE hook runs the scan on a later GUI message,
outside Delphi's current WndProc; scans are coalesced and rate-limited to
at least 15 ms apart. The old 100/300 ms periodic scan remains as fallback,
so a missed event cannot remove existing language compatibility.

New logs begin "hook-v10 detected installer page/control event" and
"hook-v10 page-event fast-scan". If a Japanese memo actually needs a new
font, "hook-v10 summary-memo Japanese font applied" measures elapsed time
from the latest page event. No page contents, file paths or game text are
recorded, and Wine and saved prefixes are not modified.

This reduces potential discovery latency, but a correct screenshot or
no timing entries cannot prove that a delayed page transition is fixed.
Compare the Back -> Next confirmation-page transition several times. If a
delay persists even with prompt font scans, investigate the installer/VCL
layout/rendering rather than further reducing scanner intervals.
