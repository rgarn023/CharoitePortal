# Charoite Core — Windows and Japanese compatibility status

## Verified on Galaxy S26 Ultra (current baseline)

| Subsystem | Scope | Current evidence |
|---|---|---|
| Japanese fonts and locale | Opt-in environment with CP932, IPA Gothic/P Gothic, Noto CJK | TPDP installer path and checklist render correctly |
| Native Win32 Unicode drawing | General GDI diagnostic | DrawTextW, ExtTextOutW and TextOutW pass |
| Native Win32 ANSI drawing (CP932) | General GDI diagnostic | With SHIFTJIS_CHARSET 128, DrawTextA and ExtTextOutA pass; ANSI_CHARSET 0 causes mojibake, as expected for CP1252 |
| Win32 owner-drawn listboxes | General diagnostic | Character-set differential replicated root cause |
| Inno Setup checklist compatibility | Opt-in installer hook | TPDP installer v8-v10 font preselect and Unicode fallback, no data mutation |
| Inno Setup summary-page font discovery | Opt-in installer hook | TPDP v10 confirms prompt font application and no observed delay |
| Other Japanese Inno installers | New generic wizard/Unicode detection | **Not yet phone-verified**: needs representative second installer |
| Non-Inno installers / game engines | General fonts and locale only | Rendering hooks intentionally *not* enabled; diagnosis per renderer required |
| English/Western games | Original runtime + opt-in graphics modes | Do not override ANSI_CHARSET 0 or CP1252 system-wide |
| Wine/Box64/graphics/audio/input | Upstream-derived runtime | Cannot guarantee game-specific compatibility without tests |

## Shared compatibility design

**First gate (Android):** Japanese Text Support must be enabled in the selected
environment, Installer Font Repair explicitly enabled (legacy Touhou Realm
defaults on), and executable must have a conservative installer name:
setup.exe, setup_*.exe, install.exe, install_*.exe, or installer.exe.

**Second gate (Windows):** The read-only Win32 monitor waits for a real Inno
TWizardForm, process ACP 932, and at least two Japanese script characters in
an eligible wizard edit/path, label, memo or title. It then launches the
architecture-matched in-process helper in that specific GUI thread. Never
try to infer Japanese based only on a game's filename or blindly change
all ANSI applications to CP932. All text content remains untouched.

**Third gate (draw operation):** Only verified owner-drawn Inno checklist
controls with Japanese Unicode item strings receive a temporary font change
when the device context charset is wrong. SaveDC/RestoreDC preserves prior
state. The v10 Unicode correction remains available after draw, and newly
displayed controls receive prompt per-thread event-driven font inspection.

No global Wine modifications and no user-installed file or save edits.

Internal filenames beginning with touhou_ are retained **for compatibility
with existing prefixes and APK upgrades**; they no longer represent a
requirement for a specific game title. Versioned app-owned helper binaries
are refreshed without removing existing Wine prefixes.

## Next acceptance tests

1. Re-test original TPDP setup.exe (path, Additional Tasks, Ready to Install)
   after generalized monitor deployment. Must have no new delay or text defect.
2. In another environment, opt into Japanese Text Support and Installer Font
   Repair; run a Japanese Inno Setup installer with a different folder name.
   Verify whether its window is recognized, Japanese text is intact and
   the helper logs attach and clean unhook.
3. Run an English-language installer and a game EXE in the same environment.
   Ensure neither receives an unexpected Japanese installer hook.
4. Test a Japanese non-Inno game that shows broken text. Collect a screenshot,
   Unicode/ANSI rendering diagnostics and Wine log. Do not assume the Inno
   helper applies to SDL, Unity, RPG Maker, Ren'Py, DirectWrite or other engines.
5. Test touch, Samsung DeX, audio, saves, updates and game launches separately
   from Japanese text. A passed text test doesn't validate those capabilities.

**Important:** This matrix reports observed compatibility, not universal
support for every Windows application or a fully independent Wine engine.
