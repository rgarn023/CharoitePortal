#!/usr/bin/env python3
"""Build a separate Charoite Core Next APK from the pinned, stable overlay.

This runs ONLY inside a fresh CI checkout after overlay.py. The original
Charoite Portal package, sources, keystore and on-device data are untouched.
"""
from pathlib import Path
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
text = text.replace('versionName "11.2"',
                    'versionName "11.2-next.0.1"')
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
""")
ui = ui.replace('"Charoite Portal"', '"Charoite Next"')
source.write_text(ui, encoding="utf-8")

# Reference-only provenance: no binary is downloaded or installed by this
# initial APK. Future integration must verify every component and its license.
reference = source_dir / "engine-reference.json"
assert reference.is_file()
destination = app / "assets/charoite-next"
destination.mkdir(parents=True, exist_ok=True)
shutil.copy2(reference, destination / reference.name)

print("Charoite Next identity and engine inventory staged (no Proton binaries installed).")
print("Rebased Java/C++ absolute paths:", native_changed)
