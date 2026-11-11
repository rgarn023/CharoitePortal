#!/usr/bin/env python3
"""Read-only PE regular-vs-delay import audit for pinned Wine29 source artifacts.

No PE or Wine execution, writes only a NEW report in runner scratch.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import stat
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = "66068032bd2203c8e53fddc92ce46b84086eb293306b2bd12bb741bf9a5e035e"
SOURCE_SHA = "c74acb09d51b447f5d5ac56c87608d3ec565a767"
SIX_HASHES = {
    "coml2": "2f5deaaf28bfeb97d44767264a0b0869ad3e5f5f2d6620bf39a8aad9968c895a",
    "imm32": "214fa5e31c2115c67644082b200f3c95b573b9ebcd0da2694f79805d2a9d8d57",
    "oleacc": "affcec1ad92002fc244173a5c67bb9f28eacbed5dd1a3b0c76801d1e511eb4b8",
    "oleaut32": "716b6caba103fed51da033566cc6e9e10abcb32cba8f985e1c9216c9038a39b5",
    "shcore": "50e99aae9e44d9e3e957bcc4f20744fcc15312dc938fe1c883e2c6341f5cf50e",
    "newdev": "0a453688ed08910a363f0d32d1617bba0a85963e8348c1506a79c27bbec1ed92",
}
TWO_HASHES = {
    "urlmon": "7d154ecbebafd484b91d1106ba57162fe52d60c828318aa467906f5b2385e3ee",
    "windowscodecs": "baa2a1bb5472f2f3a3af7a83f6198e68aa7d46df5c653334d3beb3bdb67f1f15",
}
PHONE_FIVE = {"coml2.dll", "imm32.dll", "oleacc.dll", "oleaut32.dll", "shcore.dll"}
# Kernel-mode drivers may import ntoskrnl.exe; do not reject valid PE import names.
IDENTIFIER = re.compile(r"[a-z0-9_.+-]+\.(dll|drv|exe)\Z")
FORBIDDEN = ("/data/data/", "/data/user/", "/storage/emulated/", "/sdcard/")


def safe_bytes(file: Path, maximum: int = 64 * 1024 * 1024) -> bytes:
    info = file.lstat()
    if file.is_symlink() or not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= maximum:
        raise ValueError("Unsafe or missing immutable input: " + str(file))
    result = file.read_bytes()
    if len(result) != info.st_size:
        raise ValueError("Input changed while reading")
    return result


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pe_imports(data: bytes) -> tuple[list[str], list[str]]:
    """Parse actual PE IMAGE_IMPORT_DESCRIPTOR and delay-load directory, bounded."""
    def u16(at: int) -> int:
        if at < 0 or at + 2 > len(data):
            raise ValueError("PE header out of bounds")
        return struct.unpack_from("<H", data, at)[0]

    def u32(at: int) -> int:
        if at < 0 or at + 4 > len(data):
            raise ValueError("PE header out of bounds")
        return struct.unpack_from("<I", data, at)[0]

    if len(data) < 256 or data[:2] != b"MZ":
        raise ValueError("Missing DOS PE header")
    pe = u32(0x3c)
    if pe < 64 or pe + 24 > len(data) or data[pe:pe+4] != b"PE\x00\x00":
        raise ValueError("Invalid PE offset/signature")
    machine = u16(pe + 4)
    if machine not in (0xAA64, 0xA641):
        raise ValueError("Unexpected Wine29 PE carrier machine")
    sections = u16(pe + 6)
    optional_size = u16(pe + 20)
    opt = pe + 24
    if (sections < 1 or sections > 64 or optional_size < 224 or
            opt + optional_size + 40 * sections > len(data) or u16(opt) != 0x20b):
        raise ValueError("Unsupported/truncated PE32+ image")
    image_base = struct.unpack_from("<Q", data, opt + 24)[0]
    section_table = opt + optional_size
    segments = []
    for n in range(sections):
        row = section_table + 40*n
        virt_size, virt_addr, raw_size, raw_off = struct.unpack_from("<IIII", data, row + 8)
        if raw_size and (raw_off + raw_size > len(data)):
            raise ValueError("Truncated section bytes")
        segments.append((virt_addr, raw_size, raw_off))

    def resolve(rva: int, length: int = 1) -> int:
        # The entire requested range must belong to one file-backed section.
        # A directory starting in a section but spilling into unrelated bytes
        # must not be accepted merely because the overall file is large enough.
        for virtual, size, off in segments:
            if size and virtual <= rva and length > 0 and rva + length <= virtual + size:
                return off + rva - virtual
        raise ValueError("PE import RVA range not backed by file section")

    def dll_name(rva: int) -> str:
        at = resolve(rva)
        # Require the terminator to remain in the same section as the name.
        max_name = 129
        for virtual, size, off in segments:
            if size and virtual <= rva < virtual + size:
                max_name = min(max_name, virtual + size - rva)
                break
        end = data.find(b"\x00", at, min(at + max_name, len(data)))
        if end < 0:
            raise ValueError("Unterminated PE DLL import name")
        try:
            name = data[at:end].decode("ascii").lower()
        except UnicodeDecodeError as e:
            raise ValueError("Non-ascii PE import name") from e
        if not IDENTIFIER.fullmatch(name):
            raise ValueError("Unexpected PE import name: " + name)
        return name

    def directory(index: int) -> tuple[int, int]:
        if u32(opt + 108) <= index:
            return (0, 0)
        offset = opt + 112 + index*8
        if offset + 8 > opt + optional_size:
            raise ValueError("Unbounded PE data directory")
        return u32(offset), u32(offset + 4)

    ordinary, deferred = [], []
    for index, size, result in ((1, 20, ordinary), (13, 32, deferred)):
        rva, total = directory(index)
        if bool(rva) != bool(total):
            raise ValueError("Inconsistent PE import directory RVA/size")
        if not rva:
            continue
        if total < size or total > 1_000_000:
            raise ValueError("Invalid PE import directory size")
        at = resolve(rva, total)
        if at + total > len(data):
            raise ValueError("Invalid PE import directory size")
        terminated = False
        for n in range(min(512, total // size)):
            loc = at + n*size
            row = struct.unpack_from("<"+"I"*(size//4), data, loc)
            if not any(row):
                terminated = True
                break
            name_rva = row[3] if index == 1 else row[1]
            if index == 13 and not (row[0] & 1):
                if name_rva < image_base:
                    raise ValueError("Invalid delay-load VA")
                name_rva -= image_base
            result.append(dll_name(name_rva))
        if not terminated:
            raise ValueError("Import table lacks null terminator")
    return ordinary, deferred


def load_module(path: Path, label: str):
    spec = importlib.util.spec_from_file_location(label, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def analyze(archive: Path, six: Path, two: Path) -> dict:
    for p in (archive, six, two):
        if not p.is_absolute() or p.is_symlink() or any(s in str(p) for s in FORBIDDEN):
            raise ValueError("Must use isolated absolute source artifact paths")
    if six.resolve() == two.resolve() or not six.is_dir() or not two.is_dir():
        raise ValueError("Separate six and two candidate cohorts required")
    if sha(safe_bytes(archive, 128*1024*1024)) != BASE_SHA:
        raise ValueError("Pinned Wine29 source archive SHA mismatch")
    verifier = load_module(ROOT/"charoite-wine/verify-bootstrap-bundle.py", "wine29_pe_static_source")
    manifest, _ = verifier.verify(archive)
    if (manifest.get("source_commit") != SOURCE_SHA or
            manifest.get("version") != "wine10-arm64ec-bootstrap.0.7" or
            manifest.get("component_count") != 27 or manifest.get("nls_count") != 76):
        raise ValueError("Mixed baseline source generation")
    # Verify pinned candidate binaries AND their CI audit manifests, not filenames alone.
    six_report = json.loads(safe_bytes(six/"wine29-07-six-candidates.json"))
    two_report = json.loads(safe_bytes(two/"wine29-07-eight-candidate-import-review.json"))
    if (six_report.get("source_commit") != SOURCE_SHA or
            six_report.get("baseline_source_archive_sha256") != BASE_SHA or
            two_report.get("source_commit") != SOURCE_SHA or
            two_report.get("source_archive_sha256") != BASE_SHA or
            set(six_report.get("components", {})) != set(SIX_HASHES) or
            set(two_report.get("components", {})) != set(TWO_HASHES) or
            six_report.get("launch_ready") is not False or
            two_report.get("launch_ready") is not False):
        raise ValueError("Candidate source/provenance mismatch")
    import tarfile
    with tarfile.open(archive, "r:gz") as tar:
        baseline_pe = {
            ("wineboot.exe" if name == "wineboot" else name+".dll"):
                tar.extractfile(item["path"]).read()
            for name, item in manifest["components"].items()
            if item["format"] == "PE"
        }
    if len(baseline_pe) != 24:
        raise ValueError("Expected 23 DLL and separate wineboot")
    all_pe = dict(baseline_pe)
    for root, expected, report in ((six, SIX_HASHES, six_report),
                                    (two, TWO_HASHES, two_report)):
        for name, expected_sha in expected.items():
            data = safe_bytes(root / (name+"-arm64ec.dll"))
            if sha(data) != expected_sha or report["components"][name]["sha256"] != expected_sha:
                raise ValueError("Source-verified candidate binary SHA drift: " + name)
            all_pe[name+".dll"] = data
    provided = set(all_pe) - {"wineboot.exe"}
    def inspect(items: dict[str, bytes]) -> dict:
        local_providers = {name for name in items if name.endswith(".dll")}
        regular, delayed = {}, {}
        for name, data in items.items():
            reg, defer = pe_imports(data)
            regular[name] = reg
            delayed[name] = defer
        def owners(data: dict[str, list[str]]) -> dict[str, list[str]]:
            referenced = {d for ds in data.values() for d in ds}
            return {dep: sorted(name for name, ds in data.items() if dep in ds)
                    for dep in sorted(referenced - local_providers)}
        return {
            "pe_files": len(items),
            "regular_descriptors": sum(len(d) for d in regular.values()),
            "regular_distinct": len({d for ds in regular.values() for d in ds}),
            "regular_unbundled_owners": owners(regular),
            "delay_descriptors": sum(len(d) for d in delayed.values()),
            "delay_unbundled_owners": owners(delayed),
        }
    original = inspect(baseline_pe)
    expanded = inspect(all_pe)
    # Exact Galaxy v0.66 phone audit regression from the *same* baseline source.
    if (original["regular_descriptors"] != 111 or
            original["regular_distinct"] != 21 or
            set(original["regular_unbundled_owners"]) != PHONE_FIVE or
            expanded["pe_files"] != 32 or len(provided) != 31 or
            set(expanded["regular_unbundled_owners"]) != {"wininet.dll", "propsys.dll"} or
            "winspool.drv" not in expanded["delay_unbundled_owners"]):
        raise ValueError("PE import classification disagrees with pinned evidence")
    return {
        "schema_version": 1, "source_commit": SOURCE_SHA,
        "source_archive_sha256": BASE_SHA, "provider_dll_count": len(provided),
        "baseline_phone_regression": original,
        "expanded_pe_imports": expanded,
        "next_regular_import_candidates": ["propsys.dll", "wininet.dll"],
        "delay_load_not_proven_startup_required": True,
        "regular_import_resolution_not_proven_at_runtime": True,
        "currency_boundary_rounding_unverified": True,
        "wineboot_executed": False, "windows_exe_executed": False,
        "prefix_created": False, "phone_installed": False, "launch_ready": False
    }


def main(args: list[str]) -> None:
    if len(args) != 4:
        raise SystemExit("Usage: classify.py ABS_BASELINE_TARGZ ABS_SIX_DIR ABS_TWO_DIR ABS_NEW_REPORT")
    archive, six, two, report = map(Path, args)
    if (not report.is_absolute() or report.exists() or report.is_symlink() or
            not report.parent.is_dir() or any(p in str(report) for p in FORBIDDEN)):
        raise ValueError("Refusing report overwrite or user storage")
    result = analyze(archive, six, two)
    report.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print("WINE29_ORIGINAL_GALAXY_REGULAR_IMPORTS_111_DESCRIPTORS_5_MISSING=PASS")
    print("WINE29_31_DLL_REGULAR_PE_UNBUNDLED_ONLY_PROPSYS_AND_WININET=PASS")
    print("WINE29_DELAY_IMPORTS_SEPARATELY_REPORTED_INCLUDING_WINSPool_DRV=PASS")
    print("WINE29_IMPORT_CLASSIFICATION_SOURCE_ONLY_NOT_RUNNABLE=PASS")


if __name__ == "__main__":
    main(sys.argv[1:])
