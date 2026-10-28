#!/usr/bin/env python3
"""Read-only ABI and dependency inventory of the Charoite Wine bootstrap slice.

Inspect the *same* CI cross-build tree. No prefix creation, extraction, install,
or executable launch is attempted. Unbundled imports are NOT proof of missing
runtime packages: only the seven selected bootstrap objects are inventoried.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import stat
import subprocess
import sys

SOURCE_COMMIT = "c74acb09d51b447f5d5ac56c87608d3ec565a767"
COMPONENTS = {
    "wine_loader": ("loader/wine", "elf"),
    "wineserver": ("server/wineserver", "elf"),
    "ntdll_unix": ("dlls/ntdll/ntdll.so", "elf"),
    "ntdll_arm64ec": ("dlls/ntdll/aarch64-windows/ntdll.dll", "arm64ec"),
    "kernelbase_arm64ec": ("dlls/kernelbase/aarch64-windows/kernelbase.dll", "arm64ec"),
    "kernel32_arm64ec": ("dlls/kernel32/aarch64-windows/kernel32.dll", "arm64ec"),
    "wineboot_arm64": ("programs/wineboot/aarch64-windows/wineboot.exe", "arm64"),
}

def run(*args: str) -> str:
    return subprocess.run(args, text=True, check=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE).stdout

def pe_imports(text: str) -> list[str]:
    # llvm-readobj --coff-imports reports imported DLLs as Name: DLLNAME.dll.
    # Do not confuse imported symbols with DLL filenames.
    return sorted({m.lower() for m in re.findall(
        r"^\s*Name:\s*([A-Za-z0-9_.+-]+\.dll)\s*$", text, flags=re.M)})

def elf_needed(text: str) -> list[str]:
    return sorted(set(re.findall(r"\(NEEDED\).*?\[([^\]]+)\]", text)))

def load_alignments(text: str) -> list[int]:
    values = []
    for line in text.splitlines():
        if re.match(r"^\s*LOAD\s", line):
            m = re.search(r"(0x[0-9a-fA-F]+)\s*$", line)
            if not m:
                raise ValueError("Cannot parse ELF PT_LOAD alignment")
            values.append(int(m.group(1), 16))
    if not values or any(v < 16384 for v in values):
        raise ValueError("ELF PT_LOAD segments must be 16 KiB compatible")
    return values

def pe_machine(header: str, expected: str) -> None:
    value = "0xA641" if expected == "arm64ec" else "0xAA64"
    label = "ARM64EC" if expected == "arm64ec" else "ARM64"
    if not re.search(
        rf"Machine:\s+(?:IMAGE_FILE_MACHINE_{label}|{label})\s+\({value}\)",
        header
    ):
        raise ValueError(f"Wrong Windows PE machine; expected {label} {value}")

def regular_nonempty_file(path: Path) -> None:
    st = path.lstat()
    if not stat.S_ISREG(st.st_mode) or path.is_symlink() or st.st_size == 0:
        raise ValueError("Required build input is not a regular nonempty file")

def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def inventory(build: Path, readelf: Path, readobj: Path) -> dict:
    if not build.is_absolute() or not all(p.is_absolute() and p.is_file() for p in (readelf, readobj)):
        raise ValueError("Expected absolute build and existing inspector paths")
    if not (build.parent / "charoite-source-validation.txt").is_file():
        raise ValueError("Unvalidated Charoite Wine source tree")
    if "com.charoite/" in str(build) or "com.touhoudr/" in str(build):
        raise ValueError("Stable app paths are not valid build inputs")
    result = {}
    for name, (rel, kind) in COMPONENTS.items():
        path = build / rel
        regular_nonempty_file(path)
        entry = {"path": rel, "size": path.stat().st_size, "sha256": digest(path)}
        if kind == "elf":
            header = run(str(readelf), "-h", str(path))
            if not re.search(r"Machine:\s+AArch64\b", header):
                raise ValueError("Android Wine object is not AArch64")
            headers = run(str(readelf), "-lW", str(path))
            entry.update({
                "format": "ELF", "machine": "AArch64",
                "load_alignments": load_alignments(headers),
                "needed": elf_needed(run(str(readelf), "-dW", str(path))),
            })
            m = re.search(r"\[Requesting program interpreter:\s*([^\]]+)\]", headers)
            entry["interpreter"] = m.group(1) if m else None
        else:
            pe_machine(run(str(readobj), "--file-headers", str(path)), kind)
            entry.update({
                "format": "PE", "machine": "0xA641" if kind == "arm64ec" else "0xAA64",
                "imports": pe_imports(run(str(readobj), "--coff-imports", str(path))),
            })
        result[name] = entry
    bundled_dlls = {"ntdll.dll", "kernelbase.dll", "kernel32.dll"}
    imports = {dll for x in result.values() for dll in x.get("imports", [])}
    external = {dll for x in result.values() for dll in x.get("needed", [])}
    return {
        "schema_version": 1,
        "purpose": "Bootstrap dependency inventory, not dependency closure",
        "source_commit": SOURCE_COMMIT,
        "android_package": "com.charoitx",
        "launch_ready": False,
        "installable": False,
        "prefix_created": False,
        "device_tested": False,
        "anti_cheat_supported": False,
        "components": result,
        "sampled_pe_dlls": sorted(bundled_dlls),
        "imports_not_in_sampled_pe_dlls": sorted(imports - bundled_dlls),
        "elf_needed_outside_sampled_slice": sorted(external),
        "next_steps": [
            "Resolve/import Wine PE/Unix modules, NLS and Android ELF dependencies",
            "Integrate FEX and graphics/display/input on a separated Next runtime",
            "Verify fresh isolated prefix and executable smoke tests on Galaxy",
        ],
    }

def main(argv: list[str]) -> int:
    if len(argv) != 5:
        print("Usage: audit-runtime-deps.py ABS_BUILD_DIR ABS_READELF ABS_READOBJ ABS_OUTPUT_DIR", file=sys.stderr)
        return 2
    build, readelf, readobj, output = map(Path, argv[1:])
    if not output.is_absolute() or output.exists() or not output.parent.is_dir():
        raise ValueError("Audit output must be new, with an existing parent")
    report = inventory(build, readelf, readobj)
    output.mkdir()
    (output / "runtime-dependency-inventory.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = (
        "CHAROITE_WINE_DEPENDENCY_AUDIT=PASS\n"
        f"COMPONENTS={len(report['components'])}\n"
        f"PE_IMPORTS_NOT_IN_SAMPLE={','.join(report['imports_not_in_sampled_pe_dlls'])}\n"
        f"ELF_NEEDED={','.join(report['elf_needed_outside_sampled_slice'])}\n"
        "LAUNCH_READY=false\nINSTALLABLE=false\nPREFIX_CREATED=false\n"
    )
    (output / "runtime-dependency-inventory.txt").write_text(summary, encoding="utf-8")
    print(summary, end="")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
