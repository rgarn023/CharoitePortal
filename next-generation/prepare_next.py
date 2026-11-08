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
text = text.replace('versionName "11.2"', 'versionName "11.2-next.0.111"')
text = text.replace("versionCode 33", "versionCode 142")
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
# Opt-in GitHub issue uploader: no automatic execution without consent.
# The Android JobService only reads bounded preserved v9 logs; never runs Wine.
if not any(p.get(ns + "name") == "android.permission.INTERNET"
           for p in tree.getroot().findall("uses-permission")):
    tree.getroot().insert(0, ET.Element("uses-permission",
                                      {ns + "name": "android.permission.INTERNET"}))
assert not any(s.get(ns + "name") == "com.charoitegames.core.CharoiteNextAutoReports$UploadJob"
               for s in application.findall("service"))
ET.SubElement(application, "service", {
    ns + "name": "com.charoitegames.core.CharoiteNextAutoReports$UploadJob",
    ns + "permission": "android.permission.BIND_JOB_SERVICE",
    ns + "exported": "false",
})
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
# Separate built-in Core Manager: read-only APK inventory and local display mode.
# No native module writes, Wine processes, user prefix access or runner switching.
core_manager_java = app / "java/com/charoitegames/core/CharoiteCoreManager.java"
assert not core_manager_java.exists()
shutil.copy2(source_dir / "CharoiteCoreManager.java", core_manager_java)
next_diagnostics = app / "java/com/charoitegames/core/CharoiteNextDiagnostics.java"
assert not next_diagnostics.exists()
shutil.copy2(source_dir / "CharoiteNextDiagnostics.java", next_diagnostics)
report_java = app / "java/com/charoitegames/core/CharoiteNextAutoReports.java"
assert not report_java.exists()
shutil.copy2(source_dir / "CharoiteNextAutoReports.java", report_java)
native_probe_java = app / "java/com/charoitegames/core/CharoiteWineNativeProbe.java"
assert not native_probe_java.exists()
shutil.copy2(source_dir / "CharoiteWineNativeProbe.java", native_probe_java)
server_probe_java = app / "java/com/charoitegames/core/CharoiteWineServerProbe.java"
assert not server_probe_java.exists()
shutil.copy2(source_dir / "CharoiteWineServerProbe.java", server_probe_java)
preflight_java = app / "java/com/charoitegames/core/CharoiteWineBootstrapPreflight.java"
assert not preflight_java.exists()
shutil.copy2(source_dir / "CharoiteWineBootstrapPreflight.java", preflight_java)
payload_java = app / "java/com/charoitegames/core/CharoiteWinePayloadAudit.java"
assert not payload_java.exists()
shutil.copy2(source_dir / "CharoiteWinePayloadAudit.java", payload_java)
stage_java = app / "java/com/charoitegames/core/CharoiteWineIsolatedStage.java"
assert not stage_java.exists()
shutil.copy2(source_dir / "CharoiteWineIsolatedStage.java", stage_java)
gate_java = app / "java/com/charoitegames/core/CharoiteWineBootstrapGate.java"
assert not gate_java.exists()
shutil.copy2(source_dir / "CharoiteWineBootstrapGate.java", gate_java)
wine26_java = app / "java/com/charoitegames/core/CharoiteWine26Stage.java"
assert not wine26_java.exists()
shutil.copy2(source_dir / "CharoiteWine26Stage.java", wine26_java)
wine26_native_java = app / "java/com/charoitegames/core/CharoiteWine26NativeGate.java"
assert not wine26_native_java.exists()
shutil.copy2(source_dir / "CharoiteWine26NativeGate.java", wine26_native_java)
wine26_prefix_java = app / "java/com/charoitegames/core/CharoiteWine26PrefixProbe.java"
assert not wine26_prefix_java.exists()
shutil.copy2(source_dir / "CharoiteWine26PrefixProbe.java", wine26_prefix_java)
# Fully isolated patch-0800 native cohort: never replace the Wine26 cohort.
for filename in ("CharoiteWine27Stage.java", "CharoiteWine27NativeGate.java",
                 "CharoiteWine27PrefixProbe.java",
                 "CharoiteWine27V3Forensics.java",
                 "CharoiteWine27PEAudit.java",
                 "CharoiteWine27V4Trace.java",
                 "CharoiteWine28Stage.java",
                 "CharoiteWine28NativeGate.java",
                 "CharoiteWine28V5Trace.java",
                 "CharoiteWine28V5Forensics.java",
                 "CharoiteWine28V6ServerProbe.java",
                 "CharoiteWine28V7PeHelpProbe.java",
                 "CharoiteWine28V8LayoutProbe.java",
                 "CharoiteWine28V9BuiltinBootstrapProbe.java",
                 "CharoiteWine28V9Forensics.java",
                 "CharoiteWine29Native07Audit.java",
                 "CharoiteWine29Native07VersionGate.java",
                 "CharoiteWine29Native07Stage.java",
                 "CharoiteWine29Native07PePreflight.java",
                 "CharoiteWine29Sealed012Stage.java",
                 "CharoiteWine29Sealed012PePreflight.java",
                 "CharoiteWine29V1PeHelpProbe.java",
                 "CharoiteWine29V1Forensics.java",
                 "CharoiteWine29V2BootstrapProbe.java",
                 "CharoiteWine29V3LayoutProbe.java",
                 "CharoiteWine29V3AutoInitForensics.java",
                 "CharoiteWine29V4DirectInitProbe.java",
                 "CharoiteWine29V5DriveCProbe.java",
                 "CharoiteWine29V6ChildLoaderProbe.java",
                 "CharoiteWine29V6ReadOnlyForensics.java",
                 "CharoiteWine29V7ServicesProbe.java",
                 "CharoiteWine29V7ReadOnlyForensics.java",
                 "CharoiteWine29V8UserenvProbe.java",
                 "CharoiteWine29V8ReadOnlyForensics.java",
                 "CharoiteWine29V9ScmProbe.java",
                 "CharoiteWine29V9ReadOnlyForensics.java",
                 "CharoiteWine29V10EntryProbe.java",
                 "CharoiteWine29V10ReadOnlyForensics.java",
                 "CharoiteWine29V11EntryProbe.java",
                 "CharoiteWine29V11ReadOnlyForensics.java",
                 "CharoiteWine29V12ScEntryProbe.java",
                 "CharoiteWine29V12ReadOnlyForensics.java",
                 "CharoiteWine29V13ScNoexecProbe.java",
                 "CharoiteWine29V13ReadOnlyForensics.java",
                 "CharoiteWine29V14ScWindowsPathProbe.java",
                  "CharoiteWine29V14ReadOnlyForensics.java",
                  "CharoiteWine29V15ScWindowsNoexecProbe.java",
                  "CharoiteWine29V15ReadOnlyForensics.java",
                  "CharoiteWine29V16ExecBoundaryProbe.java",
                  "CharoiteWine29V16ReadOnlyForensics.java",
                  "CharoiteWine29V17ControlCompareProbe.java",
                  "CharoiteWine29V17ReadOnlyForensics.java",
                  "CharoiteWine29V18ServerIdleProbe.java",
                   "CharoiteWine29V18ReadOnlyForensics.java"):
    target = app / "java/com/charoitegames/core" / filename
    assert not target.exists(), "Separate v3 source file already exists"
    shutil.copy2(source_dir / filename, target)

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
# The crystal C now glows visibly; continuous luminous ribbons carry
# energy from inner crystal facets inward, fading with seven-second audio.
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
movie_generated = source_dir.parent / "Charoite_C_Energy_Reference_Portal_7s.mp4"
storyboard_generated = source_dir.parent / "Charoite_C_Energy_Reference_Portal_7s_Storyboard.jpg"
assert preview_script.is_file() and not movie_generated.exists()
subprocess.run([sys.executable, str(preview_script)], check=True, cwd=source_dir.parent)
assert movie_generated.is_file() and movie_generated.stat().st_size > 100000
# Verify the full 7-second 30-fps portrait movie before embedding.
import cv2
video_capture = cv2.VideoCapture(str(movie_generated))
assert video_capture.isOpened(), "Reference-only portal MP4 cannot be decoded"
assert round(video_capture.get(cv2.CAP_PROP_FPS)) == 30
assert round(video_capture.get(cv2.CAP_PROP_FRAME_COUNT)) == 210
assert round(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)) == 480
assert round(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)) == 920
video_capture.release()
movie_raw = app / "res/raw/charoite_c_energy_reference_portal_7s.mp4"
assert not movie_raw.exists()
shutil.copyfile(movie_generated, movie_raw)
assert movie_raw.stat().st_size == movie_generated.stat().st_size
movie_generated.unlink()
if storyboard_generated.exists():
    storyboard_generated.unlink()
print("CHAROITE_NEXT_C_ENERGY_REFERENCE_PORTAL_7_SECONDS=PASS")



source = app / "java/com/winlator/TouhouEntryActivity.java"
ui = source.read_text(encoding="utf-8")
anchor = "        systemScreen.addView(runtimeCard);"
assert ui.count(anchor) == 1
ui = ui.replace(anchor, anchor + """
        spacerIn(systemScreen, 12);
        LinearLayout nextCoreCard = card();
        nextCoreCard.addView(label("CHAROITE CORE NEXT — ENGINE STATUS", 17, FOREGROUND, true));
        // The installed APK is the source of truth: this label updates every release.
        nextCoreCard.addView(label(
                com.charoitegames.core.CharoiteNextBootActivity.installedVersionLabel(this),
                12, SECONDARY, false));
        nextCoreCard.addView(label(
                com.charoitegames.core.CharoiteNextRuntime.report(this),
                12, SECONDARY, false));
        nextCoreCard.addView(label(
                "The Proton ARM64EC/FEX and Wine Staging runners are not ready. " +
                "They cannot be selected or used until verified native assets, " +
                "isolated prefixes and device smoke tests exist. No game-specific " +
                "anti-cheat bypasses are provided.", 12, SECONDARY, false));
        android.widget.Button coreModules = new android.widget.Button(this);
        coreModules.setText("Manage Charoite Core modules");
        coreModules.setAllCaps(false);
        coreModules.setOnClickListener(v ->
            com.charoitegames.core.CharoiteCoreManager.show(this));
        nextCoreCard.addView(coreModules);
        systemScreen.addView(nextCoreCard);
        // Historical Wine22-29 version/staging/one-shot probes are retained in
        // source for provenance, but never mounted into the active System view.
        // Re-enable only by an intentional source change for a new investigation.
        final boolean showArchivedWineTests = false;
        if (showArchivedWineTests) {
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
        android.widget.Button bootAudit = new android.widget.Button(this);
        bootAudit.setText("Audit modern Wine bootstrap prerequisites");
        bootAudit.setAllCaps(false);
        bootAudit.setOnClickListener(v -> {
            final String report = com.charoitegames.core.CharoiteWineBootstrapPreflight.report(this);
            new android.app.AlertDialog.Builder(this)
                .setTitle("Charoite Next — Bootstrap Preflight")
                .setMessage(report)
                .setPositiveButton("Copy report", (dialog, which) -> {
                    android.content.ClipboardManager clipboard =
                        (android.content.ClipboardManager)
                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                    if (clipboard != null)
                        clipboard.setPrimaryClip(android.content.ClipData.newPlainText(
                            "Charoite Next Bootstrap Preflight", report));
                })
                .setNegativeButton("Close", null).show();
        });
        nextCoreCard.addView(bootAudit);
        android.widget.Button modulePayload = new android.widget.Button(this);
        modulePayload.setText("Verify packaged modern Wine modules");
        modulePayload.setAllCaps(false);
        modulePayload.setOnClickListener(v -> {
            modulePayload.setEnabled(false);
            new Thread(() -> {
                final String report = com.charoitegames.core.CharoiteWinePayloadAudit.report(this);
                runOnUiThread(() -> {
                    modulePayload.setEnabled(true);
                    new android.app.AlertDialog.Builder(this)
                        .setTitle("Charoite Next — Module Archive Integrity")
                        .setMessage(report)
                        .setPositiveButton("Copy report", (dialog, which) -> {
                            android.content.ClipboardManager cb =
                                (android.content.ClipboardManager)
                                getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                            if (cb != null)
                                cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                    "Charoite Next Source-built Wine Modules", report));
                        })
                        .setNegativeButton("Close", null).show();
                });
            }, "CharoiteWinePayloadAudit").start();
        });
        nextCoreCard.addView(modulePayload);
        android.widget.Button stageWineData = new android.widget.Button(this);
        stageWineData.setText("Stage isolated modern Wine PE/NLS modules");
        stageWineData.setAllCaps(false);
        stageWineData.setOnClickListener(v -> {
            new android.app.AlertDialog.Builder(this)
                .setTitle("Stage verified Wine data?")
                .setMessage("Copies 19 Windows PE files and 76 NLS tables into a new " +
                    "private Charoite Next staging directory. This can use additional " +
                    "device storage. It does NOT start Wine, create a Wine prefix, " +
                    "install native executables, or access existing games and saves. " +
                    "If staging is interrupted, incomplete data is quarantined and " +
                    "is never used for launching.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Stage / Verify", (d, which) -> {
                    stageWineData.setEnabled(false);
                    new Thread(() -> {
                        final String report = com.charoitegames.core.CharoiteWineIsolatedStage.run(this);
                        runOnUiThread(() -> {
                            stageWineData.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — Isolated Wine Data")
                                .setMessage(report)
                                .setPositiveButton("Copy report", (dialog, button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null)
                                        cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                            "Charoite Next Isolated Wine Staging", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWineIsolatedStage").start();
                }).show();
        });
        nextCoreCard.addView(stageWineData);
        android.widget.Button nativeGate = new android.widget.Button(this);
        nativeGate.setText("Test native Wine startup prerequisites");
        nativeGate.setAllCaps(false);
        nativeGate.setOnClickListener(v -> {
            new android.app.AlertDialog.Builder(this)
                .setTitle("Test source-built Wine and wineserver?")
                .setMessage("Checks the existing isolated 95-file staging area, then " +
                    "runs only the APK-installed, hash-verified native Wine loader " +
                    "and wineserver with --version. No Wine prefix is created, " +
                    "no Windows EXE or game is launched, and no existing game data " +
                    "is read or changed. A pass does not make Wineboot ready.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Run version tests", (d, which) -> {
                    nativeGate.setEnabled(false);
                    new Thread(() -> {
                        final String report = com.charoitegames.core.CharoiteWineBootstrapGate.run(this);
                        runOnUiThread(() -> {
                            nativeGate.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — Native Bootstrap Gate")
                                .setMessage(report)
                                .setPositiveButton("Copy report", (dialog, button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null)
                                        cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                            "Charoite Next Native Bootstrap Gate", report));
                                })
                                .setNegativeButton("Close", null)
                                .show();
                        });
                    }, "CharoiteWineBootstrapGate").start();
                }).show();
        });
        nextCoreCard.addView(nativeGate);
        android.widget.Button wine26Stage = new android.widget.Button(this);
        wine26Stage.setText("Stage expanded Wine 26-module data");
        wine26Stage.setAllCaps(false);
        wine26Stage.setOnClickListener(v -> {
            new android.app.AlertDialog.Builder(this)
                .setTitle("Stage the new Wine 10 source generation?")
                .setMessage("Verifies the new full 26-component source-built archive, " +
                    "then stages only 23 Windows PE modules and 76 NLS tables " +
                    "in a DIFFERENT private, versioned slot. Existing Wine22 " +
                    "data, native loader, installed games, saves and prefixes " +
                    "remain unchanged. This uses additional device storage. " +
                    "Native Wine executables, wineboot, FEX and graphics stay " +
                    "disabled. This is NOT a runnable Windows engine.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Stage / Verify Wine26", (d, which) -> {
                    wine26Stage.setEnabled(false);
                    new Thread(() -> {
                        final String report = com.charoitegames.core.CharoiteWine26Stage.run(this);
                        runOnUiThread(() -> {
                            wine26Stage.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — Wine26 data staging")
                                .setMessage(report)
                                .setPositiveButton("Copy report", (dialog, button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null)
                                        cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                            "Charoite Next Wine26 source staging", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine26Stage").start();
                }).show();
        });
        nextCoreCard.addView(wine26Stage);
        android.widget.Button wine26Native = new android.widget.Button(this);
        wine26Native.setText("Test matched Wine26 native startup");
        wine26Native.setAllCaps(false);
        wine26Native.setOnClickListener(v -> {
            new android.app.AlertDialog.Builder(this)
                .setTitle("Test same-source Wine26 native binaries?")
                .setMessage("First re-verifies your separately staged 23 PE and " +
                    "76 NLS files, then checks all THREE matching source-built " +
                    "APK-native ELF hashes. Executes only native Wine 10 and " +
                    "wineserver with --version, with a clean environment and " +
                    "timeout. No Windows EXE, Wine prefix, Wineboot, server " +
                    "session, FEX or graphics are attempted. Existing games, " +
                    "Wine22 files, saves and prefixes remain untouched.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Run Wine26 version tests", (d, which) -> {
                    wine26Native.setEnabled(false);
                    new Thread(() -> {
                        final String report = com.charoitegames.core.CharoiteWine26NativeGate.run(this);
                        runOnUiThread(() -> {
                            wine26Native.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — Wine26 Native Bootstrap Gate")
                                .setMessage(report)
                                .setPositiveButton("Copy report", (dialog, button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null)
                                        cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                            "Charoite Next Wine26 Native Bootstrap Gate", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine26NativeGate").start();
                }).show();
        });
        nextCoreCard.addView(wine26Native);
        android.widget.Button wine26Prefix = new android.widget.Button(this);
        wine26Prefix.setText("Test isolated Wine26 prefix bootstrap");
        wine26Prefix.setAllCaps(false);
        wine26Prefix.setOnClickListener(v -> {
            new android.app.AlertDialog.Builder(this)
                .setTitle("Run first isolated Wine26 Wineboot test?")
                .setMessage("Only after verifying the full 99-file staged Wine26 data " +
                    "and all 3 APK native hashes and version probes, copies a " +
                    "source-verified set into a brand-new app-private test folder " +
                    "and tries Wineboot -i with its own NEW Wine prefix and " +
                    "wineserver. It may use extra storage, can fail or time out, " +
                    "and RETAINS diagnostic files rather than automatically " +
                    "deleting them. Never touches existing prefixes, Wine22, " +
                    "games or saves. Uses a new v2 scratch and bypasses the " +
                    "loader re-exec attempt that failed in v0.41. FEX, " +
                    "graphics and gaming remain untested.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Run isolated Wineboot probe", (dialog, which) -> {
                    wine26Prefix.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine26PrefixProbe.run(this);
                        runOnUiThread(() -> {
                            wine26Prefix.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — Wine26 isolated prefix")
                                .setMessage(report)
                                .setPositiveButton("Copy report", (d, button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null)
                                        cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                            "Charoite Next Wine26 isolated Wineboot", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine26PrefixProbe").start();
                }).show();
        });
        nextCoreCard.addView(wine26Prefix);
        android.widget.Button wine27Stage = new android.widget.Button(this);
        wine27Stage.setText("Stage patched Wine source (v3 isolated)");
        wine27Stage.setAllCaps(false);
        wine27Stage.setOnClickListener(v -> {
            new android.app.AlertDialog.Builder(this)
                .setTitle("Stage patched NLS source cohort (v3)?")
                .setMessage("Verifies the separately rebuilt 26-component source archive with " +
                    "Android-only NLS and native loader patches, " +
                    "then stages only 23 Windows PE modules and 76 NLS tables " +
                    "in a NEW 0.6 private data slot. Wine26 0.5, Wine22 " +
                    "data, native loader, installed games, saves and prefixes " +
                    "remain unchanged. This uses additional device storage. " +
                    "Native Wine executables, wineboot, FEX and graphics stay " +
                    "disabled. This is NOT a runnable Windows engine.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Stage patched 0.6 cohort", (d, which) -> {
                    wine27Stage.setEnabled(false);
                    new Thread(() -> {
                        final String report = com.charoitegames.core.CharoiteWine27Stage.run(this);
                        runOnUiThread(() -> {
                            wine27Stage.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — Wine27 data staging")
                                .setMessage(report)
                                .setPositiveButton("Copy report", (dialog, button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null)
                                        cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                            "Charoite Next Wine27 source staging", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine27Stage").start();
                }).show();
        });
        nextCoreCard.addView(wine27Stage);
        android.widget.Button wine27Native = new android.widget.Button(this);
        wine27Native.setText("Verify new patched Wine native cohort");
        wine27Native.setAllCaps(false);
        wine27Native.setOnClickListener(v -> {
            new android.app.AlertDialog.Builder(this)
                .setTitle("Verify patched native loader/ntdll/server?")
                .setMessage("First re-verifies your separately staged 23 PE and " +
                    "76 NLS files, then checks all THREE matching source-built " +
                    "APK-native ELF hashes. Executes only native Wine 10 and " +
                    "wineserver with --version, with a clean environment and " +
                    "timeout. No Windows EXE, Wine prefix, Wineboot, server " +
                    "session, FEX or graphics are attempted. Existing games, " +
                    "Wine22 files, saves and prefixes remain untouched.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Verify patched Wine native --version", (d, which) -> {
                    wine27Native.setEnabled(false);
                    new Thread(() -> {
                        final String report = com.charoitegames.core.CharoiteWine27NativeGate.run(this);
                        runOnUiThread(() -> {
                            wine27Native.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — Wine27 Native Bootstrap Gate")
                                .setMessage(report)
                                .setPositiveButton("Copy report", (dialog, button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null)
                                        cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                            "Charoite Next Wine27 Native Bootstrap Gate", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine27NativeGate").start();
                }).show();
        });
        nextCoreCard.addView(wine27Native);
        android.widget.Button wine27Prefix = new android.widget.Button(this);
        wine27Prefix.setText("Test new v3 isolated Wineboot");
        wine27Prefix.setAllCaps(false);
        wine27Prefix.setOnClickListener(v -> {
            new android.app.AlertDialog.Builder(this)
                .setTitle("Run isolated Wineboot with patched native NLS paths?")
                .setMessage("Only after verifying the full 99-file staged Wine27 data " +
                    "and all 3 APK native hashes and version probes, copies a " +
                    "source-verified set into a brand-new app-private test folder " +
                    "and tries Wineboot -i with its own NEW Wine prefix and " +
                    "wineserver. It may use extra storage, can fail or time out, " +
                    "and RETAINS diagnostic files rather than automatically " +
                    "deleting them. Never touches existing prefixes, Wine22, " +
                    "games or saves. Uses a NEW one-shot v3 scratch, with " +
                    "an APK-native source-matched ntdll and a verified private " +
                    "NLS directory. v1/v2 diagnostic evidence is preserved. " +
                    "FEX, graphics and gaming remain untested.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Run one-time v3 Wineboot probe", (dialog, which) -> {
                    wine27Prefix.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine27PrefixProbe.run(this);
                        runOnUiThread(() -> {
                            wine27Prefix.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — Wine27 isolated prefix")
                                .setMessage(report)
                                .setPositiveButton("Copy report", (d, button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null)
                                        cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                            "Charoite Next Wine27 isolated Wineboot", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine27PrefixProbe").start();
                }).show();
        });
        nextCoreCard.addView(wine27Prefix);
        android.widget.Button wine27Forensics = new android.widget.Button(this);
        wine27Forensics.setText("Inspect failed Wine27 v3 PE imports and logs (read-only)");
        wine27Forensics.setAllCaps(false);
        wine27Forensics.setOnClickListener(v -> {
            new android.app.AlertDialog.Builder(this)
                .setTitle("Inspect retained v3 Wineboot evidence?")
                .setMessage("Reads only the existing one-shot v3 scratch: "
                    + "Wineboot and wineserver-stop logs, verified NLS file "
                    + "presence and the new prefix's immediate directory names. "
                    + "No native executable, Wineboot, prefix creation, data "
                    + "modification, cleanup, v1/v2 scratch, games or saves. "
                    + "The returned report may include local file paths.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Inspect v3 without changing files", (d, which) -> {
                    wine27Forensics.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine27V3Forensics.run(this);
                        runOnUiThread(() -> {
                            wine27Forensics.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — v3 failed-prefix forensics")
                                .setMessage(report)
                                .setPositiveButton("Copy report", (dialog, button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null)
                                        cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                            "Charoite Next Wine27 v3 read-only forensics", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine27V3Forensics").start();
                }).show();
        });
        nextCoreCard.addView(wine27Forensics);

        android.widget.Button wine27V4Trace = new android.widget.Button(this);
        wine27V4Trace.setText("Test new v4 isolated traced Wineboot");
        wine27V4Trace.setAllCaps(false);
        wine27V4Trace.setOnClickListener(v -> {
            new android.app.AlertDialog.Builder(this)
                .setTitle("Run ONE fresh v4 traced Wineboot attempt?")
                .setMessage("Requires the verified 99-file patched Wine27 source cohort "
                    + "and three matched APK-native hashes plus --version checks. "
                    + "This creates only a NEW isolated v4 scratch/prefix, runs "
                    + "Wineboot -i once, and records bounded module/process/server "
                    + "diagnostics with an 8 MiB log cap and a 25-second deadline. "
                    + "It may fail or use device storage. Never reuses or deletes "
                    + "failed v1/v2/v3 evidence, installed games, user prefixes "
                    + "or Wine22. Do NOT rerun if the v4 scratch exists. "
                    + "FEX, graphics and modern gaming are not enabled.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Run ONE v4 traced Wineboot", (dialog, which) -> {
                    wine27V4Trace.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine27V4Trace.run(this);
                        runOnUiThread(() -> {
                            wine27V4Trace.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — v4 isolated traced Wineboot")
                                .setMessage(report)
                                .setPositiveButton("Copy report", (d, button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null)
                                        cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                            "Charoite Next v4 Wineboot traced result", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine27V4Trace").start();
                }).show();
        });
        nextCoreCard.addView(wine27V4Trace);

        android.widget.Button wine28Stage = new android.widget.Button(this);
        wine28Stage.setText("Stage source-patched Wine28 modules (0.7 isolated)");
        wine28Stage.setAllCaps(false);
        wine28Stage.setOnClickListener(v -> {
            new android.app.AlertDialog.Builder(this)
                .setTitle("Stage independent Wine28 PE/NLS modules?")
                .setMessage("Reads the source-verified Wine28 APK archive and "
                    + "SHA-checks 23 Windows PE modules and 76 NLS files before "
                    + "staging in a NEW private 0.7 directory. Earlier Wine22, "
                    + "Wine26, Wine27, v1/v2/v3/v4 scratch, user prefixes, "
                    + "games and saves are not touched. No Wine execution.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Stage Wine28 data only", (d, which) -> {
                    wine28Stage.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine28Stage.run(this);
                        runOnUiThread(() -> {
                            wine28Stage.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — Wine28 staging")
                                .setMessage(report)
                                .setPositiveButton("Copy report", (dialog, button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null)
                                        cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                            "Charoite Next Wine28 staging", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine28Stage").start();
                }).show();
        });
        nextCoreCard.addView(wine28Stage);

        android.widget.Button wine28Native = new android.widget.Button(this);
        wine28Native.setText("Verify matched Wine28 native cohort");
        wine28Native.setAllCaps(false);
        wine28Native.setOnClickListener(v -> {
            new android.app.AlertDialog.Builder(this)
                .setTitle("Verify source-matched Wine28 native hashes?")
                .setMessage("Re-verifies all 99 new PE/NLS files and three "
                    + "new native ELF hashes. Executes only source-built "
                    + "Wine and wineserver --version with a clean environment. "
                    + "No Wineboot, Windows application, prefix or server session.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Verify Wine28 version only", (d, which) -> {
                    wine28Native.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine28NativeGate.run(this);
                        runOnUiThread(() -> {
                            wine28Native.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — Wine28 native gate")
                                .setMessage(report)
                                .setPositiveButton("Copy report", (dialog, button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null)
                                        cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                            "Charoite Next Wine28 native gate", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine28NativeGate").start();
                }).show();
        });
        nextCoreCard.addView(wine28Native);

        android.widget.Button wine28V5 = new android.widget.Button(this);
        wine28V5.setText("Test new v5 Wine28 PE-NTDLL bootstrap (one-shot)");
        wine28V5.setAllCaps(false);
        wine28V5.setOnClickListener(v -> {
            new android.app.AlertDialog.Builder(this)
                .setTitle("Run ONE fresh Wine28 v5 prefix initialization?")
                .setMessage("Only after the new Wine28 99-file staging and "
                    + "three native hashes plus version checks PASS, copies "
                    + "these files into NEW v5 scratch and attempts Wineboot -i "
                    + "using corrected NTDLL PE/native paths. Tracing is bounded "
                    + "by an 8 MiB log cap and a 25-second execution deadline. "
                    + "May fail and use storage. NEVER overwrites or deletes "
                    + "v1/v2/v3/v4 scratch or any game, save, rootfs or user "
                    + "prefix. Do not retry if v5 scratch already exists.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Run ONE Wine28 v5 bootstrap", (dialog, which) -> {
                    wine28V5.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine28V5Trace.run(this);
                        runOnUiThread(() -> {
                            wine28V5.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — Wine28 v5 isolated Wineboot")
                                .setMessage(report)
                                .setPositiveButton("Copy report", (d, button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null)
                                        cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                            "Charoite Next Wine28 v5 Wineboot", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine28V5Trace").start();
                }).show();
        });
        nextCoreCard.addView(wine28V5);

        android.widget.Button wine28V5Forensics = new android.widget.Button(this);
        wine28V5Forensics.setText("Inspect failed Wine28 v5 bootstrap (read-only)");
        wine28V5Forensics.setAllCaps(false);
        wine28V5Forensics.setOnClickListener(v -> {
            new android.app.AlertDialog.Builder(this)
                .setTitle("Inspect retained Wine28 v5 evidence?")
                .setMessage("Reads only the existing already-used v5 scratch: "
                    + "file presence, static PE headers/direct imports, bounded "
                    + "directory names and limited Wineboot/wineserver logs. "
                    + "No native Wine execution, new prefix, writes or cleanup; "
                    + "no prior v1/v2/v3/v4 scratch, Portal, games or saves. "
                    + "The report may contain app-private file paths.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Inspect v5 without changing files", (d, which) -> {
                    wine28V5Forensics.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine28V5Forensics.run(this);
                        runOnUiThread(() -> {
                            wine28V5Forensics.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — Wine28 v5 read-only postmortem")
                                .setMessage(report)
                                .setPositiveButton("Copy report", (dlg, button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null)
                                        cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                            "Charoite Next Wine28 v5 read-only postmortem", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine28V5Forensics").start();
                }).show();
        });
        nextCoreCard.addView(wine28V5Forensics);

        // Independent native server startup diagnosis; never runs Windows PE or Wineboot.
        android.widget.Button wine28V6Server = new android.widget.Button(this);
        wine28V6Server.setText("Test isolated Wine28 wineserver only (one-shot v6)");
        wine28V6Server.setAllCaps(false);
        wine28V6Server.setOnClickListener(v -> {
            new android.app.AlertDialog.Builder(this)
                .setTitle("Run ONE independent Wine28 server-only smoke?")
                .setMessage("After verifying same-source Wine28 assets, creates a NEW "
                    + "v6 scratch/prefix and executes ONLY the APK-native wineserver "
                    + "in foreground debug mode for up to 8 seconds. Checks whether "
                    + "its new Unix socket and lock appear. Does NOT run Wineboot, "
                    + "Windows EXE, FEX, graphics or any game. Never opens or removes "
                    + "v1/v2/v3/v4/v5 scratch, stable Portal, games, saves or user "
                    + "prefixes. Uses new private storage; never repeat if v6 exists.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Run ONE v6 server-only test", (d, which) -> {
                    wine28V6Server.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine28V6ServerProbe.run(this);
                        runOnUiThread(() -> {
                            wine28V6Server.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — v6 isolated wineserver-only")
                                .setMessage(report)
                                .setPositiveButton("Copy report", (dlg, button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null)
                                        cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                            "Charoite Next Wine28 v6 server-only", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine28V6ServerProbe").start();
                }).show();
        });
        nextCoreCard.addView(wine28V6Server);

        android.widget.Button wine28V7Help = new android.widget.Button(this);
        wine28V7Help.setText("Test isolated Wine28 PE help handshake (one-shot v7)");
        wine28V7Help.setAllCaps(false);
        wine28V7Help.setOnClickListener(v -> {
            new android.app.AlertDialog.Builder(this)
                .setTitle("Run ONE Wine28 v7 Windows PE help probe?")
                .setMessage("This is a NEW fresh v7 experiment, NOT a retry of v5/v6. "
                    + "It verifies the matched 99-file Wine28 cohort, copies only "
                    + "source-verified files to new private scratch, and starts the "
                    + "APK-native wineserver in foreground. Only after observing "
                    + "its new socket/lock it launches the matched ARM64 "
                    + "wineboot.exe with --help ONLY (Windows PE execution); "
                    + "it never runs -i, installs games or requests a full prefix. "
                    + "Server startup is bounded 5s and PE help 12s, with capped "
                    + "logs. May still create private prefix files. Never accesses "
                    + "or removes old v1-v6 scratch, Wine22, games, saves or user "
                    + "prefixes. Never retry if v7 scratch exists.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Run ONE v7 PE help test", (d, which) -> {
                    wine28V7Help.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine28V7PeHelpProbe.run(this);
                        runOnUiThread(() -> {
                            wine28V7Help.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — Wine28 v7 PE help handshake")
                                .setMessage(report)
                                .setPositiveButton("Copy report", (dlg, button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null)
                                        cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                            "Charoite Next Wine28 v7 PE help", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine28V7PeHelpProbe").start();
                }).show();
        });
        nextCoreCard.addView(wine28V7Help);

        android.widget.Button wine28V8Layout = new android.widget.Button(this);
        wine28V8Layout.setText("Test corrected Wine28 ARM64 DLL paths (one-shot v8)");
        wine28V8Layout.setAllCaps(false);
        wine28V8Layout.setOnClickListener(v -> {
            new android.app.AlertDialog.Builder(this)
                .setTitle("Run ONE isolated Wine28 v8 DLL-layout probe?")
                .setMessage("v7 reached Windows PE NTDLL but failed kernel32.dll "
                    + "with c0000135. Wine's ARM64 DLL lookup expects "
                    + "WINEDLLPATH to identify a parent whose /aarch64-windows "
                    + "subfolder contains the DLLs. This experiment creates "
                    + "a NEW v8 scratch, re-verifies all 99 Wine28 files and "
                    + "matched native binaries, stages hybrid PE DLLs in the "
                    + "correct aarch64-windows location, starts only a NEW "
                    + "foreground wineserver and requests wineboot.exe --help. "
                    + "IMPORTANT: Wine can AUTOMATICALLY run internal wineboot "
                    + "--init as part of first startup in the NEW v8 prefix, "
                    + "even when --help was requested. The test can create "
                    + "new v8-only prefix files. No game, user Wine prefix, "
                    + "older v1-v7 scratch or Portal installation is read, "
                    + "deleted, migrated or reused. 5s server/12s PE deadlines. "
                    + "Never repeat once v8 scratch exists.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Run ONE new v8 DLL-layout test", (d, which) -> {
                    wine28V8Layout.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine28V8LayoutProbe.run(this);
                        runOnUiThread(() -> {
                            wine28V8Layout.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — Wine28 v8 DLL layout")
                                .setMessage(report)
                                .setPositiveButton("Copy report", (dlg, button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null)
                                        cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                            "Charoite Next Wine28 v8 DLL-layout probe", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine28V8LayoutProbe").start();
                }).show();
        });
        nextCoreCard.addView(wine28V8Layout);
        android.widget.Button wine28V9Builtin = new android.widget.Button(this);
        wine28V9Builtin.setText("Test Wine28 built-in Wineboot lookup (one-shot v9)");
        wine28V9Builtin.setAllCaps(false);
        wine28V9Builtin.setOnClickListener(v -> {
            new android.app.AlertDialog.Builder(this)
                .setTitle("Run ONE isolated Wine28 v9 built-in Wineboot probe?")
                .setMessage("v8 had correct PE kernel32 location, but Wine's "
                    + "automatic internal wineboot --init failed and requested "
                    + "--help ended with kernel32 c0000135. Source code shows "
                    + "the internal auto-init executable must be found at "
                    + "WINEDLLPATH/aarch64-windows/wineboot.exe. This NEW v9 "
                    + "test creates its own private scratch and duplicates "
                    + "the verified ARM64 Wineboot into that builtin location, "
                    + "with independent SHA-256 verification. IMPORTANT: "
                    + "Wine WILL automatically attempt wineboot --init in "
                    + "the NEW disposable v9 prefix before our requested "
                    + "wineboot --help, and may create private registry/drive "
                    + "files. Its live server and PE process have bounded "
                    + "timeouts/logs. It does NOT run games and NEVER touches "
                    + "v1-v8 scratch, existing user Wine prefixes, Portal, "
                    + "rootfs, games or saves. Authorize ONCE; v9 scratch "
                    + "is preserved and must NEVER be retried or deleted.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Run ONE new v9 Wineboot lookup test", (d, which) -> {
                    wine28V9Builtin.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine28V9BuiltinBootstrapProbe.run(this);
                        runOnUiThread(() -> {
                            wine28V9Builtin.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — Wine28 v9 DLL layout")
                                .setMessage(report)
                                .setPositiveButton("Copy report", (dlg, button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null)
                                        cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                            "Charoite Next Wine28 v9 DLL-layout probe", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine28V9BuiltinBootstrapProbe").start();
                }).show();
        });
        nextCoreCard.addView(wine28V9Builtin);



        android.widget.Button wine28V9Forensics = new android.widget.Button(this);
        wine28V9Forensics.setText("Inspect preserved Wine28 v9 logs (read-only)");
        wine28V9Forensics.setAllCaps(false);
        wine28V9Forensics.setOnClickListener(v -> {
            wine28V9Forensics.setEnabled(false);
            new Thread(() -> {
                final String report =
                    com.charoitegames.core.CharoiteWine28V9Forensics.run(this);
                runOnUiThread(() -> {
                    wine28V9Forensics.setEnabled(true);
                    new android.app.AlertDialog.Builder(this)
                        .setTitle("Charoite Next — v9 preserved Wine28 evidence")
                        .setMessage(report)
                        .setPositiveButton("Copy report", (dlg, button) -> {
                            android.content.ClipboardManager cb =
                                (android.content.ClipboardManager)
                                getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                            if (cb != null)
                                cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                    "Charoite Next v9 READ-ONLY postmortem", report));
                        })
                        .setNegativeButton("Close", null).show();
                });
            }, "CharoiteWine28V9Forensics").start();
        });
        nextCoreCard.addView(wine28V9Forensics);

        // Wine29 0.7 is installed under NEW APK asset/native names only.
        // This READ-ONLY verification never starts Wine, Wineboot or a prefix.
        android.widget.Button wine29Audit = new android.widget.Button(this);
        wine29Audit.setText("Verify Wine29 0.7 package (read-only)");
        wine29Audit.setAllCaps(false);
        wine29Audit.setOnClickListener(v -> {
            wine29Audit.setEnabled(false);
            new Thread(() -> {
                final String report =
                    com.charoitegames.core.CharoiteWine29Native07Audit.run(this);
                runOnUiThread(() -> {
                    wine29Audit.setEnabled(true);
                    new android.app.AlertDialog.Builder(this)
                        .setTitle("Charoite Next — isolated Wine29 0.7 archive audit")
                        .setMessage(report)
                        .setPositiveButton("Copy report", (dlg, button) -> {
                            android.content.ClipboardManager cb =
                                (android.content.ClipboardManager)
                                getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                            if (cb != null)
                                cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                    "Charoite Next Wine29 0.7 read-only audit", report));
                        })
                        .setNegativeButton("Close", null).show();
                });
            }, "CharoiteWine29Native07Audit").start();
        });
        nextCoreCard.addView(wine29Audit);

        // Only explicit consent invokes the separately audited Wine29 .0.7
        // loader and wineserver --version. No auto-run, prefix or Windows EXE.
        android.widget.Button wine29Version = new android.widget.Button(this);
        wine29Version.setText("Test Wine29 0.7 native --version (no prefix)");
        wine29Version.setAllCaps(false);
        wine29Version.setOnClickListener(v -> {
            new android.app.AlertDialog.Builder(this)
                .setTitle("Confirm Wine29 version-only test?")
                .setMessage("This test executes ONLY the separately verified Wine29 0.7 native "
                    + "loader and wineserver with --version, after SHA-256 checks. "
                    + "It does not run Wineboot, Windows software, games, FEX or graphics. "
                    + "No new prefix is created and old Wine28 experiments, games, saves "
                    + "and rootfs are not accessed. Each invocation requires your consent.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Run version-only test", (dialog, which) -> {
                    wine29Version.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine29Native07VersionGate.run(this);
                        runOnUiThread(() -> {
                            wine29Version.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — Wine29 native version gate")
                                .setMessage(report)
                                .setPositiveButton("Copy report", (dlg, button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null)
                                        cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                            "Charoite Next Wine29 native --version only", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine29Native07VersionGate").start();
                }).show();
        });
        nextCoreCard.addView(wine29Version);

        // Manual DATA-only Wine29 .0.7 PE/NLS stage. Only this consent
        // button may write a NEW isolated no_backup slot; NEVER Wineboot.
        android.widget.Button wine29Data = new android.widget.Button(this);
        wine29Data.setText("Stage Wine29 0.7 PE/NLS data (no execution)");
        wine29Data.setAllCaps(false);
        wine29Data.setOnClickListener(v -> {
            new android.app.AlertDialog.Builder(this)
                .setTitle("Stage new isolated Wine29 0.7 DATA?")
                .setMessage("This copies 24 source-verified Windows PE files and 76 Wine "
                    + "NLS files into a NEW private Wine29 0.7 slot only, after "
                    + "verifying the complete archive and every asset SHA-256. "
                    + "It does not start Wine, run Wineboot, create a Windows prefix, "
                    + "launch any EXE or access existing games/saves/Wine28 scratch. "
                    + "Partial failures are quarantined and never overwritten.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Stage data only", (dialog, which) -> {
                    wine29Data.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine29Native07Stage.run(this);
                        runOnUiThread(() -> {
                            wine29Data.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — Wine29 0.7 PE/NLS data")
                                .setMessage(report)
                                .setPositiveButton("Copy report", (dlg, button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null)
                                        cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                            "Charoite Next Wine29 0.7 DATA-only staging", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine29Native07Stage").start();
                }).show();
        });
        nextCoreCard.addView(wine29Data);

        // Strict read-only sealing audit. Never creates or repairs a slot, and
        // never invokes Wine/PE/Wineboot. Useful after opt-in staging.
        android.widget.Button wine29Verify = new android.widget.Button(this);
        wine29Verify.setText("Verify staged Wine29 0.7 data (read-only)");
        wine29Verify.setAllCaps(false);
        wine29Verify.setOnClickListener(v -> {
            wine29Verify.setEnabled(false);
            new Thread(() -> {
                final String report =
                    com.charoitegames.core.CharoiteWine29Native07Stage.verifyOnly(this);
                runOnUiThread(() -> {
                    wine29Verify.setEnabled(true);
                    new android.app.AlertDialog.Builder(this)
                        .setTitle("Charoite Next — Wine29 staged data read-only audit")
                        .setMessage(report)
                        .setPositiveButton("Copy report", (dlg, button) -> {
                            android.content.ClipboardManager cb =
                                (android.content.ClipboardManager)
                                getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                            if (cb != null)
                                cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                    "Charoite Next Wine29 staged-data seal audit", report));
                        })
                        .setNegativeButton("Close", null).show();
                });
            }, "CharoiteWine29Native07StageVerifyOnly").start();
        });
        nextCoreCard.addView(wine29Verify);

        // Read-only static PE/ARM64EC loader-layout inspection. It does NOT
        // execute Wine/wineserver/Wineboot or create/modify any prefix/scratch.
        android.widget.Button wine29Preflight = new android.widget.Button(this);
        wine29Preflight.setText("Preflight Wine29 0.7 PE loader layout (read-only)");
        wine29Preflight.setAllCaps(false);
        wine29Preflight.setOnClickListener(v -> {
            wine29Preflight.setEnabled(false);
            new Thread(() -> {
                final String report =
                    com.charoitegames.core.CharoiteWine29Native07PePreflight.run(this);
                runOnUiThread(() -> {
                    wine29Preflight.setEnabled(true);
                    new android.app.AlertDialog.Builder(this)
                        .setTitle("Charoite Next — Wine29 PE layout/import preflight")
                        .setMessage(report)
                        .setPositiveButton("Copy report", (dlg, button) -> {
                            android.content.ClipboardManager cb =
                                (android.content.ClipboardManager)
                                getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                            if (cb != null)
                                cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                    "Charoite Next Wine29 PE static preflight", report));
                        })
                        .setNegativeButton("Close", null).show();
                });
            }, "CharoiteWine29Native07PePreflight").start();
        });
        nextCoreCard.addView(wine29Preflight);

        // Independently sealed 34 DLL + 1 inert Wineboot PE + 76 NLS.
        // New generation has a distinct no_backup slot; no Wine execution.
        android.widget.Button wine29SealedStage = new android.widget.Button(this);
        wine29SealedStage.setText("Stage Wine29 0.12 sealed 111-file data (no execution)");
        wine29SealedStage.setAllCaps(false);
        wine29SealedStage.setOnClickListener(v -> {
            new android.app.AlertDialog.Builder(this)
                .setTitle("Stage new Wine29 0.12 sealed DATA?")
                .setMessage("Creates a NEW private source-hash-verified slot for 34 DLLs, "
                    + "one inert ARM64 Wineboot executable, and 76 NLS files. "
                    + "The previous Wine29 .0.7 100-file slot, Wine28 v1–v9, existing "
                    + "games, saves, prefixes and Portal stay untouched. "
                    + "Wine, wineserver, Wineboot, Windows EXE and graphics are NOT executed. "
                    + "Incomplete new data stays quarantined and is never deleted.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Stage new DATA only", (dialog, which) -> {
                    wine29SealedStage.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine29Sealed012Stage.run(this);
                        runOnUiThread(() -> {
                            wine29SealedStage.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — Wine29 0.12 sealed data")
                                .setMessage(report)
                                .setPositiveButton("Copy report", (dlg, button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null)
                                        cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                            "Charoite Next Wine29 0.12 sealed DATA stage", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine29Sealed012Stage").start();
                }).show();
        });
        nextCoreCard.addView(wine29SealedStage);

        // Explicit read-only recheck. No repair or runtime execution.
        android.widget.Button wine29SealedVerify = new android.widget.Button(this);
        wine29SealedVerify.setText("Verify staged Wine29 0.12 sealed data (read-only)");
        wine29SealedVerify.setAllCaps(false);
        wine29SealedVerify.setOnClickListener(v -> {
            wine29SealedVerify.setEnabled(false);
            new Thread(() -> {
                final String report =
                    com.charoitegames.core.CharoiteWine29Sealed012Stage.verifyOnly(this);
                runOnUiThread(() -> {
                    wine29SealedVerify.setEnabled(true);
                    new android.app.AlertDialog.Builder(this)
                        .setTitle("Charoite Next — Wine29 0.12 sealed audit")
                        .setMessage(report)
                        .setPositiveButton("Copy report", (dlg, button) -> {
                            android.content.ClipboardManager cb =
                                (android.content.ClipboardManager)
                                getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                            if (cb != null)
                                cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                    "Charoite Next Wine29 0.12 sealed read-only audit", report));
                        })
                        .setNegativeButton("Close", null).show();
                });
            }, "CharoiteWine29Sealed012VerifyOnly").start();
        });
        nextCoreCard.addView(wine29SealedVerify);

        
        // Verifies the already-staged 111-file Wine29 PE headers/import graph;
        // never launches Wine, wineserver, Wineboot or a Windows executable.
        android.widget.Button wine29SealedPe = new android.widget.Button(this);
        wine29SealedPe.setText("Preflight Wine29 0.12 PE imports (read-only)");
        wine29SealedPe.setAllCaps(false);
        wine29SealedPe.setOnClickListener(v -> {
            wine29SealedPe.setEnabled(false);
            new Thread(() -> {
                final String report =
                    com.charoitegames.core.CharoiteWine29Sealed012PePreflight.run(this);
                runOnUiThread(() -> {
                    wine29SealedPe.setEnabled(true);
                    new android.app.AlertDialog.Builder(this)
                        .setTitle("Charoite Next — Wine29 0.12 PE header and import preflight")
                        .setMessage(report)
                        .setPositiveButton("Copy report", (dlg, button) -> {
                            android.content.ClipboardManager cb =
                                (android.content.ClipboardManager)
                                getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                            if (cb != null)
                                cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                    "Charoite Next Wine29 0.12 PE import preflight", report));
                        })
                        .setNegativeButton("Close", null).show();
                });
            }, "CharoiteWine29Sealed012PePreflight").start();
        });
        nextCoreCard.addView(wine29SealedPe);

        // Dangerous operation only by direct user approval. Even --help MAY
        // auto-initialize an isolated Windows prefix in a one-use scratch.
        android.widget.Button wine29PeHelpV1 = new android.widget.Button(this);
        wine29PeHelpV1.setText("Wine29 v1 isolated Wineboot PE-help test (one-shot)");
        wine29PeHelpV1.setAllCaps(false);
        wine29PeHelpV1.setOnClickListener(v ->
            new android.app.AlertDialog.Builder(this)
                .setTitle("Authorize ONE Wine29 Wineboot test?")
                .setMessage("This WILL execute the source-matched Wine29 native "
                    + "wineserver and Wine loader, plus the ARM64 Windows Wineboot.exe "
                    + "--help command. Wine MAY automatically initialize its own "
                    + "new Windows prefix before showing help. One completely NEW "
                    + "private v1 scratch directory will be created and 111 source-"
                    + "hashed modules copied there. The process has bounded time "
                    + "and logs and is stopped afterwards. Existing Wine28 v1–v9, "
                    + "earlier Wine29 data slots, games, saves, prefixes, stable Portal "
                    + "and rootfs must NOT be accessed. Scratch remains preserved "
                    + "for diagnosis, including if this test fails. The test cannot "
                    + "be repeated in v1; never delete or clear app storage. "
                    + "This is NOT a game launch or a functioning runtime. "
                    + "Do you explicitly authorize this ONE Wine29 execution test?")
                .setNegativeButton("Cancel — do not execute", null)
                .setPositiveButton("Authorize ONE new v1 test", (dialog, which) -> {
                    wine29PeHelpV1.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine29V1PeHelpProbe.run(this);
                        runOnUiThread(() -> {
                            wine29PeHelpV1.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — Wine29 v1 PE-help handshake")
                                .setMessage(report)
                                .setPositiveButton("Copy report", (dlg, button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null)
                                        cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                            "Charoite Next Wine29 v1 isolated PE-help", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine29V1PeHelpProbe").start();
                }).show());
        nextCoreCard.addView(wine29PeHelpV1);

        } // Archived test controls — hidden; no stale or repeatable one-shot buttons.
        // The actionable current diagnostic and its instructions are grouped
        // together below, next to the V15 inspect / handoff buttons.
        // All old execution buttons and V1–V14 read-only probes remain hidden.

        // Inspect ONLY the retained Wine29 v1 scratch, named PE copies and
        // bounded logs. Do not execute Wine, Wineboot, or even wineserver.
        android.widget.Button wine29V1Forensics = new android.widget.Button(this);
        wine29V1Forensics.setText("Inspect preserved Wine29 v1 kernel32 failure (read-only)");
        wine29V1Forensics.setAllCaps(false);
        wine29V1Forensics.setOnClickListener(v -> {
            wine29V1Forensics.setEnabled(false);
            new Thread(() -> {
                final String report =
                    com.charoitegames.core.CharoiteWine29V1Forensics.run(this);
                runOnUiThread(() -> {
                    wine29V1Forensics.setEnabled(true);
                    new android.app.AlertDialog.Builder(this)
                        .setTitle("Charoite Next — preserved Wine29 v1 failure analysis")
                        .setMessage(report)
                        .setPositiveButton("Copy report", (dlg, button) -> {
                            android.content.ClipboardManager cb =
                                (android.content.ClipboardManager)
                                getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                            if (cb != null)
                                cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                    "Charoite Next Wine29 v1 READ-ONLY kernel32 postmortem", report));
                        })
                        .setNegativeButton("Close", null).show();
                });
            }, "CharoiteWine29V1Forensics").start();
        });
        nextCoreCard.addView(wine29V1Forensics);

        // Manual one-shot v2 ONLY, opt-in after a second explicit confirmation.
        // Never run on startup, never retry v1 or touch stable Portal data.
        final boolean showArchivedWine29V2Execution = false;
        if (showArchivedWine29V2Execution) {
        android.widget.Button wine29V2Bootstrap = new android.widget.Button(this);
        wine29V2Bootstrap.setText("Wine29 v2 bootstrap and kernel32 trace (one-shot)");
        wine29V2Bootstrap.setAllCaps(false);
        wine29V2Bootstrap.setOnClickListener(v ->
            new android.app.AlertDialog.Builder(this)
                .setTitle("Authorize ONE isolated Wine29 v2 diagnostic?")
                .setMessage("This WILL execute verified Wine29 native wineserver and loader " +
                    "plus ARM64 wineboot.exe --help. Wine MAY automatically run " +
                    "Wineboot --init internally, creating a new prefix. Only a NEW " +
                    "charoite-next-wine29-bootstrap-v2 private scratch may be written. " +
                    "Source hashes and package identity are verified before execution; " +
                    "time and logs are bounded and sanitized. The run is one-shot; " +
                    "results and scratch are retained, even on failure. Failed v1, " +
                    "other scratch, stable Portal, installed games, saves and existing " +
                    "prefixes will not be accessed. This is NOT a game or runtime test. " +
                    "Do you explicitly authorize this ONE execution?")
                .setNegativeButton("Cancel — do not execute", null)
                .setPositiveButton("Authorize ONE new v2 diagnostic", (dialog, which) -> {
                    wine29V2Bootstrap.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine29V2BootstrapProbe.run(this);
                        runOnUiThread(() -> {
                            wine29V2Bootstrap.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — Wine29 v2 isolated bootstrap trace")
                                .setMessage(report)
                                .setPositiveButton("Copy report", (dlg, button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null)
                                        cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                            "Charoite Next Wine29 v2 isolated bootstrap report", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine29V2BootstrapProbe").start();
                }).show());
        nextCoreCard.addView(wine29V2Bootstrap);
        } // V2 one-shot execution is archived; its scratch stays preserved.

        // NEW V3 test corrects the EXPLICIT Wineboot location only:
        // use verified aarch64-windows/wineboot.exe beside kernel32.dll.
        // Never auto-run; do not retry v1 or v2.
        final boolean showArchivedWine29V3Execution = false;
        if (showArchivedWine29V3Execution) {
        android.widget.Button wine29V3Layout = new android.widget.Button(this);
        wine29V3Layout.setText("Wine29 v3 matched-directory Wineboot test (one-shot)");
        wine29V3Layout.setAllCaps(false);
        wine29V3Layout.setOnClickListener(v ->
            new android.app.AlertDialog.Builder(this)
                .setTitle("Authorize ONE Wine29 v3 matched-directory test?")
                .setMessage("This WILL launch source-verified native Wine29 wineserver and " +
                    "the matched ARM64 wineboot.exe --help from aarch64-windows, beside " +
                    "kernel32.dll. Wine MAY automatically run its own --init first, " +
                    "creating a new private prefix. All 111 PE/NLS modules and native " +
                    "hashes must pass preflight. One NEW v3 private scratch is used; " +
                    "v1, v2, games, saves, stable Portal, rootfs and existing prefixes " +
                    "remain untouched. Timed and redacted traces are retained and never " +
                    "deleted or retried. No global WINEBOOTSTRAPMODE override is made. " +
                    "This is DIAGNOSTIC ONLY, not a game engine or a guaranteed fix. " +
                    "Do you explicitly authorize ONE v3 execution?")
                .setNegativeButton("Cancel — do not execute", null)
                .setPositiveButton("Authorize ONE new v3 test", (dialog, which) -> {
                    wine29V3Layout.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine29V3LayoutProbe.run(this);
                        runOnUiThread(() -> {
                            wine29V3Layout.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — Wine29 v3 layout diagnostic")
                                .setMessage(report)
                                .setPositiveButton("Copy report", (dlg, button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null)
                                        cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                            "Charoite Wine29 v3 matched PE directory report", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine29V3LayoutProbe").start();
                }).show());
        nextCoreCard.addView(wine29V3Layout);
        } // V3 one-shot execution archived after successful --help; preserved scratch untouched.
        // READ-ONLY examination of already preserved v3 evidence, no process execution.
        android.widget.Button wine29V3Forensics = new android.widget.Button(this);
        wine29V3Forensics.setText("Inspect preserved Wine29 v3 auto-init failure (read-only)");
        wine29V3Forensics.setAllCaps(false);
        wine29V3Forensics.setOnClickListener(v -> {
            wine29V3Forensics.setEnabled(false);
            new Thread(() -> {
                final String report =
                    com.charoitegames.core.CharoiteWine29V3AutoInitForensics.run(this);
                runOnUiThread(() -> {
                    wine29V3Forensics.setEnabled(true);
                    new android.app.AlertDialog.Builder(this)
                        .setTitle("Charoite Next — preserved Wine29 v3 auto-init postmortem")
                        .setMessage(report)
                        .setPositiveButton("Copy report", (dlg, button) -> {
                            android.content.ClipboardManager cb =
                                (android.content.ClipboardManager)
                                getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                            if (cb != null)
                                cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                    "Charoite Next Wine29 v3 READ-ONLY auto-init forensics", report));
                        })
                        .setNegativeButton("Close", null).show();
                });
            }, "CharoiteWine29V3AutoInitForensics").start();
        });
        nextCoreCard.addView(wine29V3Forensics);

        // Explicit, one-shot, NEW V4 experiment ONLY.
        // No process runs unless this separate confirmation is accepted.
        final boolean showArchivedWine29V4Execution = false;
        if (showArchivedWine29V4Execution) {
        android.widget.Button wine29V4DirectInit = new android.widget.Button(this);
        wine29V4DirectInit.setText("Wine29 v4 direct prefix initialization (one-shot)");
        wine29V4DirectInit.setAllCaps(false);
        wine29V4DirectInit.setOnClickListener(v ->
            new android.app.AlertDialog.Builder(this)
                .setTitle("Authorize ONE isolated Wine29 v4 prefix test?")
                .setMessage("EXPERIMENTAL: this executes the source-verified ARM64 Wine29 " +
                    "Wineboot.exe -i directly from its verified aarch64-windows directory, " +
                    "with a separate native wineserver. Wine may also attempt automatic " +
                    "--init internally and may create a new Windows prefix. The v4-only " +
                    "scratch is fresh, isolated and retained permanently. Hash gates " +
                    "must pass before creation; time and logs are bounded. This will " +
                    "NOT access or delete prior v1-v3 tests, stable Charoite Portal, " +
                    "installed games, saves, rootfs, user prefixes or other Wine slots. " +
                    "The test may fail; completion is NOT a gaming runtime claim. " +
                    "Do you explicitly authorize this ONE NEW v4 execution?")
                .setNegativeButton("Cancel — do not execute", null)
                .setPositiveButton("Authorize ONE new v4 -i test", (dialog, which) -> {
                    wine29V4DirectInit.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine29V4DirectInitProbe.run(this);
                        runOnUiThread(() -> {
                            wine29V4DirectInit.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — Wine29 v4 direct -i probe")
                                .setMessage(report)
                                .setPositiveButton("Copy report", (dlg, button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null)
                                        cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                            "Charoite Next Wine29 v4 direct -i diagnostic", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine29V4DirectInitProbe").start();
                }).show());
        nextCoreCard.addView(wine29V4DirectInit);

        } // v4 one-shot execution archived; old v4 scratch and reports retained.
        // V5 is archived after its owner-run one shot; retain source and scratch.
        final boolean showArchivedWine29V5Execution = false;
        if (showArchivedWine29V5Execution) {
        // Historical V5 owner-approved experiment. Never runs from startup.
        android.widget.Button wine29V5DriveC = new android.widget.Button(this);
        wine29V5DriveC.setText("Wine29 v5 isolated C: mapping test (one-shot)");
        wine29V5DriveC.setAllCaps(false);
        wine29V5DriveC.setOnClickListener(v ->
            new android.app.AlertDialog.Builder(this)
                .setTitle("Authorize ONE Wine29 v5 isolated C: test?")
                .setMessage("EXPERIMENTAL: Creates a NEW private Wine29 v5 scratch, " +
                    "preseeds ONLY empty drive_c and relative dosdevices/c: -> ../drive_c, " +
                    "then launches source-SHA-verified Wine29 foreground wineserver " +
                    "and ARM64 wineboot.exe -i from the already validated matched " +
                    "aarch64-windows PE directory. Wine may also auto-launch --init. " +
                    "This test will write the new private prefix, not older ones. " +
                    "The preseeded drive_c does NOT count as a successful Windows " +
                    "installation: only Windows-created subdirectories and registry " +
                    "files will be recorded separately. Logs/processes are bounded, " +
                    "and the one-shot scratch is retained without cleanup or retry. " +
                    "Wine29 v1-v4, Wine28, stable Portal, games, saves, rootfs " +
                    "and existing prefixes are NOT ACCESSED. It might fail and " +
                    "does NOT enable gaming. Authorize exactly ONE v5 execution?")
                .setNegativeButton("Cancel — do not execute", null)
                .setPositiveButton("Authorize ONE new v5 C: test", (dialog, which) -> {
                    wine29V5DriveC.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine29V5DriveCProbe.run(this);
                        runOnUiThread(() -> {
                            wine29V5DriveC.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — Wine29 v5 private C: mapping")
                                .setMessage(report)
                                .setPositiveButton("Copy report", (dlg, button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null)
                                        cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                            "Charoite Next Wine29 v5 isolated C: test", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine29V5DriveCProbe").start();
                }).show());
        nextCoreCard.addView(wine29V5DriveC);
        } // V5 one-shot archived; preserve existing v5 scratch and logs permanently.

        // Historical v6 execution is already completed, always archived.
        // Never show a repeatable button for used v6 scratch, even if the
        // underlying runnable source stays available for exact provenance.
        final boolean showArchivedWine29V6Execution = false;
        if (showArchivedWine29V6Execution) {
        // Historical v6 cohort is NOT a live game engine; once authorized exactly
        // one diagnostic in a NEW v6-only private prefix, after source/ELF gates.
        android.widget.Button wine29V6Child = new android.widget.Button(this);
        wine29V6Child.setText("Wine29 v6 native child-loader smoke (one-shot)");
        wine29V6Child.setAllCaps(false);
        wine29V6Child.setOnClickListener(v ->
            new android.app.AlertDialog.Builder(this)
                .setTitle("Authorize ONE NEW Wine29 v6 child-loader test?")
                .setMessage("This experimental diagnostic hash-verifies the signed APK-owned "
                    + "v6 native Wine loader, matching NTDLL and wineserver and all 111 "
                    + "existing sealed PE/NLS files. It then creates ONE completely NEW "
                    + "v6 private scratch and relative C: drive mapping. It starts the "
                    + "v6 native wineserver and ARM64 wineboot.exe -i. Wine may itself "
                    + "attempt automatic wineboot --init or spawn other initialization "
                    + "children in this NEW prefix. Execution and logs are time-capped, "
                    + "the new scratch is NEVER deleted/retried, and previous Wine29 "
                    + "v1-v5 scratch, Wine28, stable Portal, rootfs, games, saves, "
                    + "and user prefixes must NOT be accessed. A successful test is "
                    + "NOT proof of running Windows games. This will use private storage. "
                    + "Do you explicitly authorize exactly ONE v6 experiment?")
                .setNegativeButton("Cancel — do not execute", null)
                .setPositiveButton("Authorize ONE new v6 test", (dialog, which) -> {
                    wine29V6Child.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine29V6ChildLoaderProbe.run(this);
                        runOnUiThread(() -> {
                            wine29V6Child.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — v6 native child-loader smoke")
                                .setMessage(report)
                                .setPositiveButton("Copy report", (dlg, button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null)
                                        cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                            "Charoite Wine29 v6 child-loader diagnostics", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine29V6ChildLoaderProbe").start();
                }).show());
        nextCoreCard.addView(wine29V6Child);
        } // v6 execution archived. Previous v1-v6 scratch/logs are preserved.

        // CURRENT TEST: READ-ONLY postmortem of the owner's ALREADY completed
        // v6 one-shot. No Wine or process creation; no further authorization
        // or writes necessary. Limited to two named logs and file metadata.
        final boolean showArchivedWine29V6ReadOnly = false;
        if (showArchivedWine29V6ReadOnly) {
        android.widget.Button wine29V6Forensics = new android.widget.Button(this);
        wine29V6Forensics.setText("Inspect Wine29 v6 helper causal trace (read-only)");
        wine29V6Forensics.setAllCaps(false);
        wine29V6Forensics.setOnClickListener(v -> {
            wine29V6Forensics.setEnabled(false);
            new Thread(() -> {
                final String report =
                    com.charoitegames.core.CharoiteWine29V6ReadOnlyForensics.run(this);
                runOnUiThread(() -> {
                    wine29V6Forensics.setEnabled(true);
                    new android.app.AlertDialog.Builder(this)
                        .setTitle("Charoite Next — Wine29 v6 preserved process postmortem")
                        .setMessage(report)
                        .setPositiveButton("Copy report", (dlg, button) -> {
                            android.content.ClipboardManager cb =
                                (android.content.ClipboardManager)
                                getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                            if (cb != null)
                                cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                    "Charoite Wine29 v6 READ-ONLY postmortem", report));
                        })
                        .setNegativeButton("Close", null).show();
                });
            }, "CharoiteWine29V6ReadOnlyForensics").start();
        });
        nextCoreCard.addView(wine29V6Forensics);

        } // The v6 report remains in source but is hidden from current System.
        final boolean showArchivedWine29V7Execution = false;
        if (showArchivedWine29V7Execution) {
        android.widget.Button wine29V7Services = new android.widget.Button(this);
        wine29V7Services.setText("Test Wine29 v7 services.exe bootstrap (one-shot)");
        wine29V7Services.setAllCaps(false);
        wine29V7Services.setOnClickListener(v ->
            new android.app.AlertDialog.Builder(this)
                .setTitle("Authorize ONE new Wine29 v7 services.exe bootstrap?")
                .setMessage("This creates ONE NEW private v7 Wine prefix and executes "
                    + "the verified Wine29 native wineserver and Wineboot.exe -i. "
                    + "Wine may automatically start Windows services.exe and other "
                    + "initialization helpers. This is NOT read-only or a game test. "
                    + "The exact source-built ARM64 services.exe and 111 sealed Wine "
                    + "PE/NLS files are SHA-256 verified before any scratch is created. "
                    + "No previous v1–v6 scratch, user prefix, games, saves, rootfs "
                    + "or stable Charoite Portal is opened or changed; the new v7 "
                    + "scratch is retained, never cleared or retried. "
                    + "Authorize exactly ONE new v7 process experiment?")
                .setNegativeButton("Cancel — do not execute", null)
                .setPositiveButton("Authorize ONE v7 test", (dialog, which) -> {
                    wine29V7Services.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine29V7ServicesProbe.run(this);
                        runOnUiThread(() -> {
                            wine29V7Services.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — v7 services.exe bootstrap")
                                .setMessage(report)
                                .setPositiveButton("Copy report", (dlg, button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null)
                                        cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                            "Charoite Wine29 v7 services.exe report", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine29V7ServicesProbe").start();
                }).show());
        nextCoreCard.addView(wine29V7Services);

        } // v7 execution remains in source, but cannot be launched again.

        // Archived v7 audit is retained in code for provenance but no longer shown
        // as an active System control after the owner completed the read-only audit.
        final boolean showArchivedWine29V7ReadOnly = false;
        if (showArchivedWine29V7ReadOnly) {
        android.widget.Button wine29V7Audit = new android.widget.Button(this);
        wine29V7Audit.setText("Inspect Wine29 v7 DLL failure (read-only)");
        wine29V7Audit.setAllCaps(false);
        wine29V7Audit.setOnClickListener(v -> {
            wine29V7Audit.setEnabled(false);
            new Thread(() -> {
                final String report =
                    com.charoitegames.core.CharoiteWine29V7ReadOnlyForensics.run(this);
                runOnUiThread(() -> {
                    wine29V7Audit.setEnabled(true);
                    new android.app.AlertDialog.Builder(this)
                        .setTitle("Charoite Next — preserved v7 DLL failure audit")
                        .setMessage(report)
                        .setPositiveButton("Copy report", (dlg, which) -> {
                            android.content.ClipboardManager cb =
                                (android.content.ClipboardManager)
                                getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                            if (cb != null)
                                cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                    "Charoite Wine29 v7 READ-ONLY postmortem", report));
                        })
                        .setNegativeButton("Close", null).show();
                });
            }, "CharoiteWine29V7ReadOnlyForensics").start();
        });
        nextCoreCard.addView(wine29V7Audit);

        } // Completed preserved v7 read-only audit archived from System.

        // COMPLETED v8 execution remains available in source for provenance only.
        // Never expose or rerun the used v8 one-shot private prefix.
        final boolean showArchivedWine29V8Execution = false;
        if (showArchivedWine29V8Execution) {
        android.widget.Button wine29V8Userenv = new android.widget.Button(this);
        wine29V8Userenv.setText("Test Wine29 v8 userenv.dll services bootstrap (one-shot)");
        wine29V8Userenv.setAllCaps(false);
        wine29V8Userenv.setOnClickListener(v ->
            new android.app.AlertDialog.Builder(this)
                .setTitle("Authorize ONE new Wine29 v8 services bootstrap?")
                .setMessage("This is NOT read-only. Creates ONE NEW private v8 prefix "
                    + "and starts verified Wine29 wineserver and Wineboot -i. Wine "
                    + "may spawn services.exe, userenv.dll, and internal helper programs. "
                    + "This does NOT start games or install Windows apps. The new "
                    + "source-built userenv DLL, prior services.exe, original sealed "
                    + "111 PE/NLS and native executables are SHA-256 checked. "
                    + "Existing Wine29 v1–v7 scratch, stable Portal, games, saves, "
                    + "user prefixes and rootfs are NOT accessed, retried or cleaned. "
                    + "The new v8 scratch is retained after one use. "
                    + "Authorize exactly ONE new v8 process experiment?")
                .setNegativeButton("Cancel — do not execute", null)
                .setPositiveButton("Authorize ONE v8 test", (dialog, which) -> {
                    wine29V8Userenv.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine29V8UserenvProbe.run(this);
                        runOnUiThread(() -> {
                            wine29V8Userenv.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — v8 userenv + services bootstrap")
                                .setMessage(report)
                                .setPositiveButton("Copy report", (dlg, button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null)
                                        cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                            "Charoite Wine29 v8 userenv bootstrap report", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine29V8UserenvProbe").start();
                }).show());
        nextCoreCard.addView(wine29V8Userenv);
        } // Archived v8 execution; preserved v8 data is never retried or deleted.

        // ARCHIVED v8 read-only audit: completed and preserved; not current System test.
        final boolean showArchivedWine29V8ReadOnly = false;
        if (showArchivedWine29V8ReadOnly) {
        // Former read-only v8 audit; clipboard was a short
        // bounded summary and explicit END marker, never raw 600KB+ traces.
        android.widget.Button wine29V8Audit = new android.widget.Button(this);
        wine29V8Audit.setText("Inspect Wine29 v8 registry + services (read-only)");
        wine29V8Audit.setAllCaps(false);
        wine29V8Audit.setOnClickListener(v -> {
            wine29V8Audit.setEnabled(false);
            new Thread(() -> {
                final String report =
                    com.charoitegames.core.CharoiteWine29V8ReadOnlyForensics.run(this);
                runOnUiThread(() -> {
                    wine29V8Audit.setEnabled(true);
                    new android.app.AlertDialog.Builder(this)
                        .setTitle("Charoite Next — v8 registry and services read-only audit")
                        .setMessage(report)
                        .setPositiveButton("Copy short report", (dlg, button) -> {
                            android.content.ClipboardManager cb =
                                (android.content.ClipboardManager)
                                getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                            if (cb != null)
                                cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                    "Charoite Wine29 v8 SHORT READ-ONLY postmortem", report));
                        })
                        .setNegativeButton("Close", null).show();
                });
            }, "CharoiteWine29V8ReadOnlyForensics").start();
        });
        nextCoreCard.addView(wine29V8Audit);
        } // Do not rerun historical v8 audit from the current System UI.

        // Historical v9 execution: already used; NEVER allow retry from the current System screen.
        final boolean showArchivedWine29V9Execution = false;
        if (showArchivedWine29V9Execution) {
        // Historical Wine29 v9 one-shot, NEW v9 isolated scratch ONLY.
        android.widget.Button wine29V9Scm = new android.widget.Button(this);
        wine29V9Scm.setText("Test Wine29 v9 Service Manager query (one-shot)");
        wine29V9Scm.setAllCaps(false);
        wine29V9Scm.setOnClickListener(v ->
            new android.app.AlertDialog.Builder(this)
                .setTitle("Authorize ONE new Wine29 v9 SCM query?")
                .setMessage("This is NOT read-only. It will create a NEW independent "
                    + "private v9 prefix, start Wine29 wineserver and Wineboot -i, "
                    + "and, ONLY if the same private server remains alive after a "
                    + "successful Wineboot exit, start the verified Windows ARM64 "
                    + "sc.exe query client to test Service Control Manager reachability. "
                    + "Wine may also start services.exe and userenv.dll internally. "
                    + "Existing v8 and earlier scratch, stable Charoite Portal, "
                    + "games, saves, rootfs, user prefixes and app settings will NOT "
                    + "be read, rerun, deleted or reset. The new v9 scratch and "
                    + "three logs are preserved after this single attempt. "
                    + "No Windows games or applications are installed or launched. "
                    + "A second tap cannot retry a used v9 scratch.")
                .setNegativeButton("Cancel — do not execute",null)
                .setPositiveButton("Authorize ONE v9 query", (dialog,which) -> {
                    wine29V9Scm.setEnabled(false);
                    new Thread(() -> {
                        final String report = com.charoitegames.core.CharoiteWine29V9ScmProbe.run(this);
                        runOnUiThread(() -> {
                            wine29V9Scm.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — Wine29 v9 SCM query report")
                                .setMessage(report)
                                .setPositiveButton("Copy short report", (dlg,button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if(cb!=null) cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                        "Charoite Wine29 v9 one-shot SCM query",report));
                                })
                                .setNegativeButton("Close",null).show();
                        });
                    }, "CharoiteWine29V9ScmProbe").start();
                }).show());
        nextCoreCard.addView(wine29V9Scm);
        } // Executing v9 a second time is forbidden.

        // The owner completed the V9 read-only audit. Keep source for provenance,
        // but do not clutter the active System screen or expose archived actions.
        final boolean showArchivedWine29V9ReadOnly = false;
        if (showArchivedWine29V9ReadOnly) {
        android.widget.Button wine29V9Audit = new android.widget.Button(this);
        wine29V9Audit.setText("Inspect Wine29 v9 SCM failure (read-only)");
        wine29V9Audit.setAllCaps(false);
        wine29V9Audit.setOnClickListener(v -> {
            wine29V9Audit.setEnabled(false);
            new Thread(() -> {
                final String report = com.charoitegames.core.CharoiteWine29V9ReadOnlyForensics.run(this);
                runOnUiThread(() -> {
                    wine29V9Audit.setEnabled(true);
                    new android.app.AlertDialog.Builder(this)
                        .setTitle("Charoite Next — Wine29 v9 preserved SCM audit")
                        .setMessage(report)
                        .setPositiveButton("Copy short report", (dlg,button) -> {
                            android.content.ClipboardManager cb =
                                (android.content.ClipboardManager)
                                getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                            if(cb!=null)cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                "Charoite Wine29 v9 preserved SCM audit",report));
                        })
                        .setNegativeButton("Close",null).show();
                });
            }, "CharoiteWine29V9ReadOnlyForensics").start();
        });
        nextCoreCard.addView(wine29V9Audit);
        } // V9 read-only inspection complete; V9 scratch must remain untouched.

        // V10 one-shot has been consumed; keep code for provenance only.
        final boolean showArchivedWine29V10Execution = false;
        if (showArchivedWine29V10Execution) {
        // ARCHIVED: the one-shot V10 boundary
        // diagnostic, not a repeated V9 SCM query. It is never automatic.
        android.widget.Button wine29V10Entry = new android.widget.Button(this);
        wine29V10Entry.setText("Test Wine29 v10 sc.exe PE entry (one-shot)");
        wine29V10Entry.setAllCaps(false);
        wine29V10Entry.setOnClickListener(v ->
            new android.app.AlertDialog.Builder(this)
                .setTitle("Authorize ONE fresh Wine29 v10 PE-entry diagnostic?")
                .setMessage("NOT read-only. This test first SHA-256 verifies the existing "
                    + "source-pinned Wine29 native/PE/NLS assets. It creates exactly "
                    + "ONE NEW private v10 scratch and C: prefix, starts native "
                    + "Wine29 wineserver and Wineboot -i (Wine may spawn services.exe "
                    + "and other Windows bootstrap helpers), then if successful "
                    + "checks native Wine loader --version and starts the verified "
                    + "ARM64 sc.exe with NO arguments to test whether its PE entry "
                    + "is reached. NO SCM query, games, Windows apps, or installations. "
                    + "V9 and all earlier Wine29/Wine28 scratch, stable Charoite Portal, "
                    + "rootfs, existing user prefixes, games and saves are NOT "
                    + "accessed or changed. New V10 logs are retained after this "
                    + "single attempt, with bounded time and output. No retry of "
                    + "an already-used V10 scratch is allowed. This is independent "
                    + "authorization for ONE V10 experiment.")
                .setNegativeButton("Cancel — do not execute",null)
                .setPositiveButton("Authorize ONE fresh v10 test", (dialog,which) -> {
                    wine29V10Entry.setEnabled(false);
                    new Thread(() -> {
                        final String report = com.charoitegames.core.CharoiteWine29V10EntryProbe.run(this);
                        runOnUiThread(() -> {
                            wine29V10Entry.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — v10 native / PE entry")
                                .setMessage(report)
                                .setPositiveButton("Copy short report", (dlg,button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                        getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if(cb!=null) cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                        "Charoite Wine29 v10 PE-entry report",report));
                                })
                                .setNegativeButton("Close",null).show();
                        });
                    }, "CharoiteWine29V10EntryProbe").start();
                }).show());
        nextCoreCard.addView(wine29V10Entry);
        } // V10 execution never repeated. Retained v10 scratch is immutable.

        // Archived V10 read-only report; consumed V10 scratch untouched by V11.
        final boolean showArchivedWine29V10ReadOnly = false;
        if (showArchivedWine29V10ReadOnly) {
        // Archived Wine29 diagnostic: strictly READ ONLY on fixed V10 logs.
        android.widget.Button wine29V10Audit = new android.widget.Button(this);
        wine29V10Audit.setText("Inspect Wine29 v10 native loader failure (read-only)");
        wine29V10Audit.setAllCaps(false);
        wine29V10Audit.setOnClickListener(v -> {
            wine29V10Audit.setEnabled(false);
            new Thread(() -> {
                final String report = com.charoitegames.core.CharoiteWine29V10ReadOnlyForensics.run(this);
                runOnUiThread(() -> {
                    wine29V10Audit.setEnabled(true);
                    new android.app.AlertDialog.Builder(this)
                        .setTitle("Charoite Next — V10 preserved native loader audit")
                        .setMessage(report)
                        .setPositiveButton("Copy short report", (dlg,which) -> {
                            android.content.ClipboardManager cb =
                                (android.content.ClipboardManager)
                                getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                            if(cb!=null)cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                "Charoite Wine29 v10 read-only audit",report));
                        })
                        .setNegativeButton("Close",null).show();
                });
            }, "CharoiteWine29V10ReadOnlyForensics").start();
        });
        nextCoreCard.addView(wine29V10Audit);
        } // All V10 actions are archived after the preserved report was supplied.

        // Archived: V11 already ran once on the owner's device. NEVER run it again.
        final boolean showArchivedWine29V11Execution = false;
        if (showArchivedWine29V11Execution) {
        // Historical V11 one-shot action is retained only in unreachable source.
        // V11 scratch must remain untouched except for the allowlisted read-only audit.
        android.widget.Button wine29V11Entry = new android.widget.Button(this);
        wine29V11Entry.setText("Test Wine29 v11 native version + sc.exe entry (one-shot)");
        wine29V11Entry.setAllCaps(false);
        wine29V11Entry.setOnClickListener(v ->
            new android.app.AlertDialog.Builder(this)
                .setTitle("Authorize ONE fresh Wine29 v11 isolated diagnostic?")
                .setMessage("NOT read-only. This test first verifies source-pinned "
                    + "Wine29 assets and creates a new private V11 scratch and C: "
                    + "prefix. It may launch Wine, Wineboot -i, wineserver and internal "
                    + "Windows service helpers in the new prefix. It compares two "
                    + "native Wine --version checks (WINELOADERNOEXEC set and unset) "
                    + "and then independently attempts ARM64 sc.exe with NO arguments "
                    + "to look for a PE entry/usage response. There is NO SCM query, "
                    + "game, installer or Windows application. V1-V10/Wine28 scratch, "
                    + "stable Charoite Portal, user prefixes, games, saves and rootfs "
                    + "are not accessed. V11 is a SINGLE attempt: never repeat it "
                    + "or delete its scratch if an attempt has started. "
                    + "Existing app data is preserved; no background execution.")
                .setNegativeButton("Cancel — do not execute",null)
                .setPositiveButton("Authorize ONE fresh v11 test", (dialog,which) -> {
                    wine29V11Entry.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine29V11EntryProbe.run(this);
                        runOnUiThread(() -> {
                            wine29V11Entry.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — V11 native command gate")
                                .setMessage(report)
                                .setPositiveButton("Copy short report", (dlg,button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                            getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if(cb!=null)cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                        "Charoite Wine29 v11 one-shot report",report));
                                })
                                .setNegativeButton("Close",null).show();
                        });
                    }, "CharoiteWine29V11EntryProbe").start();
                }).show());
        nextCoreCard.addView(wine29V11Entry);
        } // V11 execution retired permanently after first use.

        // Historical preserved V11 postmortem: archived from live System actions.
        // The five fixed V11 logs and metadata remain untouched.
        final boolean showArchivedWine29V11ReadOnly = false;
        if (showArchivedWine29V11ReadOnly) {
        android.widget.Button wine29V11Audit = new android.widget.Button(this);
        wine29V11Audit.setText("Inspect Wine29 v11 server exit (read-only)");
        wine29V11Audit.setAllCaps(false);
        wine29V11Audit.setOnClickListener(v -> {
            wine29V11Audit.setEnabled(false);
            new Thread(() -> {
                final String report =
                    com.charoitegames.core.CharoiteWine29V11ReadOnlyForensics.run(this);
                runOnUiThread(() -> {
                    wine29V11Audit.setEnabled(true);
                    new android.app.AlertDialog.Builder(this)
                        .setTitle("Charoite Next — V11 preserved lifecycle audit")
                        .setMessage(report)
                        .setPositiveButton("Copy short report", (dlg,which) -> {
                            android.content.ClipboardManager cb =
                                (android.content.ClipboardManager)
                                    getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                            if (cb!=null) cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                "Charoite Wine29 v11 read-only report",report));
                        })
                        .setNegativeButton("Close",null).show();
                });
            }, "CharoiteWine29V11ReadOnlyForensics").start();
        });
        nextCoreCard.addView(wine29V11Audit);
        } // V11 read-only evidence consumed: do not clutter the current System tab.

        // V12 one-shot execution is completed and permanently archived.
        final boolean showArchivedWine29V12Execution = false;
        if (showArchivedWine29V12Execution) {
        // Sole active Wine29 diagnostic. The user must authorize one NEW V12
        // scratch/prefix explicitly; repeated execution is blocked by the runner.
        android.widget.Button wine29V12Entry = new android.widget.Button(this);
        wine29V12Entry.setText("Test Wine29 v12 sc.exe PE entry (one-shot)");
        wine29V12Entry.setAllCaps(false);
        wine29V12Entry.setOnClickListener(v ->
            new android.app.AlertDialog.Builder(this)
                .setTitle("Authorize ONE fresh Wine29 v12 PE-entry diagnostic?")
                .setMessage("NOT read-only. This is a ONE-SHOT experimental Wine test, "
                    + "limited to a brand-new private V12 scratch and prefix. "
                    + "It verifies source-pinned Wine modules, then may execute the "
                    + "private foreground wineserver, ARM64 Wineboot -i and internal "
                    + "Windows helpers, followed by exactly one no-argument ARM64 "
                    + "sc.exe PE-entry test while checking foreground server liveness. "
                    + "No native --version checks, no SCM query or service control, "
                    + "no games, installers, Steam, Battle.net or graphics. "
                    + "Stable Charoite Portal, existing user prefixes, games, saves, "
                    + "rootfs, Wine28 and Wine29 V1-V11 scratch are not accessed. "
                    + "If V12 scratch already exists, this test is BLOCKED; never "
                    + "retry, delete or clear any scratch or app data. "
                    + "Raw bounded logs remain private on this phone.")
                .setNegativeButton("Cancel — do not execute", null)
                .setPositiveButton("Authorize ONE fresh v12 test", (dialog,which) -> {
                    wine29V12Entry.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine29V12ScEntryProbe.run(this);
                        runOnUiThread(() -> {
                            wine29V12Entry.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — V12 first sc.exe PE entry")
                                .setMessage(report)
                                .setPositiveButton("Copy short report", (dlg,button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                            getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb!=null) cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                        "Charoite Wine29 v12 one-shot report",report));
                                })
                                .setNegativeButton("Close",null).show();
                        });
                    }, "CharoiteWine29V12ScEntryProbe").start();
                }).show());
        nextCoreCard.addView(wine29V12Entry);
        } // V12 execution permanently retired. Never rerun or delete scratch.

        // Owner completed V12 preserved report; keep its inspector archived.
        final boolean showArchivedWine29V12ReadOnly = false;
        if (showArchivedWine29V12ReadOnly) {
        android.widget.Button wine29V12Audit = new android.widget.Button(this);
        wine29V12Audit.setText("Inspect Wine29 v12 sc.exe exit (read-only)");
        wine29V12Audit.setAllCaps(false);
        wine29V12Audit.setOnClickListener(v -> {
            wine29V12Audit.setEnabled(false);
            new Thread(() -> {
                final String report =
                    com.charoitegames.core.CharoiteWine29V12ReadOnlyForensics.run(this);
                runOnUiThread(() -> {
                    wine29V12Audit.setEnabled(true);
                    new android.app.AlertDialog.Builder(this)
                        .setTitle("Charoite Next — V12 preserved PE-entry audit")
                        .setMessage(report)
                        .setPositiveButton("Copy short report", (dlg,which) -> {
                            android.content.ClipboardManager cb =
                                (android.content.ClipboardManager)
                                    getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                            if (cb != null) cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                "Charoite Wine29 v12 read-only report", report));
                        })
                        .setNegativeButton("Close",null).show();
                });
            }, "CharoiteWine29V12ReadOnlyForensics").start();
        });
        nextCoreCard.addView(wine29V12Audit);

        } // V12 read-only inspector archived, all V12 data untouched.

        // V13 executed once on the owner device; archive its execution permanently.
        final boolean showArchivedWine29V13Execution = false;
        if (showArchivedWine29V13Execution) {
        android.widget.Button wine29V13Entry = new android.widget.Button(this);
        wine29V13Entry.setText("Test Wine29 v13 sc.exe loader handoff (one-shot)");
        wine29V13Entry.setAllCaps(false);
        wine29V13Entry.setOnClickListener(v ->
            new android.app.AlertDialog.Builder(this)
                .setTitle("Authorize ONE fresh Wine29 v13 sc.exe loader diagnostic?")
                .setMessage("NOT read-only. This stages only a NEW private V13 scratch, "
                    + "starts a bounded Wineboot -i with internal helpers, then one "
                    + "NO-ARGUMENT ARM64 sc.exe. WINELOADERNOEXEC is UNSET ONLY for "
                    + "sc.exe; Wineboot and the private server keep the V12 setting. "
                    + "No native version probe, SCM query/service changes, game, "
                    + "installer, Steam, Battle.net or graphics. Raw bounded logs "
                    + "remain on the phone. Prior V1-V12 and Wine28 scratch, stable "
                    + "Portal, rootfs, existing prefixes, games and saves are never "
                    + "accessed. An existing V13 scratch blocks retries. Never "
                    + "uninstall, clear data or delete any scratch.")
                .setNegativeButton("Cancel — do not execute", null)
                .setPositiveButton("Authorize ONE fresh v13 test", (dialog, which) -> {
                    wine29V13Entry.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine29V13ScNoexecProbe.run(this);
                        runOnUiThread(() -> {
                            wine29V13Entry.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — V13 sc.exe loader handoff")
                                .setMessage(report)
                                .setPositiveButton("Copy short report", (dlg, button) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                            getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null) cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                        "Charoite Wine29 v13 one-shot report", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine29V13ScNoexecProbe").start();
                }).show());
        nextCoreCard.addView(wine29V13Entry);

        } // V13 execution consumed; do not rerun or clear scratch.
        // V13 preserved forensic report was supplied; keep inspector archived.
        final boolean showArchivedWine29V13ReadOnly = false;
        if (showArchivedWine29V13ReadOnly) {
        // Archived Wine29 System diagnostic: preserved V13 evidence, READ ONLY.
        android.widget.Button wine29V13Audit = new android.widget.Button(this);
        wine29V13Audit.setText("Inspect Wine29 v13 sc.exe exit (read-only)");
        wine29V13Audit.setAllCaps(false);
        wine29V13Audit.setOnClickListener(v -> {
            wine29V13Audit.setEnabled(false);
            new Thread(() -> {
                final String report = com.charoitegames.core.CharoiteWine29V13ReadOnlyForensics.run(this);
                runOnUiThread(() -> {
                    wine29V13Audit.setEnabled(true);
                    new android.app.AlertDialog.Builder(this)
                        .setTitle("Charoite Next — V13 preserved sc.exe audit")
                        .setMessage(report)
                        .setPositiveButton("Copy short report", (dlg, button) -> {
                            android.content.ClipboardManager cb =
                                (android.content.ClipboardManager)
                                    getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                            if (cb != null) cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                "Charoite Wine29 V13 read-only report", report));
                        })
                        .setNegativeButton("Close", null).show();
                });
            }, "CharoiteWine29V13ReadOnlyForensics").start();
        });
        nextCoreCard.addView(wine29V13Audit);
        } // V13 read-only audit completed; scratch never modified.




        // Archived one-shot V14 execution: owner has consumed this private scratch.
        // Do not expose any way to replay it after the preserved V14 report.
        final boolean showArchivedWine29V14Execution = false;
        if (showArchivedWine29V14Execution) {
        android.widget.Button wine29V14WindowsPath = new android.widget.Button(this);
        wine29V14WindowsPath.setText("Test Wine29 v14 sc.exe Windows C: path (one-shot)");
        wine29V14WindowsPath.setAllCaps(false);
        wine29V14WindowsPath.setOnClickListener(v ->
            new android.app.AlertDialog.Builder(this)
                .setTitle("Authorize ONE new private Wine29 v14 Windows-path test?")
                .setMessage("NOT read-only. In a completely NEW v14 private scratch, verify "
                    + "the source-pinned Wine29 modules, launch bounded Wineboot -i "
                    + "and its internal helpers/private wineserver, then copy the "
                    + "same verified ARM64 sc.exe ONLY into newly created private "
                    + "C:\\\\windows\\\\system32 and attempt ONE no-argument sc.exe "
                    + "using that Windows C: path (instead of V13's Unix path). "
                    + "Keep V13's NOEXEC-unset sc.exe environment. NO SCM query, "
                    + "service change, games, Steam/Battle.net or native --version. "
                    + "V1-V13 scratch, Wine28, stable Portal, rootfs, user prefixes, "
                    + "games/saves are NEVER accessed. If v14 scratch already exists, "
                    + "the test is blocked. Never uninstall/clear data or delete scratch.")
                .setNegativeButton("Cancel — do not execute", null)
                .setPositiveButton("Authorize ONE fresh v14 test", (dialog, which) -> {
                    wine29V14WindowsPath.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine29V14ScWindowsPathProbe.run(this);
                        runOnUiThread(() -> {
                            wine29V14WindowsPath.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — V14 Windows-path sc.exe diagnostic")
                                .setMessage(report)
                                .setPositiveButton("Copy short report", (dlg, btn) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                            getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null) cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                        "Charoite Wine29 V14 one-shot report", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine29V14ScWindowsPathProbe").start();
                }).show());
        nextCoreCard.addView(wine29V14WindowsPath);

        } // V14 execution permanently consumed; no rerun or cleanup.
        // V14 read-only audit is completed; keep historical code, retire its button.
        final boolean showArchivedWine29V14ReadOnly = false;
        if (showArchivedWine29V14ReadOnly) {
        // Only ACTIVE Wine29 System diagnostic: V14 preserved logs and named metadata.
        // Read-only: no process or Wine execution; never creates new scratch or follows C:.
        android.widget.Button wine29V14Audit = new android.widget.Button(this);
        wine29V14Audit.setText("Inspect Wine29 v14 sc.exe exit (read-only)");
        wine29V14Audit.setAllCaps(false);
        wine29V14Audit.setOnClickListener(v -> {
            wine29V14Audit.setEnabled(false);
            new Thread(() -> {
                final String report =
                    com.charoitegames.core.CharoiteWine29V14ReadOnlyForensics.run(this);
                runOnUiThread(() -> {
                    wine29V14Audit.setEnabled(true);
                    new android.app.AlertDialog.Builder(this)
                        .setTitle("Charoite Next — V14 preserved sc.exe exit 127")
                        .setMessage(report)
                        .setPositiveButton("Copy short report", (dlg, btn) -> {
                            android.content.ClipboardManager cb =
                                (android.content.ClipboardManager)
                                    getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                            if (cb != null) cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                "Charoite Wine29 V14 preserved read-only report", report));
                        })
                        .setNegativeButton("Close", null).show();
                });
            }, "CharoiteWine29V14ReadOnlyForensics").start();
        });
        nextCoreCard.addView(wine29V14Audit);
        } // Preserved V14 audit consumed; NO V14 replay, scan, or cleanup.

        // The V15 one-shot has been consumed on the owner device. Permanently hide it.
        final boolean showArchivedWine29V15Execution = false;
        if (showArchivedWine29V15Execution) {
        // Archived Wine29 test: fresh V15 one-shot, explicit opt-in.
        android.widget.Button wine29V15Entry = new android.widget.Button(this);
        wine29V15Entry.setText("Test Wine29 v15 Windows sc.exe + NOEXEC=1 (one-shot)");
        wine29V15Entry.setAllCaps(false);
        wine29V15Entry.setOnClickListener(v ->
            new android.app.AlertDialog.Builder(this)
                .setTitle("Authorize ONE fresh Wine29 v15 private diagnostic?")
                .setMessage("NOT read-only. This creates ONLY a NEW v15 private scratch "
                    + "after source/hash preflight, may run bounded Wineboot, services.exe, "
                    + "wineserver and ONE no-argument sc.exe launch. It retains V14's "
                    + "private Windows C: system32 sc.exe location but changes only "
                    + "the sc.exe launch variable WINELOADERNOEXEC to 1. "
                    + "NO SCM query, service commands, games, installers, Steam or "
                    + "Battle.net. Existing V1-V14/Wine28 scratch, stable Portal, "
                    + "games, saves, prefixes and rootfs are NOT accessed. If v15 "
                    + "scratch already exists, refuse execution. Never uninstall, "
                    + "clear data, rerun or delete used V15 scratch.")
                .setNegativeButton("Cancel — do not execute", null)
                .setPositiveButton("Authorize ONE fresh v15 test", (dialog, which) -> {
                    wine29V15Entry.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine29V15ScWindowsNoexecProbe.run(this);
                        runOnUiThread(() -> {
                            wine29V15Entry.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — V15 Windows sc.exe NOEXEC diagnostic")
                                .setMessage(report)
                                .setPositiveButton("Copy short report", (dlg, btn) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                            getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null) cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                        "Charoite Wine29 V15 one-shot report", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine29V15ScWindowsNoexecProbe").start();
                }).show());
        nextCoreCard.addView(wine29V15Entry);
        } // V15 consumed: no replay, cleanup or write actions.

        // Archived V15 read-only copy: owner already supplied the complete audit.
        // Keep implementation for source provenance but hide completed action.
        final boolean showArchivedWine29V15ReadOnly = false;
        if (showArchivedWine29V15ReadOnly) {
        // Sole ACTIVE Wine29 diagnostic: V15 preserved evidence, STRICT READ ONLY.
        // Keep instructions, the actual test button, and the handoff link together
        // within System; never force the owner to search another tab for steps.
        LinearLayout wine29CurrentAction = card();
        wine29CurrentAction.addView(label("CURRENT WINE29 ACTION — V15 READ-ONLY",
                16, FOREGROUND, true));
        wine29CurrentAction.addView(label(
                "V15 execution and its preserved audit are COMPLETE. No further V15 " +
                "execution is authorized. The independent Windows sc.exe attempt " +
                "returned 127 with no output; PE entry, SCM and root cause remain " +
                "unverified. To re-copy the existing evidence for a new chat ONLY: " +
                "tap Inspect, then Copy short report. The handoff link is the " +
                "FIRST line of the copied report. This inspection reads three " +
                "existing V15 logs and named metadata ONLY: no Wine execution, " +
                "retry, scratch changes or cleanup. Preserve all old prefixes, " +
                "games and saves. A NEW V16 test is not yet authorized or available.",
                12, SECONDARY, false));
        android.widget.Button wine29V15Audit = new android.widget.Button(this);
        wine29V15Audit.setText("Inspect Wine29 v15 sc.exe + server (read-only)");
        wine29V15Audit.setAllCaps(false);
        wine29V15Audit.setOnClickListener(v -> {
            wine29V15Audit.setEnabled(false);
            new Thread(() -> {
                final String report =
                    com.charoitegames.core.CharoiteWine29V15ReadOnlyForensics.run(this);
                runOnUiThread(() -> {
                    wine29V15Audit.setEnabled(true);
                    new android.app.AlertDialog.Builder(this)
                        .setTitle("Charoite Next — V15 preserved exit 127 / server audit")
                        .setMessage(report)
                        .setPositiveButton("Copy short report", (dlg, btn) -> {
                            android.content.ClipboardManager cb =
                                (android.content.ClipboardManager)
                                    getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                            if (cb != null) cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                "Charoite Wine29 V15 read-only report", report));
                        })
                        .setNegativeButton("Close", null).show();
                });
            }, "CharoiteWine29V15ReadOnlyForensics").start();
        });
        wine29CurrentAction.addView(wine29V15Audit);
        android.widget.Button handoffButton = new android.widget.Button(this);
        handoffButton.setText("Open current project handoff");
        handoffButton.setAllCaps(false);
        handoffButton.setOnClickListener(v -> startActivity(new android.content.Intent(
                android.content.Intent.ACTION_VIEW,
                android.net.Uri.parse("https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md"))));
        wine29CurrentAction.addView(handoffButton);
        nextCoreCard.addView(wine29CurrentAction);
        } // V15 inspected and retired; no UI routes to consumed data.

        // Current one-shot V16: instructions, opt-in, report copy, and handoff
        // button are adjacent under System. Never auto-execute on opening app.
        final boolean showArchivedWine29V16Execution = false;
        if (showArchivedWine29V16Execution) {
        LinearLayout wine29V16Action = card();
        wine29V16Action.addView(label("CURRENT WINE29 ACTION — V16 NATIVE EXEC BOUNDARY",
                16, FOREGROUND, true));
        wine29V16Action.addView(label(
                "NEW PRIVATE V16 ONLY. This is NOT read-only: after a separate " +
                "confirmation it creates one new V16 scratch/prefix and can run " +
                "private wineserver, Wineboot and internal services, followed by " +
                "ONE no-argument Windows C: sc.exe launch with NOEXEC=1. No SCM " +
                "query, games, installers, or network. Logs separately capture " +
                "Android native process launch acceptance/failure, timing, " +
                "process exit, and wineserver state. These do NOT prove PE mapping " +
                "or cause of exit 127. Old V1–V15 and Wine28 scratch, stable Portal, " +
                "user prefixes, saves and games are never accessed. If V16 exists, " +
                "the test refuses to run again. Never uninstall, clear storage, " +
                "retry or delete old evidence. TO RUN: tap the test, read the full " +
                "consent, choose Authorize ONE fresh v16 test, then Copy short " +
                "report through END marker into your next chat. The handoff URL " +
                "is on the FIRST line of that report.",
                12, SECONDARY, false));
        android.widget.Button wine29V16Exec = new android.widget.Button(this);
        wine29V16Exec.setText("Test Wine29 v16 sc.exe native boundary (one-shot)");
        wine29V16Exec.setAllCaps(false);
        wine29V16Exec.setOnClickListener(v ->
            new android.app.AlertDialog.Builder(this)
                .setTitle("Authorize ONE new private V16 exec-boundary test?")
                .setMessage("THIS EXECUTES WINE: creates exactly one NEW V16 private " +
                    "scratch/prefix, starts a bounded foreground wineserver and " +
                    "Wineboot/internal services, and attempts ONE no-argument " +
                    "Windows C:\\\\windows\\\\system32\\\\sc.exe entry with NOEXEC=1. " +
                    "Independent Android process-start and exit observations are " +
                    "recorded; a native launch is NOT proof of Windows PE entry " +
                    "or SCM. The test performs no service query or game launch. " +
                    "All V1–V15/Wine28 previous scratch, stable Portal, existing " +
                    "user prefixes, saves, games and rootfs remain untouched. " +
                    "If V16 scratch already exists, execution is blocked. " +
                    "No retry, cleanup, uninstall or data clear. Do you explicitly " +
                    "authorize this ONE V16 execution test?")
                .setNegativeButton("Cancel — do not execute", null)
                .setPositiveButton("Authorize ONE fresh v16 test", (dialog, which) -> {
                    wine29V16Exec.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine29V16ExecBoundaryProbe.run(this);
                        runOnUiThread(() -> {
                            wine29V16Exec.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — V16 native exec boundary")
                                .setMessage(report)
                                .setPositiveButton("Copy short report", (dlg, btn) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                            getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null) cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                        "Charoite Wine29 V16 native exec boundary", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine29V16ExecBoundaryProbe").start();
                }).show());
        wine29V16Action.addView(wine29V16Exec);
        android.widget.Button v16HandoffButton = new android.widget.Button(this);
        v16HandoffButton.setText("Open current project handoff");
        v16HandoffButton.setAllCaps(false);
        v16HandoffButton.setOnClickListener(v -> startActivity(new android.content.Intent(
                android.content.Intent.ACTION_VIEW,
                android.net.Uri.parse("https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md"))));
        wine29V16Action.addView(v16HandoffButton);
        nextCoreCard.addView(wine29V16Action);
        } // Consumed V16: original execution action permanently hidden.
        final boolean showArchivedWine29V16ReadOnly = false;
        if (showArchivedWine29V16ReadOnly) {
        LinearLayout wine29V16ReadOnlyAction = card();
        wine29V16ReadOnlyAction.addView(label("CURRENT WINE29 ACTION — V16 PRESERVED READ-ONLY", 16, FOREGROUND, true));
        wine29V16ReadOnlyAction.addView(label(
                "V16 one-shot execution has completed and must NEVER be repeated. " +
                "Android accepted the native loader, but independent Windows sc.exe " +
                "exited 127 with no output; the foreground server stopped and PE mapping " +
                "and SCM remain UNVERIFIED. TO ACT: tap the read-only inspection button, " +
                "then Copy short report into your next chat. The first report line is " +
                "the handoff URL. This only reads three preserved V16 logs and named " +
                "V16 metadata. No Wine, process creation, retries, cleanup, other " +
                "generations, registry contents, games, saves or app-data clearing.",
                12, SECONDARY, false));
        android.widget.Button wine29V16ReadOnly = new android.widget.Button(this);
        wine29V16ReadOnly.setText("Inspect Wine29 v16 sc.exe + server (read-only)");
        wine29V16ReadOnly.setAllCaps(false);
        wine29V16ReadOnly.setOnClickListener(v -> {
            wine29V16ReadOnly.setEnabled(false);
            new Thread(() -> {
                final String report = com.charoitegames.core.CharoiteWine29V16ReadOnlyForensics.run(this);
                runOnUiThread(() -> {
                    wine29V16ReadOnly.setEnabled(true);
                    new android.app.AlertDialog.Builder(this)
                        .setTitle("Charoite Next — V16 preserved native boundary audit")
                        .setMessage(report)
                        .setPositiveButton("Copy short report", (dlg, btn) -> {
                            android.content.ClipboardManager cb = (android.content.ClipboardManager)
                                getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                            if (cb != null) cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                "Charoite Wine29 V16 preserved read-only report", report));
                        })
                        .setNegativeButton("Close", null).show();
                });
            }, "CharoiteWine29V16ReadOnlyForensics").start();
        });
        wine29V16ReadOnlyAction.addView(wine29V16ReadOnly);
        android.widget.Button v16ReadOnlyHandoff = new android.widget.Button(this);
        v16ReadOnlyHandoff.setText("Open current project handoff");
        v16ReadOnlyHandoff.setAllCaps(false);
        v16ReadOnlyHandoff.setOnClickListener(v -> startActivity(new android.content.Intent(
                android.content.Intent.ACTION_VIEW,
                android.net.Uri.parse("https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md"))));
        wine29V16ReadOnlyAction.addView(v16ReadOnlyHandoff);
        nextCoreCard.addView(wine29V16ReadOnlyAction);
        } // Read-only V16 audit retired from System; evidence retained unchanged.

        // V17 one-shot is consumed, no re-execution route.
        final boolean showArchivedWine29V17Execution = false;
        if (showArchivedWine29V17Execution) {
        // Archived new-generation action; independent, fresh one-shot V17 only.
        LinearLayout wine29V17Action = card();
        wine29V17Action.addView(label("CURRENT WINE29 ACTION — V17 CONTROL COMPARISON",
                16, FOREGROUND, true));
        wine29V17Action.addView(label(
                "NEW PRIVATE V17 ONLY. This is NOT read-only: after a separate " +
                "confirmation it creates one new V17 scratch/prefix and can run " +
                "private wineserver, Wineboot and internal services, then ONE " +
                "independent Wineboot.exe --help positive control, followed by " +
                "ONE no-argument Windows C: sc.exe launch with NOEXEC=1. No SCM " +
                "query, games, installers, or network. Logs separately capture " +
                "two independent Android native launches, timing, distinct exits " +
                "and wineserver state. If the control shuts down the server, " +
                "sc.exe will NOT launch. These do NOT prove PE mapping " +
                "or cause of exit 127. Old V1–V16 and Wine28 scratch, stable Portal, " +
                "user prefixes, saves and games are never accessed. If V17 exists, " +
                "the test refuses to run again. Never uninstall, clear storage, " +
                "retry or delete old evidence. TO RUN: tap the test, read the full " +
                "consent, choose Authorize ONE fresh v17 test, then Copy short " +
                "report through END marker into your next chat. The handoff URL " +
                "is on the FIRST line of that report.",
                12, SECONDARY, false));
        android.widget.Button wine29V17Exec = new android.widget.Button(this);
        wine29V17Exec.setText("Test Wine29 v17 control vs sc.exe (one-shot)");
        wine29V17Exec.setAllCaps(false);
        wine29V17Exec.setOnClickListener(v ->
            new android.app.AlertDialog.Builder(this)
                .setTitle("Authorize ONE new private V17 exec-boundary test?")
                .setMessage("THIS EXECUTES WINE: creates exactly one NEW V17 private " +
                    "scratch/prefix, starts a bounded foreground wineserver and " +
                    "Wineboot/internal services, then independently runs ONE verified " +
                    "Wineboot.exe --help positive control followed by ONE no-argument " +
                    "Windows C:\\\\windows\\\\system32\\\\sc.exe entry with NOEXEC=1. " +
                    "Independent Android process-start and exit observations are " +
                    "recorded; a native launch is NOT proof of Windows PE entry " +
                    "or SCM. The test performs no service query or game launch. " +
                    "All V1–V16/Wine28 previous scratch, stable Portal, existing " +
                    "user prefixes, saves, games and rootfs remain untouched. " +
                    "If V17 scratch already exists, execution is blocked. " +
                    "No retry, cleanup, uninstall or data clear. Do you explicitly " +
                    "authorize this ONE V17 execution test?")
                .setNegativeButton("Cancel — do not execute", null)
                .setPositiveButton("Authorize ONE fresh v17 test", (dialog, which) -> {
                    wine29V17Exec.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine29V17ControlCompareProbe.run(this);
                        runOnUiThread(() -> {
                            wine29V17Exec.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — V17 control comparison")
                                .setMessage(report)
                                .setPositiveButton("Copy short report", (dlg, btn) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                            getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null) cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                        "Charoite Wine29 V17 native exec boundary", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine29V17ControlCompareProbe").start();
                }).show());
        wine29V17Action.addView(wine29V17Exec);
        android.widget.Button v17HandoffButton = new android.widget.Button(this);
        v17HandoffButton.setText("Open current project handoff");
        v17HandoffButton.setAllCaps(false);
        v17HandoffButton.setOnClickListener(v -> startActivity(new android.content.Intent(
                android.content.Intent.ACTION_VIEW,
                android.net.Uri.parse("https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md"))));
        wine29V17Action.addView(v17HandoffButton);
        nextCoreCard.addView(wine29V17Action);
        } // V17 one-shot consumed permanently; not replayable.

        // Only ACTIVE Wine29 action: four V17 preserved logs, STRICT READ ONLY.
        // All instructions and both buttons grouped under System.
        final boolean showArchivedWine29V17ReadOnly = false;
        if (showArchivedWine29V17ReadOnly) {
        LinearLayout wine29V17ReadOnlyAction = card();
        wine29V17ReadOnlyAction.addView(label(
                "CURRENT WINE29 ACTION — V17 PRESERVED READ-ONLY",
                16, FOREGROUND, true));
        wine29V17ReadOnlyAction.addView(label(
                "V17 one-shot execution is COMPLETE. Independent Wineboot --help " +
                "control exited 127 with no output, and the private server was " +
                "not alive afterward. Protective gate skipped independent sc.exe. " +
                "PE mapping, SCM and cause remain UNKNOWN. TO ACT: tap Inspect " +
                "Wine29 v17 control + server (read-only), then Copy short report " +
                "into a new chat. The handoff URL is the FIRST report line. " +
                "Only FOUR preserved V17 logs and named V17 private metadata. " +
                "No Wine processes, registry contents, retries, writes, cleanup, " +
                "prior V1–V16/Wine28 scratch, stable Portal, games, saves, rootfs " +
                "or user prefixes. Never uninstall or clear storage.",
                12, SECONDARY, false));
        android.widget.Button wine29V17ReadOnly = new android.widget.Button(this);
        wine29V17ReadOnly.setText("Inspect Wine29 v17 control + server (read-only)");
        wine29V17ReadOnly.setAllCaps(false);
        wine29V17ReadOnly.setOnClickListener(v -> {
            wine29V17ReadOnly.setEnabled(false);
            new Thread(() -> {
                final String report =
                    com.charoitegames.core.CharoiteWine29V17ReadOnlyForensics.run(this);
                runOnUiThread(() -> {
                    wine29V17ReadOnly.setEnabled(true);
                    new android.app.AlertDialog.Builder(this)
                        .setTitle("Charoite Next — V17 preserved control postmortem")
                        .setMessage(report)
                        .setPositiveButton("Copy short report", (dlg, btn) -> {
                            android.content.ClipboardManager cb =
                                (android.content.ClipboardManager)
                                    getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                            if (cb != null) cb.setPrimaryClip(
                                android.content.ClipData.newPlainText(
                                    "Wine29 V17 preserved read-only report", report));
                        })
                        .setNegativeButton("Close", null).show();
                });
            }, "CharoiteWine29V17ReadOnlyForensics").start();
        });
        wine29V17ReadOnlyAction.addView(wine29V17ReadOnly);
        android.widget.Button v17ReadOnlyHandoff = new android.widget.Button(this);
        v17ReadOnlyHandoff.setText("Open current project handoff");
        v17ReadOnlyHandoff.setAllCaps(false);
        v17ReadOnlyHandoff.setOnClickListener(v -> startActivity(new android.content.Intent(
                android.content.Intent.ACTION_VIEW,
                android.net.Uri.parse("https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md"))));
        wine29V17ReadOnlyAction.addView(v17ReadOnlyHandoff);
        nextCoreCard.addView(wine29V17ReadOnlyAction);
        } // V17 preserved report already supplied; V17 UI retired, evidence retained.


        // V18 execution permanently consumed; retain source, retire all execution UI.
        final boolean showArchivedWine29V18Execution = false;
        if (showArchivedWine29V18Execution) {
        // ACTIVE V18: fresh, explicit one-shot private server idle lifecycle baseline.
        // Instructions remain in the same System card as the test and handoff.
        LinearLayout wine29V18Action = card();
        wine29V18Action.addView(label(
                "CURRENT WINE29 ACTION — V18 SERVER IDLE LIFECYCLE",
                16, FOREGROUND, true));
        wine29V18Action.addView(label(
                "NEW PRIVATE V18 SCRATCH ONLY. NOT READ ONLY: if separately authorized, " +
                "this one-shot test verifies the pinned Wine29 modules, starts a private " +
                "wineserver and one Wineboot -i with internal Wine services, then observes " +
                "the foreground server at 0, 1, 3, 8 and 12 seconds after Wineboot. " +
                "NO independent Wineboot --help, sc.exe, SCM query, installers, games or " +
                "network; no retries or deletion. When the observation is complete the " +
                "test stops only its private server process, without deleting scratch " +
                "or traces. V17 and V1–V16, Wine28, stable Portal, user prefixes, saves " +
                "and rootfs are NOT ACCESSED. This records timing, not causation or " +
                "game readiness. To run: tap Test, read the scope and explicitly choose " +
                "Authorize ONE fresh v18 test, then Copy short report from first-line " +
                "Handoff through END OF SHORT V18 IDLE REPORT into a new chat. " +
                "Never uninstall, clear app data or touch prior scratch.",
                12, SECONDARY, false));
        android.widget.Button wine29V18Exec = new android.widget.Button(this);
        wine29V18Exec.setText("Test Wine29 v18 server lifecycle (one-shot)");
        wine29V18Exec.setAllCaps(false);
        wine29V18Exec.setOnClickListener(v ->
            new android.app.AlertDialog.Builder(this)
                .setTitle("Authorize ONE fresh V18 server idle-lifecycle test?")
                .setMessage("THIS EXECUTES WINE ONCE in a NEW private V18 scratch. " +
                    "It runs private wineserver and Wineboot -i/internal services, " +
                    "then observes server liveness for up to 12 seconds, WITHOUT " +
                    "any second native launcher, independent sc.exe, SCM operation, " +
                    "installer or game. At completion only the owned V18 process may " +
                    "be terminated; V18 scratch and logs remain forever. The probe " +
                    "fails closed if V18 scratch already exists. V17 and all earlier " +
                    "generations, stable Portal, saved games and user prefixes are " +
                    "NOT ACCESSED. Never retry, delete, uninstall or clear storage. " +
                    "Do you explicitly authorize this ONE new V18 execution?")
                .setNegativeButton("Cancel — do not execute", null)
                .setPositiveButton("Authorize ONE fresh v18 test", (dialog, which) -> {
                    wine29V18Exec.setEnabled(false);
                    new Thread(() -> {
                        final String report =
                            com.charoitegames.core.CharoiteWine29V18ServerIdleProbe.run(this);
                        runOnUiThread(() -> {
                            wine29V18Exec.setEnabled(true);
                            new android.app.AlertDialog.Builder(this)
                                .setTitle("Charoite Next — V18 server idle lifecycle")
                                .setMessage(report)
                                .setPositiveButton("Copy short report", (dlg, btn) -> {
                                    android.content.ClipboardManager cb =
                                        (android.content.ClipboardManager)
                                            getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                                    if (cb != null) cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                        "Charoite Wine29 V18 server lifecycle report", report));
                                })
                                .setNegativeButton("Close", null).show();
                        });
                    }, "CharoiteWine29V18ServerIdleProbe").start();
                }).show());
        wine29V18Action.addView(wine29V18Exec);
        android.widget.Button v18HandoffButton = new android.widget.Button(this);
        v18HandoffButton.setText("Open current project handoff");
        v18HandoffButton.setAllCaps(false);
        v18HandoffButton.setOnClickListener(v -> startActivity(new android.content.Intent(
                android.content.Intent.ACTION_VIEW,
                android.net.Uri.parse("https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md"))));
        wine29V18Action.addView(v18HandoffButton);
        nextCoreCard.addView(wine29V18Action);
        } // V18 permanently consumed; never replay or clear evidence.

        // ACTIVE V18 preserved idle-lifecycle forensics, strict read-only.
        // Instructions, inspection action and handoff stay together under System.
        LinearLayout wine29V18ReadOnlyAction = card();
        wine29V18ReadOnlyAction.addView(label(
                "CURRENT WINE29 ACTION — V18 PRESERVED READ-ONLY",
                16, FOREGROUND, true));
        wine29V18ReadOnlyAction.addView(label(
                "V18 ONE-SHOT IS COMPLETE AND PERMANENTLY CONSUMED. STRICT READ ONLY: " +
                "no Wine/Wineboot, services.exe, wineserver, sc.exe, processes, retries, " +
                "scratch creation, writes, cleanup or deletion. Examine ONLY two fixed " +
                "preserved V18 logs and explicitly named V18 private metadata; registry " +
                "file CONTENTS are not read, raw process paths/lines are not copied. " +
                "No V1–V17, Wine28, stable Portal, games, saves, user prefixes or rootfs " +
                "access. This examines the server that exited with code 1 during idle " +
                "observation after Wineboot -i exit 0. Read-only evidence does NOT " +
                "establish server exit cause, independent Windows PE mapping or SCM. " +
                "Tap Inspect, then Copy short report from first-line Handoff through " +
                "END OF SHORT V18 READ-ONLY REPORT into a new chat. " +
                "Never uninstall, clear data, retry or delete V18 or older scratch.",
                12, SECONDARY, false));
        android.widget.Button wine29V18Inspect = new android.widget.Button(this);
        wine29V18Inspect.setText("Inspect Wine29 v18 idle server (read-only)");
        wine29V18Inspect.setAllCaps(false);
        wine29V18Inspect.setOnClickListener(v -> {
            wine29V18Inspect.setEnabled(false);
            new Thread(() -> {
                final String report =
                    com.charoitegames.core.CharoiteWine29V18ReadOnlyForensics.run(this);
                runOnUiThread(() -> {
                    wine29V18Inspect.setEnabled(true);
                    new android.app.AlertDialog.Builder(this)
                        .setTitle("Charoite Next — V18 preserved idle-server postmortem")
                        .setMessage(report)
                        .setPositiveButton("Copy short report", (dlg, btn) -> {
                            android.content.ClipboardManager cb =
                                (android.content.ClipboardManager)
                                    getSystemService(android.content.Context.CLIPBOARD_SERVICE);
                            if (cb != null) cb.setPrimaryClip(android.content.ClipData.newPlainText(
                                    "Wine29 V18 preserved read-only report", report));
                        })
                        .setNegativeButton("Close", null).show();
                });
            }, "CharoiteWine29V18ReadOnlyForensics").start();
        });
        wine29V18ReadOnlyAction.addView(wine29V18Inspect);
        android.widget.Button v18ReadOnlyHandoff = new android.widget.Button(this);
        v18ReadOnlyHandoff.setText("Open current project handoff");
        v18ReadOnlyHandoff.setAllCaps(false);
        v18ReadOnlyHandoff.setOnClickListener(v -> startActivity(new android.content.Intent(
                android.content.Intent.ACTION_VIEW,
                android.net.Uri.parse("https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md"))));
        wine29V18ReadOnlyAction.addView(v18ReadOnlyHandoff);
        nextCoreCard.addView(wine29V18ReadOnlyAction);


        // Optional auto-upload is not part of the V16 manual test; retire it.
        final boolean showHistoricalAutomaticReporter = false;
        if (showHistoricalAutomaticReporter) {
        android.widget.Button autoReporter = new android.widget.Button(this);
        autoReporter.setText("Automatic phone diagnostics (GitHub opt-in)");
        autoReporter.setAllCaps(false);
        autoReporter.setOnClickListener(v ->
            com.charoitegames.core.CharoiteNextAutoReports.showSettings(this));
        nextCoreCard.addView(autoReporter);
        } // manual-only V16; no unrelated System diagnostic buttons.

        // Retain startup/audio diagnostic implementation for future support,
        // but do not clutter the current Wine29-only System test surface.
        final boolean showArchivedStartupDiagnostics = false;
        if (showArchivedStartupDiagnostics) {
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
        } // Startup/audio diagnostic action hidden from the active System tab.
""")
# Real onCreate registers the Portal and handles the one-time direct-root
# cold boot fallback for Samsung legacy tasks. No splash on normal resume.
create_anchor = "        super.onCreate(savedInstanceState);\n        CharoiteEnvironments.initialize(this);"
assert ui.count(create_anchor) == 1
ui = ui.replace(create_anchor, (
    "        super.onCreate(savedInstanceState);\n"
    "        com.charoitegames.core.CharoiteNextBootActivity"
    ".onPortalCreated(this, savedInstanceState);\n"
    "        CharoiteEnvironments.initialize(this);\n"
    "        com.charoitegames.core.CharoiteNextAutoReports.schedule(this);\n"
    "        com.charoitegames.core.CharoiteNextAutoReports.sendOnLaunch(this);"), 1)

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
