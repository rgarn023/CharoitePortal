#!/usr/bin/env python3
"""Read-only SHA-256 and metadata validation of Charoite Wine kernel PE modules."""
import hashlib
import json
from pathlib import Path
import re
import sys

EXPECTED = ("kernelbase", "kernel32")
SOURCE_SHA = "c74acb09d51b447f5d5ac56c87608d3ec565a767"


def verify(directory: Path) -> dict:
    if not directory.is_dir():
        raise ValueError("Missing experimental kernel DLL directory")
    metadata = directory / "kernel-bridge-manifest.json"
    manifest = json.loads(metadata.read_text(encoding="utf-8"))
    if (manifest.get("schema_version") != 1 or
        manifest.get("source_commit") != SOURCE_SHA or
        manifest.get("android_package") != "com.charoitx" or
        manifest.get("pe_machine") != "0xA641" or
        manifest.get("machine") != "IMAGE_FILE_MACHINE_ARM64EC" or
        manifest.get("launch_ready") is not False or
        manifest.get("installable") is not False or
        manifest.get("base_slice_required") is not True):
        raise ValueError("Experimental Wine kernel manifest must fail closed")
    components = manifest.get("components")
    if not isinstance(components, dict) or set(components) != set(EXPECTED):
        raise ValueError("Kernel32 and kernelbase must both be present")
    expected_files = {"kernel-bridge-manifest.json"}
    for name in EXPECTED:
        filename = f"{name}-arm64ec.dll"
        header_name = f"{name}-pe-header.txt"
        expected_files.update((filename, header_name))
        record = components[name]
        if record.get("file") != filename or record.get("pe_machine") != "0xA641":
            raise ValueError("Unexpected PE component name or ABI")
        binary = directory / filename
        if binary.is_symlink() or not binary.is_file() or binary.stat().st_size == 0:
            raise ValueError(f"Missing regular PE component: {name}")
        digest = hashlib.sha256(binary.read_bytes()).hexdigest()
        if digest != record.get("sha256") or binary.stat().st_size != record.get("size"):
            raise ValueError(f"Hash/size mismatch for {name}")
        header = (directory / header_name).read_text(encoding="utf-8")
        if not re.search(r"Machine:\s+IMAGE_FILE_MACHINE_ARM64EC\s+\(0xA641\)", header):
            raise ValueError(f"Wrong inspected PE type for {name}")
    if {p.name for p in directory.iterdir()} != expected_files:
        raise ValueError("Unexpected files in experimental PE module bundle")
    return manifest


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: verify-kernel-bridge.py DIR")
    result = verify(Path(sys.argv[1]))
    print("CHAROITE_ARM64EC_KERNEL_BUNDLE_VERIFIED=PASS")
    print("LAUNCH_READY=false")
    print("Components:", ", ".join(sorted(result["components"])))
