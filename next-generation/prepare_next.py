#!/usr/bin/env python3
"""Build a separate Charoite Core Next APK from the pinned, stable overlay.

This runs ONLY inside a fresh CI checkout after overlay.py. The original
Charoite Portal package, sources, keystore and on-device data are untouched.
"""
from pathlib import Path
from generate_crystal_startup import generate as generate_crystal_chime
from make_fullbleed_boot import generate as generate_fullbleed_boot
from make_portrait_boot import generate as generate_portrait_boot
import hashlib
import subprocess
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
text = text.replace('versionName "11.2"', 'versionName "11.2-next.0.33"')
text = text.replace("versionCode 33", "versionCode 64")
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
# Route cold-start HOME/LAUNCHER through a ten-second Charoite Core screen.
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
server_probe_java = app / "java/com/charoitegames/core/CharoiteWineServerProbe.java"
assert not server_probe_java.exists()
shutil.copy2(source_dir / "CharoiteWineServerProbe.java", server_probe_java)
boot_java = app / "java/com/charoitegames/core/CharoiteNextBootActivity.java"
assert not boot_java.exists()
shutil.copy2(source_dir / "CharoiteNextBootActivity.java", boot_java)

# Generate the longer version of the original crystal resonance as a
# 7-second PCM WAV. It plays ONLY while the crystal portal splash is visible,
# and fades to silence before the main Portal is revealed.
chime = app / "res/raw/charoite_crystal_startup.wav"
assert not chime.exists()
assert generate_crystal_chime(chime) == round(44100 * 7.0)

# The exact 1536x1536 image personally provided as the required reference.
# Do not generate, upsample, redesign, crop, or alter it. Reuse identical bytes
# in Charoite Next's launcher and boot resources; stable Portal is unaffected.
approved_art = source_dir / "assets/charoite_next_boot_reference.jpg"
approved_sha = "2f368b7731f8ff96db03842e0f36b62bc9d22c48fcdb77ed864846d6be44b748"
image_bytes = approved_art.read_bytes()
assert hashlib.sha256(image_bytes).hexdigest() == approved_sha, "User-approved boot image changed"
assert image_bytes[:3] == b"\xff\xd8\xff" and image_bytes[-2:] == b"\xff\xd9"
boot_art = app / "res/drawable-nodpi/charoite_next_boot_scene.jpg"
assert not boot_art.exists()
boot_art.write_bytes(image_bytes)
next_launcher_icon = app / "res/drawable-nodpi/charoite_portal_icon.jpg"
assert next_launcher_icon.exists()
next_launcher_icon.write_bytes(image_bytes)
# The launcher icon stays byte-for-byte identical to the supplied master.
# Only the *boot presentation* gets a transparent, no-black-corners copy
# and a blurred edge-to-edge violet background of the same artwork.
boot_unframed = app / "res/drawable-nodpi/charoite_next_boot_unframed.png"
boot_backdrop = app / "res/drawable-nodpi/charoite_next_boot_backdrop.jpg"
assert generate_fullbleed_boot(approved_art, boot_unframed, boot_backdrop) == (
    boot_unframed, boot_backdrop)
# This portrait artwork is an ACTUAL 960×1840 seamless scene, not a stretched
# icon or a floating square over its blurred copy. Generated deterministically
# from the approved master; no launcher/icon changes.
boot_portrait = app / "res/drawable-nodpi/charoite_next_boot_portrait.jpg"
assert generate_portrait_boot(approved_art, boot_portrait) == boot_portrait

# Use the ACTUAL black-purple spiral from the newly approved edited image,
# placed larger to match the user's red-spiral area inside the original C.
# The crystal itself glows, and inward-feeding wisps dissolve with the 7s audio.
# Original crystal art, native title and all runtime data stay intact.
# This is silent H.264 packaged as a local app resource, never downloaded
# while the phone starts and never placed into the stable Portal build.
# The Android TextureView falls back to the still boot if decoding fails.
# Ensure the EXACT extracted spiral from the user's newly approved edited image
# is present and has not been swapped for another generated illustration.
reference_vortex = source_dir / "assets/charoite_user_edited_portal_v33.webp"
assert reference_vortex.is_file(), "Missing edited-image vortex texture"
assert hashlib.sha256(reference_vortex.read_bytes()).hexdigest() == (
    "09691efddf9741c9df083efc9ef2c869afc0861dd8ecdedb191bce6c862d76fc"
), "Reference spiral artwork changed"
print("CHAROITE_NEXT_USER_EDITED_VORTEX_REFERENCE_EXACT_MATCH=PASS")
preview_script = source_dir.parent / "docs/previews/render_crystal_awakening.py"
movie_generated = source_dir.parent / "Charoite_C_Glow_Reference_Portal_7s.mp4"
storyboard_generated = source_dir.parent / "Charoite_C_Glow_Reference_Portal_7s_Storyboard.jpg"
assert preview_script.is_file() and not movie_generated.exists()
subprocess.run([sys.executable, str(preview_script)], check=True, cwd=source_dir.parent)
assert movie_generated.is_file() and movie_generated.stat().st_size > 100000
# Verify a full 7-second 24-fps portrait movie before embedding.
import cv2
video_capture = cv2.VideoCapture(str(movie_generated))
assert video_capture.isOpened(), "Reference-only portal MP4 cannot be decoded"
assert round(video_capture.get(cv2.CAP_PROP_FPS)) == 30
assert round(video_capture.get(cv2.CAP_PROP_FRAME_COUNT)) == 210
assert round(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)) == 480
assert round(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)) == 920
video_capture.release()
movie_raw = app / "res/raw/charoite_c_glow_reference_portal_7s.mp4"
assert not movie_raw.exists()
shutil.copyfile(movie_generated, movie_raw)
assert movie_raw.stat().st_size == movie_generated.stat().st_size
movie_generated.unlink()
if storyboard_generated.exists():
    storyboard_generated.unlink()
print("CHAROITE_NEXT_C_GLOW_REFERENCE_PORTAL_7_SECONDS=PASS")



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
        android.widget.Button serverVersionProbe = new android.widget.Button(this);
        serverVersionProbe.setText("Test source-built wineserver --version");
        serverVersionProbe.setAllCaps(false);
        serverVersionProbe.setOnClickListener(v -> {
            serverVersionProbe.setEnabled(false);
            new Thread(() -> {
                final String report = com.charoitegames.core.CharoiteWineServerProbe.run(this);
                runOnUiThread(() -> {
                    serverVersionProbe.setEnabled(true);
                    new android.app.AlertDialog.Builder(this)
                        .setTitle("Charoite Next — Wineserver Version Test")
                        .setMessage(report)
                        .setPositiveButton("Copy report", (dialog, which) -> {
                            android.content.ClipboardManager cb =
                                (android.content.ClipboardManager)
                                getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                            if (cb != null)
                                cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                    "Charoite Next Wineserver Native Probe", report));
                        })
                        .setNegativeButton("Close", null)
                        .show();
                });
            }, "CharoiteWineServerProbe").start();
        });
        nextCoreCard.addView(serverVersionProbe);
        android.widget.Button startupDiagnostics = new android.widget.Button(this);
        startupDiagnostics.setText("Startup / audio diagnostics");
        startupDiagnostics.setAllCaps(false);
        startupDiagnostics.setOnClickListener(v -> {
            final String report = com.charoitegames.core.CharoiteNextBootActivity
                    .startupReport(this);
            new android.app.AlertDialog.Builder(this)
                .setTitle("Charoite Next — Startup diagnostics")
                .setMessage(report)
                .setPositiveButton("Copy report", (dialog, which) -> {
                    android.content.ClipboardManager cb =
                        (android.content.ClipboardManager)
                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                    if (cb != null)
                        cb.setPrimaryClip(android.content.ClipData.newPlainText(
                            "Charoite Next Startup Diagnostics", report));
                })
                .setNegativeButton("Close", null)
                .show();
        });
        nextCoreCard.addView(startupDiagnostics);
""")
# Real onCreate registers the Portal and handles the one-time direct-root
# cold boot fallback for Samsung legacy tasks. No splash on normal resume.
create_anchor = "        super.onCreate(savedInstanceState);\n        CharoiteEnvironments.initialize(this);"
assert ui.count(create_anchor) == 1
ui = ui.replace(create_anchor, (
    "        super.onCreate(savedInstanceState);\n"
    "        com.charoitegames.core.CharoiteNextBootActivity"
    ".onPortalCreated(this, savedInstanceState);\n"
    "        CharoiteEnvironments.initialize(this);"), 1)

# The fallback is prepared in onCreate and mounted synchronously in
# onPostCreate, after the full Portal view is assembled but BEFORE first draw.
# Inserting this at onResume/postDelayed caused the visible Portal flash.
assert "void onPostCreate(" not in ui, "Unexpected upstream onPostCreate override"
post_create_anchor = "    @Override public void onDestroy() {\n"
assert ui.count(post_create_anchor) == 1
ui = ui.replace(post_create_anchor, (
    "    @Override protected void onPostCreate(android.os.Bundle savedInstanceState) {\n"
    "        super.onPostCreate(savedInstanceState);\n"
    "        com.charoitegames.core.CharoiteNextBootActivity"
    ".onPortalPostCreated(this);\n"
    "    }\n\n" + post_create_anchor), 1)

# onResume consumes the one-time cold-start chime only, never shows a splash.
resume_anchor = "        super.onResume();\n        if (CharoiteGameSessions.hasPendingInstallerScan(this)) {"
assert ui.count(resume_anchor) == 1
ui = ui.replace(resume_anchor, (
    "        super.onResume();\n"
    "        com.charoitegames.core.CharoiteNextBootActivity"
    ".onPortalResumed(this);\n"
    "        if (CharoiteGameSessions.hasPendingInstallerScan(this)) {"), 1)

# Keep first-start audio reliability after Portal window is visible.
focus_anchor = "    @Override public void onDestroy() {\n"
assert ui.count(focus_anchor) == 1
ui = ui.replace(focus_anchor, (
    "    @Override public void onWindowFocusChanged(boolean hasFocus) {\n"
    "        super.onWindowFocusChanged(hasFocus);\n"
    "        com.charoitegames.core.CharoiteNextBootActivity"
    ".onPortalWindowFocusChanged(this, hasFocus);\n"
    "    }\n\n" + focus_anchor), 1)

# A truly finished Portal is a new session; Home/Recents do not destroy it.
destroy_anchor = "    @Override public void onDestroy() {\n"
assert ui.count(destroy_anchor) == 1
ui = ui.replace(destroy_anchor, (
    destroy_anchor +
    "        com.charoitegames.core.CharoiteNextBootActivity"
    ".notePortalDestroyed(this);\n"), 1)

# Deliberately do not inject onPause/onRestart/onNewIntent/onUserLeaveHint:
# those are not launch events, and were the cause of unwanted replay.
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
