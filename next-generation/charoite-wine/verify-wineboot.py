#!/usr/bin/env python3
"""No-extraction, no-install Wineboot ARM64EC experimental artifact verification."""
import hashlib
import json
from pathlib import Path
import re
import sys


def verify(root: Path) -> dict:
    manifest = json.loads((root / "wineboot-manifest.json").read_text(encoding="utf-8"))
    if (manifest.get("schema_version") != 1 or
        manifest.get("android_package") != "com.charoitx" or
        manifest.get("source_commit") != "c74acb09d51b447f5d5ac56c87608d3ec565a767" or
        manifest.get("pe_machine") != "0xA641" or
        manifest.get("status") != "compiled-not-executed" or
        manifest.get("prefix_created") is not False or
        manifest.get("launch_ready") is not False or
        manifest.get("installable") is not False or
        manifest.get("file") != "wineboot-arm64ec.exe"):
        raise ValueError("Unsafe, wrong-architecture or unsupported Wineboot manifest")
    expected = {"wineboot-arm64ec.exe", "wineboot-pe-header.txt", "wineboot-manifest.json"}
    if {p.name for p in root.iterdir()} != expected:
        raise ValueError("Unexpected Wineboot artifact files")
    binary = root / "wineboot-arm64ec.exe"
    if binary.is_symlink() or not binary.is_file() or not binary.stat().st_size:
        raise ValueError("Missing Wineboot PE file")
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    if digest != manifest.get("sha256") or binary.stat().st_size != manifest.get("size"):
        raise ValueError("Wineboot file content is tampered")
    header = (root / "wineboot-pe-header.txt").read_text(encoding="utf-8")
    if not re.search(r"Machine:\s+IMAGE_FILE_MACHINE_ARM64EC\s+\(0xA641\)", header):
        raise ValueError("Wineboot PE header does not indicate ARM64EC")
    return manifest


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: verify-wineboot.py DIR")
    verify(Path(sys.argv[1]))
    print("CHAROITE_WINEBOOT_MANIFEST_VERIFIED=PASS")
    print("PREFIX_CREATED=false")
