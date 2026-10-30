#!/usr/bin/env python3
"""Package a pinned, independently verified 22-component Wine archive as an inert APK asset.

The payload contains 19 PE files, 3 native ELFs, and 76 NLS tables. It is never
extracted, installed or executed by this step. The stable package is untouched.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

RUN = 40898982875
ARTIFACT = 12908731604
WINE_SHA = "c74acb09d51b447f5d5ac56c87608d3ec565a767"
ASSET = "charoite-next/wine-bootstrap-22.tar.gz"
INDEX = "charoite-next/wine-bootstrap-payload.json"
MAX_BYTES = 64 * 1024 * 1024

def digest(data):
    return hashlib.sha256(data).hexdigest()

def make_index(manifest, report, raw, manifest_raw, report_raw):
    if (manifest.get("version") != "wine10-arm64ec-bootstrap.0.4"
            or manifest.get("source_commit") != WINE_SHA
            or manifest.get("android_package") != "com.charoitx"
            or manifest.get("component_count") != 22
            or manifest.get("nls_count") != 76
            or any(manifest.get(k) is not False for k in (
                "launch_ready", "installable", "prefix_created",
                "device_tested", "anti_cheat_supported"))
            or not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_BYTES):
        raise ValueError("Untrusted source archive or runtime readiness")
    gaps = report.get("windows_imports_not_bundled")
    if (not isinstance(gaps, list) or gaps != sorted(set(gaps))
            or manifest.get("window_imports_unresolved_count") != len(gaps)):
        raise ValueError("Unverified PE dependency inventory")
    return {
        "schema_version": 1, "android_package": "com.charoitx",
        "wine_source_sha": WINE_SHA, "source_run": RUN, "source_artifact": ARTIFACT,
        "archive_asset": ASSET, "archive_size": len(raw), "archive_sha256": digest(raw),
        "bundle_manifest_sha256": digest(manifest_raw),
        "dependency_review_sha256": digest(report_raw),
        "component_count": 22, "pe_component_count": 19,
        "native_component_count": 3, "nls_count": 76,
        "windows_imports_not_bundled_count": len(gaps),
        "launch_ready": False, "installable_as_runtime": False,
        "archive_extracted": False, "prefix_created": False,
        "fex_installed": False, "graphics_verified": False,
        "device_boot_tested": False, "anti_cheat_supported": False,
        "scope": "Verified immutable APK archive only; no executable runtime installed",
    }

def stage(archive, upstream):
    archive, upstream = Path(archive).resolve(), Path(upstream).resolve()
    app = upstream / "app/src/main"
    if not (app / "AndroidManifest.xml").is_file():
        raise ValueError("Missing Next-only Android build tree")
    if any(term in str(app) for term in ("/data/data/", "/data/user/", "/storage/emulated/")):
        raise ValueError("Never stage into Android application data")
    verifier_path = Path(__file__).resolve().parent / "charoite-wine/verify-bootstrap-bundle.py"
    spec = importlib.util.spec_from_file_location("charoite_bundle_payload_verify", verifier_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    manifest, report = module.verify(archive)
    if archive.is_symlink() or archive.stat().st_size > MAX_BYTES:
        raise ValueError("Unsafe archive size or symlink")
    import tarfile
    with tarfile.open(archive, "r:gz") as tar:
        manifest_raw = tar.extractfile("manifest.json").read()
        report_raw = tar.extractfile("dependency-review.json").read()
    raw = archive.read_bytes()
    index = make_index(manifest, report, raw, manifest_raw, report_raw)
    dest = app / "assets" / ASSET
    index_dest = app / "assets" / INDEX
    if dest.exists() or index_dest.exists():
        raise ValueError("Refusing to overwrite bundled payload")
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Both are APK assets, not writable executable modules or user-installed runtimes.
    shutil.copyfile(archive, dest)
    index_dest.write_text(json.dumps(index, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    if digest(dest.read_bytes()) != index["archive_sha256"]:
        raise ValueError("Staged bootstrap archive hash mismatch")
    print("CHAROITE_NEXT_COHERENT_WINE_ARCHIVE_PACKAGED=PASS")
    print("CHAROITE_NEXT_WINE_ARCHIVE_SIZE="+str(index["archive_size"]))
    print("CHAROITE_NEXT_WINE_ARCHIVE_SHA256="+index["archive_sha256"])
    print("CHAROITE_NEXT_MODERN_LAUNCH_READY=false")
    return index

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: stage_bootstrap_payload.py VERIFIED_ARCHIVE NEXT_UPSTREAM")
    stage(sys.argv[1], sys.argv[2])
