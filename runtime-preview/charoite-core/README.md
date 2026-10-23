# Charoite Core (Android runtime module) — v0.1

**Charoite Core is not an operating system.** It is a reusable compatibility-runtime component bundled inside Touhou Launcher for Android. It operates within Android/One UI and does not require root, system changes, a separate installed app, or Samsung DeX replacement.

## Implemented now

`CharoiteCore.java` is compiled in the same Android APK and already called by `TouhouEntryActivity.java` to coordinate:

- **Bundled runtime readiness:** Compare the current APK timestamp with the original `engine_prepared_apk_timestamp` preference key, prepare a pinned Winlator-derived Wine/Box64 root filesystem when needed, preserve per-game Wine prefixes, and record completion only after the launcher confirms a valid container.
- **Graphics configuration:** Choose the current normal or conservative WineD3D/Box64 graphics preset for an existing container. These are upstream-derived technologies, not in-house Wine or Proton forks.
- **First-time container defaults:** Create a default profile for a new game environment without replacing an existing container.
- **Desktop launch policy:** Detect an external/multi-window environment, choose one of the existing 1280x720/1600x900/1920x1080/800x600 Windows resolutions, and configure DeX pointer-capture preferences, all without changing the saved game container when switching monitors.

## Integration

GitHub Actions clones pinned upstream Winlator source, then `runtime-preview/overlay.py` copies this file to `app/src/main/java/com/charoitegames/core/CharoiteCore.java` alongside the Touhou-specific launcher source. The Android Java compiler checks the integration. The package ID remains **`com.touhoudr`**.

The current `CharoiteCore.java` is a shared **source module**, not yet an independently published AAR/SDK, a cross-app service, or a separate GitHub repository. It currently depends on Winlator-derived runtime types. Future launchers could share this source module first, with a stable public interface added once another real client needs it. Avoid promising instant cross-app access to private Wine paths: Android sandboxes each app.

## Project boundaries

| Touhou Launcher | Charoite Core |
|---|---|
| Game library and draggable icon arrangement | Engine version/re-extraction policy |
| Touhou-specific executable discovery and naming | Shared graphics configurations |
| Game import and original installer flow | Initial Windows container defaults |
| Launcher UI and error/diagnostic presentation | Display resolution and input launch choices |
| Touhou-specific fonts/hooks presently in overlay | Later candidate: generalized language packs and compatibility profiles |

**Preservation contract:** Do not change Android package ID, erase or rename Wine prefixes, or relocate `C:\TouhouPocket\` staging paths as part of the rebrand. Runtime ZIP archives must not contain user home prefix files. Avoid invasive refactors of tested installer behavior. No third-party games included.

## Future work (not yet implemented)

Define stable versioned APIs; separate engine assets from launcher-specific content; regression tests for container preservation; per-game compatibility profiles; durable signing for in-place APK upgrades; additional consumer launcher(s); optional independent source packaging. Test on physical Galaxy + Samsung DeX before promising full device compatibility.
