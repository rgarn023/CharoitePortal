#!/usr/bin/env python3
"""Stage verified Wine API DLLs as READ-ONLY diagnostic APK assets.

Never produce an executable runtime, install files or touch phone prefixes.
Only CI's fresh Android app source output may be the destination.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent
RUN_ID = 40791083178
SOURCE_SHA = "c1658e2d20260ff413e6ba6c47f460e2d5e7cec1"
WINE_BASE_SHA = "c74acb09d51b447f5d5ac56c87608d3ec565a767"
FOUNDATION_ARTIFACT = 12861682823
EXPANSION_ARTIFACT = 12861074729
FOUNDATION_MANIFEST_SHA = "1a795a07b9a803c66e8ccba47d20b70ab97e54741e24376cb863a9ba0fb3b33d"
EXPANSION_MANIFEST_SHA = "3af80951c6192c10b885228071ed27c29b3009035497bc6c05d5d640a071f065"

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, str(ROOT / "charoite-wine" / path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def hash_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def stage(foundation, expansion, upstream):
    foundation = Path(foundation).resolve()
    expansion = Path(expansion).resolve()
    upstream = Path(upstream).resolve()
    app = upstream / "app/src/main"
    if not (app / "AndroidManifest.xml").is_file():
        raise ValueError("Android checkout missing; no output created")
    if not (app / "assets/charoite-next/engine-reference.json").is_file():
        raise ValueError("Charoite Next overlay was not applied")
    dest = app / "assets/charoite-next/wine-ci"
    if dest.exists():
        raise ValueError("Refusing to overwrite Wine diagnostic assets")
    fv = load("foundation_verifier", "verify-pe-foundation.py")
    ev = load("expansion_verifier", "verify-pe-expansion.py")
    fv.verify(foundation)
    ev.verify(expansion, foundation)
    if hash_file(foundation / "pe-foundation-manifest.json") != FOUNDATION_MANIFEST_SHA:
        raise ValueError("Artifact differs from exact verified GitHub foundation")
    if hash_file(expansion / "pe-expansion-manifest.json") != EXPANSION_MANIFEST_SHA:
        raise ValueError("Artifact differs from exact verified GitHub expansion")
    # Nothing is staged before all validation above has completed.
    dest.mkdir()
    manifest = {
        "schema_version": 1,
        "project": "Charoite Core Next Wine PE device diagnostic",
        "source_run": RUN_ID,
        "source_code_sha": SOURCE_SHA,
        "wine_upstream_sha": WINE_BASE_SHA,
        "android_package": "com.charoitx",
        "foundation_artifact": FOUNDATION_ARTIFACT,
        "expansion_artifact": EXPANSION_ARTIFACT,
        "status": "read-only-pe-diagnostics-not-runnable",
        "launch_ready": False,
        "installable_as_runtime": False,
        "prefix_created": False,
        "device_tested": False,
        "anti_cheat_supported": False,
        "components": {},
    }
    for name, src, source_name in (
        ("foundation", foundation, "pe-foundation-manifest.json"),
        ("expansion", expansion, "pe-expansion-manifest.json"),
    ):
        group = json.loads((src / source_name).read_text(encoding="utf-8"))
        (dest / name).mkdir()
        shutil.copyfile(src / source_name, dest / name / source_name)
        for dll_name, attrs in group["components"].items():
            filename = attrs["file"]
            shutil.copyfile(src / filename, dest / name / filename)
            manifest["components"][dll_name] = {
                "asset": f"charoite-next/wine-ci/{name}/{filename}",
                "sha256": attrs["sha256"],
                "size": attrs["size"],
                "raw_machine": "0xAA64",
                "arm64ec_ci_verified": True,
            }
    if len(manifest["components"]) != 7:
        raise ValueError("Unexpected diagnostic library inventory")
    (dest / "wine-ci-evidence.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(f"CHAROITE_NEXT_WINE_PE_DIAGNOSTIC_STAGED=PASS components={len(manifest['components'])}")
    print("CHAROITE_NEXT_MODERN_RUNNER_NOT_INSTALLED")
    return manifest

if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: stage_wine_probe.py FOUNDATION_DIR EXPANSION_DIR UPSTREAM")
    stage(*sys.argv[1:])
