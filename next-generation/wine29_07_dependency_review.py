#!/usr/bin/env python3
"""Wine29 0.7 source-verified direct-import owner review; CI only.

Audit the exact immutable source archive used by the phone, then attribute
unbundled imported DLL names to each referencing Windows PE module.
Does not compile, run Wine/Wineboot/PE, modify prefixes or access phone data.
This is a *static import inventory*, not a runnable-loader certification.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

SOURCE = "c74acb09d51b447f5d5ac56c87608d3ec565a767"
VERSION = "wine10-arm64ec-bootstrap.0.7"
SHA256 = "66068032bd2203c8e53fddc92ce46b84086eb293306b2bd12bb741bf9a5e035e"
PHONE_GAP = ("coml2.dll", "imm32.dll", "oleacc.dll", "oleaut32.dll", "shcore.dll")
PHONE_DLLS = 23
PHONE_NLS = 76
PHONE_IMPORT_DESCRIPTORS = 111
PHONE_DISTINCT_IMPORTS = 21
IDENTIFIER = re.compile(r"[a-z0-9_]+")
DLL = re.compile(r"[a-z0-9_.-]+\.dll")


def inspect(manifest: dict, attestation: dict) -> dict:
    """Only accepts a complete 27-component verified Wine29 source cohort."""
    if (manifest.get("version") != VERSION or
        manifest.get("source_commit") != SOURCE or
        manifest.get("component_count") != 27 or
        manifest.get("nls_count") != PHONE_NLS):
        raise ValueError("Untrusted Wine29 source generation")
    components = manifest.get("components")
    if not isinstance(components, dict) or len(components) != 27:
        raise ValueError("Incomplete Wine29 27-component manifest")
    if set(name for name, item in components.items()
           if isinstance(item, dict) and item.get("format") == "ELF") != {
               "wine", "wineserver", "ntdll_unix"
           }:
        raise ValueError("Wine29 native ELF cohort mismatch")
    names = set()
    imported_by = {}
    pe = 0
    for component, item in components.items():
        if not isinstance(item, dict):
            raise ValueError("Invalid source manifest component")
        if item["format"] != "PE":
            continue
        pe += 1
        if (not IDENTIFIER.fullmatch(component) or
            not isinstance(item.get("imports"), list) or
            not all(isinstance(x, str) and DLL.fullmatch(x)
                    for x in item["imports"]) or
            len(item["imports"]) > 256 or
            len(set(item["imports"])) != len(item["imports"])):
            raise ValueError("Invalid source-verified import metadata: " + component)
        expected_path = ("runtime/pe/arm64/wineboot.exe" if component == "wineboot"
                         else "runtime/pe/arm64ec/" + component + ".dll")
        if item.get("path") != expected_path:
            raise ValueError("Wine29 source PE path mismatch: " + component)
        if component != "wineboot":
            names.add(component + ".dll")
        for dll in item["imports"]:
            imported_by.setdefault(dll, set()).add(
                "wineboot.exe" if component == "wineboot" else component + ".dll")
    if pe != 24 or len(names) != PHONE_DLLS or not {
        "ntdll.dll", "kernel32.dll", "apisetschema.dll"
    }.issubset(names):
        raise ValueError("Not exactly 23 independent Windows DLL and ARM64 wineboot PE")
    imported = sorted(imported_by)
    gaps = sorted(set(imported) - names)
    if (attestation.get("schema_version") != 1 or
        attestation.get("bundled_windows_dlls") != sorted(names) or
        attestation.get("observed_windows_imports") != imported or
        attestation.get("windows_imports_not_bundled") != gaps or
        manifest.get("window_imports_unresolved_count") != len(gaps)):
        raise ValueError("Independent dependency-review mismatch")
    if not set(PHONE_GAP).issubset(gaps):
        raise ValueError("Phone five direct imports missing from source audit: " +
                         ",".join(sorted(set(PHONE_GAP) - set(gaps))))
    source_only = sorted(set(gaps) - set(PHONE_GAP))
    return {
        "schema_version": 1,
        "purpose": "read-only source-verified Wine29 direct import ownership",
        "source_commit": SOURCE,
        "bundle_version": VERSION,
        "source_archive_sha256": SHA256,
        "phone_version": "11.2-next.0.66",
        "android_package": "com.charoitx",
        "pe_files": pe,
        "dll_files": len(names),
        "nls_files": PHONE_NLS,
        "source_distinct_imports": len(imported),
        "phone_distinct_imports": PHONE_DISTINCT_IMPORTS,
        "phone_import_descriptors": PHONE_IMPORT_DESCRIPTORS,
        "source_unbundled_imports": gaps,
        "phone_reported_direct_unbundled_imports": list(PHONE_GAP),
        "source_only_unbundled_imports": source_only,
        "source_unbundled_import_owners": {dll: sorted(imported_by[dll]) for dll in gaps},
        "phone_direct_import_owners": {
            dll: sorted(imported_by[dll]) for dll in PHONE_GAP
        },
        "scope_note": ("Pinned Wine source import inventory has broader scope than "
                       "the phone's regular PE import-table scan; source-only names "
                       "may include delay-load or other imports, not proven fatal."),
        "launch_ready": False,
        "windows_exe_executed": False,
        "wineboot_executed": False,
        "prefix_created": False,
        "not_proven": "Loader import resolution, working prefix and application compatibility"
    }


def review(archive: Path, output: Path) -> dict:
    archive = Path(archive)
    output = Path(output)
    if (not archive.is_absolute() or archive.is_symlink() or not archive.is_file() or
        not output.is_absolute() or output.is_symlink() or output.exists() or
        not output.parent.is_dir() or output.parent.is_symlink() or
        any(p in str(archive) + " " + str(output) for p in (
            "/data/data/", "/data/user/", "/storage/emulated/"
        ))):
        raise ValueError("Require fresh CI-only archive/output, never Android/user data")
    if hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
        raise ValueError("Pinned Wine29 0.7 archive digest mismatch")
    verifier = Path(__file__).resolve().parent / "charoite-wine/verify-bootstrap-bundle.py"
    spec = importlib.util.spec_from_file_location("wine29_import_verifier", verifier)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    manifest, attestation = module.verify(archive)
    result = inspect(manifest, attestation)
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("WINE29_07_PINNED_SOURCE_IMPORT_OWNER_AUDIT=PASS")
    print("PHONE_FIVE_IMPORTS_INCLUDED_IN_SOURCE_REVIEW=PASS")
    print("SOURCE_DISTINCT_IMPORTS=" + str(result["source_distinct_imports"]))
    print("SOURCE_UNBUNDLED_IMPORT_COUNT=" + str(len(result["source_unbundled_imports"])))
    print("SOURCE_ONLY_UNBUNDLED_IMPORT_COUNT=" + str(
        len(result["source_only_unbundled_imports"])))
    for dll, owners in result["source_unbundled_import_owners"].items():
        scope = "PHONE_DIRECT_AND_SOURCE" if dll in PHONE_GAP else "SOURCE_ONLY"
        print("UNBUNDLED_IMPORT_OWNER " + scope + " " + dll + ": " + ",".join(owners))
    print("WINE29_PE_EXECUTION=NOT_ATTEMPTED")
    print("WINDOWS_LAUNCH_READY=FALSE")
    return result


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: wine29_07_dependency_review.py ABS_PINNED_SOURCE_ARCHIVE ABS_NEW_JSON")
    review(Path(sys.argv[1]), Path(sys.argv[2]))
