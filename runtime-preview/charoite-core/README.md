# Charoite Core (Android runtime module) — v0.8

**Charoite Core is not an operating system.** It is a reusable compatibility-runtime component bundled inside Touhou Launcher for Android. It operates within Android/One UI and does not require root, system changes, a separate installed app, or Samsung DeX replacement.

## Implemented now

`CharoiteCore.java` is compiled in the same Android APK and already called by `TouhouEntryActivity.java` to coordinate:

- **Bundled runtime readiness:** Compare the current APK timestamp with the original `engine_prepared_apk_timestamp` preference key, prepare a pinned Winlator-derived Wine/Box64 root filesystem when needed, preserve per-game Wine prefixes, and record completion only after the launcher confirms a valid container.
- **Graphics configuration:** Choose the current normal or conservative WineD3D/Box64 graphics preset for an existing container. These are upstream-derived technologies, not in-house Wine or Proton forks.
- **First-time container defaults:** Create a default profile for a new game environment without replacing an existing container.
- **Desktop launch policy:** Detect an external/multi-window environment, choose one of the existing 1280x720/1600x900/1920x1080/800x600 Windows resolutions, and configure DeX pointer-capture preferences, all without changing the saved game container when switching monitors.

## Integration

GitHub Actions clones pinned upstream Winlator source, then `runtime-preview/overlay.py` copies this file to `app/src/main/java/com/charoitegames/core/CharoiteCore.java` alongside the Touhou-specific launcher source. The Android Java compiler checks the integration. The new clean-install package ID is **`com.charoite`**; the old package remains separate.

The current `CharoiteCore.java` is a shared **source module**, not yet an independently published AAR/SDK, a cross-app service, or a separate GitHub repository. It currently depends on Winlator-derived runtime types. Future launchers could share this source module first, with a stable public interface added once another real client needs it. Avoid promising instant cross-app access to private Wine paths: Android sandboxes each app.

## Project boundaries

| Touhou Launcher | Charoite Core |
|---|---|
| Game library and draggable icon arrangement | Engine version/re-extraction policy |
| Touhou-specific executable discovery and naming | Shared graphics configurations |
| Game import and original installer flow | Initial Windows container defaults |
| Launcher UI and error/diagnostic presentation | Display resolution and input launch choices |
| Touhou-specific fonts/hooks presently in overlay | Later candidate: generalized language packs and compatibility profiles |

**Preservation contract:** The Oct 2026 one-time package-ID transition installs as a separate new app. Do not erase or rename Wine prefixes as part of later APK updates, or relocate `C:\TouhouPocket\` staging paths. Runtime ZIP archives must not contain user home prefix files. Avoid invasive refactors of tested installer behavior. No third-party games included.

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

The Android icon and public brand are now **Charoite Portal** (original purple gemstone/space gateway, no Touhou icon). Android package `com.charoite` is the new permanent identity; keep it unchanged on later updates. All of these modules remain within one APK, without replacing Android or One UI.

**Validation:** Native Android compilation and APK artifact integrity can verify the source integration, but real-device testing is still required. Creating arbitrary environments consumes substantial phone storage, and Wine game compatibility is not guaranteed. A stable APK signing pipeline is needed before safe, reliable in-place releases.


## Compact Portal header and themed realm banner

The Charoite Portal shell displays **Charoite Portal** only once as a small, bold heading at the top, with **Charoite Core** directly underneath. Beneath those labels, it shows the *active environment name* as large, bold, accessible Android text over a wide, rounded, themed graphic banner. **There is no app icon beside the realm name.**

The reusable `CharoiteThemes.realmBanner(template)` method supplies a background drawable to the Portal UI:
- Touhou Realm gets original sakura blossoms and branch illustration on a dark plum-to-rose banner.
- General Gaming and user-created custom environments get original violet cosmic rings, light points, and a portal arc composition.
- Both are suitable for legible white titles over a darker left-hand gradient and independent of user-selected full-screen wallpapers. Switching environments re-renders the matching banner.

Implemented in `runtime-preview/TouhouEntryActivity.java`; Android/One UI home-screen adaptive icon is unchanged.


## Reusable touch-swipe pages — v0.4

`CharoiteSwipePager.java` is a shared `ScrollView` with a host callback for left/right finger or stylus swipes. It recognizes gestures only when horizontal movement clearly dominates vertical movement and exceeds a density-aware distance. Vertical scrolling remains native; Samsung DeX mouse drags are not interpreted as page swipes. It does not handle long-press tile reorder operations or launch games. It asks the host to select the previous or next tab; the Portal clamps the page index from Library (0), Setup (1), to System (2) without wrapping. `CharoitePageTabs` remains the single source of tab styling and selected state, synchronized through `showSection`.

The Portal has environment-aware messaging across Library, Setup and System. Only Touhou Realm shows the Gensokyo-specific empty-library caption or the explanation about its original Touhou game storage. Generic/created environments display their own realm name and neutral storage guidance. The System environment help message and already-installed General Gaming message are not Touhou-specific.

The realm header remains reusable `CharoiteThemes.realmBanner` artwork, but the banner is 120dp tall rather than 164dp, with reduced padding and still-large bold realm lettering. These are UI-only changes: Wine/Box64, new package ID, Touhou prefix paths, per-environment registry and wallpaper data are not modified.


## Charoite Core v0.5 — portable environment files and repaired tab swipes

**Portable environments:** The app uses human-readable, versioned `.cenv` profiles in UTF-8 JSON. `CharoiteEnvironmentFiles.java` validates the schema, size (at most 16 KiB), keys, environment names, themes and supported compatibility values. It never loads scripts, external code, absolute paths or executables from a portable profile. `CharoiteEnvironments.installFromFile()` adds a fresh local environment with a new isolated Wine container ID; repeated imports are renamed rather than overwriting existing profiles. The user's installed Windows games, Wine prefix, existing environmental preferences and saves are not serialized or moved.

**Android Storage Access Framework:** `Install Environment` uses `ACTION_OPEN_DOCUMENT` to select a downloaded `.cenv` on the phone, followed by a validation/confirmation preview. `Create Environment` asks the user to save a `.cenv` via `ACTION_CREATE_DOCUMENT` before creating a new local realm. `Export Environment (.CENV)` saves the selected realm's settings to a user-chosen document. Users need no broad file/storage permissions. Export does *not* include user-installed games, saves, or custom wallpaper images. Android document providers choose the final folder/name.

**Swipe correction:** `CharoiteSwipePager` now observes `dispatchTouchEvent` rather than relying on `onInterceptTouchEvent`, which was unreliable when child buttons/layouts handled events. It recognizes a completed horizontal finger/stylus gesture anywhere in the scrollable content, including over child controls, while preserving vertical scrolling, touches, game-tile drag/drop and DeX mouse. Edge gestures and multipointer gestures are ignored. The page index still clamps to Library / Setup / System.

The built-in General Gaming preset is **no longer installed automatically by the Install button**; a sample downloadable `environment-profiles/General-Gaming.cenv` is provided in the repository. Original Charoite Portal icon, installed game paths, and new package ID `com.charoite` is used on clean installs.


## Charoite Core v0.6 — branding isolation and device rotation

**Branding:** The main Charoite Portal/Charoite Core UI is the only app-level launcher. `runtime-preview/overlay.py` removes old upstream home-screen launcher intents, makes the hidden upstream MainActivity internal, replaces user-facing Winlator notification titles and taps, translates locale overrides for app labels/notifications, and changes the optional About website reference to Charoite Portal branding. Original upstream legal notices and LGPL copyright/licensing assets remain bundled as required. The pinned Wine/Box64/Winlator-derived **implementation is still present** for compatibility; don't describe this as a native independent Wine replacement.

**Rotation:** `TouhouEntryActivity` and `XServerDisplayActivity` have `fullSensor` activity orientation, with `configChanges` configured to keep the active Wine/XServer session alive on phone rotation. The old `SCREEN_ORIENTATION_SENSOR_LANDSCAPE` runtime override is gone. On configuration changes the game view/touch overlays are relaid out, while Android's `GLSurfaceView` automatically invokes the `GLRenderer.onSurfaceChanged` viewport transform to fit the existing Wine framebuffer to the rotated screen. The game process is **not** intentionally restarted when rotating.

**Wine desktop orientation:** `CharoiteCore.automaticGameResolution` and `chosenGameResolution` choose portrait variants of the supported game sizes (600×800, 720×1280, 900×1600, 1080×1920) for new sessions in portrait, and the corresponding landscape sizes otherwise; this applies to both installers and gameplay. It doesn't alter the persistent container's fixed resolution. Because the upstream X11 root-screen size is fixed at launch and has no dynamic RandR implementation, **rotating an already-running Wine game scales the view to fit but does not change that game's native Windows desktop resolution until its next launch**. Fixed-resolution games may letterbox. Changing this would require a significant additional Wine/X11 resizing implementation.

**Testing:** GitHub Actions compiles and integrity-checks the Android APK; physical Samsung Galaxy phone and DeX tests are still needed to confirm orientation, input-controls layout and app visibility. Keep the new Android package ID `com.charoite` stable for all future APK updates. Debug signing can impede an in-place APK update.


## Charoite Core v0.7 — Touhou Japanese installer optional-task font rendering

The screenshot of the Japanese Inno Setup **Select Additional Tasks** page showed otherwise legible Japanese headings/button text but damaged checkbox item labels. The existing Wine Japanese locale / CP932 / IPA Gothic setup was already in place; however `touhou_font_hook.c` v1 only repaired a path-specific `TEdit` and never handled Inno's owner-drawn `TNewCheckListBox` or labels on later wizard pages.

New scope-limited helper v2:
- Hooks only the known Touhou setup.exe GUI thread discovered by the existing local `touhou_probe` in the Touhou Realm.
- Scans controls on subsequent installer pages every ~500ms, including `TNewCheckListBox`/checkboxes/static labels and Windows edit controls, and assigns compatible IPA P Gothic `SHIFTJIS_CHARSET` fonts *inside the original installer process* if appropriate.
- Preserves original UTF-16 window/control text and never edits game executables, installer translations, original paths or user file data. If original Unicode strings are already mojibake, a font change by itself is **not** guaranteed to recover them.
- Logs a bounded `task-... utf16=` sample from the task checklist to `C:\touhou_font_hook.log` in the existing local Wine prefix; launch diagnostics can read this file to distinguish wrong fonts from already-corrupted text.
- Keeps the thread-local helper alive across installer wizard pages (up to five minutes, stopping when installer thread exits). The prior 18-second helper could exit before the task page appeared.
- Refreshes bundled app-owned 32/64-bit hook and helper executables in existing Touhou Wine prefixes using a `.touhou-japanese-helpers-v2` marker, so upgrading the APK really installs the new helper binaries. Games and saves remain untouched.

Compiled into `Charoite Portal v0.7` via GitHub Actions. Device validation is still required.


## Charoite Core v0.8 — shared game importer + Japanese compatibility

**All cross-environment game-folder import behavior lives in Core**, not the historical `TouhouEntryActivity.java` shell. `CharoiteGameImport.java` owns Android Storage Access Framework folder/file copying, 6 GB/12,000-file limits, canonical safe-name checks, cleanup of only the new failed import, EXE discovery, selection of playable EXEs ahead of setup.exe, and **`shouldLaunchAfterImport(Selection)`**. Folder selection always produces an import-only result; only deliberately selecting a standalone installer EXE allows Portal to start the Windows wizard. The launcher remains a thin adapter for library UI, saved tile metadata, and explicit `XServerDisplayActivity` launches. The original Touhou C: drive staging location is preserved.

**All Japanese character-compatibility implementation is now Core-owned.** `CharoiteJapaneseSupport.java` handles licensed Noto/IPA Japanese fonts, `ja_JP.utf8`, Wine CP932/locale registry, font substitutes, and upgrading per-prefix Win32 helpers without touching games/saves. `charoite-core/japanese/` owns the reproducible Japanese support pack build script, 32/64-bit Inno font hook/helper source, and read-only Win32 codepage probe. GitHub Actions compiles these from Core, and `overlay.py` bundles the resulting assets unchanged. Duplicated historical root-level files were removed so fixes cannot drift between copies.

`CharoiteCore.japaneseCompatibilityEnabled(Context)` centrally selects Japanese settings per environment: **Touhou Realm defaults ON**, other realms default OFF, and the **System → Japanese Text Support** button enables/disables Japanese support for the currently selected realm. The opt-in choice persists in the established activity preferences. A backward-compatible optional `japaneseText` setting in version-1 `.cenv` profile files allows exporting/importing Japanese text compatibility with a portable realm.

The original Touhou-specific font hook still runs **only** with Japanese support enabled in Touhou Realm and when launching the known original `setup.exe`; it does not globally inject hooks into arbitrary games. Other realms can use Core's ordinary Japanese codepage/font support without the special Touhou installer helper. Existing Touhou Japanese installation folders, game files and saves remain in place.

Verification: GitHub Android CI first runs Core ownership/import regression tests, builds both arch Win32 font helpers from Core and finally compiles the combined Android APK. Real-device Japanese optional-task text and folder-picker behavior must be tested separately.
