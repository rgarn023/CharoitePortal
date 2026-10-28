#!/usr/bin/env python3
"""Reproducible, minimal Touhou runtime preview overlay on a pinned Winlator source checkout."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

if len(sys.argv) != 2:
    raise SystemExit("Usage: overlay.py PATH_TO_WINLATOR_APP")
root = Path(sys.argv[1]).resolve()
assert (root / "app/src/main/AndroidManifest.xml").is_file(), "Not a Winlator Android source tree"

# Force Gradle's debug signing to use the app-specific cached keystore.
# Upgrades must not rotate keys unexpectedly or change com.charoite.
gradle_path = root / "app/build.gradle"
gradle_source = gradle_path.read_text(encoding="utf-8")
gradle_marker = "    buildTypes {"
assert gradle_source.count(gradle_marker) == 1, "Upstream signing config changed"
gradle_source = gradle_source.replace(gradle_marker, """
    signingConfigs {
        debug {
            storeFile file(System.getProperty("user.home") + "/.android/debug.keystore")
            storePassword "android"
            keyAlias "androiddebugkey"
            keyPassword "android"
        }
    }

""" + gradle_marker)
gradle_marker = "    buildTypes {\n        debug {"
assert gradle_source.count(gradle_marker) == 1, "Upstream buildTypes.debug changed"
gradle_source = gradle_source.replace(gradle_marker,
    "    buildTypes {\n        debug {\n            signingConfig signingConfigs.debug")
gradle_path.write_text(gradle_source, encoding="utf-8")


gradle = root / "app/build.gradle"
src = gradle.read_text(encoding="utf-8")
assert "applicationId 'com.winlator'" in src, "Upstream application ID changed, review before building"
src = src.replace("applicationId 'com.winlator'", "applicationId 'com.charoite'")
assert "implementation 'androidx.appcompat:appcompat:1.4.0'" in src, "Upstream dependencies changed"
src = src.replace("implementation 'androidx.appcompat:appcompat:1.4.0'",
    "implementation 'androidx.appcompat:appcompat:1.4.0'\n    implementation 'androidx.documentfile:documentfile:1.0.1'")
gradle.write_text(src, encoding="utf-8")

strings = root / "app/src/main/res/values/strings.xml"
src = strings.read_text(encoding="utf-8")
assert '<string name="app_name">Winlator</string>' in src, "Upstream app name changed"
src = src.replace('<string name="app_name">Winlator</string>',
                  '<string name="app_name">Charoite Portal</string>')
# Remove upstream branding from visible startup and background notifications.
# This does NOT change the runtime's original Winlator-derived architecture.
for original, branded in (
    ('<string name="starting_up">Starting up...</string>',
     '<string name="starting_up">Launching Windows game...</string>'),
    ('<string name="fgs_notification_content_else">Winlator is running in the background</string>',
     '<string name="fgs_notification_content_else">Charoite Portal is running</string>'),
    ('<string name="fgs_notification_channel_desc">Keeps Winlator running in the background so a wine session is not interrupted by Android\\\'s background process management.</string>',
     '<string name="fgs_notification_channel_desc">Keeps Charoite Portal active while a Windows game is running.</string>'),
):
    assert original in src, f"Upstream string changed: {original[:58]}"
    src = src.replace(original, branded)
strings.write_text(src, encoding="utf-8")

# Android locale overrides default resources. Translate only user-visible names
# and notification titles so Portuguese/Russian phones won't show Winlator.
import re
for localized in (root / "app/src/main/res").glob("values-*/strings.xml"):
    localized_text = localized.read_text(encoding="utf-8")
    localized_text = re.sub(r'(<string name="app_name">).*?(</string>)',
        r'\g<1>Charoite Portal\2', localized_text, count=1, flags=re.DOTALL)
    for key in ("fgs_notification_content_else", "fgs_notification_channel_desc"):
        expr = r'(<string name="' + key + r'">)(.*?)(</string>)'
        localized_text = re.sub(expr, lambda m: m.group(1) +
            re.sub("Winlator", "Charoite Portal", m.group(2), flags=re.I) +
            m.group(3), localized_text, count=1, flags=re.DOTALL)
    localized.write_text(localized_text, encoding="utf-8")


# Runtime assets use a same-length replacement Android package name to preserve\n# native ELF interpreter and library offsets. Do not change this ID without\n# rewriting runtime-preview/rewrite_prefix.py in tandem.\n# The provider authority must not collide with separately installed Winlator.
manifest_path = root / "app/src/main/AndroidManifest.xml"
ET.register_namespace("android", "http://schemas.android.com/apk/res/android")
a = "{http://schemas.android.com/apk/res/android}"
manifest = ET.parse(manifest_path)
app = manifest.getroot().find("application")
assert app is not None
# The previous JPEG asset was unintentionally damaged in GitHub transfer:
# 12 missing JPEG quantization-table bytes made it undecodable despite a
# successful Gradle APK build. Repair the exact known asset and enforce a
# checksum for the valid, originally approved user-selected artwork.
import hashlib
image_path = Path(__file__).resolve().parent / "charoite_portal_icon.jpg"
image_bytes = image_path.read_bytes()
bad_sha = "7c5c8fdf88b71fd23fb01740f516b866108edbf57af962aa50bca599bdd1b338"
good_sha = "28668d5426e7d7977880b6e8406c14a47972565a7f637a8c16fcd1cde2788aa5"
if hashlib.sha256(image_bytes).hexdigest() == bad_sha:
    image_bytes = image_bytes[:108] + bytes([0x82]) * 12 + image_bytes[108:]
assert hashlib.sha256(image_bytes).hexdigest() == good_sha, (
    "Charoite Portal launcher icon is not the validated artwork"
)
assert image_bytes.startswith(b"\xff\xd8") and image_bytes.endswith(b"\xff\xd9"), (
    "Charoite Portal icon isn't a complete JPEG"
)
icon_destination = root / "app/src/main/res/drawable-nodpi/charoite_portal_icon.jpg"
icon_destination.parent.mkdir(parents=True, exist_ok=True)
icon_destination.write_bytes(image_bytes)

# Android 8+ (including Samsung One UI) needs a real adaptive mipmap icon.
# Upstream Winlator's ic_launcher adaptive icons depict the generic Android
# graphic, so explicitly overwrite both icon resources as well as manifest
# references rather than relying on a raw @drawable image.
adaptive_dir = root / "app/src/main/res/mipmap-anydpi-v26"
adaptive_dir.mkdir(parents=True, exist_ok=True)
foreground = root / "app/src/main/res/drawable/charoite_portal_foreground.xml"
foreground.parent.mkdir(parents=True, exist_ok=True)
foreground.write_text("""<?xml version="1.0" encoding="utf-8"?>
<inset xmlns:android="http://schemas.android.com/apk/res/android"
    android:drawable="@drawable/charoite_portal_icon"
    android:inset="10dp" />
""", encoding="utf-8")
background = root / "app/src/main/res/drawable/charoite_portal_background.xml"
background.write_text("""<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android">
    <solid android:color="#100C27"/>
</shape>
""", encoding="utf-8")
adaptive_xml = """<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@drawable/charoite_portal_background"/>
    <foreground android:drawable="@drawable/charoite_portal_foreground"/>
</adaptive-icon>
"""
for name in ("ic_launcher.xml", "ic_launcher_round.xml"):
    (adaptive_dir / name).write_text(adaptive_xml, encoding="utf-8")
# Legacy devices also resolve the matching approved icon instead of inherited
# upstream mipmap PNGs. mipmap-anydpi overrides density-specific Winlator art.
legacy_dir = root / "app/src/main/res/mipmap-anydpi"
legacy_dir.mkdir(parents=True, exist_ok=True)
legacy_xml = """<?xml version="1.0" encoding="utf-8"?>
<bitmap xmlns:android="http://schemas.android.com/apk/res/android"
    android:src="@drawable/charoite_portal_icon"
    android:antialias="true" android:filter="true"/>
"""
for name in ("ic_launcher.xml", "ic_launcher_round.xml"):
    (legacy_dir / name).write_text(legacy_xml, encoding="utf-8")
app.set(a + "icon", "@mipmap/ic_launcher")
app.set(a + "roundIcon", "@mipmap/ic_launcher_round")
# Explicit freeform/multi-window support for DeX on external displays.
app.set(a + "resizeableActivity", "true")
app.set(a + "label", "@string/app_name")
original_main = next((activity for activity in app.findall("activity")
    if activity.get(a + "name") == "com.winlator.MainActivity"), None)
assert original_main is not None, "Winlator launcher activity not found"
original_main.set(a + "exported", "false")
original_main.set(a + "label", "@string/app_name")
filters = original_main.findall("intent-filter")
assert len(filters) == 1, "Unexpected Winlator launcher intent filters"
for filt in filters:
    original_main.remove(filt)
for provider in app.findall("provider"):
    if provider.get(a + "authorities") == "com.winlator.FileProvider":
        provider.set(a + "authorities", "com.charoite.FileProvider")
entry = ET.Element("activity", {
    a + "name": "com.winlator.TouhouEntryActivity",
    a + "exported": "true",
    a + "screenOrientation": "fullSensor",
    a + "configChanges": "keyboard|keyboardHidden|orientation|screenSize|screenLayout|smallestScreenSize|density|navigation|uiMode",
    a + "resizeableActivity": "true",
    a + "theme": "@style/AppThemeDark"
})
intent = ET.SubElement(entry, "intent-filter")
ET.SubElement(intent, "action", {a + "name": "android.intent.action.MAIN"})
ET.SubElement(intent, "category", {a + "name": "android.intent.category.LAUNCHER"})
app.insert(0, entry)
file_manager_activity = ET.Element("activity", {
    a + "name": "com.charoitegames.core.CharoiteFileManagerActivity",
    a + "exported": "false",
    a + "screenOrientation": "fullSensor",
    a + "resizeableActivity": "true",
    a + "theme": "@style/AppThemeDark"
})
app.insert(1, file_manager_activity)
# Upstream forces games into landscape, which can interfere with DeX
# freeform windows. Phone launches request sensor-landscape at runtime.
xserver_activity = next((activity for activity in app.findall("activity")
    if activity.get(a + "name") == "com.winlator.XServerDisplayActivity"), None)
assert xserver_activity is not None, "Upstream game window activity missing"
xserver_activity.set(a + "screenOrientation", "fullSensor")
xserver_activity.set(a + "configChanges", "keyboard|keyboardHidden|orientation|screenSize|screenLayout|smallestScreenSize|density|navigation|uiMode")
xserver_activity.set(a + "resizeableActivity", "true")
xserver_activity.set(a + "label", "@string/app_name")
manifest.write(manifest_path, encoding="utf-8", xml_declaration=True)

# Account for FileProvider authority referenced in Java code (none may be present).
java_root = root / "app/src/main/java"
for java in java_root.rglob("*.java"):
    text = java.read_text(encoding="utf-8")
    if '"com.winlator.FileProvider"' in text:
        java.write_text(text.replace('"com.winlator.FileProvider"',
            '"com.charoite.FileProvider"'), encoding="utf-8")

target = java_root / "com/winlator/TouhouEntryActivity.java"
assert not target.exists(), "Upstream has a colliding Touhou entry activity"
overlay = Path(__file__).resolve().parent / "TouhouEntryActivity.java"
target.write_bytes(overlay.read_bytes())

# The Windows bootstrap has a Portal-owned startup presentation, not a
# second Winlator launcher. It replaces only the full-screen preloader view.
startup_source = overlay.parent / "CharoiteStartupScreen.java"
startup_target = java_root / "com/winlator/CharoiteStartupScreen.java"
assert startup_source.is_file() and not startup_target.exists()
startup_target.write_bytes(startup_source.read_bytes())
preloader_path = java_root / "com/winlator/core/PreloaderDialog.java"
preloader_code = preloader_path.read_text(encoding="utf-8")
old_preloader = "        dialog.setContentView(R.layout.preloader_dialog);"
assert preloader_code.count(old_preloader) == 1, "Upstream PreloaderDialog changed"
preloader_code = preloader_code.replace(old_preloader,
    "        dialog.setContentView(com.winlator.CharoiteStartupScreen.create(activity));")
preloader_path.write_text(preloader_code, encoding="utf-8")

# Charoite Core is a reusable source module packaged INSIDE the same APK.
# Unlike a new Android OS or a separate background app it shares the existing
# process, Wine storage, package ID, and native runtime. Compile the real source
# with the launcher so CI catches API or integration regressions.
core_source = overlay.parent / "charoite-core/CharoiteCore.java"
assert core_source.is_file(), "Charoite Core runtime source missing"
core_destination = java_root / "com/charoitegames/core/CharoiteCore.java"
assert not core_destination.exists(), "Upstream Charoite Core path conflict"
core_destination.parent.mkdir(parents=True, exist_ok=True)
core_destination.write_bytes(core_source.read_bytes())

# Shared Charoite Core owns all game import and Japanese compatibility,
# including Japanese locale/font registration independent of Touhou UI.
for module in ("CharoiteGameImport.java", "CharoiteJapaneseSupport.java",
               "CharoiteGameLibrary.java", "CharoiteGameDiscovery.java",
               "CharoiteGameProfiles.java", "CharoiteGameControlProfiles.java", "CharoiteGameSessions.java",
               "CharoiteLegacyKeyboard.java", "CharoiteHardwareSkin.java",
               "CharoiteBattleNetSupport.java",
               "CharoiteDiagnostics.java", "CharoiteRenderingDiagnostics.java",
               "CharoiteGraphicsProfiles.java", "CharoiteWindowPolicy.java",
               "CharoiteSoftKeyboard.java", "CharoiteShardOfDreamsSupport.java",
               "CharoiteFileManagerActivity.java", "CharoiteGameRemoval.java",
               "CharoiteGameIcons.java"):
    module_source = overlay.parent / "charoite-core" / module
    module_dest = java_root / "com/charoitegames/core" / module
    assert module_source.is_file(), f"Missing Core module: {module}"
    assert not module_dest.exists(), f"Upstream Core source collision: {module}"
    module_dest.write_bytes(module_source.read_bytes())
wallpaper_source = overlay.parent / "charoite-core/CharoiteWallpaper.java"
assert wallpaper_source.is_file(), "Charoite Wallpaper module missing"
wallpaper_destination = java_root / "com/charoitegames/core/CharoiteWallpaper.java"
assert not wallpaper_destination.exists(), "Upstream Charoite Wallpaper path conflict"
wallpaper_destination.write_bytes(wallpaper_source.read_bytes())

# Connected Library / Setup / System page tabs are a reusable Core widget,
# with host-supplied titles/palette/selection callback. No duplicate UI logic
# should remain in the Touhou-specific launcher.
tabs_source = overlay.parent / "charoite-core/CharoitePageTabs.java"
assert tabs_source.is_file(), "Charoite Core page tabs source missing"
tabs_destination = java_root / "com/charoitegames/core/CharoitePageTabs.java"
assert not tabs_destination.exists(), "Upstream Charoite page tabs path conflict"
tabs_destination.write_bytes(tabs_source.read_bytes())

swipe_source = overlay.parent / "charoite-core/CharoiteSwipePager.java"
assert swipe_source.is_file(), "Charoite swipe navigation module missing"
swipe_destination = java_root / "com/charoitegames/core/CharoiteSwipePager.java"
assert not swipe_destination.exists(), "Upstream swipe navigation path conflict"
swipe_destination.write_bytes(swipe_source.read_bytes())

profile_source = overlay.parent / "charoite-core/CharoiteEnvironmentFiles.java"
assert profile_source.is_file(), "Portable Charoite .cenv profile module missing"
profile_destination = java_root / "com/charoitegames/core/CharoiteEnvironmentFiles.java"
assert not profile_destination.exists(), "Upstream portable profile conflict"
profile_destination.write_bytes(profile_source.read_bytes())

environment_source = overlay.parent / "charoite-core/CharoiteEnvironments.java"
assert environment_source.is_file(), "Charoite Environment registry missing"
environment_destination = java_root / "com/charoitegames/core/CharoiteEnvironments.java"
assert not environment_destination.exists(), "Environment source collides with upstream"
environment_destination.write_bytes(environment_source.read_bytes())

theme_source = overlay.parent / "charoite-core/CharoiteThemes.java"
assert theme_source.is_file(), "Charoite theme source missing"
theme_destination = java_root / "com/charoitegames/core/CharoiteThemes.java"
assert not theme_destination.exists(), "Upstream Charoite theme path conflict"
theme_destination.write_bytes(theme_source.read_bytes())


# The read-only Wine diagnostics executable is cross-compiled by Actions and
# bundled as an asset, never committed as a binary to the source repository.
probe_binary = overlay.parent / "charoite-core/japanese/touhou_probe.exe"
assert probe_binary.is_file(), "Compile touhou_probe.exe before applying overlay"
probe_asset = root / "app/src/main/assets/japanese/touhou_probe.exe"
probe_asset.parent.mkdir(parents=True, exist_ok=True)
probe_asset.write_bytes(probe_binary.read_bytes())
# Windows installers may be 32-bit while the Wine runtime is 64-bit. Both
# matching bitness thread-hook helpers must ship alongside the diagnostic.
for arch in ("32", "64"):
    for suffix in (".exe", ".dll"):
        stem = "touhou_font_helper" if suffix == ".exe" else "touhou_font_hook"
        original = overlay.parent / "charoite-core/japanese" / f"{stem}{arch}{suffix}"
        assert original.is_file(), f"Missing compiled scoped font asset: {original}"
        (probe_asset.parent / original.name).write_bytes(original.read_bytes())



# Additional Wine-side legacy scan-code input backend (Touhou 8 only).
scan_binary = overlay.parent / "charoite-core/input/charoite_keyscan.exe"
assert scan_binary.is_file(), "Compile charoite_keyscan.exe before overlay"
scan_asset = root / "app/src/main/assets/input/charoite_keyscan.exe"
scan_asset.parent.mkdir(parents=True, exist_ok=True)
scan_asset.write_bytes(scan_binary.read_bytes())

# Battle.net-only guest-side DNS/HTTPS and running-Agent diagnosis.
# The executable is opt-in and writes only numeric status codes; never logs
# Blizzard login tokens, requests, account information or file contents.
bnet_probe = overlay.parent / "charoite-core/diagnostics/charoite_bnet_network_probe.exe"
assert bnet_probe.is_file() and bnet_probe.stat().st_size > 5000, (
    "Compile Wine Battle.net network probe before applying overlay"
)
bnet_asset = root / "app/src/main/assets/diagnostics/charoite_bnet_network_probe.exe"
bnet_asset.parent.mkdir(parents=True, exist_ok=True)
bnet_asset.write_bytes(bnet_probe.read_bytes())

# General, read-only Windows GDI rendering diagnostic. This is an ordinary
# test program, not an injected Wine DLL or visual text overlay.
gdi_binary = overlay.parent / "charoite-core/rendering/charoite_gdi_probe32.exe"
assert gdi_binary.is_file() and gdi_binary.stat().st_size > 10000, (
    "Compile Charoite Core GDI diagnostic before applying overlay"
)
gdi_asset = root / "app/src/main/assets/rendering/charoite_gdi_probe32.exe"
gdi_asset.parent.mkdir(parents=True, exist_ok=True)
gdi_asset.write_bytes(gdi_binary.read_bytes())
owner_binary = overlay.parent / "charoite-core/rendering/charoite_ownerdraw_probe32.exe"
assert owner_binary.is_file() and owner_binary.stat().st_size > 10000, (
    "Compile general owner-draw diagnostic before applying overlay"
)
owner_asset = root / "app/src/main/assets/rendering/charoite_ownerdraw_probe32.exe"
owner_asset.write_bytes(owner_binary.read_bytes())

# JNI entrypoints retain the com.winlator Java package, but native C/C++
# files also bake in app-private cache locations. Rewrite ONLY absolute
# /data/data/... paths (not JNI symbol names).
native_path_changes = 0
cpp_root = root / "app/src/main/cpp"
for native_source in cpp_root.rglob("*"):
    if native_source.is_file() and native_source.suffix in (".c", ".cc", ".cpp", ".h", ".hpp"):
        before = native_source.read_bytes()
        if b"/data/data/com.winlator" in before:
            native_source.write_bytes(before.replace(
                b"/data/data/com.winlator", b"/data/data/com.charoite"))
            native_path_changes += 1
print(f"Rebased {native_path_changes} C/C++ app-private path sources")

# Instrument the Wine renderer instead of leaving "Starting up" forever.
display = java_root / "com/winlator/XServerDisplayActivity.java"
code = display.read_text(encoding="utf-8")
# Keep standard immersive sensor-landscape on phones, but preserve DeX
# window decorations and allow the Windows game activity to be resized.
dex_ui_original = """        AppUtils.hideSystemUI(this);
        AppUtils.keepScreenOn(this);"""
assert code.count(dex_ui_original) == 1, "Upstream game UI initialization changed"
code = code.replace(dex_ui_original, """        if (getIntent().getBooleanExtra("touhou_desktop_window", false)) {
            // Non-immersive external-window mode: leave DeX window chrome intact.
            getWindow().getDecorView().setSystemUiVisibility(android.view.View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
        } else {
            // Windows installers/games follow the phone's physical orientation,
            // preserving the existing Wine/XServer session and its game saves.
            AppUtils.hideSystemUI(this);
        }
        AppUtils.keepScreenOn(this);
        // Only Library GAME launches enable the shared Core handheld shell.
        // Installers and DeX preserve their window and pointer behavior.
        com.charoitegames.core.CharoiteWindowPolicy.configureSession(
                getIntent().getStringExtra("exec_path"),
                getIntent().getBooleanExtra("charoite_handheld_game", false) &&
                !getIntent().getBooleanExtra("touhou_desktop_window", false));
        // A soft keyboard should overlay the bottom handheld controls,
        // not resize or pan TPDP's compositor-scaled game surface.
        // Non-TPDP games and DeX retain their existing keyboard behavior.
        if (com.charoitegames.core.CharoiteWindowPolicy.enlargeHandheldGame(
                getIntent().getStringExtra("exec_path"),
                getIntent().getBooleanExtra("touhou_desktop_window", false))) {
            getWindow().setSoftInputMode(
                    android.view.WindowManager.LayoutParams.SOFT_INPUT_ADJUST_NOTHING);
        }""")

# Reuse the Charoite Core handheld buttons for every game session, but
# never for an installer or DeX window. Keep TPDP's proven keyboard mapping.
tpdp_touch_source = overlay.parent / "charoite-core/CharoiteTpdpTouchControls.java"
tpdp_touch_target = java_root / "com/charoitegames/core/CharoiteTpdpTouchControls.java"
assert tpdp_touch_source.is_file() and not tpdp_touch_target.exists()
tpdp_touch_target.parent.mkdir(parents=True, exist_ok=True)
tpdp_touch_target.write_bytes(tpdp_touch_source.read_bytes())

# The base game's 480x360 and Shard's larger 4:3 windows require the same
# upper-handheld surface, but with independent native window sizes.
# TPDP's 480x360 game window remains small if we only reposition it in
# the Wine desktop. Use the existing Winlator compositor's aspect-ratio-
# preserving fullscreen-window transformation on phones. Importantly, this
# scales the *image* and pointer mapping, not TPDP's D3D9 render target,
# saved container resolution, or verified DXVK profile.
tpdp_large_game_anchor = (
    '        renderer.setForceWindowsFullscreen(shortcut != null && '
    'shortcut.getExtra("forceFullscreen", "0").equals("1"));'
)
assert code.count(tpdp_large_game_anchor) == 1, "Upstream fullscreen setting changed"
code = code.replace(tpdp_large_game_anchor, tpdp_large_game_anchor + """
        // Charoite Core owns the TPDP handheld presentation policy.
        // Leave DeX, installers and unrelated games' display settings alone.
        if (com.charoitegames.core.CharoiteWindowPolicy.enlargeHandheldGame(
                getIntent().getStringExtra("exec_path"),
                getIntent().getBooleanExtra("touhou_desktop_window", false))) {
            renderer.setForceWindowsFullscreen(true);
        }
""")

tpdp_touch_anchor = "        rootView.addView(inputControlsView);"
assert code.count(tpdp_touch_anchor)==1, "Winlator input layer changed"
code = code.replace(tpdp_touch_anchor, tpdp_touch_anchor + """
        // All Library games get the same Core handheld layout and frame.
        // Key mapping can differ; game graphics profiles are unaffected.
        if (getIntent().getBooleanExtra("charoite_handheld_game", false) &&
                !getIntent().getBooleanExtra("touhou_desktop_window", false)) {
            com.charoitegames.core.CharoiteTpdpTouchControls.attach(
                    this,rootView,(keyCode,pressed) -> {
                        // Inject the physical X11 key directly, with genuine
                        // DOWN/UP hold state. The inherited Android KeyEvent
                        // handler otherwise releases Shift on ANY key-up:
                        // that breaks Touhou 8 Focus + Shot combinations.
                        String gameExe = getIntent().getStringExtra("exec_path");
                        boolean touhou8 = com.charoitegames.core
                                .CharoiteLegacyKeyboard.requiresWindowsKeyboard(gameExe);
                        // Touhou 8 can poll either Win32/DirectInput or X11.
                        // Default DUAL attempts both (held DOWN/UP pairs);
                        // the More menu also lets the user isolate either
                        // backend while testing their particular translation.
                        // TPDP and all other games use the existing X11 path.
                        boolean fallback = touhou8 && com.charoitegames.core
                                .CharoiteLegacyKeyboard.useFallback(keyCode, pressed);
                        if (touhou8 && com.charoitegames.core
                                .CharoiteLegacyKeyboard.useScan())
                            com.charoitegames.core.CharoiteLegacyKeyboard.sendScan(
                                    keyCode, pressed);
                        if (touhou8 && com.charoitegames.core
                                .CharoiteLegacyKeyboard.useWindow())
                            com.charoitegames.core.CharoiteLegacyKeyboard.sendWindow(
                                    keyCode, pressed);
                        if (touhou8 && com.charoitegames.core
                                .CharoiteLegacyKeyboard.useWin32() || fallback) {
                            com.charoitegames.core.CharoiteLegacyKeyboard.send(
                                    xServer, gameExe, keyCode, pressed);
                        }
                        if (!touhou8 || com.charoitegames.core
                                .CharoiteLegacyKeyboard.useX11() || fallback) {
                            if (touhou8 && pressed) com.charoitegames.core
                                    .CharoiteLegacyKeyboard.prepareX11Focus(
                                            xServer, gameExe);
                            com.winlator.xserver.XKeycode key =
                                    com.charoitegames.core.CharoiteGameControlProfiles
                                            .toXKeycode(keyCode);
                            if (key != null) {
                                if (pressed) xServer.injectKeyPress(key);
                                else xServer.injectKeyRelease(key);
                                if (touhou8) com.charoitegames.core
                                        .CharoiteLegacyKeyboard.recordX11(keyCode, pressed);
                            }
                        }
                    }, this::confirmReturnToCharoitePortal,
                    com.charoitegames.core.CharoiteCore.isTpdpGameExecutable(
                            getIntent().getStringExtra("exec_path")),
                    getIntent().getStringExtra("exec_path"));
        }
""")

# WinHandler silently discards keyboardEvent() before its Wine-side INIT.
# Expose the handshake so Charoite can distinguish missing input transport.
handler_source = java_root / "com/winlator/winhandler/WinHandler.java"
handler_code = handler_source.read_text(encoding="utf-8")
handler_anchor = "    public void keyboardEvent(byte vkey, int flags) {"
assert handler_code.count(handler_anchor) == 1, "Upstream WinHandler changed"
handler_code = handler_code.replace(handler_anchor, """    public boolean isCharoiteKeyboardReady() {
        return running && initReceived && socket != null;
    }

""" + handler_anchor)
handler_source.write_text(handler_code, encoding="utf-8")

# Handle an actual phone teardown picture selected through the Android picker.
activity_result_anchor = """        super.onActivityResult(requestCode, resultCode, data);"""
assert code.count(activity_result_anchor) == 1, "Upstream activity result callback changed"
code = code.replace(activity_result_anchor, activity_result_anchor + """
        if (com.charoitegames.core.CharoiteHardwareSkin.onImageSelected(
                this, requestCode, resultCode, data)) return;
""")

# Charoite session drawer: only essential actions, themed from the realm
# already snapshotted into each launch Intent. Do not read another Activity's
# preferences or replace the upstream session/input/window implementations.
menu_brand_anchor = "        navigationView.setNavigationItemSelectedListener(this);"
assert code.count(menu_brand_anchor) == 1, "Upstream runtime drawer changed"
code = code.replace(menu_brand_anchor, menu_brand_anchor + """
        // A handheld already has a popup keyboard. DeX has its physical
        // keyboard. Phone installers/login windows still need a keyboard.
        boolean charoitePhoneKeyboard =
                !getIntent().getBooleanExtra("charoite_handheld_game", false) &&
                !getIntent().getBooleanExtra("touhou_desktop_window", false);
        for (int i = 0; i < menu.size(); i++) {
            android.view.MenuItem entry = menu.getItem(i);
            entry.setVisible(entry.getItemId() == R.id.menu_item_exit ||
                    (charoitePhoneKeyboard &&
                     entry.getItemId() == R.id.menu_item_keyboard));
        }
        menu.findItem(R.id.menu_item_exit).setTitle("Return to Charoite Portal");
        String charoiteTheme = getIntent().getStringExtra("charoite_environment_theme");
        String charoiteName = getIntent().getStringExtra("charoite_environment_name");
        boolean charoiteSakura = "touhou".equals(charoiteTheme) ||
                "sakura".equals(charoiteTheme);
        navigationView.setBackgroundColor(charoiteSakura ? 0xff251B2B : 0xff1D1730);
        navigationView.setItemTextColor(android.content.res.ColorStateList.valueOf(
                0xffF8F2FF));
        navigationView.setItemIconTintList(android.content.res.ColorStateList.valueOf(
                charoiteSakura ? 0xffF3B7DC : 0xffCAB4FF));
        android.graphics.drawable.GradientDrawable charoiteMenuPlate =
                new android.graphics.drawable.GradientDrawable(
                        android.graphics.drawable.GradientDrawable.Orientation.TL_BR,
                        charoiteSakura ? new int[]{0xff54304E, 0xff39223F} :
                                new int[]{0xff453067, 0xff2F214B});
        charoiteMenuPlate.setCornerRadius(
                14f * getResources().getDisplayMetrics().density);
        navigationView.setItemBackground(new android.graphics.drawable.RippleDrawable(
                android.content.res.ColorStateList.valueOf(0x55E7C7FF),
                charoiteMenuPlate, null));
        android.view.View charoiteHeader = navigationView.getHeaderView(0);
        if (charoiteHeader != null) {
            charoiteHeader.setBackground(
                    com.charoitegames.core.CharoiteThemes.realmBanner(charoiteTheme));
            android.widget.TextView charoiteEnvironmentLabel =
                    charoiteHeader.findViewById(R.id.charoite_session_environment);
            if (charoiteEnvironmentLabel != null)
                charoiteEnvironmentLabel.setText(charoiteName == null ||
                        charoiteName.trim().isEmpty() ? "Windows Gaming" : charoiteName);
        }
""")

# A drawer Exit must use the same save-progress confirmation as PORTAL.
drawer_exit_anchor = """            case R.id.menu_item_exit:
                exit();
                break;"""
assert code.count(drawer_exit_anchor) == 1, "Upstream game drawer Exit changed"
code = code.replace(drawer_exit_anchor, """            case R.id.menu_item_exit:
                drawerLayout.closeDrawers();
                confirmReturnToCharoitePortal();
                break;""")

# Winlator's TouchpadView converts rapid consecutive finger taps into
# rapid native mouse clicks. On Shard handheld these can toggle the
# Windows game window. Use two taps' own coordinates, NOT the compositor
# frame rectangle (it uses a different transform and missed real taps).
# Suppress only the SECOND nearby single-finger TAP, never the first,
# drag, multitouch, native mouse, non-Shard game, or DeX.
touchpad_source = java_root / "com/winlator/widget/TouchpadView.java"
touchpad_code = touchpad_source.read_text(encoding="utf-8")
touchpad_tap_anchor = """                if (finger1.isTap()) {
                    if (moveCursorToTouchpoint) xServer.injectPointerMove(finger1.x, finger1.y);
                    pressPointerButtonLeft(finger1);
                }"""
assert touchpad_code.count(touchpad_tap_anchor) == 1, (
    "Upstream TouchpadView single-finger click handler changed"
)
touchpad_code = touchpad_code.replace(touchpad_tap_anchor, """                if (finger1.isTap() && !charoiteSuppressShardDoubleTap(finger1)) {
                    if (moveCursorToTouchpoint) xServer.injectPointerMove(finger1.x, finger1.y);
                    pressPointerButtonLeft(finger1);
                }""")
touchpad_function_anchor = "    private void handleFingerUp(Finger finger1) {"
assert touchpad_code.count(touchpad_function_anchor) == 1, (
    "Upstream TouchpadView tap dispatcher changed"
)
touchpad_code = touchpad_code.replace(touchpad_function_anchor, """    private boolean charoiteSuppressShardDoubleTap(Finger finger) {
        if (!(getContext() instanceof android.app.Activity)) return false;
        android.app.Activity activity = (android.app.Activity)getContext();
        return com.charoitegames.core.CharoiteWindowPolicy.suppressShardTouchDoubleTap(
                activity.getIntent().getStringExtra("exec_path"),
                activity.getIntent().getBooleanExtra("touhou_desktop_window", false),
                xServer.screenInfo, finger.x, finger.y);
    }

""" + touchpad_function_anchor)
# Keep Android mouse/touch coordinates synchronized with the LIVE
# projected Wine screen when a phone changes physical orientation.
touchpad_viewport_anchor = """        viewTransformation.update(outerWidth, outerHeight, innerWidth, innerHeight);"""
assert touchpad_code.count(touchpad_viewport_anchor) == 1, (
    "Upstream TouchpadView viewport transform changed"
)
touchpad_code = touchpad_code.replace(touchpad_viewport_anchor,
    """        com.charoitegames.core.CharoiteWindowPolicy.updateLiveViewport(
                viewTransformation, xServer.screenInfo, outerWidth, outerHeight,
                xServer.activity.getIntent().getStringExtra("exec_path"),
                xServer.activity.getIntent().getBooleanExtra(
                        "touhou_desktop_window", false));""")
# GL uses a bottom-origin viewport Y, but pointer gestures arrive in
# top-origin Android coordinates. Convert the projected scene offset back
# before constructing the physical -> guest touch transform.
touchpad_top_origin_anchor = """            XForm.makeTranslation(xform, -viewTransformation.viewOffsetX, -viewTransformation.viewOffsetY);"""
assert touchpad_code.count(touchpad_top_origin_anchor) == 1, (
    "Upstream Android touch coordinate transform changed"
)
touchpad_code = touchpad_code.replace(touchpad_top_origin_anchor,
    """            int charoiteViewTop = outerHeight -
                    viewTransformation.viewOffsetY - viewTransformation.viewHeight;
            XForm.makeTranslation(xform,
                    -viewTransformation.viewOffsetX, -charoiteViewTop);""")
touchpad_rotation_anchor = """    public boolean onTouchEvent(MotionEvent event) {
"""
assert touchpad_code.count(touchpad_rotation_anchor) == 1, (
    "Upstream TouchpadView input callback changed"
)
touchpad_code = touchpad_code.replace(touchpad_rotation_anchor,
    touchpad_rotation_anchor + """        if (event.getActionMasked() == MotionEvent.ACTION_DOWN &&
                getWidth() > 0 && getHeight() > 0) {
            updateXform(getWidth(), getHeight(),
                    xServer.screenInfo.width, xServer.screenInfo.height);
        }
""")

touchpad_source.write_text(touchpad_code, encoding="utf-8")

# TPDP/Shard handheld sessions must not inherit the upstream keyboard
# cursor-tracking translation, which visibly pushes their Wine game image up.
# Other Windows games and DeX retain the original cursor-following behavior.
keyboard_pan_anchor = "        AppUtils.observeSoftKeyboardVisibility(drawerLayout, renderer::setScreenOffsetYRelativeToCursor);"
assert code.count(keyboard_pan_anchor) == 1, "Upstream IME renderer offset hook changed"
code = code.replace(keyboard_pan_anchor, """        if (com.charoitegames.core.CharoiteWindowPolicy.enlargeHandheldGame(
                getIntent().getStringExtra("exec_path"),
                getIntent().getBooleanExtra("touhou_desktop_window", false))) {
            // Keep the upper handheld display stationary when the IME appears.
            renderer.setScreenOffsetYRelativeToCursor(false);
        } else {
            AppUtils.observeSoftKeyboardVisibility(drawerLayout,
                    renderer::setScreenOffsetYRelativeToCursor);
        }""")

# Keep Wine/XServer alive during device rotation. GLSurfaceView automatically
# calls GLRenderer.onSurfaceChanged(new width, height); its viewTransformation
# then fits the live Wine image to the new phone surface size. This does NOT
# secretly restart the installer/game or overwrite the Wine container.
rotation_java = """    @Override
    public void onConfigurationChanged(android.content.res.Configuration newConfig) {
        super.onConfigurationChanged(newConfig);
        if (xServerView != null) {
            xServerView.post(() -> {
                xServerView.requestLayout();
                xServerView.requestRender();
                if (inputControlsView != null) inputControlsView.requestLayout();
                if (touchpadView != null) touchpadView.requestLayout();
            });
        }
    }

"""
tpdp_window_layout = """    // Charoite Core owns the window policy; Winlator provides XServer events.
    private boolean charoiteBnetMonitorStarted = false;

    /** Monitor the ACTUAL Battle.net Wine session, unlike the standalone
     * diagnostic activity which necessarily has a separate process lifetime.
     * Never touch Blizzard files; the observer is a Charoite-owned Win32 EXE.
     */
    private void startCharoiteBattleNetMonitor() {
        if (charoiteBnetMonitorStarted ||
                !getIntent().getBooleanExtra("charoite_bnet_monitor", false))
            return;
        charoiteBnetMonitorStarted = true;
        if (container != null)
            com.charoitegames.core.CharoiteBattleNetSupport.noteLiveAgentMonitorState(
                    container.getRootDir(), "ARMED");
        final android.os.Handler ui = new android.os.Handler(
                android.os.Looper.getMainLooper());
        final int[] attempts = {0};
        final Runnable[] invoke = new Runnable[1];
        invoke[0] = () -> {
            if (isFinishing() || isDestroyed()) return;
            attempts[0]++;
            if (winHandler == null || !winHandler.isCharoiteKeyboardReady()) {
                if (container != null && attempts[0] == 1)
                    com.charoitegames.core.CharoiteBattleNetSupport.noteLiveAgentMonitorState(
                            container.getRootDir(), "WAITING_FOR_WINE");
                if (attempts[0] < 12) ui.postDelayed(invoke[0], 1000);
                else {
                    if (container != null)
                        com.charoitegames.core.CharoiteBattleNetSupport.noteLiveAgentMonitorState(
                                container.getRootDir(), "WINE_BRIDGE_TIMEOUT");
                    android.util.Log.w("CharoiteBattleNet",
                            "Wine bridge never became ready for launch monitor");
                }
                return;
            }
            try {
                if (container == null) throw new java.io.IOException("No container");
                com.charoitegames.core.CharoiteBattleNetSupport.prepareGuestNetworkProbe(
                        this, container.getRootDir());
                winHandler.exec(
                        "C:\\\\CharoitePortal\\\\Diagnostics\\\\charoite_bnet_network_probe.exe",
                        getIntent().getBooleanExtra("charoite_bnet_try_start_rpc", false) &&
                        !getIntent().getBooleanExtra("charoite_bnet_rpc_preflight", false)
                                ? "/monitor /try-rpcss-start" : "/monitor");
                com.charoitegames.core.CharoiteBattleNetSupport.noteLiveAgentMonitorState(
                        container.getRootDir(), "COMMAND_SENT");
                android.util.Log.i("CharoiteBattleNet",
                        "In-session Agent monitor launched; 16 bounded samples");
            } catch (Exception error) {
                if (container != null)
                    com.charoitegames.core.CharoiteBattleNetSupport.noteLiveAgentMonitorState(
                            container.getRootDir(), "PREPARE_FAILED");
                android.util.Log.w("CharoiteBattleNet",
                        "In-session monitor cannot start", error);
            }
        };
        ui.post(invoke[0]);
    }

    private void confirmReturnToCharoitePortal() {
        if (isFinishing() || isDestroyed()) return;
        new androidx.appcompat.app.AlertDialog.Builder(this)
                .setTitle("Return to Charoite Portal?")
                .setMessage("The Windows session will close. Save game progress or finish any installation first; unsaved work may be lost.")
                .setNegativeButton("Stay Here", null)
                .setPositiveButton("Return to Portal", (dialog, which) -> {
                    com.charoitegames.core.CharoiteDiagnostics.requestPortalExit(this);
                    exit();
                })
                .show();
    }

    private void centerTpdpGameWindow(Window window) {
        com.charoitegames.core.CharoiteWindowPolicy.centerGameWindow(
                this, xServer, screenInfo, window,
                getIntent().getStringExtra("exec_path"),
                getIntent().getBooleanExtra("touhou_desktop_window", false));
    }

"""
assert code.count("    @Override\n    public void onWindowFocusChanged(boolean hasFocus) {") == 1, "Window focus insertion point changed"
code = code.replace(
    "    @Override\n    public void onWindowFocusChanged(boolean hasFocus) {",
    tpdp_window_layout + "    @Override\n    public void onWindowFocusChanged(boolean hasFocus) {")
rotation_anchor = "    @Override\n    public void onWindowFocusChanged(boolean hasFocus) {"
assert code.count(rotation_anchor) == 1, "Upstream game rotation insertion changed"
code = code.replace(rotation_anchor, rotation_java + rotation_anchor)

# Pick a per-launch Wine virtual desktop size, never changing the
# persistent Wine container or files when moving between DeX and phone.
old_guest_screen = "            screenInfo = resolveScreenInfo(container.getScreenSize());"
assert code.count(old_guest_screen) == 1, "Upstream container screenInfo marker changed"
code = code.replace(old_guest_screen, old_guest_screen + """
            if (getIntent().hasExtra("touhou_display_size")) {
                String requested = getIntent().getStringExtra("touhou_display_size");
                if (requested != null && requested.matches("800x600|1280x720|1600x900|1920x1080|600x800|720x1280|900x1600|1080x1920|960x1280|960x1600|960x1920"))
                    screenInfo = resolveScreenInfo(requested);
            }""")

# Winlator already handles Android key and mouse events. On DeX choose
# whether to capture the pointer, defaulting to a freely movable cursor.
old_mouse = '        capturePointerOnExternalMouse = preferences.getBoolean("capture_pointer_on_external_mouse", true);'
assert code.count(old_mouse) == 1, "Upstream mouse-capture marker changed"
code = code.replace(old_mouse,
    '        capturePointerOnExternalMouse = getIntent().getBooleanExtra("touhou_pointer_capture", ' +
    'preferences.getBoolean("capture_pointer_on_external_mouse", true));')
# Before-client RPC initialization: unlike the later post-window monitor,
# this command is the FIRST Win32 application Wine explorer launches. After
# successful preflight it forwards the existing WinHandler arguments via
# CreateProcessW, preserving the normal Battle.net client/Agent code path.
bnet_prelaunch_anchor = '            String guestExecutable = "wine explorer /desktop="+desktopName+","+xServer.screenInfo+" "+getWineStartCommand();'
assert code.count(bnet_prelaunch_anchor) == 1, "Upstream Windows guest launch anchor changed"
code = code.replace(bnet_prelaunch_anchor, """            String charoiteNormalWinHandler = getWineStartCommand();
            String guestExecutable = "wine explorer /desktop="+desktopName+","+xServer.screenInfo+" "+charoiteNormalWinHandler;
            if (getIntent().getBooleanExtra("charoite_bnet_rpc_preflight", false) &&
                    "battle-net-gaming".equals(getIntent().getStringExtra("charoite_environment_id")) &&
                    getIntent().hasExtra("exec_path")) {
                // The service startup and rollback happen BEFORE Wine launches
                // the installed client; CEF no longer has to initialize first.
                final String winHandlerPrefix = "C:\\\\windows\\\\winhandler.exe ";
                if (charoiteNormalWinHandler.startsWith(winHandlerPrefix)) {
                    try {
                        com.charoitegames.core.CharoiteBattleNetSupport.prepareGuestNetworkProbe(
                                this, container.getRootDir());
                        guestExecutable = "wine explorer /desktop="+desktopName+","+xServer.screenInfo+
                                " C:\\\\CharoitePortal\\\\Diagnostics\\\\charoite_bnet_network_probe.exe /preflight-launch "+
                                charoiteNormalWinHandler.substring(winHandlerPrefix.length());
                        com.charoitegames.core.CharoiteBattleNetSupport.noteLiveAgentMonitorState(
                                container.getRootDir(), "RPC_PREFLIGHT_ARMED");
                    } catch (java.io.IOException error) {
                        com.charoitegames.core.CharoiteBattleNetSupport.noteLiveAgentMonitorState(
                                container.getRootDir(), "RPC_PREFLIGHT_PREPARE_FAILED");
                        // Avoid crashing the user session on a probe copy error.
                    }
                } else {
                    com.charoitegames.core.CharoiteBattleNetSupport.noteLiveAgentMonitorState(
                            container.getRootDir(), "RPC_PREFLIGHT_PREFIX_MISMATCH");
                }
            }
            if (container != null &&
                    getIntent().getBooleanExtra("charoite_bnet_monitor", false) &&
                    "battle-net-gaming".equals(getIntent().getStringExtra("charoite_environment_id"))) {
                // Record actual parsed renderer and assembled client command,
                // not just UI selection. Do NOT persist command lines or paths.
                com.charoitegames.core.CharoiteBattleNetSupport.recordBattleNetLaunchCommand(
                        container.getRootDir(),
                        getIntent().getBooleanExtra("charoite_bnet_rpc_preflight", false),
                        getIntent().getBooleanExtra("charoite_bnet_agent_compatibility", false),
                        getIntent().getBooleanExtra("charoite_bnet_disable_gpu", false),
                        charoiteNormalWinHandler.contains(" --disable-gpu"),
                        GraphicsDrivers.VIRGL.equals(this.graphicsDriver[1]),
                        DXWrappers.WINED3D.equals(this.dxwrapper));
            }
""")

# Battle.net CEF launcher: Blizzard recommends --disable-gpu when its
# embedded browser is blank/spinning. Append arguments only to the installed
# client under the selected Battle.net environment (never setup.exe, TPDP or
# other users' Windows programs). The launcher and prefix remain unmodified.
bnet_cmd_anchor = r'            cmdArgs = "/dir "+StringUtils.escapeDOSPath(execDir)+" \""+filename+"\""+execArgs;'
assert code.count(bnet_cmd_anchor) == 1, "Upstream Wine launch argument hook changed"
code = code.replace(bnet_cmd_anchor, bnet_cmd_anchor + """
            if (getIntent().getBooleanExtra("charoite_bnet_disable_gpu", false) &&
                    "battle-net-gaming".equals(
                        getIntent().getStringExtra("charoite_environment_id")) &&
                    (filename.equalsIgnoreCase("Battle.net Launcher.exe") ||
                     filename.equalsIgnoreCase("Battle.net.exe"))) {
                // Blizzard's documented workaround for CEF hardware GPU faults.
                // Applies to exactly this launch; no registry/cache deletion.
                cmdArgs += " --disable-gpu";
            }
            if (getIntent().getBooleanExtra("charoite_bnet_in_process_gpu", false) &&
                    "battle-net-gaming".equals(
                        getIntent().getStringExtra("charoite_environment_id")) &&
                    (filename.equalsIgnoreCase("Battle.net Launcher.exe") ||
                     filename.equalsIgnoreCase("Battle.net.exe"))) {
                // Alternative Chromium CEF GPU-process isolation trial.
                // Mutually exclusive with --disable-gpu; never persisted.
                cmdArgs += " --in-process-gpu";
            }
""")

# TPDP base game can run at 60 FPS with audio but present a black DirectX 9
# window under some WineD3D backends. Use a per-launch DXVK/Turnip selection:
# the original container and every other game keep their saved settings.
# Source: pinned Winlator XServerDisplayActivity local variables before the
# existing wrapper and graphics-driver parsers.
tpdp_backend_anchor = "            this.graphicsDriver = GraphicsDrivers.parseIdentifiers(graphicsDriver);"
assert code.count(tpdp_backend_anchor) == 1, "Winlator graphics parser moved"
code = code.replace(tpdp_backend_anchor, """
            // Charoite Core resolves the compatibility profile automatically
            // for known executables; unknown games keep container defaults.
            com.charoitegames.core.CharoiteGraphicsProfiles.Profile coreGraphics =
                    com.charoitegames.core.CharoiteGraphicsProfiles.forExecutable(
                        getIntent().getStringExtra("exec_path"));
            if (coreGraphics != null) {
                graphicsDriver = coreGraphics.graphicsDriver;
                dxwrapper = coreGraphics.dxWrapper;
                dxwrapperConfig = coreGraphics.dxWrapperConfig;
                graphicsDriverConfig = coreGraphics.graphicsDriverConfig;
            }
            if (getIntent().getBooleanExtra("charoite_bnet_agent_compatibility", false)) {
                // Explicit retry for a Battle.net Agent launch failure:
                // avoid Vulkan/DXVK and use the existing VirGL + WineD3D
                // alternative. Does not edit the saved Wine container.
                graphicsDriver = GraphicsDrivers.VIRGL + "," +
                        GraphicsDrivers.DEFAULT_OPENGL_DRIVER;
                dxwrapper = DXWrappers.WINED3D;
                dxwrapperConfig = "";
                graphicsDriverConfig = "";
            }
""" + tpdp_backend_anchor)

old_show = "        preloaderDialog.show(R.string.starting_up);"
assert code.count(old_show) == 1, "Startup dialog marker changed"
code = code.replace(old_show, """        final boolean[] touhouWindowOpened = {false};
        final int[] tpdpContentEvents = {0};
        final int[] tpdpSurfaceEvents = {0};
        if (getIntent().hasExtra("exec_path")) {
            com.charoitegames.core.CharoiteDiagnostics.begin(this, getIntent().getStringExtra("exec_path"));
            com.charoitegames.core.CharoiteDiagnostics.recordGraphicsBackend(
                    this, this.dxwrapper, this.graphicsDriver[0],
                    this.graphicsDriver[1],
                    com.charoitegames.core.CharoiteGraphicsProfiles.diagnosticModeForExecutable(
                         getIntent().getStringExtra("exec_path")));
            com.charoitegames.core.CharoiteDiagnostics.recordAudioBackend(
                    this, this.audioDriver);
            ProcessHelper.addDebugCallback(com.charoitegames.core.CharoiteDiagnostics.CALLBACK);
            new android.os.Handler(android.os.Looper.getMainLooper()).postDelayed(() -> {
                if (!isFinishing() && !touhouWindowOpened[0]) {
                    com.charoitegames.core.CharoiteDiagnostics.fail(this, "No Windows game window appeared after 45 seconds. Check Wine/Box64 and graphics compatibility.");
                    preloaderDialog.closeOnUiThread();
                    new androidx.appcompat.app.AlertDialog.Builder(this)
                        .setTitle("Windows game did not start")
                        .setMessage("The Windows engine failed to display the game.\\n\\nReturn to Charoite Portal and open Launch Diagnostics, or switch to Compatibility Graphics.")
                        .setCancelable(false)
                        .setPositiveButton("Return to Charoite Portal", (d, which) -> exit())
                        .show();
                }
            }, 45000);
        }
""" + old_show)
content_anchor = "                if (window.id == frameRatingWindowId) frameRating.update();"
assert code.count(content_anchor) == 1, "XServer content update hook changed"
code = code.replace(content_anchor, content_anchor + """
                // X11 content callbacks can fire once per frame or more.
                // Do not collect counters on Shard's rendering hot path;
                // base TPDP keeps its existing diagnostic sampling.
                if (getIntent().hasExtra("exec_path") &&
                        !com.charoitegames.core.CharoiteShardOfDreamsSupport.isExpansionGame(
                                getIntent().getStringExtra("exec_path")) &&
                        com.charoitegames.core.CharoiteCore.isTpdpGameExecutable(
                                getIntent().getStringExtra("exec_path")) &&
                        window.isRenderable() && !window.isDesktopWindow()) {
                    tpdpContentEvents[0]++;
                    if (window.isSurface()) tpdpSurfaceEvents[0]++;
                    if (tpdpContentEvents[0] == 1 || tpdpContentEvents[0] % 120 == 0)
                        com.charoitegames.core.CharoiteDiagnostics.recordX11ContentActivity(
                                XServerDisplayActivity.this,
                                tpdpContentEvents[0], tpdpSurfaceEvents[0]);
                }
""")
window_map_anchor = "            public void onMapWindow(Window window) {"
assert code.count(window_map_anchor) == 1, "Wine window map listener changed"
code = code.replace(window_map_anchor, window_map_anchor + """
                // Record mapped Wine X-windows; window mapping does not
                // necessarily mean the game has presented visible pixels.
                if (getIntent().hasExtra("exec_path") && window.isRenderable())
                    com.charoitegames.core.CharoiteDiagnostics.recordMappedWindow(
                        XServerDisplayActivity.this, window.getClassName(),
                        window.getName(), window.getWidth(), window.getHeight(),
                        window.getRootX(), window.getRootY());
                centerTpdpGameWindow(window);
""")
geometry_tracking_anchor = "            @Override\n            public void onUnmapWindow(Window window) {"
assert code.count(geometry_tracking_anchor) == 1, "Wine window unmap listener changed"
code = code.replace(geometry_tracking_anchor, """
            @Override
            public void onUpdateWindowGeometry(Window window, boolean resized) {
                centerTpdpGameWindow(window);
            }

            @Override
            public void onModifyWindowProperty(Window window, Property property) {
                centerTpdpGameWindow(window);
            }

""" + geometry_tracking_anchor)
old_cursor = "                    xServerView.getRenderer().setCursorVisible(true);"
assert code.count(old_cursor) == 1, "Window-open marker changed"
code = code.replace(old_cursor, """                    touhouWindowOpened[0] = true;
                    if (getIntent().hasExtra("exec_path")) com.charoitegames.core.CharoiteDiagnostics.windowOpened(XServerDisplayActivity.this);
                    if (getIntent().getBooleanExtra("charoite_bnet_monitor", false))
                        startCharoiteBattleNetMonitor();
""" + old_cursor)
old_exit = """        if (intent.hasExtra("exec_path")) {
            AppUtils.RestartApplicationOptions options = new AppUtils.RestartApplicationOptions();
            options.containerId = container.id;
            options.startPath = FileUtils.getDirname(intent.getStringExtra("exec_path"));
            AppUtils.restartApplication(this, options);
        }
        else AppUtils.restartApplication(this);"""
assert code.count(old_exit) == 1, "Upstream exit routing marker changed"
code = code.replace(old_exit, """        if (intent.hasExtra("exec_path")) {
            ProcessHelper.removeDebugCallback(com.charoitegames.core.CharoiteDiagnostics.CALLBACK);
            Intent home = new Intent(this, TouhouEntryActivity.class);
            home.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
            startActivity(home);
            finish();
        }
        else {
             Intent home = new Intent(this, TouhouEntryActivity.class);
             home.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
             startActivity(home);
             finish();
         }""")
old_callback = "        guestProgramLauncherComponent.setTerminationCallback((status) -> exit());"
assert code.count(old_callback) == 1, "Guest-process exit callback changed"
code = code.replace(old_callback, """        guestProgramLauncherComponent.setTerminationCallback((status) -> {
            if (getIntent().hasExtra("exec_path"))
                com.charoitegames.core.CharoiteDiagnostics.finishGuestProcess(this, status);
            runOnUiThread(this::exit);
        });""")
# Apply TPDP-only diagnostics after Wine's saved container env-vars have
# loaded, so the user can inspect actual Direct3D failures after black frames.
tpdp_debug_anchor = "        guestProgramLauncherComponent.setEnvVars(envVars);"
assert code.count(tpdp_debug_anchor) == 1, "Winlator guest environment marker changed"
code = code.replace(tpdp_debug_anchor, """
        // The installed Battle.net client uses Chromium Embedded Framework.
        // Wine CEF builds sometimes require disabling locationapi; append
        // only this DLL rule to existing overrides, without replacing them.
        // One launch only; no registry, Wine prefix or game changes.
        if (getIntent().getBooleanExtra("charoite_bnet_disable_gpu", false) &&
                "battle-net-gaming".equals(
                    getIntent().getStringExtra("charoite_environment_id"))) {
            String overrides = envVars.get("WINEDLLOVERRIDES");
            if (!java.util.regex.Pattern.compile(
                    "(^|;)locationapi=", java.util.regex.Pattern.CASE_INSENSITIVE)
                    .matcher(overrides).find()) {
                envVars.put("WINEDLLOVERRIDES", overrides.isEmpty() ?
                        "locationapi=d" : overrides + ";locationapi=d");
            }
            // Hint for CEF PAGE_WRITECOPY mismatches; harmless if unsupported.
            envVars.put("WINE_SIMULATE_WRITECOPY", "1");
        }
        // A safe, session-local troubleshooting mode for Battle.net Agent.
        // Wine/Box64 process synchronization failures can prevent the
        // updater from starting. This is experimental, opt-in only and
        // leaves the selected container and installed games unchanged.
        if (getIntent().getBooleanExtra("charoite_bnet_agent_compatibility", false)) {
            envVars.put("WINEESYNC", "0");
            envVars.put("WINEFSYNC", "0");
            envVars.put("WINEDEBUG", "err+all,warn+all");
        }
        // Charoite Core owns per-game graphics launch options and diagnostics.
        // This native bridge never reads deprecated manual TPDP preferences.
        if (getIntent().hasExtra("exec_path")) {
            com.charoitegames.core.CharoiteGraphicsProfiles.configureLaunchEnvironment(
                    this, rootFS, envVars, getIntent().getStringExtra("exec_path"));
        }
        if (getIntent().hasExtra("exec_path") &&
                com.charoitegames.core.CharoiteGraphicsProfiles.forExecutable(
                        getIntent().getStringExtra("exec_path")) == null &&
                com.charoitegames.core.CharoiteCore.japaneseCompatibilityEnabled(this) &&
                com.charoitegames.core.CharoiteCore.isJapaneseInstallerCandidate(
                        getIntent().getStringExtra("exec_path"))) {
            // Keep existing installer diagnosis separate from game profiles.
            envVars.put("WINEDEBUG", "err+all,warn+all");
        }
        if (container != null &&
                getIntent().getBooleanExtra("charoite_bnet_monitor", false) &&
                "battle-net-gaming".equals(getIntent().getStringExtra("charoite_environment_id"))) {
            String dllOverrides = envVars.get("WINEDLLOVERRIDES");
            com.charoitegames.core.CharoiteBattleNetSupport.recordBattleNetRuntimeEnv(
                    container.getRootDir(),
                    "0".equals(envVars.get("WINEESYNC")),
                    "0".equals(envVars.get("WINEFSYNC")),
                    dllOverrides != null && java.util.regex.Pattern.compile(
                            "(^|;)locationapi=", java.util.regex.Pattern.CASE_INSENSITIVE)
                            .matcher(dllOverrides).find());
        }
""" + tpdp_debug_anchor)
display.write_text(code, encoding="utf-8")

# The upstream renderer drawer had a Winlator header. Replace the visible
# header layout with accessible Charoite labels. Runtime Java sets the realm
# art from the same template as the Portal banner and writes the launch name.
menu_header_path = root / "app/src/main/res/layout/main_menu_header.xml"
menu_header_original = menu_header_path.read_text(encoding="utf-8")
assert '@drawable/logo' in menu_header_original, "Upstream runtime header changed"
menu_header_path.write_text("""<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="154dp"
    android:orientation="vertical"
    android:gravity="bottom|start"
    android:padding="20dp"
    android:background="#302149">
    <TextView
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="CHAROITE CORE"
        android:textColor="#FFF5FF"
        android:textStyle="bold"
        android:letterSpacing="0.07"
        android:textSize="19sp" />
    <TextView
        android:id="@+id/charoite_session_environment"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="Windows Gaming"
        android:layout_marginTop="8dp"
        android:textColor="#F3E1FF"
        android:textSize="16sp"
        android:maxLines="2"
        android:ellipsize="end" />
</LinearLayout>
""", encoding="utf-8")

# Keep the enlarged, aspect-preserving TPDP window in the upper display
# area, rather than the upstream default screen center. The fullscreen
# transform handles touch/pointer hit testing as well as display scaling.
gl_renderer = java_root / "com/winlator/renderer/GLRenderer.java"
gl_renderer_code = gl_renderer.read_text(encoding="utf-8")

# A running Wine guest keeps its launch-time desktop mode while the phone
# rotates. Recalculate the Android projection when GLSurfaceView resizes
# and whenever the game's mapped X11 client changes, using one scale value
# for both axes. Game frame / graphics backend remain unchanged.
surface_rotation_anchor = """        viewTransformation.update(width, height, xServer.screenInfo.width, xServer.screenInfo.height);
        viewportNeedsUpdate = true;"""
assert gl_renderer_code.count(surface_rotation_anchor) == 1, (
    "Upstream onSurfaceChanged viewport update changed"
)
gl_renderer_code = gl_renderer_code.replace(surface_rotation_anchor,
    surface_rotation_anchor + """
        if (com.charoitegames.core.CharoiteWindowPolicy.enlargeHandheldGame(
                xServer.activity.getIntent().getStringExtra("exec_path"),
                xServer.activity.getIntent().getBooleanExtra(
                        "touhou_desktop_window", false))) {
            updateScene();
        }""")
scene_rotation_anchor = """            collectRenderableWindows(xServer.windowManager.rootWindow, xServer.windowManager.rootWindow.getX(), xServer.windowManager.rootWindow.getY());
        }
    }"""
assert gl_renderer_code.count(scene_rotation_anchor) == 1, (
    "Upstream GL scene rebuilding changed"
)
gl_renderer_code = gl_renderer_code.replace(scene_rotation_anchor,
    """            collectRenderableWindows(xServer.windowManager.rootWindow, xServer.windowManager.rootWindow.getX(), xServer.windowManager.rootWindow.getY());
        }
        if (com.charoitegames.core.CharoiteWindowPolicy.enlargeHandheldGame(
                xServer.activity.getIntent().getStringExtra("exec_path"),
                xServer.activity.getIntent().getBooleanExtra(
                        "touhou_desktop_window", false))) {
            com.charoitegames.core.CharoiteWindowPolicy.updateLiveViewport(
                    viewTransformation, xServer.screenInfo,
                    surfaceWidth, surfaceHeight,
                    xServer.activity.getIntent().getStringExtra("exec_path"),
                    xServer.activity.getIntent().getBooleanExtra(
                            "touhou_desktop_window", false));
            viewportNeedsUpdate = true;
        }
    }""")


# Observe existing Android GL draws without changing the frame limiter or
# making per-frame disk writes. The sample is Core-owned and Shard-only.
android_draw_anchor = """    public void onDrawFrame(GL10 gl) {
"""
assert gl_renderer_code.count(android_draw_anchor) == 1, (
    "Upstream GL onDrawFrame hook changed"
)
gl_renderer_code = gl_renderer_code.replace(android_draw_anchor,
    android_draw_anchor + """        com.charoitegames.core.CharoiteDiagnostics.recordAndroidDraw();
        long charoiteDrawStarted = com.charoitegames.core.CharoiteDiagnostics.beginAndroidDrawMeasure();
""")

# Measure rendering CPU submission only, not GPU time, and without
# changing the renderer's EGL swap interval or native frame scheduling.
android_draw_end_anchor = """        else drawFrame();
    }

    protected void drawFrame() {"""
assert gl_renderer_code.count(android_draw_end_anchor) == 1, (
    "Upstream GL render completion hook changed"
)
gl_renderer_code = gl_renderer_code.replace(android_draw_end_anchor,
    """        else drawFrame();
        com.charoitegames.core.CharoiteDiagnostics.endAndroidDrawMeasure(
                charoiteDrawStarted);
    }

    protected void drawFrame() {""")

# Shard's game drawable can be a larger or widescreen window. The two
# upstream filters (size and decoration) must BOTH be relaxed for Shard's
# verified game drawable, or it stays native-sized with a floating titlebar.
# Other executables and TPDP base retain the original fullscreen filtering.
oversized_shard_anchor = (
    "                boolean inBounds = width >= ScreenInfo.MIN_WIDTH && height >= ScreenInfo.MIN_HEIGHT && width < xServer.screenInfo.width && height < xServer.screenInfo.height;"
)
assert gl_renderer_code.count(oversized_shard_anchor) == 1, (
    "Upstream fullscreen client-size policy changed"
)
gl_renderer_code = gl_renderer_code.replace(oversized_shard_anchor,
    oversized_shard_anchor + """
                // The Shard parent and 960x720 client must NOT both be
                // transformed, including when the parent passes normal bounds.
                if (com.charoitegames.core.CharoiteWindowPolicy.isShardHandheldContainer(
                        window, xServer.screenInfo,
                        xServer.activity.getIntent().getStringExtra("exec_path"),
                        xServer.activity.getIntent().getBooleanExtra(
                                "touhou_desktop_window", false))) {
                    inBounds = false;
                } else {
                    inBounds = inBounds ||
                        com.charoitegames.core.CharoiteWindowPolicy.allowOversizedShardGame(
                                window, xServer.screenInfo,
                                xServer.activity.getIntent().getStringExtra("exec_path"),
                                xServer.activity.getIntent().getBooleanExtra(
                                        "touhou_desktop_window", false));
                }
""")

# Upstream also rejects windows that report decorations even if their real
# client surface is the Shard game. The core identifies only leaf game windows.
shard_decorations_anchor = (
    "window.getType() == Window.Type.NORMAL && inBounds && window.hasNoDecorations()"
)
assert gl_renderer_code.count(shard_decorations_anchor) == 1, (
    "Upstream fullscreen decoration filter changed"
)
gl_renderer_code = gl_renderer_code.replace(shard_decorations_anchor,
    """window.getType() == Window.Type.NORMAL && inBounds &&
                    (window.hasNoDecorations() ||
                     com.charoitegames.core.CharoiteWindowPolicy.allowDecoratedShardClient(
                         window, xServer.screenInfo,
                         xServer.activity.getIntent().getStringExtra("exec_path"),
                         xServer.activity.getIntent().getBooleanExtra(
                             "touhou_desktop_window", false)))""")


tpdp_viewport_anchor = (
    "                    fullscreenTransformation.update(xServer.screenInfo, "
    "window.getWidth(), window.getHeight());"
)
assert gl_renderer_code.count(tpdp_viewport_anchor) == 1, "Upstream window scale hook changed"
gl_renderer_code = gl_renderer_code.replace(tpdp_viewport_anchor, tpdp_viewport_anchor + """
                    com.charoitegames.core.CharoiteWindowPolicy.placeScaledGame(
                            fullscreenTransformation, xServer.screenInfo, window,
                            xServer.activity.getIntent().getStringExtra("exec_path"),
                            xServer.activity.getIntent().getBooleanExtra(
                                    "touhou_desktop_window", false));
""")
# The decorated parent can receive a second fullscreen transform. Scale
# it to the same portrait percentage so the title/border won't remain at
# full width while the actual 4:3 game picture is reduced.
# The actual TPDP image is a distinct Win32 client with a separate
# decorated parent. Suppress only its parent *drawable*, not the Win32
# parent itself. This avoids a titlebar above / line below the client.
native_frame_anchor = (
    "                    if (parent != xServer.windowManager.rootWindow && "
    "parent.getChildCount() == 1 && parent.hasDecoration(Decoration.BORDER) "
    "&& parent.hasDecoration(Decoration.TITLE)) {"
)
assert gl_renderer_code.count(native_frame_anchor) == 1, (
    "Upstream decorated parent selection changed"
)
gl_renderer_code = gl_renderer_code.replace(native_frame_anchor, """
                    if (com.charoitegames.core.CharoiteWindowPolicy.hideNativeFrame(
                            parent, window, xServer.screenInfo,
                            xServer.activity.getIntent().getStringExtra("exec_path"),
                            xServer.activity.getIntent().getBooleanExtra(
                                    "touhou_desktop_window", false))) {
                        // The child is still rendered full-size. The Core
                        // outline replaces Wine's independently scaled border.
                        parent.setFullscreenTransformation(null);
                        removeRenderableWindow(parent);
                    }
                    else """ + native_frame_anchor.lstrip())

tpdp_parent_scale_anchor = (
    "                        parentFullscreenTransformation.update("
    "xServer.screenInfo, parent.getWidth(), parent.getHeight());"
)
assert gl_renderer_code.count(tpdp_parent_scale_anchor) == 1, (
    "Upstream decorated game window scaling changed"
)
gl_renderer_code = gl_renderer_code.replace(
    tpdp_parent_scale_anchor, tpdp_parent_scale_anchor + """
                        com.charoitegames.core.CharoiteWindowPolicy.alignWindowFrame(
                                parentFullscreenTransformation, fullscreenTransformation,
                                parent, window, xServer.screenInfo,
                                xServer.activity.getIntent().getStringExtra("exec_path"),
                                xServer.activity.getIntent().getBooleanExtra(
                                        "touhou_desktop_window", false));
""")
gl_renderer.write_text(gl_renderer_code, encoding="utf-8")



# Existing game foreground notifications were still hardcoded "Winlator"
# even after app_name changed, and their Open action targeted old MainActivity.
# Change presentation/target only; retain internal class names for native ABI.
service_path = java_root / "com/winlator/services/ForegroundService.java"
service_code = service_path.read_text(encoding="utf-8")
old_target = "Class<?> targetActivity = containerActive ? XServerDisplayActivity.class : MainActivity.class;"
assert service_code.count(old_target) == 1, "Upstream notification destination changed"
service_code = service_code.replace(old_target,
    "Class<?> targetActivity = containerActive ? XServerDisplayActivity.class : com.winlator.TouhouEntryActivity.class;")
assert service_code.count('"Winlator",') == 1, "Upstream notification title changed"
service_code = service_code.replace('"Winlator",', '"Charoite Portal",')
assert service_code.count('"Winlator is running in the background"') == 1
service_code = service_code.replace('"Winlator is running in the background"',
    '"Charoite Portal is running in the background"')
service_code = service_code.replace('"Winlator:ForegroundService"',
    '"CharoitePortal:ForegroundService"')
# A fresh channel prevents carrying the previous name as a legacy channel.
service_code = service_code.replace('"winlator.FGS"', '"charoiteportal.FGS"')
service_path.write_text(service_code, encoding="utf-8")

# The legacy third-party About dialog isn't on the Portal path; if an internal
# runtime menu opens it, show Charoite identity, not upstream product website.
# Source attributions and upstream LGPL license must stay in assets/licenses.
about_path = java_root / "com/winlator/contentdialog/AboutDialog.java"
about_code = about_path.read_text(encoding="utf-8")
webpage_old = 'tvWebpage.setText(Html.fromHtml("<a href=\\"https://www.winlator.org\\">winlator.org</a>", Html.FROM_HTML_MODE_LEGACY));'
assert about_code.count(webpage_old) == 1, "Upstream About website changed"
about_code = about_code.replace(webpage_old,
    'tvWebpage.setText("Charoite Games · Charoite Portal");')
about_path.write_text(about_code, encoding="utf-8")


# Report Box64/loader existence and mode before attempting Android execve.
guest = java_root / "com/winlator/xenvironment/components/GuestProgramLauncherComponent.java"
guest_code = guest.read_text(encoding="utf-8")

# Start the scoped Japanese font monitor early for setup.exe in the same
# Wine session. It observes the original UTF-16 path and applies a compatible
# font in the installer's GUI thread once that control exists. Never changes
# the installer command line or its original installation destination.
guest_code = guest_code.replace(
    "    private static int pid = -1;",
    "    private static int pid = -1;\n    private static volatile int probePid = -1;",
)
stop_old = """                Process.killProcess(pid);
                pid = -1;"""
assert guest_code.count(stop_old) == 1, "Guest stop() method changed"
guest_code = guest_code.replace(stop_old, stop_old + """
                if (probePid != -1) {
                    Process.killProcess(probePid);
                    probePid = -1;
                }""")
return_old = """        return ProcessHelper.exec(command, envVars, rootDir, (status) -> {"""
assert guest_code.count(return_old) == 1, "Box64 Windows guest runner changed"
return_new = """        final int mainPid = ProcessHelper.exec(command, envVars, rootDir, (status) -> {"""
guest_code = guest_code.replace(return_old, return_new)
return_end = """            if (terminationCallback != null) terminationCallback.call(status);
        });"""
assert guest_code.count(return_end) == 1, "Box64 Windows callback ending changed"
guest_code = guest_code.replace(return_end, return_end + """
        if (guestExecutable != null &&
                com.charoitegames.core.CharoiteCore.isJapaneseInstallerCandidate(guestExecutable) &&
                com.charoitegames.core.CharoiteCore.useTouhouInstallerFontProbe(environment.getContext()) &&
                mainPid > 0) {
            final EnvVars probeEnv = new EnvVars();
            probeEnv.putAll(envVars);
            new Thread(() -> {
                try {
                    // Start near Wine launch; monitor waits for the original
                    // Japanese destination control to be created.
                    Thread.sleep(100);
                    if (pid != mainPid) return;
                    String commandProbe = rootDir + "/usr/local/bin/box64 wine C:\\\\touhou_probe.exe";
                    probePid = ProcessHelper.exec(commandProbe, probeEnv, rootDir,
                            (status) -> probePid = -1);
                    com.charoitegames.core.CharoiteDiagnostics.recordLine(
                            "Japanese installer font monitor started (pid=" + probePid + ").");
                } catch (InterruptedException ignored) {
                    Thread.currentThread().interrupt();
                } catch (Exception error) {
                    com.charoitegames.core.CharoiteDiagnostics.recordLine(
                            "Japanese installer probe could not start: " + error);
                }
            }, "touhou-wine-japanese-probe").start();
        }
        return mainPid;""")

exec_marker = '        String command = rootDir+"/usr/local/bin/box64 "+guestExecutable;'
assert guest_code.count(exec_marker) == 1, "Box64 launcher entry changed"
guest_code = guest_code.replace(exec_marker, """        File box64File = new File(rootDir, "usr/local/bin/box64");
        File glibcLoader = new File(rootDir, "lib/ld-linux-aarch64.so.1");
        if (box64File.isFile() && !box64File.canExecute()) {
            FileUtils.chmod(box64File, 0755);
        }
        com.charoitegames.core.CharoiteDiagnostics.recordLine("Box64 native path: exists=" +
            box64File.isFile() + ", execute=" + box64File.canExecute() +
            "; glibc loader exists=" + glibcLoader.isFile() +
            ", execute=" + glibcLoader.canExecute() +
            "; Android appId=" + environment.getContext().getPackageName());
        if (!box64File.isFile() || !box64File.canExecute() || !glibcLoader.isFile()) {
            com.charoitegames.core.CharoiteDiagnostics.recordLine("Wine launch blocked before exec: missing or non-executable Box64/loader");
            return -1;
        }

""" + exec_marker)
guest.write_text(guest_code, encoding="utf-8")


log_file = java_root / "com/winlator/core/ProcessHelper.java"
process_code = log_file.read_text(encoding="utf-8")
old_catch = "        catch (Exception e) {}\n        return pid;"
assert process_code.count(old_catch) == 1, "Process failure marker changed"
process_code = process_code.replace(old_catch,
    "        catch (Exception e) { com.charoitegames.core.CharoiteDiagnostics.recordLine(\"Native Windows process start failed: \" + e); }\n        return pid;")
log_file.write_text(process_code, encoding="utf-8")



# Japanese Shift-JIS locale is set for the guest process, not Android itself.
locale_java = java_root / "com/winlator/core/LocaleHelper.java"
locale_code = locale_java.read_text(encoding="utf-8")
locale_marker = '        envVars.put("LC_ALL", "en_US.UTF-8");'
assert locale_code.count(locale_marker) == 1, "Winlator language fallback changed"
# The default remains English for General Gaming. Touhou opts into Japanese
# in its own Wine guest, without modifying Android device locale.
# Wine guest scoped locale is chosen below from the current environment.
locale_java.write_text(locale_code, encoding="utf-8")

launcher = java_root / "com/winlator/xenvironment/components/GuestProgramLauncherComponent.java"
launch_code = launcher.read_text(encoding="utf-8")
launch_marker = '        if (this.envVars != null) envVars.putAll(this.envVars);'
assert launch_code.count(launch_marker) == 1, "Guest process locale hook changed"
launch_code = launch_code.replace(launch_marker, launch_marker + """
        // Override English Android UI locale and custom container settings only
        // for the Wine guest. Most Japanese Touhou setup programs use CP932.
        boolean useJapanese = com.charoitegames.core.CharoiteCore.japaneseCompatibilityEnabled(
                environment.getContext());
        if (useJapanese) {
            envVars.put("LANG", "ja_JP.UTF-8");
            envVars.put("LC_ALL", "ja_JP.UTF-8");
            envVars.put("LC_CTYPE", "ja_JP.UTF-8");
        }
""")
launcher.write_text(launch_code, encoding="utf-8")

display_code = display.read_text(encoding="utf-8")

fonts_marker = '        if (containerDataChanged) container.saveData();'
assert display_code.count(fonts_marker) == 1, "Wine registry setup hook changed"
display_code = display_code.replace(fonts_marker, fonts_marker + """
        try {
            if (com.charoitegames.core.CharoiteCore.japaneseCompatibilityEnabled(this))
                com.charoitegames.core.CharoiteJapaneseSupport.ensure(this, rootFS, container);
        } catch (Exception error) {
            com.charoitegames.core.CharoiteDiagnostics.recordLine("Japanese locale/font initialization failed: " + error);
        }
""")
display.write_text(display_code, encoding="utf-8")

# Both the upstream license and original attribution travel with the APK.
license_dir = root / "app/src/main/assets/licenses"
license_dir.mkdir(parents=True, exist_ok=True)
(license_dir / "Winlator-LGPL-2.1.txt").write_bytes((root / "LICENSE").read_bytes())
(license_dir / "Touhou-Pocket-NOTICE.md").write_bytes((overlay.parent / "NOTICE.md").read_bytes())
print("Applied Charoite Portal + Charoite Core overlay and preserved license notices")
