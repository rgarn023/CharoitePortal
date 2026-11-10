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
    return set(raw)


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
    output = []
    for provider in sorted(SOURCE_BLOBS):
        row = parse_makefile(provider, inputs[provider])
        needs = []
        for name in row["imports"]:
            # PE imports can be .dll, .sys or .exe. The sealing cohort
            # explicitly includes DLLs only; an unsealed import may still
            # be provided elsewhere in the package.
            if name + ".dll" not in pe_names:
                needs.append(name)
        row["imports_not_in_sealed_dlls"] = sorted(needs)
        output.append(row)
    return {
        "source_revision": SOURCE_REV,
        "source_only": True,
        "provider_source_files_verified": len(output),
        "missing_provider_pe_not_auto_bundled": sorted(SOURCE_BLOBS),
        "unix_companion_required_by": [x["module"] for x in output if x["has_native_companion"]],
        "external_build_macro_modules": [x["module"] for x in output if x["build_macros"]],
        "providers": output,
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
    copyqueue = json.loads(a.copyqueue.read_text(encoding="utf-8"))
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
