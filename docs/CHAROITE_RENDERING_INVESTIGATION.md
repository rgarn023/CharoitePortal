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
