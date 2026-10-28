#!/usr/bin/env python3
"""Build a non-installing Charoite Wine ABI-checked experimental binary slice.

Four binaries MUST come from the same pinned patched Wine configure/build tree.
This archive is not a complete/launchable runtime and must not be installed.
"""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tarfile

SOURCE_SHA = "c74acb09d51b447f5d5ac56c87608d3ec565a767"
COMPONENTS = {
    "wineserver": ("server/wineserver", "bin/wineserver", "elf"),
    "wine_loader": ("loader/wine", "bin/wine", "elf"),
    "ntdll_unix": ("dlls/ntdll/ntdll.so", "lib/ntdll.so", "elf"),
    "ntdll_arm64ec": (
        "dlls/ntdll/aarch64-windows/ntdll.dll",
        "lib/wine/aarch64-windows/ntdll.dll",
        "pe",
    ),
}

SOURCE_FILES = {
    "wine_lgpl": ("COPYING.LIB", "source/COPYING.LIB"),
    "wine_license": ("LICENSE", "source/LICENSE"),
    "source_patch_delta": ("charoite-source-delta.patch", "source/charoite-source-delta.patch"),
    "vendor_mit": ("@vendor-license", "source/WEHAVEPHONES-MIT.txt"),
}


def source_file(build_dir: Path, filename: str) -> Path:
    if filename == "@vendor-license":
        return Path(__file__).resolve().parent / "UPSTREAM-WEHAVEPHONES-LICENSE.txt"
    return build_dir.parent / filename


def run(*argv: str) -> str:
    return subprocess.run(argv, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=True).stdout


def file_digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def check_file(path: Path) -> None:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or path.is_symlink() or info.st_size == 0:
        raise ValueError(f"Required nonempty regular file missing: {path}")


def elf_metadata(path: Path, readelf: str) -> dict:
    header = run(readelf, "-h", str(path))
    if not re.search(r"Machine:\s+AArch64\b", header):
        raise ValueError(f"Not an Android AArch64 ELF: {path.name}")
    program_headers = run(readelf, "-lW", str(path))
    alignments = []
    for line in program_headers.splitlines():
        if re.match(r"\s*LOAD\s", line):
            match = re.search(r"(0x[\da-fA-F]+)\s*$", line)
            if not match:
                raise ValueError(f"Bad PT_LOAD alignment: {line}")
            alignments.append(int(match.group(1), 16))
    if not alignments or any(a < 16_384 for a in alignments):
        raise ValueError(f"Android 16 KiB alignment not met: {path.name} {alignments}")
    interp_match = re.search(r"\[Requesting program interpreter:\s*([^\]]+)\]",
                             program_headers)
    dynamic = run(readelf, "-d", str(path))
    needed = re.findall(r"\(NEEDED\).*?\[([^\]]+)\]", dynamic)
    # Never claim launch readiness without loader/system dependency checks.
    return {
        "format": "ELF64",
        "machine": "AArch64",
        "load_alignment": alignments,
        "interpreter": interp_match.group(1) if interp_match else None,
        "needed": sorted(needed),
    }


def pe_metadata(path: Path, readobj: str) -> dict:
    header = run(readobj, "--file-headers", str(path))
    if not re.search(
        r"Machine:\s+(?:IMAGE_FILE_MACHINE_ARM64EC|ARM64EC|0xA641)\b", header
    ):
        raise ValueError(f"Windows DLL is not ARM64EC PE 0xA641: {path.name}")
    return {"format": "PE", "machine": "ARM64EC", "pe_machine": "0xA641"}


def build_manifest(build_dir: Path, readelf: str, readobj: str) -> dict:
    if "com.charoite/" in str(build_dir):
        raise ValueError("Refusing Charoite stable app path")
    if not (build_dir.parent / "charoite-source-validation.txt").is_file():
        raise ValueError("Missing signed-off source preparation report")
    result = {}
    for name, (relative, bundled, typ) in COMPONENTS.items():
        path = build_dir / relative
        check_file(path)
        abi = elf_metadata(path, readelf) if typ == "elf" else pe_metadata(path, readobj)
        result[name] = {
            "file": bundled,
            "size": path.stat().st_size,
            "sha256": file_digest(path),
            **abi,
        }
    license_sources = {}
    for name, (source_name, dest) in SOURCE_FILES.items():
        p = source_file(build_dir, source_name)
        check_file(p)
        license_sources[name] = {
            "file": dest,
            "size": p.stat().st_size,
            "sha256": file_digest(p),
        }
    return {
        "schema_version": 1,
        "source_files": license_sources,
        "source_reconstruction": {
            "upstream_repository": "https://github.com/The412Banner/proton-wine",
            "upstream_commit": SOURCE_SHA,
            "patch": "source/charoite-source-delta.patch",
            "integration_source": "https://github.com/rgarn023/CharoitePortal/tree/main/next-generation/charoite-wine",
            "note": "Wine LGPL; reapply corresponding source delta to pinned upstream. Additional third-party obligations apply to future full runners.",
        },
        "name": "Charoite Wine ARM64EC source-built base slice",
        "version": "wine10-arm64ec-slice.0.1",
        "source_commit": SOURCE_SHA,
        "android_package": "com.charoitx",
        "target_android_api": 35,
        "page_size": 16384,
        "launch_ready": False,
        "installable": False,
        "status": "abi-validated-components-only",
        "components": result,
        "missing_for_runtime": [
            "complete Wine PE/Unix DLL tree and NLS data",
            "FEX and x86/x64 bridge",
            "Android display/input/graphics drivers",
            "DXVK, VKD3D-Proton and Mesa Vulkan",
            "fresh independent prefix and end-to-end device tests",
        ],
        "anti_cheat": "no bypass or kernel emulation; vendor support required",
    }


def package(build_dir: Path, output: Path, readelf: str, readobj: str) -> Path:
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite runtime slice: {output}")
    if not output.parent.is_dir():
        raise ValueError("Output parent must already exist")
    manifest = build_manifest(build_dir, readelf, readobj)
    output.mkdir()
    files_root = output / "slice"
    for entry in manifest["components"].values():
        dest = files_root / entry["file"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        source_name = next(src for src, dst, _ in COMPONENTS.values()
                           if dst == entry["file"])
        shutil.copyfile(build_dir / source_name, dest)
        dest.chmod(0o755 if entry["format"] == "ELF64" else 0o644)
        if file_digest(dest) != entry["sha256"]:
            raise ValueError("Bundle hash mismatch")
    for name, (source_name, bundled) in SOURCE_FILES.items():
        source = source_file(build_dir, source_name)
        dest = output / bundled
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
        dest.chmod(0o644)
        if file_digest(dest) != manifest["source_files"][name]["sha256"]:
            raise ValueError("Wine corresponding source/license mismatch")
    payload = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    (output / "manifest.json").write_text(payload, encoding="utf-8")
    archive = output.parent / "charoite-wine-arm64ec-base-slice.tar.gz"
    if archive.exists():
        raise FileExistsError(f"Refusing to overwrite archive: {archive}")
    # Reproducible archive metadata, no parent paths, and no symlinks.
    with archive.open("wb") as sink, gzip.GzipFile(
        filename="", mode="wb", fileobj=sink, mtime=0
    ) as compressed, tarfile.open(mode="w", fileobj=compressed) as tar:
        for path in [output / "manifest.json", *sorted(files_root.rglob("*")),
                     *sorted((output / "source").rglob("*"))]:
            if not path.is_file():
                continue
            relative = path.relative_to(output).as_posix()
            info = tarfile.TarInfo(relative)
            info.size = path.stat().st_size
            info.mode = 0o755 if relative.startswith("slice/bin/") else 0o644
            info.uid = 0
            info.gid = 0
            info.mtime = 0
            with path.open("rb") as handle:
                tar.addfile(info, handle)
    report = output.parent / "charoite-slice-validation.txt"
    report.write_text(
        "CHAROITE_WINE_SLICE_ABI_CHECK=PASS\n"
        "ANDROID_PACKAGE=com.charoitx\n"
        "LAUNCH_READY=false\n"
        f"SOURCE_COMMIT={SOURCE_SHA}\n"
        f"ARCHIVE_SHA256={file_digest(archive)}\n"
        f"ARCHIVE_SIZE={archive.stat().st_size}\n",
        encoding="utf-8",
    )
    return archive


def main(argv: list[str]) -> int:
    if len(argv) != 5:
        print("Usage: package-runtime-slice.py ABS_BUILD_DIR ABS_OUTPUT_DIR ABS_READELF ABS_READOBJ", file=sys.stderr)
        return 2
    build_dir, output, readelf, readobj = map(Path, argv[1:])
    if not all(p.is_absolute() for p in (build_dir, output, readelf, readobj)):
        raise ValueError("All arguments must use absolute paths")
    archive = package(build_dir, output, str(readelf), str(readobj))
    print(f"CHAROITE_WINE_SLICE_ABI_CHECK=PASS: {archive}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
