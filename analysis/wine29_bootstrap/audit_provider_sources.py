#!/usr/bin/env python3
"""Read-only pinned Wine29 provider SOURCE dependency audit. No PE execution.

Checks exact eight source Makefile blobs against the pinned source revision
and the sealed 111-file archive. A missing import in this cohort is only a
packaging coverage gap, NOT proof the runtime lacks the module elsewhere.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re

SOURCE_REV = "c74acb09d51b447f5d5ac56c87608d3ec565a767"
# Official blobs from the exact pinned The412Banner/proton-wine revision.
SOURCE_BLOBS = {
    "mscms.dll": ("mscms", "3033960279813fab5e20c8f4dbf45ad3a4de004a"),
    "hidclass.sys": ("hidclass.sys", "57a8fd792979e87eeeccc15ed13cf7d139c13656"),
    "mouhid.sys": ("mouhid.sys", "79bc38a92b4bdbaf44c40dfb9aa10f14a071eb1b"),
    "winebth.sys": ("winebth.sys", "12d1b4ddcc9f00b0e22b908ee6b217e87ca86b36"),
    "winebus.sys": ("winebus.sys", "db32faee5b382136e06c3068dd9436cc01c2f472"),
    "winehid.sys": ("winehid.sys", "c37e59f0d26a3c6db1606b4ef9df7d7ce7fb477c"),
    "wineusb.sys": ("wineusb.sys", "0c6bb77f14302733656db0f9ce4d8945f8c2f4a0"),
    "winexinput.sys": ("winexinput.sys", "64241631552e8befa031bfe515a38be877fa5097"),
}

def git_blob_sha(source: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(source)).encode() + b"\0" + source).hexdigest()

def parse_makefile(provider: str, text: str) -> dict:
    if provider not in SOURCE_BLOBS or not text or len(text) > 16384:
        raise ValueError("Unrecognized provider/source input")
    def value(field: str) -> str:
        matches = re.findall(r"(?m)^" + re.escape(field) + r"\s*=\s*(.*?)\s*$", text)
        if len(matches) > 1:
            raise ValueError("Duplicate Makefile field")
        return matches[0] if matches else ""
    if value("MODULE") != provider:
        raise ValueError("Provider Makefile MODULE mismatched")
    imports = value("IMPORTS").split()
    if not imports:
        raise ValueError("Provider has no declared imports")
    # Every token must be an ordinary Wine import or a recognized Make macro.
    # Never silently discard an unknown token: that understates the build
    # dependency closure and can incorrectly label a provider as buildable.
    macro_pattern = r"\$\([A-Z][A-Z_0-9]*\)"
    ordinary_pattern = r"[a-z0-9][a-z0-9_-]*"
    if any(not (re.fullmatch(ordinary_pattern, token) or
                re.fullmatch(macro_pattern, token)) for token in imports):
        raise ValueError("Unrecognized provider import or build expression")
    macros = sorted(set(token for token in imports
                        if re.fullmatch(macro_pattern, token)))
    native = value("UNIXLIB")
    # Source recipes for the pinned eight must not silently gain or lose
    # native companions. An arbitrary valid-looking .so name is not enough
    # evidence for the Android/Bionic dependency closure.
    expected_native = {
        "winebth.sys": "winebth.so",
        "winebus.sys": "winebus.so",
        "wineusb.sys": "wineusb.so",
    }.get(provider, "")
    if native != expected_native:
        raise ValueError("Pinned Unix companion identity changed")
    return {
        "module": provider,
        "imports": sorted(t for t in imports if re.fullmatch(ordinary_pattern, t)),
        "build_macros": macros,
        "unix_companion": native or None,
        "has_native_companion": bool(native),
    }

def strict_json_object(pairs: list[tuple[str, object]]) -> dict:
    """Reject duplicate JSON keys before source-only provenance validation.

    json.loads normally accepts repeated keys and retains only the final
    value, making a contradictory source_only/wine_executed/v28_reused
    assertion invisible to the next audit stage.
    """
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate key in CopyFiles audit JSON")
        result[key] = value
    return result


def parse_copyqueue_json(raw: str) -> dict:
    """Reject ambiguous or non-standard JSON values, including NaN."""
    def reject_constant(value: str) -> None:
        raise ValueError("Non-standard CopyFiles audit JSON constant")
    parsed = json.loads(raw, object_pairs_hook=strict_json_object,
                        parse_constant=reject_constant)
    if not isinstance(parsed, dict):
        raise ValueError("CopyFiles audit must be a JSON object")
    return parsed


def validate_copyqueue_provider_list(copyqueue: object) -> set[str]:
    """Require an unambiguous, exact source-only handoff from the INF audit.

    Converting arbitrary JSON values directly to a set can accept a string,
    silently collapse duplicates, or mask a malformed prior audit result.
    """
    if not isinstance(copyqueue, dict):
        raise ValueError("Expected CopyFiles audit JSON object")
    if (copyqueue.get("source_only") is not True or
            copyqueue.get("wine_executed") is not False or
            copyqueue.get("v28_reused") is not False):
        raise ValueError("Expected strictly source-only preserved-generation audit")
    raw = copyqueue.get("resource_providers_not_in_sealed_pe")
    if (not isinstance(raw, list) or len(raw) != len(SOURCE_BLOBS) or
            any(not isinstance(item, str) for item in raw) or
            len(set(raw)) != len(raw) or set(raw) != set(SOURCE_BLOBS)):
        raise ValueError("Malformed or changed pinned CopyFiles provider list")
    # Validate the *rest* of the producer's coverage evidence, not just its
    # provider list. Otherwise a failed/partial INF audit could supply the
    # expected eight names and be misrepresented as a complete source gate.
    if (copyqueue.get("phone_accessed") is not False or
            copyqueue.get("rpcss_registration_declared") is not True or
            copyqueue.get("arm64_copy_sections") !=
            ["colorfiles", "etcfiles", "inffiles", "nlsfiles", "sortfiles"] or
            copyqueue.get("requested_nls_not_in_sealed") != [] or
            type(copyqueue.get("requested_nls_count")) is not int or
            type(copyqueue.get("sealed_nls_count")) is not int or
            copyqueue["requested_nls_count"] != copyqueue["sealed_nls_count"] or
            copyqueue["sealed_nls_count"] != 76 or
            type(copyqueue.get("copyfile_rows")) is not int or
            copyqueue["copyfile_rows"] <= 0 or
            type(copyqueue.get("resource_provider_count")) is not int):
        raise ValueError("Incomplete or contradictory CopyFiles source coverage")
    included = copyqueue.get("resource_providers_in_sealed_pe")
    if (not isinstance(included, list) or
            any(not isinstance(item, str) for item in included) or
            len(set(included)) != len(included) or
            set(included) & set(raw) or
            copyqueue["resource_provider_count"] != len(included) + len(raw)):
        raise ValueError("Contradictory sealed resource provider coverage")
    return set(raw)


def planned_provider_build_order(dependencies: dict[str, set[str]]) -> list[str]:
    """Stable dependency-first source build plan; cycles are a hard blocker.

    Edges point from a provider to another provider it imports. This is
    *planning only*, never evidence that a PE/native binary exists.
    """
    nodes = set(SOURCE_BLOBS)
    if set(dependencies) != nodes or any(
            not isinstance(edges, set) or not edges <= nodes or node in edges
            for node, edges in dependencies.items()):
        raise ValueError("Invalid pinned provider dependency graph")
    pending = {name: set(edges) for name, edges in dependencies.items()}
    ordered = []
    while pending:
        ready = sorted(name for name, edges in pending.items() if not edges)
        if not ready:
            raise ValueError("Circular planned provider dependency: " +
                             ",".join(sorted(pending)))
        ordered.extend(ready)
        for name in ready:
            del pending[name]
        for edges in pending.values():
            edges.difference_update(ready)
    return ordered


def analyze(inputs: dict[str, str], pe_names: set[str],
            missing_providers: set[str]) -> dict:
    if missing_providers != set(SOURCE_BLOBS):
        raise ValueError("Pinned missing-provider list changed")
    if set(inputs) != set(SOURCE_BLOBS):
        raise ValueError("Pinned provider source input list changed")
    if (not isinstance(pe_names, set) or len(pe_names) != 34 or
            any(not isinstance(name, str) or
                re.fullmatch(r"[a-z0-9][a-z0-9_-]*\.dll", name) is None
                for name in pe_names)):
        raise ValueError("Expected 34 normalized sealed PE DLL names")
    # Build a *planning* graph from pinned Makefile IMPORTS, not a verified
    # PE import table. .sys modules are outside the sealed DLL-only cohort.
    # Internal edges must not be mistaken for closed imports until each PE
    # binary and any Unix companion has been cross-built and checked.
    provider_by_stem = {name.rsplit(".", 1)[0]: name for name in SOURCE_BLOBS}
    output = []
    provider_dependencies = {}
    for provider in sorted(SOURCE_BLOBS):
        row = parse_makefile(provider, inputs[provider])
        sealed = []
        planned = []
        unresolved = []
        for name in row["imports"]:
            if name + ".dll" in pe_names:
                sealed.append(name)
            elif name in provider_by_stem:
                planned.append({"import": name, "provider": provider_by_stem[name]})
            else:
                unresolved.append(name)
        provider_dependencies[provider] = {edge["provider"] for edge in planned}
        row["imports_in_sealed_dlls"] = sorted(sealed)
        row["imports_in_missing_provider_plan"] = sorted(
            planned, key=lambda edge: (edge["import"], edge["provider"]))
        row["imports_outside_sealed_and_provider_plan"] = sorted(unresolved)
        # Retain existing report field for downstream consumers: this is
        # still *all* imports not present as a sealed DLL, including edges
        # to other planned providers, not just external dependencies.
        row["imports_not_in_sealed_dlls"] = sorted(
            edge["import"] for edge in planned) + sorted(unresolved)
        row["imports_not_in_sealed_dlls"].sort()
        output.append(row)
    build_order = planned_provider_build_order(provider_dependencies)
    # Turn source-only inventory into a concrete cross-build work queue.
    # These are *unverified* requirements, never a claim that a PE or
    # Android/Bionic companion was compiled or that imports are resolved.
    for row in output:
        blockers = []
        if row["imports_outside_sealed_and_provider_plan"]:
            blockers.append("EXTERNAL_IMPORT_RESOLUTION")
        if row["imports_in_missing_provider_plan"]:
            blockers.append("PLANNED_PROVIDER_PE_BUILD")
        if row["has_native_companion"]:
            blockers.append("ANDROID_BIONIC_UNIX_COMPANION")
        if row["build_macros"]:
            blockers.append("EXTERNAL_BUILD_MACRO_LINKAGE")
        blockers.append("PINNED_ARM64_PE_BUILD_AND_IMPORT_TABLE")
        row["crossbuild_verification_blockers"] = blockers
        row["crossbuild_verified"] = False
    return {
        "provider_crossbuild_work_queue": [
            {"provider": name, "blockers": next(
                row["crossbuild_verification_blockers"] for row in output
                if row["module"] == name)}
            for name in build_order
        ],
        "provider_crossbuild_work_queue_only": True,
        "source_revision": SOURCE_REV,
        "source_only": True,
        "provider_source_files_verified": len(output),
        "missing_provider_pe_not_auto_bundled": sorted(SOURCE_BLOBS),
        "unix_companion_required_by": [x["module"] for x in output if x["has_native_companion"]],
        "external_build_macro_modules": [x["module"] for x in output if x["build_macros"]],
        "providers": output,
        "provider_import_plan_only": True,
        "provider_source_build_order": build_order,
        "provider_source_build_order_only": True,
        "provider_pe_binaries_verified": False,
        "provider_native_companions_verified": False,
        "provider_import_closure_verified": False,
        "wine_executed": False,
        "phone_accessed": False,
        "v28_reused": False,
        "runtime_correction_verified": False,
        "interpretation": (
            "The source supplies build recipes, not a complete verified "
            "Android runtime. Check cross-built PE and native import closure "
            "before proposing any new fresh-prefix experiment."
        ),
    }

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--source-dir", type=Path, required=True)
    p.add_argument("--sealed", type=Path, required=True)
    p.add_argument("--copyqueue", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    if a.source_dir.is_symlink() or not a.source_dir.is_dir():
        raise ValueError("Unsafe provider source directory")
    source = {}
    for provider, (dirname, expected) in SOURCE_BLOBS.items():
        directory = a.source_dir / dirname
        path = directory / "Makefile.in"
        # A symlinked parent bypasses path.is_symlink() on the leaf.
        # Reject both levels before reading any provider source bytes.
        if (directory.is_symlink() or not directory.is_dir() or
                path.is_symlink() or not path.is_file() or
                path.stat().st_size > 16384):
            raise ValueError("Missing or linked pinned Makefile")
        data = path.read_bytes()
        if git_blob_sha(data) != expected:
            raise ValueError("Pinned Makefile Git blob identity mismatch")
        source[provider] = data.decode("utf-8")
    if a.copyqueue.is_symlink() or a.copyqueue.stat().st_size > 32768:
        raise ValueError("Unsafe source audit input")
    copyqueue = parse_copyqueue_json(a.copyqueue.read_text(encoding="utf-8"))
    missing = validate_copyqueue_provider_list(copyqueue)
    root = Path(__file__).resolve().parents[2]
    stage = root / "next-generation/stage_wine29_sealed012.py"
    spec = importlib.util.spec_from_file_location("charoite_sealed012_provider_audit", stage)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    manifest, payload = module.validate_archive(a.sealed)
    providers = {name.split("/")[-1].lower() for name in payload
                 if name.startswith("data/pe/arm64ec/")}
    result = analyze(source, providers, missing)
    if a.out.is_symlink() or a.out.exists():
        raise ValueError("Never overwrite source-only audit")
    data = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if len(data) > 32768:
        raise ValueError("Output unexpectedly large")
    a.out.write_text(data, encoding="utf-8")
    print("WINE29_PINNED_SOURCE_PROVIDER_DEPENDENCY_AUDIT=PASS")
    print("PROVIDER_SOURCE_FILES_VERIFIED=" + str(len(result["providers"])))
    print("UNIX_COMPANION_PROVIDER_COUNT=" + str(len(result["unix_companion_required_by"])))
    print("BUILD_MACRO_PROVIDER_COUNT=" + str(len(result["external_build_macro_modules"])))
    print("RUNTIME_CORRECTION_VERIFIED=FALSE")
    print("NO_WINE_NO_APK_NO_PHONE_NO_V28=PASS")

if __name__ == "__main__":
    main()
