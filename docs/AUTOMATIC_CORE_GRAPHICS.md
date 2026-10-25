# Charoite Core automatic game graphics compatibility

## Working base TPDP profile — October 25, 2026

Galaxy S26 Ultra physical testing **confirmed base Touhou Puppet Dance
Performance v1.34 works** using the bundled **DXVK 1.10.3 + Turnip**.
Earlier WineD3D/VirGL, Zink, native Vulkan, and DXVK 2.4.1 attempts
showed black windows or incomplete startup. Do not regress the working
profile.

## Architecture

- `CharoiteGraphicsProfiles.java` is a reusable Charoite Core catalog.
  For known TPDP game executables `gn_enbu.exe` and `enbu_ap.exe`,
  it selects the bundled DXVK 1.10.3 + Turnip combination and its
  diagnostic log settings. The base game is validated; expansion support
  has **not** been validated on the user's phone.
- `CharoiteGameSessions.java` invokes automatic Core policy when launching
  a game and never reads old manual per-game graphics preferences.
- `CharoiteWindowPolicy.java` owns TPDP phone-window positioning, while
  `CharoiteTpdpTouchControls.java` owns touch keyboard overlays.
- `CharoiteDiagnostics.java` owns all launch, OpenGL/D3D, DXVK, and
  audio reporting. CharoiteJapaneseSupport owns Japanese-font behavior.
- The pinned Winlator overlay is an **integration bridge only**: it copies
  compiled Charoite Core classes into the Android app and hands driver,
  environment, and window callbacks to Core. JNI/native Wine code still
  comes from the attributed Winlator/Wine runtime; it cannot be moved into
  standalone Java Core without replacing the underlying engine.
- Portal's System screen explains that game profiles apply automatically;
  it no longer exposes TPDP-specific renderer cycling or DXVK buttons.
  Other programs still use their existing saved graphics configuration.

## Compatibility and data safety

Former `tpdp_graphics_mode` values are retained in existing preferences
but ignored during launch, so an older selected trial backend cannot
silently override the confirmed working DXVK 1.10.3 profile.

This update uses the original Android package `com.touhoudr` and does
not remove, migrate, reinstall, overwrite or reset saved games or Wine
prefixes. Winlator's existing graphics-wrapper extraction can update
Wine-managed wrapper DLLs as needed at launch, without changing game
files or erasing saves. The active game's audio backend remains untouched.

This system can accept additional verified profiles for other games
without adding per-game special cases to Portal. Do not claim an
unverified title is playable solely because it shares the TPDP renderer.
