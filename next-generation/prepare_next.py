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
text = text.replace('versionName "11.2"', 'versionName "11.2-next.0.43"')
text = text.replace("versionCode 33", "versionCode 74")
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
                 "CharoiteWine27PrefixProbe.java"):
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
