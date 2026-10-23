#!/usr/bin/env python3
"""Reproducible, minimal Touhou runtime preview overlay on a pinned Winlator source checkout."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

if len(sys.argv) != 2:
    raise SystemExit("Usage: overlay.py PATH_TO_WINLATOR_APP")
root = Path(sys.argv[1]).resolve()
assert (root / "app/src/main/AndroidManifest.xml").is_file(), "Not a Winlator Android source tree"

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
                  '<string name="app_name">Touhou Launcher</string>')
# Remove upstream branding from visible startup and background notifications.
# This does NOT change the runtime's original Winlator-derived architecture.
for original, branded in (
    ('<string name="starting_up">Starting up...</string>',
     '<string name="starting_up">Launching Touhou game...</string>'),
    ('<string name="fgs_notification_content_else">Winlator is running in the background</string>',
     '<string name="fgs_notification_content_else">Touhou Launcher is running</string>'),
    ('<string name="fgs_notification_channel_desc">Keeps Winlator running in the background so a wine session is not interrupted by Android\\\'s background process management.</string>',
     '<string name="fgs_notification_channel_desc">Keeps Touhou Launcher active while a Windows game is running.</string>'),
):
    assert original in src, f"Upstream string changed: {original[:58]}"
    src = src.replace(original, branded)
strings.write_text(src, encoding="utf-8")

# Runtime assets use a same-length replacement Android package name to preserve\n# native ELF interpreter and library offsets. Do not change this ID without\n# rewriting runtime-preview/rewrite_prefix.py in tandem.\n# The provider authority must not collide with separately installed Winlator.
manifest_path = root / "app/src/main/AndroidManifest.xml"
ET.register_namespace("android", "http://schemas.android.com/apk/res/android")
a = "{http://schemas.android.com/apk/res/android}"
manifest = ET.parse(manifest_path)
app = manifest.getroot().find("application")
assert app is not None
# Dedicated Touhou OS shrine emblem (original vector) replaces stock launcher icon.
icon_destination = root / "app/src/main/res/drawable/touhou_pocket_icon.xml"
icon_destination.parent.mkdir(parents=True, exist_ok=True)
icon_destination.write_bytes((Path(__file__).resolve().parent / "touhou_pocket_icon.xml").read_bytes())
app.set(a + "icon", "@drawable/touhou_pocket_icon")
app.set(a + "roundIcon", "@drawable/touhou_pocket_icon")
# Explicit freeform/multi-window support for DeX on external displays.
app.set(a + "resizeableActivity", "true")
original_main = next((activity for activity in app.findall("activity")
    if activity.get(a + "name") == "com.winlator.MainActivity"), None)
assert original_main is not None, "Winlator launcher activity not found"
original_main.set(a + "exported", "false")
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
    a + "screenOrientation": "unspecified",
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
xserver_activity.set(a + "screenOrientation", "unspecified")
xserver_activity.set(a + "resizeableActivity", "true")
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


# The read-only Wine diagnostics executable is cross-compiled by Actions and
# bundled as an asset, never committed as a binary to the source repository.
probe_binary = overlay.parent / "touhou_probe.exe"
assert probe_binary.is_file(), "Compile touhou_probe.exe before applying overlay"
probe_asset = root / "app/src/main/assets/japanese/touhou_probe.exe"
probe_asset.parent.mkdir(parents=True, exist_ok=True)
probe_asset.write_bytes(probe_binary.read_bytes())
# Windows installers may be 32-bit while the Wine runtime is 64-bit. Both
# matching bitness thread-hook helpers must ship alongside the diagnostic.
for arch in ("32", "64"):
    for suffix in (".exe", ".dll"):
        stem = "touhou_font_helper" if suffix == ".exe" else "touhou_font_hook"
        original = overlay.parent / f"{stem}{arch}{suffix}"
        assert original.is_file(), f"Missing compiled scoped font asset: {original}"
        (probe_asset.parent / original.name).write_bytes(original.read_bytes())



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
            setRequestedOrientation(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE);
            AppUtils.hideSystemUI(this);
        }
        AppUtils.keepScreenOn(this);""")

# Pick a per-launch Wine virtual desktop size, never changing the
# persistent Wine container or files when moving between DeX and phone.
old_guest_screen = "            screenInfo = resolveScreenInfo(container.getScreenSize());"
assert code.count(old_guest_screen) == 1, "Upstream container screenInfo marker changed"
code = code.replace(old_guest_screen, old_guest_screen + """
            if (getIntent().hasExtra("touhou_display_size")) {
                String requested = getIntent().getStringExtra("touhou_display_size");
                if (requested != null && requested.matches("800x600|1280x720|1600x900|1920x1080"))
                    screenInfo = resolveScreenInfo(requested);
            }""")

# Winlator already handles Android key and mouse events. On DeX choose
# whether to capture the pointer, defaulting to a freely movable cursor.
old_mouse = '        capturePointerOnExternalMouse = preferences.getBoolean("capture_pointer_on_external_mouse", true);'
assert code.count(old_mouse) == 1, "Upstream mouse-capture marker changed"
code = code.replace(old_mouse,
    '        capturePointerOnExternalMouse = getIntent().getBooleanExtra("touhou_pointer_capture", ' +
    'preferences.getBoolean("capture_pointer_on_external_mouse", true));')
old_show = "        preloaderDialog.show(R.string.starting_up);"
assert code.count(old_show) == 1, "Startup dialog marker changed"
code = code.replace(old_show, """        final boolean[] touhouWindowOpened = {false};
        if (getIntent().hasExtra("exec_path")) {
            TouhouDiagnostics.begin(this, getIntent().getStringExtra("exec_path"));
            ProcessHelper.addDebugCallback(TouhouDiagnostics.CALLBACK);
            new android.os.Handler(android.os.Looper.getMainLooper()).postDelayed(() -> {
                if (!isFinishing() && !touhouWindowOpened[0]) {
                    TouhouDiagnostics.fail(this, "No Windows game window appeared after 45 seconds. Check Wine/Box64 and graphics compatibility.");
                    preloaderDialog.closeOnUiThread();
                    new androidx.appcompat.app.AlertDialog.Builder(this)
                        .setTitle("Touhou game did not start")
                        .setMessage("The Windows engine failed to display the game.\\n\\nReturn to Touhou Pocket and open Launch Diagnostics, or switch to Compatibility Graphics.")
                        .setCancelable(false)
                        .setPositiveButton("Return to Touhou Pocket", (d, which) -> exit())
                        .show();
                }
            }, 45000);
        }
""" + old_show)
old_cursor = "                    xServerView.getRenderer().setCursorVisible(true);"
assert code.count(old_cursor) == 1, "Window-open marker changed"
code = code.replace(old_cursor, """                    touhouWindowOpened[0] = true;
                    if (getIntent().hasExtra("exec_path")) TouhouDiagnostics.windowOpened(XServerDisplayActivity.this);
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
            ProcessHelper.removeDebugCallback(TouhouDiagnostics.CALLBACK);
            Intent home = new Intent(this, TouhouEntryActivity.class);
            home.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
            startActivity(home);
            finish();
        }
        else AppUtils.restartApplication(this);""")
old_callback = "        guestProgramLauncherComponent.setTerminationCallback((status) -> exit());"
assert code.count(old_callback) == 1, "Guest-process exit callback changed"
code = code.replace(old_callback, """        guestProgramLauncherComponent.setTerminationCallback((status) -> {
            if (getIntent().hasExtra("exec_path") && status != 0)
                TouhouDiagnostics.fail(this, "Wine/Box64 process exited with status " + status + ". See logs below.");
            runOnUiThread(this::exit);
        });""")
display.write_text(code, encoding="utf-8")

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
                guestExecutable.toLowerCase(java.util.Locale.ROOT).contains("setup.exe") &&
                mainPid > 0) {
            final EnvVars probeEnv = new EnvVars();
            probeEnv.putAll(envVars);
            new Thread(() -> {
                try {
                    // Start near Wine launch; monitor waits for the original
                    // Japanese destination control to be created.
                    Thread.sleep(750);
                    if (pid != mainPid) return;
                    String commandProbe = rootDir + "/usr/local/bin/box64 wine C:\\\\touhou_probe.exe";
                    probePid = ProcessHelper.exec(commandProbe, probeEnv, rootDir,
                            (status) -> probePid = -1);
                    com.winlator.TouhouDiagnostics.recordLine(
                            "Japanese installer font monitor started (pid=" + probePid + ").");
                } catch (InterruptedException ignored) {
                    Thread.currentThread().interrupt();
                } catch (Exception error) {
                    com.winlator.TouhouDiagnostics.recordLine(
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
        com.winlator.TouhouDiagnostics.recordLine("Box64 native path: exists=" +
            box64File.isFile() + ", execute=" + box64File.canExecute() +
            "; glibc loader exists=" + glibcLoader.isFile() +
            ", execute=" + glibcLoader.canExecute() +
            "; Android appId=" + environment.getContext().getPackageName());
        if (!box64File.isFile() || !box64File.canExecute() || !glibcLoader.isFile()) {
            com.winlator.TouhouDiagnostics.recordLine("Wine launch blocked before exec: missing or non-executable Box64/loader");
            return -1;
        }

""" + exec_marker)
guest.write_text(guest_code, encoding="utf-8")


log_file = java_root / "com/winlator/core/ProcessHelper.java"
process_code = log_file.read_text(encoding="utf-8")
old_catch = "        catch (Exception e) {}\n        return pid;"
assert process_code.count(old_catch) == 1, "Process failure marker changed"
process_code = process_code.replace(old_catch,
    "        catch (Exception e) { com.winlator.TouhouDiagnostics.recordLine(\"Native Windows process start failed: \" + e); }\n        return pid;")
log_file.write_text(process_code, encoding="utf-8")

diagnostics = java_root / "com/winlator/TouhouDiagnostics.java"
assert not diagnostics.exists(), "Conflicting upstream diagnostics class"
diagnostics.write_bytes((overlay.parent / "TouhouDiagnostics.java").read_bytes())


# Japanese Shift-JIS locale is set for the guest process, not Android itself.
locale_java = java_root / "com/winlator/core/LocaleHelper.java"
locale_code = locale_java.read_text(encoding="utf-8")
locale_marker = '        envVars.put("LC_ALL", "en_US.UTF-8");'
assert locale_code.count(locale_marker) == 1, "Winlator language fallback changed"
locale_code = locale_code.replace(locale_marker,
    '        envVars.put("LC_ALL", "ja_JP.UTF-8");')
locale_java.write_text(locale_code, encoding="utf-8")

launcher = java_root / "com/winlator/xenvironment/components/GuestProgramLauncherComponent.java"
launch_code = launcher.read_text(encoding="utf-8")
launch_marker = '        if (this.envVars != null) envVars.putAll(this.envVars);'
assert launch_code.count(launch_marker) == 1, "Guest process locale hook changed"
launch_code = launch_code.replace(launch_marker, launch_marker + """
        // Override English Android UI locale and custom container settings only
        // for the Wine guest. Most Japanese Touhou setup programs use CP932.
        envVars.put("LANG", "ja_JP.UTF-8");
        envVars.put("LC_ALL", "ja_JP.UTF-8");
        envVars.put("LC_CTYPE", "ja_JP.UTF-8");
""")
launcher.write_text(launch_code, encoding="utf-8")

japanese_file = java_root / "com/winlator/TouhouJapaneseSupport.java"
assert not japanese_file.exists(), "Upstream Japanese support class conflict"
japanese_file.write_bytes((overlay.parent / "TouhouJapaneseSupport.java").read_bytes())

display_code = display.read_text(encoding="utf-8")

fonts_marker = '        if (containerDataChanged) container.saveData();'
assert display_code.count(fonts_marker) == 1, "Wine registry setup hook changed"
display_code = display_code.replace(fonts_marker, fonts_marker + """
        try {
            TouhouJapaneseSupport.ensure(this, rootFS, container);
        } catch (Exception error) {
            TouhouDiagnostics.recordLine("Japanese locale/font initialization failed: " + error);
        }
""")
display.write_text(display_code, encoding="utf-8")

# Both the upstream license and original attribution travel with the APK.
license_dir = root / "app/src/main/assets/licenses"
license_dir.mkdir(parents=True, exist_ok=True)
(license_dir / "Winlator-LGPL-2.1.txt").write_bytes((root / "LICENSE").read_bytes())
(license_dir / "Touhou-Pocket-NOTICE.md").write_bytes((overlay.parent / "NOTICE.md").read_bytes())
print("Applied Touhou Launcher + Charoite Core overlay and preserved license notices")
