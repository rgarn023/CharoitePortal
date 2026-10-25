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
# Upgrades must not rotate keys unexpectedly or change com.touhoudr.
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
src = src.replace("applicationId 'com.winlator'", "applicationId 'com.touhoudr'")
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
        provider.set(a + "authorities", "com.touhoudr.FileProvider")
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
            '"com.touhoudr.FileProvider"'), encoding="utf-8")

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
               "CharoiteGameProfiles.java", "CharoiteGameSessions.java",
               "CharoiteDiagnostics.java", "CharoiteRenderingDiagnostics.java",
               "CharoiteGraphicsProfiles.java", "CharoiteWindowPolicy.java"):
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
                b"/data/data/com.winlator", b"/data/data/com.touhoudr"))
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
        AppUtils.keepScreenOn(this);""")

# Reuse the TPDP Charoite Core keyboard buttons, without loading a
# duplicate Winlator controls profile or changing Wine container settings.
tpdp_touch_source = overlay.parent / "charoite-core/CharoiteTpdpTouchControls.java"
tpdp_touch_target = java_root / "com/charoitegames/core/CharoiteTpdpTouchControls.java"
assert tpdp_touch_source.is_file() and not tpdp_touch_target.exists()
tpdp_touch_target.parent.mkdir(parents=True, exist_ok=True)
tpdp_touch_target.write_bytes(tpdp_touch_source.read_bytes())

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
        // TPDP's documented arrow + Z/X/C/S/A/D/Space bindings; keyboard
        // input is sent to Wine through the existing XServer keyboard.
        // Touch-only: DeX remains usable with real keyboard/mouse devices.
        if (getIntent().hasExtra("exec_path") &&
                com.charoitegames.core.CharoiteCore.isTpdpGameExecutable(
                    getIntent().getStringExtra("exec_path")) &&
                !getIntent().getBooleanExtra("touhou_desktop_window", false)) {
            com.charoitegames.core.CharoiteTpdpTouchControls.attach(
                    this,rootView,(keyCode,pressed) -> {
                        long tick=android.os.SystemClock.uptimeMillis();
                        int action=pressed ? android.view.KeyEvent.ACTION_DOWN :
                                android.view.KeyEvent.ACTION_UP;
                        xServer.keyboard.onKeyEvent(new android.view.KeyEvent(
                                tick,tick,action,keyCode,0));
                    });
        }
""")

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
                if (requested != null && requested.matches("800x600|1280x720|1600x900|1920x1080|600x800|720x1280|900x1600|1080x1920"))
                    screenInfo = resolveScreenInfo(requested);
            }""")

# Winlator already handles Android key and mouse events. On DeX choose
# whether to capture the pointer, defaulting to a freely movable cursor.
old_mouse = '        capturePointerOnExternalMouse = preferences.getBoolean("capture_pointer_on_external_mouse", true);'
assert code.count(old_mouse) == 1, "Upstream mouse-capture marker changed"
code = code.replace(old_mouse,
    '        capturePointerOnExternalMouse = getIntent().getBooleanExtra("touhou_pointer_capture", ' +
    'preferences.getBoolean("capture_pointer_on_external_mouse", true));')
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
                if (getIntent().hasExtra("exec_path") &&
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
""" + tpdp_debug_anchor)
display.write_text(code, encoding="utf-8")

# Keep the enlarged, aspect-preserving TPDP window in the upper display
# area, rather than the upstream default screen center. The fullscreen
# transform handles touch/pointer hit testing as well as display scaling.
gl_renderer = java_root / "com/winlator/renderer/GLRenderer.java"
gl_renderer_code = gl_renderer.read_text(encoding="utf-8")
tpdp_viewport_anchor = (
    "                    fullscreenTransformation.update(xServer.screenInfo, "
    "window.getWidth(), window.getHeight());"
)
assert gl_renderer_code.count(tpdp_viewport_anchor) == 1, "Upstream window scale hook changed"
gl_renderer_code = gl_renderer_code.replace(tpdp_viewport_anchor, tpdp_viewport_anchor + """
                    com.charoitegames.core.CharoiteWindowPolicy.placeScaledGame(
                            fullscreenTransformation, xServer.screenInfo,
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
