#!/usr/bin/env python3
"""Seal and verify six pinned-source ARM64EC Wine29 dependency candidates.

CI-only static PE/parser hash manifest. Does NOT invoke Wine or PE files.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import stat
import struct
import subprocess
import sys

SOURCE_COMMIT = "c74acb09d51b447f5d5ac56c87608d3ec565a767"
BASELINE = "66068032bd2203c8e53fddc92ce46b84086eb293306b2bd12bb741bf9a5e035e"
GENERATION = "wine10-arm64ec-dependencies.0.8-candidate"
MODULES = ("coml2", "imm32", "oleacc", "oleaut32", "shcore", "newdev")
PHONE_DIRECT = ("coml2.dll", "imm32.dll", "oleacc.dll", "oleaut32.dll", "shcore.dll")
MAX_FILE = 32 * 1024 * 1024


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def raw_coff_machine(data: bytes) -> int:
    if len(data) < 0x40 or data[:2] != b"MZ":
        raise ValueError("Missing MZ executable header")
    offset = struct.unpack_from("<I", data, 0x3c)[0]
    if offset > len(data) - 24 or data[offset:offset+4] != b"PE\x00\x00":
        raise ValueError("Invalid PE signature/offset")
    machine = struct.unpack_from("<H", data, offset + 4)[0]
    if machine not in (0xAA64, 0xA641):
        raise ValueError("Not source-supported hybrid ARM64/ARM64EC PE")
    return machine


def regular_bytes(path: Path) -> bytes:
    info = path.lstat()
    if (path.is_symlink() or not stat.S_ISREG(info.st_mode) or
            info.st_size <= 0 or info.st_size > MAX_FILE):
        raise ValueError("Invalid/linked/oversized Wine29 candidate: " + str(path))
    data = path.read_bytes()
    if len(data) != info.st_size:
        raise ValueError("Wine29 candidate size changed while reading")
    return data


def info_for(folder: Path, name: str, readobj: Path) -> dict:
    binary = folder / (name + "-arm64ec.dll")
    data = regular_bytes(binary)
    raw_machine = raw_coff_machine(data)
    header = folder / (name + "-pe-header.txt")
    importlog = folder / (name + "-pe-imports.txt")
    hdr = regular_bytes(header)
    imp = regular_bytes(importlog)
    if b"Machine: IMAGE_FILE_MACHINE_ARM64EC (0xA641)" not in hdr:
        raise ValueError("Missing independently verified ARM64EC view: " + name)
    fresh_header = subprocess.run(
        [str(readobj), "--file-headers", str(binary)], check=True,
        capture_output=True).stdout
    fresh_imports = subprocess.run(
        [str(readobj), "--coff-imports", str(binary)], check=True,
        capture_output=True).stdout
    if hdr != fresh_header or imp != fresh_imports:
        raise ValueError("Candidate LLVM ABI/import inspection differs")
    names = sorted(set(v.lower() for v in re.findall(
        rb"^\s*Name:\s*([A-Za-z0-9_.+-]+\.dll)\s*$", imp, re.M)))
    imports = [v.decode("ascii") for v in names]
    return {
        "filename": binary.name, "size": len(data), "sha256": sha256(data),
        "arm64ec_view": "0xA641", "raw_arm64x_carrier": f"0x{raw_machine:04X}",
        "imports": imports, "header_log_sha256": sha256(hdr),
        "import_log_sha256": sha256(imp),
    }


def inspect(folder: Path, readobj: Path) -> dict:
    if not folder.is_absolute() or folder.is_symlink() or not folder.is_dir():
        raise ValueError("Require separate isolated new candidate output")
    if not readobj.is_absolute() or not readobj.is_file():
        raise ValueError("Missing ABI checker")
    if any(p in str(folder) for p in (
        "/data/data/", "/data/user/", "/storage/emulated/", "/sdcard/"
    )):
        raise ValueError("Refusing Android/user storage")
    results = {name: info_for(folder, name, readobj) for name in MODULES}
    all_imports = sorted(set(s for v in results.values() for s in v["imports"]))
    return {
        "schema_version": 1, "generation": GENERATION,
        "source_commit": SOURCE_COMMIT, "baseline_source_archive_sha256": BASELINE,
        "android_package": "com.charoitx", "component_count": 6,
        "phone_direct_import_targets": list(PHONE_DIRECT),
        "wineboot_broader_source_candidate": "newdev.dll",
        "components": results,
        "observed_candidate_imports": all_imports,
        "candidate_imports_not_in_candidate_set": sorted(
            set(all_imports) - {n + ".dll" for n in MODULES}),
        "launch_ready": False,
        "wineboot_executed": False, "windows_exe_executed": False,
        "prefix_created": False, "device_tested": False, "installed": False,
        "provenance_note": "Fresh pinned Wine29 .0.7 source build; candidate-only CI artifact, not a runtime.",
    }


def run(mode: str, folder: Path, readobj: Path) -> dict:
    if mode not in ("create", "verify"):
        raise ValueError("Invalid candidate audit operation")
    report_path = folder / "wine29-07-six-candidates.json"
    results = inspect(folder, readobj)
    if mode == "create":
        if report_path.exists() or report_path.is_symlink():
            raise ValueError("Refusing overwrite of candidate manifest")
        report_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    else:
        original = json.loads(regular_bytes(report_path).decode("utf-8"))
        if original != results:
            raise ValueError("Source-matched candidate SHA/import/architecture drift")
        allowed = {report_path.name}
        for name in MODULES:
            allowed.update({name+"-arm64ec.dll",name+"-pe-header.txt",name+"-pe-imports.txt"})
        if {x.name for x in folder.iterdir()} != allowed:
            raise ValueError("Unexpected files in sealed candidate artifact")
    print("WINE29_07_SIX_DLL_ARM64EC_VIEW_AND_RAW_PE_HEADERS=PASS")
    print("WINE29_07_SIX_SOURCE_BUILT_CANDIDATE_HASHES=PASS")
    print("WINE29_07_CANDIDATE_DIRECT_IMPORT_NAMES="+str(len(results["observed_candidate_imports"])))
    print("WINE29_07_PREFIX_AND_PE_EXECUTION=NOT_ATTEMPTED")
    return results


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: verify-wine29-deps.py create|verify ABS_NEW_CANDIDATES ABS_LLVM_READOBJ")
    run(sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]))
