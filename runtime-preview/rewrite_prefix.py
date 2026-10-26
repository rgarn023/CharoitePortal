#!/usr/bin/env python3
"""Patch pinned, licensed Winlator runtime tarballs to match this app's real Android UID path.

The prebuilt Box64 ARM64 ELF interpreter, Wine rootfs and graphics drivers carry
hard-coded /data/data/com.winlator/... paths. Merely changing applicationId in
Gradle breaks native execution. Both IDs deliberately have the same byte length
so this edit does NOT move ELF sections, PT_INTERP, symbol offsets, or RPATHs.
The original source and license files are retained; no game data is modified.
"""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ORIGINAL = b"com.winlator"
TARGET = b"com.charoite"
assert len(ORIGINAL) == len(TARGET), "ELF-safe path rewrite must preserve byte length"

MANDATORY = {
    "rootfs.tzst",
    "box64/box64-0.4.4.tzst",
    "container_pattern.tzst",
}

def run(*args: str) -> None:
    subprocess.run(args, check=True)

def rewrite_archive(archive: Path) -> int:
    with tempfile.TemporaryDirectory(prefix="charoite-runtime-") as temp:
        extracted = Path(temp) / "unpacked"
        extracted.mkdir()
        # Archives come from a pinned, audited upstream revision. GNU tar
        # preserves relative links, modes, and executable attributes.
        run("tar", "--use-compress-program=zstd", "-xf", str(archive), "-C", str(extracted))
        touched = 0
        for current, dirs, files in os.walk(extracted, followlinks=False):
            for name in [*dirs, *files]:
                path = Path(current) / name
                if path.is_symlink():
                    link = os.readlink(path)
                    if "com.winlator" in link:
                        path.unlink()
                        path.symlink_to(link.replace("com.winlator", "com.charoite"))
                        touched += 1
                elif path.is_file():
                    blob = path.read_bytes()
                    if ORIGINAL in blob:
                        path.write_bytes(blob.replace(ORIGINAL, TARGET))
                        touched += 1
        if touched:
            tmp_archive = archive.with_name(archive.name + ".updated")
            if tmp_archive.exists():
                tmp_archive.unlink()
            try:
                run("tar", "--use-compress-program=zstd", "-cf",
                    str(tmp_archive), "-C", str(extracted), ".")
                tmp_archive.replace(archive)
            finally:
                tmp_archive.unlink(missing_ok=True)
        return touched

def main(root: Path) -> None:
    assets = root / "app/src/main/assets"
    if not assets.is_dir():
        raise SystemExit(f"Missing upstream assets dir: {assets}")
    all_archives = sorted(assets.rglob("*.tzst"))
    found = {str(path.relative_to(assets)) for path in all_archives}
    missing = MANDATORY - found
    if missing:
        raise RuntimeError(f"Missing pinned component archives: {sorted(missing)}")
    archive_count = 0
    modified_files = 0
    for archive in all_archives:
        changed = rewrite_archive(archive)
        if changed:
            archive_count += 1
            modified_files += changed
            print(f"Rebased {archive.relative_to(assets)}: {changed} native paths", flush=True)
    if archive_count < 3 or modified_files < 10:
        raise RuntimeError("Runtime native-path rewrite produced too few changes; stop unsafe build")
    print(f"Rebased {archive_count} archives, {modified_files} files/links from "
          f"{ORIGINAL.decode()} to {TARGET.decode()}", flush=True)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: rewrite_prefix.py UPSTREAM_WINLATOR_SOURCE")
    main(Path(sys.argv[1]).resolve())
