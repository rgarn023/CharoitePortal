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
    "implementation 'androidx.appcompat:appcompat:1.4.0'\\n    implementation 'androidx.documentfile:documentfile:1.0.1'")
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
    a + "theme": "@android:style/Theme.Material.NoActionBar"
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

# Both the upstream license and original attribution travel with the APK.
license_dir = root / "app/src/main/assets/licenses"
license_dir.mkdir(parents=True, exist_ok=True)
(license_dir / "Winlator-LGPL-2.1.txt").write_bytes((root / "LICENSE").read_bytes())
(license_dir / "Touhou-Pocket-NOTICE.md").write_bytes((overlay.parent / "NOTICE.md").read_bytes())
print("Applied Touhou runtime preview overlay and preserved license notices")
