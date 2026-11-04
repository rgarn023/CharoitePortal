#!/usr/bin/env python3
"""Verify a freshly built, separate Wine29 native source cohort (CI ONLY).

This preflight validates compiled Android ARM64 ELFs and Windows ARM64EC
ntdll from the SAME .0.7 source tree. It never executes Wine, installs an
APK, creates a prefix, or merges the frozen Wine29 .0.6 data payload.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys

SOURCE_COMMIT = "c74acb09d51b447f5d5ac56c87608d3ec565a767"
GENERATION = "wine10-arm64ec-bootstrap.0.7"
BINARIES = {
    "wine": ("loader/wine", ("CHAROITE_WINE29_NATIVE_DIR", "libcharoite_wine29_ntdll.so")),
    "wineserver": ("server/wineserver", ("CHAROITE_WINE29_DATA_DIR", "Wine29/Wine28 selector conflict")),
    "ntdll_unix": ("dlls/ntdll/ntdll.so", ("CHAROITE_WINE29_PE_DIR", "CHAROITE_WINE29_DATA_DIR", "apisetschema.dll")),
}
WINDOWS_NTDLL = "dlls/ntdll/aarch64-windows/ntdll.dll"
MAX_ELF_BYTES = 32 * 1024 * 1024
MAX_PE_BYTES = 32 * 1024 * 1024


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def regular(path: Path, maximum: int) -> bytes:
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= maximum:
        raise ValueError("Missing or unsafe compiled Wine29 source file: " + str(path))
    return path.read_bytes()


def command(tool: Path, *args: str) -> str:
    # The pinned Android NDK exposes llvm-readelf as a symlink to llvm-readobj.
    # Accept links ONLY when the resolved executable stays in the exact
    # checksum-pinned toolchain bin directory; reject escaping links.
    try:
        resolved = tool.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError("Missing pinned inspection tool: " + str(tool)) from exc
    if (not tool.is_absolute() or not resolved.is_file() or
            resolved.parent != tool.parent.resolve(strict=True)):
        raise ValueError("Inspection tool escapes pinned toolchain directory: " + str(tool))
    return subprocess.run([str(tool), *args], check=True, text=True, capture_output=True).stdout


def verify_native(build: Path, readelf: Path, readobj: Path, source: Path) -> dict:
    proof = json.loads(regular(source/"charoite-wine29-native-source-validation.json", 65536))
    delta = regular(source/"charoite-wine29-native-source-delta.patch", 4 * 1024 * 1024)
    if (proof.get("generation") != GENERATION or proof.get("source_commit") != SOURCE_COMMIT
            or proof.get("package") != "com.charoitx"
            or proof.get("runtime_executable") is not False
            or proof.get("device_tested") is not False
            or proof.get("native_elf_installed") is not False
            or proof.get("delta_sha256") != digest(delta)
            or proof.get("legacy_wine28_cohort_modified") is not False
            or set(proof.get("patch_sources", {})) != {
                "loader/main.c", "dlls/ntdll/unix/loader.c", "server/unicode.c"
            }):
        raise ValueError("Missing coherent Wine29 source-patch provenance")
    for rel, hashes in proof["patch_sources"].items():
        source_hash = digest(regular(source/rel, 8 * 1024 * 1024))
        if source_hash != hashes.get("after_sha256") or source_hash == hashes.get("before_sha256"):
            raise ValueError("Source changed after Wine29 native patch: " + rel)
    if not (source/"charoite-source-validation.txt").is_file():
        raise ValueError("Missing original verified Wine source")
    if not (build.parent == source and build.name == "charoite-arm64ec-android"):
        raise ValueError("Compiled binaries must be from exact patched source tree")

    components = {}
    for name, (rel, markers) in BINARIES.items():
        path = build/rel
        data = regular(path, MAX_ELF_BYTES)
        if len(data) < 20 or data[:6] != b"\x7fELF\x02\x01" or struct.unpack_from("<H", data, 18)[0] != 183:
            raise ValueError("Not an Android AArch64 ELF: " + name)
        header = command(readelf, "-h", str(path))
        if not re.search(r"Machine:\s+AArch64\b", header):
            raise ValueError("Unexpected ELF architecture: " + name)
        segments = command(readelf, "-lW", str(path))
        alignments = []
        for line in segments.splitlines():
            if re.match(r"^\s+LOAD\s", line):
                match = re.search(r"(0x[0-9a-fA-F]+)\s*$", line)
                if match is None:
                    raise ValueError("Unparseable Android ELF alignment: " + name)
                alignments.append(int(match.group(1), 16))
        if not alignments or min(alignments) < 16384:
            raise ValueError("Wine29 native ELF lacks 16 KiB page alignment: " + name)
        for marker in markers:
            if marker.encode() not in data:
                raise ValueError("Compiled Wine29 source selector missing: " + name + "/" + marker)
        dynamic = command(readelf, "-dW", str(path))
        needed = sorted(set(re.findall(r"\(NEEDED\).*?\[([^\]]+)\]", dynamic)))
        components[name] = {
            "format": "ELF", "sha256": digest(data), "size": len(data),
            "machine": "AArch64", "load_alignments": alignments, "needed": needed
        }
    pe = regular(build/WINDOWS_NTDLL, MAX_PE_BYTES)
    if len(pe) < 0x40 or pe[:2] != b"MZ":
        raise ValueError("Source-matched Windows NTDLL PE is invalid")
    pe_report = command(readobj, "--file-headers", str(build/WINDOWS_NTDLL))
    if not re.search(r"Machine:\s+IMAGE_FILE_MACHINE_ARM64EC\s+\(0xA641\)", pe_report):
        raise ValueError("Not source-matched Windows ARM64EC NTDLL")
    components["ntdll_windows"] = {"format": "PE", "sha256": digest(pe),
                                    "size": len(pe), "machine": "ARM64EC"}
    return {
        "schema_version": 1, "source_generation": GENERATION,
        "source_commit": SOURCE_COMMIT, "package": "com.charoitx",
        "source_patch_sha256": proof["delta_sha256"],
        "components": components,
        "native_elf_count": 3, "windows_ntdll_pe_count": 1,
        "new_27_component_archive_verified": False,
        "native_elf_installed": False, "launch_ready": False,
        "device_tested": False, "prefix_created": False,
        "wineboot_executed": False, "anti_cheat_supported": False
    }


def publish(source: Path, readelf: Path, readobj: Path, output: Path) -> dict:
    if not all(p.is_absolute() for p in (source, readelf, readobj, output)):
        raise ValueError("Only isolated absolute CI paths permitted")
    for path in (source, output):
        if any(part in path.parts for part in ("data", "storage", "sdcard")):
            # Explicitly restrict Android /data and shared-storage install paths;
            # CI workspace roots have /home/runner or /tmp prefixes.
            if str(path).startswith(("/data/", "/storage/", "/sdcard/")):
                raise ValueError("Refusing Android user app paths")
    if (output.exists() or output.is_symlink()
            or not output.parent.is_dir() or source.is_symlink()):
        raise ValueError("Refusing existing or unsafe Wine29 artifact destination")
    build = source/"charoite-arm64ec-android"
    report = verify_native(build, readelf, readobj, source)
    # All reads, tool inspections and source checks have succeeded before any
    # write. Never package a mixed, partially checked native cohort.
    output.mkdir()
    for name, (relative, _markers) in BINARIES.items():
        shutil.copyfile(build/relative, output/{"wine": "wine-arm64", "wineserver": "wineserver-arm64",
                                                 "ntdll_unix": "ntdll-arm64.so"}[name])
    shutil.copyfile(build/WINDOWS_NTDLL, output/"ntdll-arm64ec.dll")
    shutil.copyfile(source/"charoite-wine29-native-source-validation.json",
                    output/"source-proof.json")
    (output/"native-compile-report.json").write_text(json.dumps(report, sort_keys=True, indent=2)+"\n")
    return report


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit("Usage: verify-wine29-native-compile.py ABS_PATCHED_SOURCE ABS_READELF ABS_READOBJ ABS_NEW_OUTPUT")
    result = publish(*(Path(x) for x in sys.argv[1:]))
    print("WINE29_SOURCE_MATCHED_NATIVE_COMPILE=PASS")
    print("SOURCE_GENERATION=" + result["source_generation"])
    print("ELF_COUNT=3")
    print("WINDOWS_NTDLL_PE_COUNT=1")
    print("RUNTIME_LAUNCH_READY=false")
