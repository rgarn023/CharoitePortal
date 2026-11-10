#!/usr/bin/env python3
"""Read-only SOURCE/ARTIFACT audit for Wine29 ARM64 DefaultInstall CopyFiles.

Never runs Wine or accesses an Android device/prefix. Inputs are a checksummed
CI-generated wine.inf and the immutable 111-file sealed PE/NLS archive.
A provider missing from the sealed cohort means coverage is UNCONFIRMED; it
does not prove a Wine copy failure or a service installation failure.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re

EXPECTED_INF_SHA = "5c7a7041399370937bdaaec11bac8ab64b910d6a1877b6afb582ad1d6a2f894a"
EXPECTED_SECTIONS = ("colorfiles", "etcfiles", "inffiles", "nlsfiles", "sortfiles")
MAX_INF = 1024 * 1024
MAX_REPORT = 32 * 1024

def parse_sections(inf: str) -> dict[str, list[str]]:
    if not inf or len(inf) > MAX_INF or "\x00" in inf:
        raise ValueError("Missing, oversized or binary Wine INF")
    sections: dict[str, list[str]] = {}
    section = None
    for raw in inf.splitlines():
        line = raw.strip()
        if not line or line.startswith(";"):
            continue
        if line.startswith("["):
            if not line.endswith("]"):
                raise ValueError("Malformed INF section")
            section = line[1:-1].lower()
            if not re.fullmatch(r"[a-z0-9_.-]+", section) or section in sections:
                raise ValueError("Duplicate/unsafe INF section")
            sections[section] = []
            continue
        if section is None:
            raise ValueError("INF content outside section")
        sections[section].append(line)
    return sections

def audit(inf: str, sealed_names: set[str]) -> dict:
    sections = parse_sections(inf)
    install = sections.get("defaultinstall.ntarm64")
    if not install:
        raise ValueError("ARM64 install section missing")
    copies = [line.split("=", 1)[1] for line in install
              if re.match(r"(?i)^copyfiles\s*=", line)]
    if len(copies) != 1:
        raise ValueError("ARM64 CopyFiles directive missing/ambiguous")
    names = tuple(part.strip().lower() for part in copies[0].split(","))
    if names != EXPECTED_SECTIONS:
        raise ValueError("Unexpected ARM64 CopyFiles sections/order")
    if any(not sections.get(name) for name in names):
        raise ValueError("Missing/empty CopyFiles source section")
    if not any(re.match(r"(?i)^addservice\s*=\s*rpcss\s*,", line)
               for line in sections.get("defaultinstall.ntarm64.services", [])):
        raise ValueError("Pinned INF does not declare RpcSs service registration")
    if len(sealed_names) != 111 or len(set(sealed_names)) != 111:
        raise ValueError("Unexpected sealed file count")
    pe_names = {path.split("/")[-1].lower() for path in sealed_names
                if path.startswith("data/pe/arm64ec/")}
    nls_names = {path.split("/")[-1].lower() for path in sealed_names
                 if path.startswith("data/nls/")}
    if len(pe_names) != 34 or len(nls_names) != 76:
        raise ValueError("Unexpected pinned PE/NLS cohort")
    count = 0
    nls_requested, providers = set(), set()
    for name in names:
        for row in sections[name]:
            if row.startswith(";"):
                continue
            count += 1
            item = row.split(",", 1)[0].strip().lower()
            if name in ("nlsfiles", "sortfiles"):
                if not re.fullmatch(r"[a-z0-9_]+\.nls", item):
                    raise ValueError("Unexpected NLS CopyFiles item")
                nls_requested.add(item)
            else:
                # Wine INF resource rows use embedded @%11% and @%12%
                # provider PE images to create system/INF files.
                match = re.search(r"(?i)@%1[12]%\\([a-z0-9_]+\.(?:dll|sys))", row)
                if not match:
                    raise ValueError("Unrecognized non-NLS resource copy source")
                providers.add(match.group(1).lower())
    return {
        "source_only": True,
        "wine_executed": False,
        "phone_accessed": False,
        "v28_reused": False,
        "rpcss_registration_declared": True,
        "arm64_copy_sections": list(names),
        "copyfile_rows": count,
        "requested_nls_count": len(nls_requested),
        "sealed_nls_count": len(nls_names),
        "requested_nls_not_in_sealed": sorted(nls_requested - nls_names),
        "resource_provider_count": len(providers),
        "resource_providers_in_sealed_pe": sorted(providers & pe_names),
        "resource_providers_not_in_sealed_pe": sorted(providers - pe_names),
        "interpretation": (
            "Sealed cohort coverage only. Absent PE resource providers may "
            "be available from other Wine components; neither absence nor "
            "the observed V28 copy/rename error proves SCM failure."
        ),
    }

def audit_artifacts(inf_path: Path, archive_path: Path) -> dict:
    if (inf_path.is_symlink() or not inf_path.is_file()
            or not 4096 < inf_path.stat().st_size < MAX_INF):
        raise ValueError("Unsafe generated INF input")
    data = inf_path.read_bytes()
    if hashlib.sha256(data).hexdigest() != EXPECTED_INF_SHA:
        raise ValueError("Pinned generated INF hash differs")
    root = Path(__file__).resolve().parents[2]
    stage = root / "next-generation/stage_wine29_sealed012.py"
    spec = importlib.util.spec_from_file_location("charoite_sealed012_audit", stage)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    manifest, payload = module.validate_archive(archive_path)
    if manifest["file_count"] != 111:
        raise ValueError("Unexpected pinned source archive")
    return audit(data.decode("utf-8-sig"), set(payload))

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inf", type=Path, required=True)
    parser.add_argument("--sealed", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit_artifacts(args.inf, args.sealed)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if len(encoded) > MAX_REPORT:
        raise ValueError("Audit result exceeds bound")
    if args.out.is_symlink() or args.out.exists():
        raise ValueError("Never overwrite source audit output")
    args.out.write_text(encoded, encoding="utf-8")
    print("WINE29_ARM64_COPYQUEUE_PINNED_SOURCE_AUDIT=PASS")
    print("COPYFILE_ROWS=" + str(result["copyfile_rows"]))
    print("UNSTAGED_NLS_COUNT=" + str(len(result["requested_nls_not_in_sealed"])))
    print("UNSTAGED_PE_RESOURCE_PROVIDER_COUNT=" +
          str(len(result["resource_providers_not_in_sealed_pe"])))
    print("SCM_RUNNING_STATUS=UNPROVEN")
    print("NO_WINE_NO_APK_NO_PHONE_NO_V28=PASS")

if __name__ == "__main__":
    main()
