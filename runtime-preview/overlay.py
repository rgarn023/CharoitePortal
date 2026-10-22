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
src = src.replace("applicationId 'com.winlator'", "applicationId 'games.charoite.touhoupocket.runtime'")
assert "implementation 'androidx.appcompat:appcompat:1.4.0'" in src, "Upstream dependencies changed"
src = src.replace("implementation 'androidx.appcompat:appcompat:1.4.0'",
    "implementation 'androidx.appcompat:appcompat:1.4.0'\n    implementation 'androidx.documentfile:documentfile:1.0.1'")
gradle.write_text(src, encoding="utf-8")

strings = root / "app/src/main/res/values/strings.xml"
src = strings.read_text(encoding="utf-8")
assert '<string name="app_name">Winlator</string>' in src, "Upstream app name changed"
strings.write_text(src.replace('<string name="app_name">Winlator</string>',
    '<string name="app_name">Touhou Pocket Launcher</string>'), encoding="utf-8")

# The provider authority must not collide with a separately installed stock Winlator.
manifest_path = root / "app/src/main/AndroidManifest.xml"
ET.register_namespace("android", "http://schemas.android.com/apk/res/android")
a = "{http://schemas.android.com/apk/res/android}"
manifest = ET.parse(manifest_path)
app = manifest.getroot().find("application")
assert app is not None
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
        provider.set(a + "authorities", "games.charoite.touhoupocket.runtime.FileProvider")
entry = ET.Element("activity", {
    a + "name": "com.winlator.TouhouEntryActivity",
    a + "exported": "true",
    a + "screenOrientation": "sensor",
    a + "theme": "@style/AppThemeDark"
})
intent = ET.SubElement(entry, "intent-filter")
ET.SubElement(intent, "action", {a + "name": "android.intent.action.MAIN"})
ET.SubElement(intent, "category", {a + "name": "android.intent.category.LAUNCHER"})
app.insert(0, entry)
manifest.write(manifest_path, encoding="utf-8", xml_declaration=True)

# Account for FileProvider authority referenced in Java code (none may be present).
java_root = root / "app/src/main/java"
for java in java_root.rglob("*.java"):
    text = java.read_text(encoding="utf-8")
    if '"com.winlator.FileProvider"' in text:
        java.write_text(text.replace('"com.winlator.FileProvider"',
            '"games.charoite.touhoupocket.runtime.FileProvider"'), encoding="utf-8")

target = java_root / "com/winlator/TouhouEntryActivity.java"
assert not target.exists(), "Upstream has a colliding Touhou entry activity"
overlay = Path(__file__).resolve().parent / "TouhouEntryActivity.java"
target.write_bytes(overlay.read_bytes())

# Instrument the Wine renderer instead of leaving "Starting up" forever.
display = java_root / "com/winlator/XServerDisplayActivity.java"
code = display.read_text(encoding="utf-8")
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

# Both the upstream license and original attribution travel with the APK.
license_dir = root / "app/src/main/assets/licenses"
license_dir.mkdir(parents=True, exist_ok=True)
(license_dir / "Winlator-LGPL-2.1.txt").write_bytes((root / "LICENSE").read_bytes())
(license_dir / "Touhou-Pocket-NOTICE.md").write_bytes((overlay.parent / "NOTICE.md").read_bytes())
print("Applied Touhou runtime preview overlay and preserved license notices")
