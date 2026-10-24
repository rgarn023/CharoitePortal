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
