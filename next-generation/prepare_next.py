#!/usr/bin/env python3
"""Build a separate Charoite Core Next APK from the pinned, stable overlay.

This runs ONLY inside a fresh CI checkout after overlay.py. The original
Charoite Portal package, sources, keystore and on-device data are untouched.
"""
from pathlib import Path
from generate_crystal_startup import generate as generate_crystal_chime
import re
import shutil
import sys
import xml.etree.ElementTree as ET

if len(sys.argv) != 2:
    raise SystemExit("Usage: prepare_next.py PATH_TO_PINNED_UPSTREAM")

root = Path(sys.argv[1]).resolve()
source_dir = Path(__file__).resolve().parent
gradle = root / "app/build.gradle"
app = root / "app/src/main"
assert app.is_dir()
text = gradle.read_text(encoding="utf-8")
assert text.count("applicationId 'com.charoite'") == 1
text = text.replace("applicationId 'com.charoite'",
                    "applicationId 'com.charoitx'")
assert text.count("/.android/debug.keystore") == 1, "Original signing identity path changed"
text = text.replace("/.android/debug.keystore", "/.android/charoite-next.keystore")
assert text.count('versionName "11.2"') == 1
assert text.count("versionCode 33") == 1
text = text.replace('versionName "11.2"', 'versionName "11.2-next.0.5"')
text = text.replace("versionCode 33", "versionCode 36")
gradle.write_text(text, encoding="utf-8")

# Keep the Java namespaces com.winlator and com.charoitegames.core because
# native JNI and internal compile references depend on them. Only the Android
# UID, FileProvider and absolute filesystem paths change.
manifest_path = app / "AndroidManifest.xml"
ET.register_namespace("android", "http://schemas.android.com/apk/res/android")
ns = "{http://schemas.android.com/apk/res/android}"
tree = ET.parse(manifest_path)
for node in tree.getroot().iter("provider"):
    if node.get(ns + "authorities") == "com.charoite.FileProvider":
        node.set(ns + "authorities", "com.charoitx.FileProvider")
# Route cold-start HOME/LAUNCHER through a five-second Charoite Core screen.
# Existing direct/internal game launch activities and intent contracts are retained.
application = tree.getroot().find("application")
assert application is not None
launcher = [activity for activity in application.findall("activity")
            if activity.get(ns + "name") == "com.winlator.TouhouEntryActivity"]
assert len(launcher) == 1
entry = launcher[0]
launcher_intents = [node for node in entry.findall("intent-filter")
                    if any(child.get(ns + "name") == "android.intent.action.MAIN"
                           for child in node.findall("action"))]
assert len(launcher_intents) == 1, "Expected exactly one original launcher intent"
filters = launcher_intents[0]
assert any(cat.get(ns + "name") == "android.intent.category.LAUNCHER"
           for cat in filters.findall("category"))
entry.remove(filters)
boot = ET.Element("activity", {
    ns + "name": "com.charoitegames.core.CharoiteNextBootActivity",
    ns + "exported": "true",
    ns + "screenOrientation": "fullSensor",
    ns + "configChanges": "keyboard|keyboardHidden|orientation|screenSize|screenLayout|smallestScreenSize|density|navigation|uiMode",
    ns + "theme": "@style/AppThemeDark",
})
boot.append(filters)
application.insert(0, boot)
tree.write(manifest_path, encoding="utf-8", xml_declaration=True)

for p in (app / "res").glob("values*/strings.xml"):
    text = p.read_text(encoding="utf-8")
    text, replacements = re.subn(
        r'(<string name="app_name">)Charoite Portal(</string>)',
        r'\g<1>Charoite Next\2', text, count=1)
    # Some locales have their own app_name or inherit defaults; all must
    # use Charoite Next if the overlay generated the English name.
    if p.parent.name == "values" and replacements != 1:
        raise RuntimeError("Required default app name missing")
    p.write_text(text, encoding="utf-8")

native_changed = 0
for directory, suffixes in (
        (app / "java", (".java",)),
        (app / "cpp", (".c", ".cc", ".cpp", ".h", ".hpp"))):
    for path in directory.rglob("*"):
        if not path.is_file() or path.suffix not in suffixes:
            continue
        old = path.read_bytes()
        new = old.replace(b"/data/data/com.charoite/",
                          b"/data/data/com.charoitx/")
        new = new.replace(b'"com.charoite.FileProvider"',
                          b'"com.charoitx.FileProvider"')
        if new != old:
            path.write_bytes(new)
            native_changed += 1
assert native_changed > 0, "No Java/native private paths rebased to Next package"

# The experimental engine inventory is a separate, additive source module.
# It does NOT silently replace the existing Wine/Box64 engine.
next_java = app / "java/com/charoitegames/core/CharoiteNextRuntime.java"
assert not next_java.exists()
shutil.copy2(source_dir / "CharoiteNextRuntime.java", next_java)
next_diagnostics = app / "java/com/charoitegames/core/CharoiteNextDiagnostics.java"
assert not next_diagnostics.exists()
shutil.copy2(source_dir / "CharoiteNextDiagnostics.java", next_diagnostics)
native_probe_java = app / "java/com/charoitegames/core/CharoiteWineNativeProbe.java"
assert not native_probe_java.exists()
shutil.copy2(source_dir / "CharoiteWineNativeProbe.java", native_probe_java)
boot_java = app / "java/com/charoitegames/core/CharoiteNextBootActivity.java"
assert not boot_java.exists()
shutil.copy2(source_dir / "CharoiteNextBootActivity.java", boot_java)

# Generate the original crystal-chime sound as an Android raw resource. The
# sound is played only after the actual Portal home view is displayed.
chime = app / "res/raw/charoite_crystal_startup.wav"
assert not chime.exists()
assert generate_crystal_chime(chime) == round(44100 * 1.85)

source = app / "java/com/winlator/TouhouEntryActivity.java"
ui = source.read_text(encoding="utf-8")
anchor = "        systemScreen.addView(runtimeCard);"
assert ui.count(anchor) == 1
ui = ui.replace(anchor, anchor + """
        spacerIn(systemScreen, 12);
        LinearLayout nextCoreCard = card();
        nextCoreCard.addView(label("CHAROITE CORE NEXT — ENGINE STATUS", 17, FOREGROUND, true));
        nextCoreCard.addView(label(
                com.charoitegames.core.CharoiteNextRuntime.report(this),
                12, SECONDARY, false));
        nextCoreCard.addView(label(
                "The Proton ARM64EC/FEX and Wine Staging runners are not ready. " +
                "They cannot be selected or used until verified native assets, " +
                "isolated prefixes and device smoke tests exist. No game-specific " +
                "anti-cheat bypasses are provided.", 12, SECONDARY, false));
        systemScreen.addView(nextCoreCard);
        android.widget.Button nextDiagnostics = new android.widget.Button(this);
        nextDiagnostics.setText("Run Core Next device diagnostics");
        nextDiagnostics.setAllCaps(false);
        nextDiagnostics.setOnClickListener(v -> {
            final String diagnosticReport =
                com.charoitegames.core.CharoiteNextDiagnostics.deviceReport(this);
            new android.app.AlertDialog.Builder(this)
                .setTitle("Charoite Core Next — Device Diagnostics")
                .setMessage(diagnosticReport)
                .setPositiveButton("Copy report", (dialog, which) -> {
                    android.content.ClipboardManager clipboard =
                        (android.content.ClipboardManager)
                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                    if (clipboard != null)
                        clipboard.setPrimaryClip(android.content.ClipData.newPlainText(
                            "Charoite Next Device Diagnostics", diagnosticReport));
                })
                .setNegativeButton("Close", null)
                .show();
        });
        nextCoreCard.addView(nextDiagnostics);
        android.widget.Button nativeWineProbe = new android.widget.Button(this);
        nativeWineProbe.setText("Test source-built Wine --version");
        nativeWineProbe.setAllCaps(false);
        nativeWineProbe.setOnClickListener(v -> {
            nativeWineProbe.setEnabled(false);
            new Thread(() -> {
                final String report = com.charoitegames.core.CharoiteWineNativeProbe.run(this);
                runOnUiThread(() -> {
                    nativeWineProbe.setEnabled(true);
                    new android.app.AlertDialog.Builder(this)
                        .setTitle("Charoite Next — Native Wine Startup Test")
                        .setMessage(report)
                        .setPositiveButton("Copy report", (dialog, which) -> {
                            android.content.ClipboardManager cb =
                                (android.content.ClipboardManager)
                                getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                            if (cb != null)
                                cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                    "Charoite Next Native Wine Startup", report));
                        })
                        .setNegativeButton("Close", null)
                        .show();
                });
            }, "CharoiteWineNativeProbe").start();
        });
        nextCoreCard.addView(nativeWineProbe);
""")
# Play once only after main Portal content has been built, never during boot.
home_render = "        render();\n        refreshReadyState();\n        initializeEngineOnFirstLaunch();"
assert ui.count(home_render) >= 1, "Main-screen bootstrap contract changed"
# This sequence also runs on environment switches; inject into onCreate only.
ui = ui.replace(home_render,
                "        render();\n" +
                "        com.charoitegames.core.CharoiteNextBootActivity" +
                ".playArrivalChimeIfRequested(this);\n" +
                "        refreshReadyState();\n" +
                "        initializeEngineOnFirstLaunch();", 1)
ui = ui.replace('"Charoite Portal"', '"Charoite Next"')
source.write_text(ui, encoding="utf-8")

# Reference-only provenance: no binary is downloaded or installed by this
# initial APK. Future integration must verify every component and its license.
reference = source_dir / "engine-reference.json"
assert reference.is_file()
destination = app / "assets/charoite-next"
destination.mkdir(parents=True, exist_ok=True)
shutil.copy2(reference, destination / reference.name)

print("Charoite Next identity, engine inventory and read-only device diagnostics staged.")
print("Rebased Java/C++ absolute paths:", native_changed)
