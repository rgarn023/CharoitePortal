#!/usr/bin/env python3
"""Read-only Charoite Wine slice verification. Does not unpack or install anything."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import tarfile

EXPECTED_PATHS = {
    "wineserver": "slice/bin/wineserver",
    "wine_loader": "slice/bin/wine",
    "ntdll_unix": "slice/lib/ntdll.so",
    "ntdll_arm64ec": "slice/lib/wine/aarch64-windows/ntdll.dll",
}
SOURCE_SHA = "c74acb09d51b447f5d5ac56c87608d3ec565a767"


def verify(path: Path) -> dict:
    if not path.is_file():
        raise ValueError("Missing experimental runtime slice")
    with tarfile.open(path, "r:gz") as archive:
        members = archive.getmembers()
        expected = {"manifest.json", *EXPECTED_PATHS.values()}
        actual = {m.name for m in members}
        if len(members) != len(expected) or actual != expected:
            raise ValueError(f"Unexpected runtime archive contents: {sorted(actual)}")
        for m in members:
            p = PurePosixPath(m.name)
            if (not m.isfile() or m.name.startswith("/") or
                p.is_absolute() or ".." in p.parts or m.size <= 0 or
                m.size > 256 * 1024 * 1024):
                raise ValueError(f"Invalid runtime payload member: {m.name}")
        with archive.extractfile("manifest.json") as stream:
            manifest = json.loads(stream.read())
        if (manifest.get("schema_version") != 1 or
            manifest.get("source_commit") != SOURCE_SHA or
            manifest.get("android_package") != "com.charoitx" or
            manifest.get("launch_ready") is not False or
            manifest.get("installable") is not False or
            manifest.get("status") != "abi-validated-components-only"):
            raise ValueError("Unsafe/incompatible experimental Charoite Wine manifest")
        found = manifest.get("components")
        if not isinstance(found, dict) or set(found) != set(EXPECTED_PATHS):
            raise ValueError("Missing mandatory base runtime component")
        for name, archive_path in EXPECTED_PATHS.items():
            info = found[name]
            if info.get("file") != archive_path.removeprefix("slice/"):
                raise ValueError(f"Runtime path not canonical: {name}")
            if len(info.get("sha256", "")) != 64:
                raise ValueError("Missing SHA256")
            h = hashlib.sha256()
            with archive.extractfile(archive_path) as stream:
                size = 0
                while block := stream.read(1048576):
                    h.update(block)
                    size += len(block)
            if size != info.get("size") or h.hexdigest() != info["sha256"]:
                raise ValueError(f"Tampered runtime file: {name}")
            if name == "ntdll_arm64ec":
                if info.get("pe_machine") != "0xA641":
                    raise ValueError("Wrong ARM64EC PE architecture")
            else:
                if info.get("machine") != "AArch64" or not info.get("load_alignment"):
                    raise ValueError("Wrong native Android architecture")
                if min(info["load_alignment"]) < 16384:
                    raise ValueError("Insufficient Android ELF 16 KiB alignment")
    return manifest


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: verify-runtime-slice.py EXPERIMENTAL_ARCHIVE")
    result = verify(Path(sys.argv[1]))
    print("CHAROITE_WINE_SLICE_ARCHIVE_VERIFIED=PASS")
    print("LAUNCH_READY=false")
    print("Components:", ", ".join(sorted(result["components"])))
