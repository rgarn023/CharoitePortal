# Charoite Core (Android runtime module) — v0.3

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

## Charoite Wallpaper (implemented October 23, 2026)

The reusable wallpaper storage/display policy lives in `runtime-preview/charoite-core/CharoiteWallpaper.java`, compiled into the same APK through `runtime-preview/overlay.py`. It does not manage Android system wallpaper or require Android storage permissions.

- `importImage(context, uri)` uses Android's system `ACTION_OPEN_DOCUMENT` image picker from the Touhou Launcher front end and copies an image (max 50 MiB) to a temporary app-private file. It validates image MIME where available and decodable image dimensions before replacing the saved wallpaper. A failed import leaves the previous image intact.
- `loadBitmap(context, maxDimension)` downsamples large camera images for safe display. `hasWallpaper` and `removeWallpaper` manage the app-private image only.
- `getMode(prefs)` and `setMode(prefs, mode)` persist **Crop to Fill** (center crop) or **Fit Whole Image** (letterbox) in the existing Touhou activity-private preferences.
- Touhou Launcher alone owns the image picker, wallpaper preview, UI tint/contrast, and layering. Wallpaper appears behind the Library, Setup and System screens, not inside a Wine game, and never changes the Samsung One UI / Android system wallpaper.
- The bottom navigation bar was lifted ~14dp with extra bottom padding in this release to improve separation from Samsung's system navigation area.

GitHub Actions run [39948092801](https://github.com/rgarn023/TouhouPocketLauncher/actions/runs/39948092801) for code SHA `a2036ec07e11a0c8009da4c3c24b79310bcaa9db` completed **success**. APK SHA256: `b702c5be1b62bf529934acbb5abd322d1df41faf9f729cc89120bfd9d7886502`. Japanese font helpers and 35 JNI libraries intact. Real-device wallpaper picker/DeX resizing remain untested.

## Reusable page tabs — Charoite Core v0.2

`CharoitePageTabs.java` is a reusable native Android connected-page-tab view owned by Charoite Core, **not** by Touhou Launcher. It accepts arbitrary tab names, a selection callback, and a palette supplied by the host app. Core handles:
- A single attached page-tab strip with equal-width buttons, rounded **top** corners and flat bottom edges.
- An elevated and accent-highlighted active tab, contrasting inactive pages, 48dp touch targets, and accessibility descriptions.
- Light/dark palette updates, selection state and screen-size-independent bottom navigation clearance (88dp bar with 21dp bottom padding).

Touhou Launcher constructs `new CharoitePageTabs(this, new String[]{"Library", "Setup", "System"}, this::showSection)`, supplies its palette and current selection, and controls the actual Library, Setup and System screens. Those page names and their content remain app-specific; **all tab visuals and selection handling are in Charoite Core**. The Android overlay copies the Java class into the app's core package so the packaged APK compiles it. Future launchers may reuse this class with different page names.

## Charoite Portal environment manager (v0.3)

New `CharoiteEnvironments.java` registers independent Windows Wine containers under stable IDs and tracks an active environment. First-run migration registers **Touhou Realm** from the original `touhou_container` ID or pre-existing first Wine container, without relocating/deleting files. Touhou continues using its original `game_library` preference and `C:\TouhouPocket\` staging folder. Each later environment uses its own container ID, game list preference and `C:\CharoitePortal\` staging folder.

The Portal System UI can **Switch** between environments; **Install** the built-in offline General Gaming template; and **Create** a custom environment with its own name. Both installation/creation add a registry record, switch to that record, and asynchronously prepare a new Wine container when needed. There is no untrusted remote environment installer or arbitrary archive import in this version. No environment deletion or destructive migration implemented.

New `CharoiteThemes.java` draws distinct offline **Touhou sakura** and **Charoite cosmic** default wallpapers; CharoiteWallpaper has environment-id overloads for image selection, saved Fit/Crop mode, preview and removal. Existing Touhou wallpaper file and setting keys are preserved. `CharoiteCore.java` maintains separate graphics/DeX preferences for non-Touhou environments but retains the original preference keys for Touhou. Existing Japan-specific CP932/font hooks are scoped to Touhou Realm; general Windows profiles use the upstream English locale default.

The Android icon and public brand are now **Charoite Portal** (original purple gemstone/space gateway, no Touhou icon). Android package `com.touhoudr` must remain unchanged to protect user-owned game storage. All of these modules remain within one APK, without replacing Android or One UI.

**Validation:** Native Android compilation and APK artifact integrity can verify the source integration, but real-device testing is still required. Creating arbitrary environments consumes substantial phone storage, and Wine game compatibility is not guaranteed. A stable APK signing pipeline is needed before safe, reliable in-place releases.


## Compact Portal header and themed realm banner

The Charoite Portal shell displays **Charoite Portal** only once as a small, bold heading at the top, with **Charoite Core** directly underneath. Beneath those labels, it shows the *active environment name* as large, bold, accessible Android text over a wide, rounded, themed graphic banner. **There is no app icon beside the realm name.**

The reusable `CharoiteThemes.realmBanner(template)` method supplies a background drawable to the Portal UI:
- Touhou Realm gets original sakura blossoms and branch illustration on a dark plum-to-rose banner.
- General Gaming and user-created custom environments get original violet cosmic rings, light points, and a portal arc composition.
- Both are suitable for legible white titles over a darker left-hand gradient and independent of user-selected full-screen wallpapers. Switching environments re-renders the matching banner.

Implemented in `runtime-preview/TouhouEntryActivity.java`; Android/One UI home-screen adaptive icon is unchanged.
