#!/usr/bin/env python3
"""Stage ONLY the pinned, source-verified Wine29 v6 native cohort in a fresh Next APK.

CI packaging only. No Wine execution, no device storage, no user prefixes.
The GitHub workflow separately pins and verifies the source artifact digest.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import struct
import sys

SOURCE_REV = "c74acb09d51b447f5d5ac56c87608d3ec565a767"
SOURCE_RUN = 42386856463
SOURCE_SHA = "0975c168b1c2e3981a6bf26f9908cd51e006ae4e"
SOURCE_ARTIFACT_ID = 13580236073
SOURCE_ARTIFACT_DIGEST = "sha256:9f4cb990e50ae9cc0be0fa4ea64bdbf9e939c0acbb0dde9a9c7bf04aa94ae12c"
INDEX = "charoite-next/wine29-v6/wine29-v6-native-index.json"
FILES = {
    "loader": "libcharoite_wine29_v6_loader.so",
    "ntdll": "libcharoite_wine29_v6_ntdll.so",
    "wineserver": "libcharoite_wine29_v6_wineserver.so",
}
MAX_ELF = 32 * 1024 * 1024
ALLOWED_ARTIFACT = set(FILES.values()) | {n + ".program-headers.txt" for n in FILES.values()} | {
    "source-patch-evidence.json", "build-report.txt", "native-sha256.txt"
}

def digest(b):
    return hashlib.sha256(b).hexdigest()

def verify_source(artifact: Path):
    if artifact.is_symlink() or not artifact.is_dir():
        raise ValueError("Untrusted Wine29 v6 source artifact directory")
    entries = {p.name for p in artifact.iterdir()}
    if entries != ALLOWED_ARTIFACT or any((p.is_symlink() or not p.is_file()) for p in artifact.iterdir()):
        raise ValueError("Wrong v6 source artifact file inventory")
    evidence = json.loads((artifact / "source-patch-evidence.json").read_text())
    if not (
        evidence.get("source_revision") == SOURCE_REV
        and evidence.get("original_loader_git_blob") == "2f978520af6c216586baa081caa4c1db38207fd4"
        and evidence.get("modified_files") == ["dlls/ntdll/unix/loader.c", "loader/main.c", "server/unicode.c"]
        and evidence.get("selector_env") == "CHAROITE_WINE29_V6_LOADER_EXEC"
        and evidence.get("matched_native_ntdll_env") == "CHAROITE_WINE29_V6_NATIVE_DIR"
        and evidence.get("isolated_pe_selector") == "CHAROITE_WINE29_V6_PE_DIR"
        and evidence.get("isolated_nls_selector") == "CHAROITE_WINE29_V6_DATA_DIR"
        and evidence.get("matched_native_ntdll") == FILES["ntdll"]
        and evidence.get("candidate_native_loader") == FILES["loader"]
        and evidence.get("mode") == "SOURCE_PATCH_ONLY_FAIL_CLOSED"
        and evidence.get("android_apk_built") is False
        and evidence.get("phone_wine_executed") is False
        and evidence.get("one_shot_enabled") is False
        and all(re.fullmatch("[0-9a-f]{64}", evidence.get(k, ""))
                for k in ("source_patch_sha256", "main_loader_patch_sha256", "nls_server_patch_sha256"))
    ):
        raise ValueError("Pinned Wine29 v6 native source evidence mismatch")
    hashes = {}
    for line in (artifact / "native-sha256.txt").read_text().splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})\s+\./(libcharoite_wine29_v6_(?:loader|ntdll|wineserver)\.so)", line)
        if not match or match.group(2) in hashes:
            raise ValueError("Untrusted v6 native SHA list")
        hashes[match.group(2)] = match.group(1)
    if set(hashes) != set(FILES.values()):
        raise ValueError("Incomplete v6 ELF hash list")
    records = {}
    for component, filename in FILES.items():
        f = artifact / filename
        data = f.read_bytes()
        if (not 1024 < len(data) <= MAX_ELF or digest(data) != hashes[filename]
                or data[:6] != b"\x7fELF\x02\x01"
                or struct.unpack_from("<H", data, 16)[0] != 3
                or struct.unpack_from("<H", data, 18)[0] != 183):
            raise ValueError("Invalid/unverified Wine29 v6 ELF " + component)
        aligns = []
        for line in (artifact / (filename + ".program-headers.txt")).read_text().splitlines():
            if line.lstrip().startswith("LOAD "):
                aligns.append(int(line.split()[-1], 16))
        if not aligns or min(aligns) < 16384:
            raise ValueError("Non-16KiB aligned ELF " + component)
        if component == "loader":
            if b"CHAROITE_WINE29_V6_NATIVE_DIR" not in data or FILES["ntdll"].encode() not in data:
                raise ValueError("V6 native loader lacks matched NTDLL-only selector")
        if component == "ntdll":
            if (b"CHAROITE_WINE29_V6_LOADER_EXEC" not in data or FILES["loader"].encode() not in data
                    or b"CHAROITE_WINE29_V6_PE_DIR" not in data
                    or b"CHAROITE_WINE29_V6_DATA_DIR" not in data):
                raise ValueError("V6 NTDLL lacks exact child executable selector")
        if component == "wineserver" and b"CHAROITE_WINE29_V6_DATA_DIR" not in data:
            raise ValueError("V6 wineserver lacks own NLS selector")
        records[component] = {"filename": filename, "sha256": hashes[filename],
                              "size": len(data), "elf_machine": "AArch64",
                              "min_load_alignment": min(aligns)}
    return evidence, records

def stage(artifact_arg, prepared_arg):
    artifact = Path(artifact_arg)
    prepared = Path(prepared_arg)
    for p in (artifact, prepared):
        if p.is_symlink() or not p.is_absolute() or any(x in str(p)
                for x in ("/data/user/", "/data/data/", "/storage/emulated/")):
            raise ValueError("Only isolated CI source/build absolute paths allowed")
    evidence, records = verify_source(artifact)
    app = prepared / "app/src/main"
    libdir = app / "jniLibs/arm64-v8a"
    assets = app / "assets"
    gradle = prepared / "app/build.gradle"
    old = libdir / "libcharoite_wine29_loader.so"
    sealed = assets / "charoite-next/wine29-sealed012/wine29-sealed012-index.json"
    if (not (app / "AndroidManifest.xml").is_file() or not libdir.is_dir()
            or not gradle.is_file() or not old.is_file() or not sealed.is_file()
            or json.loads(sealed.read_text()).get("wine_source_commit") != SOURCE_REV):
        raise ValueError("Original Next 111-file Wine29 baseline not verified")
    original_hash = digest(old.read_bytes())
    dest = assets / INDEX
    target_libs = [libdir / v for v in FILES.values()]
    if dest.exists() or dest.is_symlink() or any(p.exists() or p.is_symlink() for p in target_libs):
        raise ValueError("Refusing v6 native cohort overwrite")
    old_gradle = gradle.read_text()
    if any(v in old_gradle for v in FILES.values()):
        raise ValueError("Refusing pre-existing v6 doNotStrip rules")
    index = {
        "schema_version": 1, "package": "com.charoitx",
        "native_source_revision": SOURCE_REV, "source_commit": SOURCE_SHA,
        "source_run": SOURCE_RUN, "source_artifact_id": SOURCE_ARTIFACT_ID,
        "source_artifact_digest": SOURCE_ARTIFACT_DIGEST,
        "pinned_original_wine29_sha256": original_hash,
        "sealed_111_file_cohort": "wine10-arm64ec-dependencies.0.12-sealed-data-candidate",
        "native_files": records,
        "preflight_verified": True, "native_executed": False,
        "wineboot_executed": False, "prefix_created": False,
        "apk_only_native_stage": True, "device_tested": False,
        "launch_ready": False, "games_tested": False,
    }
    # Source and original-cohort validation complete before writes.
    dest.parent.mkdir(parents=True, exist_ok=False)
    for component, filename in FILES.items():
        data = (artifact / filename).read_bytes()
        target = libdir / filename
        target.write_bytes(data)
        target.chmod(0o755)
        if digest(target.read_bytes()) != records[component]["sha256"]:
            raise ValueError("V6 native staged copy changed")
    dest.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n")
    gradle.write_text(old_gradle + "\nandroid {\n    packagingOptions {\n" +
                      "".join('        doNotStrip "**/' + n + '"\n' for n in FILES.values()) +
                      "    }\n}\n")
    if digest(old.read_bytes()) != original_hash:
        raise ValueError("Original Wine29 ELF was modified")
    print("WINE29_V6_NATIVE_3_APK_ELF_HASHES=PASS")
    print("WINE29_V6_OLD_WINE29_NATIVE_UNTOUCHED=PASS")
    print("WINE29_V6_APK_STAGING_ONLY_NO_PHONE_EXECUTION=PASS")
    return index

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: stage_wine29_v6_native.py PINNED_ARTIFACT_FOLDER PREPARED_NEXT_UPSTREAM")
    stage(sys.argv[1], sys.argv[2])
