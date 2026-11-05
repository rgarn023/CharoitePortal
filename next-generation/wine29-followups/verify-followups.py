#!/usr/bin/env python3
"""Source-only Wine29 +6+2 static import inventory; never execute PE/Wine."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import stat
import sys

ROOT = Path(__file__).resolve().parents[1]
BASELINE_SHA = "66068032bd2203c8e53fddc92ce46b84086eb293306b2bd12bb741bf9a5e035e"
SOURCE = "c74acb09d51b447f5d5ac56c87608d3ec565a767"
EXTRA = ("urlmon", "windowscodecs")
OUTPUT = "wine29-07-eight-candidate-import-review.json"
FORBIDDEN = ("/data/data/", "/data/user/", "/storage/emulated/", "/sdcard/")


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sixlib = load(ROOT / "wine29-deps/verify-wine29-deps.py", "wine29_six_verifier")
bundlelib = load(ROOT / "charoite-wine/verify-bootstrap-bundle.py", "wine29_source_bundle")


def import_closure(baseline: dict, six: dict, extra: dict) -> dict:
    """Conservative graph: report missing names, not loader readiness."""
    components = baseline.get("components", {})
    if (baseline.get("source_commit") != SOURCE or
        baseline.get("version") != "wine10-arm64ec-bootstrap.0.7" or
        len(components) != 27 or
        set(six) != set(sixlib.MODULES) or set(extra) != set(EXTRA)):
        raise ValueError("Unmatched source cohorts")
    providers = {name + ".dll" for name, v in components.items()
                 if v.get("format") == "PE" and name != "wineboot"}
    if len(providers) != 23:
        raise ValueError("Original 23 PE providers missing")
    providers |= {name + ".dll" for name in six} | {name + ".dll" for name in extra}
    owners = {}
    for name, info in components.items():
        if info.get("format") != "PE":
            continue
        label = "wineboot.exe" if name == "wineboot" else name + ".dll"
        imports = info.get("imports")
        if not isinstance(imports, list):
            raise ValueError("Incomplete baseline import inventory")
        for dep in imports:
            owners.setdefault(dep.lower(), set()).add(label)
    for cohort in (six, extra):
        for name, info in cohort.items():
            for dep in info["imports"]:
                owners.setdefault(dep.lower(), set()).add(name + ".dll")
    unresolved = {d: sorted(names) for d, names in sorted(owners.items())
                  if d not in providers}
    return {
        "provider_dll_count": len(providers),
        "observed_import_name_count": len(owners),
        "unresolved_import_names": sorted(unresolved),
        "unresolved_import_owners": unresolved,
        "new_two_imports": {n: extra[n]["imports"] for n in EXTRA},
    }


def safe_file(path: Path, max_size: int = 128 * 1024 * 1024) -> bytes:
    info = path.lstat()
    if path.is_symlink() or not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= max_size:
        raise ValueError("Not a safe regular source-only file: " + str(path))
    data = path.read_bytes()
    if len(data) != info.st_size:
        raise ValueError("File changed during review")
    return data


def inspect(archive: Path, six: Path, output: Path, readobj: Path) -> dict:
    for p in (archive, six, output, readobj):
        if not p.is_absolute() or p.is_symlink() or any(x in str(p) for x in FORBIDDEN):
            raise ValueError("Require absolute, isolated CI-only inputs")
    if output.resolve() == six.resolve() or not output.is_dir() or not readobj.is_file():
        raise ValueError("Must keep new two candidates separate from previous six")
    if hashlib.sha256(safe_file(archive)).hexdigest() != BASELINE_SHA:
        raise ValueError("Pinned original Wine29 archive hash differs")
    baseline, _ = bundlelib.verify(archive)
    audited_six = sixlib.run("verify", six, readobj)
    if (audited_six["source_commit"] != SOURCE or
        audited_six["baseline_source_archive_sha256"] != BASELINE_SHA or
        audited_six["component_count"] != 6 or
        audited_six["launch_ready"] is not False):
        raise ValueError("Six candidate source audit mismatch")
    extra = {name: sixlib.info_for(output, name, readobj) for name in EXTRA}
    graph = import_closure(baseline, audited_six["components"], extra)
    result = {
        "schema_version": 1,
        "generation": "wine10-arm64ec-dependencies.0.9-transitive-candidate",
        "source_commit": SOURCE,
        "source_archive_sha256": BASELINE_SHA,
        "six_candidate_generation": audited_six["generation"],
        "portability_patch_proof_sha256": audited_six["portability_patch_proof_sha256"],
        "component_count": 2,
        "components": extra,
        "merged_static_graph": graph,
        "not_proof_of_loader_dependency_closure": True,
        "not_proof_of_currency_rounding_equivalence": True,
        "source_only": True,
        "launch_ready": False,
        "wineboot_executed": False,
        "windows_exe_executed": False,
        "prefix_created": False,
        "device_tested": False,
        "installed": False,
    }
    return result


def run(mode: str, archive: Path, six: Path, output: Path, readobj: Path) -> dict:
    if mode not in ("create", "verify"):
        raise ValueError("Invalid follow-up audit mode")
    result = inspect(archive, six, output, readobj)
    report = output / OUTPUT
    if mode == "create":
        if report.exists() or report.is_symlink():
            raise ValueError("Refusing to overwrite existing report")
        report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    else:
        old = json.loads(safe_file(report).decode("utf-8"))
        if old != result:
            raise ValueError("Drift in copied PE, ARM64EC metadata or merged import graph")
        allowed = {OUTPUT}
        for name in EXTRA:
            allowed |= {name+"-arm64ec.dll",name+"-pe-header.txt",name+"-pe-imports.txt"}
        if {p.name for p in output.iterdir()} != allowed:
            raise ValueError("Unexpected file in new sealed two-DLL cohort")
    print("WINE29_07_TWO_NEW_SOURCE_BUILT_ARM64EC_DLLS=PASS")
    print("WINE29_07_EIGHT_CANDIDATE_MERGED_STATIC_IMPORT_GRAPH=PASS")
    print("STATIC_IMPORTS_OUTSIDE_23_PLUS_6_PLUS_2="+str(
        len(result["merged_static_graph"]["unresolved_import_names"])))
    print("WINEBOOT_AND_PHONE_EXECUTION=NOT_ATTEMPTED")
    return result


if __name__ == "__main__":
    if len(sys.argv) != 6:
        raise SystemExit("Usage: verify-followups.py create|verify ABS_ARCHIVE ABS_VERIFIED_SIX ABS_NEW_TWO ABS_LLVM_READOBJ")
    run(sys.argv[1], *(Path(s) for s in sys.argv[2:]))
