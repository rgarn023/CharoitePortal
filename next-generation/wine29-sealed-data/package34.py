#!/usr/bin/env python3
"""Sealed, reproducible Wine29 34-DLL + Wineboot + NLS DATA archive, CI only.

Never executes Wine, Wineboot, PE, wineserver, or modifies Android/prefix data.
Native ELF files are excluded, with source-verified hashes recorded separately.
"""
from __future__ import annotations

import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import stat
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
GENERATION = "wine10-arm64ec-dependencies.0.12-sealed-data-candidate"
RUNS = {"baseline": 41749167248, "six": 41938936238,
        "two": 41940958989, "direct": 41943773293, "mpr": 41943773293}
MAX_MEMBER = 64 * 1024 * 1024


def load(path, label):
    spec = importlib.util.spec_from_file_location(label, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = load(ROOT / "wine29-imports/verify34.py", "wine29_34_verified_input_gate")
prior = gate.prior


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_output(path: Path) -> None:
    if (not path.is_absolute() or path.is_symlink() or
            path.exists() or not path.parent.is_dir() or
            any(s in str(path) for s in prior.FORBIDDEN)):
        raise ValueError("Refuse overwrite, Android storage, link, or relative archive path")


def source_snapshot(base: Path, six: Path, two: Path, direct: Path, mpr: Path):
    # This gate validates pinned archive SHA, ALL independent candidate manifests
    # and SHA-256s, PE headers, and ALL 35 ordinary/delay import tables.
    report = gate.inspect(base, six, two, direct, mpr)
    if (report["provider_count"] != 34 or report["pe_image_count"] != 35 or
            report["ordinary_import_descriptors"] != 186 or
            report["delayed_import_descriptors"] != 68 or
            report["regular_unbundled_import_names"] or
            len(report["delayed_import_owners_outside_cohort"]) != 15):
        raise ValueError("Source-only import-graph baseline changed")

    payload = {}
    stages = {}
    native = {}
    with tarfile.open(base, "r:gz") as archive:
        manifest = json.load(archive.extractfile("manifest.json"))
        for name, item in sorted(manifest["components"].items()):
            raw = archive.extractfile(item["path"]).read()
            if sha(raw) != item["sha256"] or len(raw) != item["size"]:
                raise ValueError("Source archive component drift: " + name)
            if item["format"] == "ELF":
                native[name] = {"source_path": item["path"],
                                "size": len(raw), "sha256": sha(raw)}
            elif item["format"] == "PE":
                dest = ("data/pe/arm64/wineboot.exe" if name == "wineboot"
                        else "data/pe/arm64ec/" + name + ".dll")
                payload[dest] = raw
                stages[dest] = "baseline"
            else:
                raise ValueError("Unknown source component")
        for name, item in sorted(manifest["nls_files"].items()):
            raw = archive.extractfile(item["path"]).read()
            if sha(raw) != item["sha256"] or len(raw) != item["size"]:
                raise ValueError("Source archive NLS drift: " + name)
            dest = "data/nls/" + name
            payload[dest] = raw
            stages[dest] = "baseline"

    if set(native) != {"wine", "wineserver", "ntdll_unix"}:
        raise ValueError("Three original native ELF provenance entries required")
    for cohort, folder, names in (
            ("six", six, tuple(prior.SIX_HASHES)),
            ("two", two, tuple(prior.TWO_HASHES)),
            ("direct", direct, ("propsys", "wininet")),
            ("mpr", mpr, ("mpr",))):
        for name in names:
            dest = "data/pe/arm64ec/" + name + ".dll"
            if dest in payload:
                raise ValueError("Duplicate candidate PE module: " + name)
            payload[dest] = prior.safe_bytes(folder / (name + "-arm64ec.dll"))
            stages[dest] = cohort

    names = [p for p in payload if p.startswith("data/pe/arm64ec/")]
    nls = [p for p in payload if p.startswith("data/nls/")]
    if len(names) != 34 or len(nls) != 76 or len(payload) != 111:
        raise ValueError("Expected exactly 34 DLL + one Wineboot + 76 NLS")

    # Re-evaluate graph on the exact output data, not only source manifests.
    pe = {p.rsplit("/", 1)[-1]: b for p, b in payload.items()
          if p.startswith("data/pe/")}
    regular, delayed = {}, {}
    for name, data in pe.items():
        regular[name], delayed[name] = prior.pe_imports(data)
    providers = set(pe) - {"wineboot.exe"}

    def owners(table):
        refs = {name for values in table.values() for name in values}
        return {name: sorted(owner for owner, values in table.items() if name in values)
                for name in sorted(refs - providers)}

    if (owners(regular) or
            owners(delayed) != report["delayed_import_owners_outside_cohort"] or
            sum(map(len, regular.values())) != 186 or
            sum(map(len, delayed.values())) != 68):
        raise ValueError("Assembled PE import graph differs from independent closure")

    files = {
        path: {"sha256": sha(data), "size": len(data), "cohort": stages[path]}
        for path, data in sorted(payload.items())
    }
    record = {
        "schema_version": 1, "generation": GENERATION,
        "android_package": "com.charoitx",
        "source_commit": prior.SOURCE_SHA,
        "baseline_source_archive_sha256": prior.BASE_SHA,
        "immutable_source_run_ids": RUNS,
        "file_count": 111, "pe_dll_count": 34, "wineboot_pe_count": 1,
        "nls_count": 76, "native_elf_files_in_bundle": 0,
        "native_elf_source_provenance_only": native,
        "files": files,
        "regular_import_descriptors": 186,
        "regular_unbundled_import_names": [],
        "delay_import_descriptors": 68,
        "delayed_import_owners_outside_cohort":
            report["delayed_import_owners_outside_cohort"],
        "portable_currency_rounding_equivalence_proven": False,
        "native_loader_resolution_proven": False,
        "source_only": True, "data_only": True,
        "wineboot_executed": False, "windows_exe_executed": False,
        "wineserver_executed": False, "prefix_created": False,
        "phone_installed": False, "launch_ready": False
    }
    return payload, record


def record_bytes(record: dict) -> bytes:
    return (json.dumps(record, sort_keys=True, indent=2) + "\n").encode("utf-8")


def write_archive(path: Path, payload: dict, record: dict) -> None:
    safe_output(path)
    data = {**payload, "manifest.json": record_bytes(record)}
    with path.open("xb") as out:
        with gzip.GzipFile(filename="", fileobj=out, mode="wb", mtime=0,
                           compresslevel=9) as zipped:
            with tarfile.open(fileobj=zipped, mode="w",
                              format=tarfile.USTAR_FORMAT) as tar:
                for name, raw in sorted(data.items()):
                    if not (0 < len(raw) <= MAX_MEMBER):
                        raise ValueError("Unsafe artifact item size")
                    member = tarfile.TarInfo(name)
                    member.size = len(raw)
                    member.mode = 0o444
                    member.mtime = member.uid = member.gid = 0
                    member.uname = member.gname = ""
                    tar.addfile(member, io.BytesIO(raw))


def validate_members(members, expected: set[str]) -> None:
    if len(members) != len(expected) or {m.name for m in members} != expected:
        raise ValueError("Duplicate, extra, or missing sealed archive member")
    for m in members:
        if (not m.isfile() or m.issym() or not 0 < m.size <= MAX_MEMBER or
                m.mode != 0o444 or m.uid != 0 or m.gid != 0 or m.mtime != 0 or
                m.name.startswith("/") or ".." in m.name.split("/")):
            raise ValueError("Invalid sealed archive member/type/permissions")


def verify_archive(path: Path, payload: dict, record: dict) -> str:
    if (not path.is_absolute() or path.is_symlink() or not path.is_file() or
            any(s in str(path) for s in prior.FORBIDDEN)):
        raise ValueError("Refuse missing/linked/user-storage artifact")
    data = {**payload, "manifest.json": record_bytes(record)}
    with tarfile.open(path, "r:gz") as archive:
        members = archive.getmembers()
        validate_members(members, set(data))
        for name, original in data.items():
            item = archive.extractfile(name).read()
            if item != original:
                raise ValueError("Archived module, NLS or manifest SHA drift: " + name)
    return sha(path.read_bytes())


def main(args):
    if len(args) != 7 or args[0] not in {"build", "verify"}:
        raise SystemExit(
            "Usage: package34.py build|verify ABS_BASELINE_TAR ABS_SIX ABS_TWO "
            "ABS_DIRECT ABS_MPR ABS_DATA_ONLY_TARGZ")
    op = args[0]
    base, six, two, direct, mpr, dest = (Path(p) for p in args[1:])
    payload, record = source_snapshot(base, six, two, direct, mpr)
    if op == "build":
        write_archive(dest, payload, record)
    hashval = verify_archive(dest, payload, record)
    print("WINE29_07_34_DLL_76_NLS_SEALED_DATA_ONLY=PASS")
    print("WINE29_07_111_FILES_AND_NATIVE_ELF_PROVENANCE_SEPARATED=PASS")
    print("WINE29_07_ORDINARY_IMPORT_GAPS=0")
    print("WINE29_07_WINEBOOT_AND_PHONE_EXECUTION=NOT_ATTEMPTED")
    print("ARCHIVE_SHA256=" + hashval)


if __name__ == "__main__":
    main(sys.argv[1:])
