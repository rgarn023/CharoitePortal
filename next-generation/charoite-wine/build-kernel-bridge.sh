#!/usr/bin/env bash
# Experimental Wine 10 ARM64EC core DLLs from the *same* Android build tree.
# Requires the previously successful ntdll + loader/server base-slice build.
# Produces a read-only CI diagnostic; never installs or changes any prefix.
set -euo pipefail

if [[ $# -ne 3 || "${1:-}" != /* || "${2:-}" != /* || "${3:-}" != /* ]]; then
    echo "Usage: build-kernel-bridge.sh ABS_ANDROID_BUILD ABS_LLVM_READOBJ ABS_OUTPUT" >&2
    exit 2
fi
build_dir="$1"
readobj="$2"
output="$3"
test -x "$readobj" || { echo "Missing pinned ARM64EC PE inspector" >&2; exit 3; }
test -f "$build_dir/../charoite-source-validation.txt" || {
    echo "Unvalidated Charoite Wine source" >&2; exit 3;
}
test -s "$build_dir/dlls/ntdll/aarch64-windows/ntdll.dll" || {
    echo "ARM64EC ntdll must be built first from same tree" >&2; exit 3;
}
test ! -e "$output" || {
    echo "Refusing to overwrite a Charoite experimental kernel bundle" >&2; exit 4;
}

cd "$build_dir"
# Wine's configure --enable-archs=arm64ec,aarch64 creates hybrid PE modules
# under aarch64-windows; module machine type MUST still be independently checked.
make -j2 \
  dlls/kernelbase/aarch64-windows/kernelbase.dll \
  dlls/kernel32/aarch64-windows/kernel32.dll

mkdir "$output"
for name in kernelbase kernel32; do
    dll="$PWD/dlls/$name/aarch64-windows/$name.dll"
    [[ -s "$dll" && ! -L "$dll" ]] || {
        echo "Missing compiled Wine ARM64EC $name module" >&2; exit 5;
    }
    "$readobj" --file-headers "$dll" > "$output/$name-pe-header.txt"
    grep -E 'Machine: IMAGE_FILE_MACHINE_ARM64EC|Machine: ARM64EC|Machine: 0xA641' \
      "$output/$name-pe-header.txt" || {
        echo "Wrong Windows PE machine type for $name" >&2; exit 5;
      }
    cp "$dll" "$output/$name-arm64ec.dll"
done

python3 - "$output" <<'PY'
from pathlib import Path
import hashlib, json, sys
d = Path(sys.argv[1])
manifest = {
    "schema_version": 1,
    "project": "Charoite Wine ARM64EC experimental kernel DLL bridge",
    "source_commit": "c74acb09d51b447f5d5ac56c87608d3ec565a767",
    "machine": "IMAGE_FILE_MACHINE_ARM64EC",
    "pe_machine": "0xA641",
    "android_package": "com.charoitx",
    "launch_ready": False,
    "installable": False,
    "base_slice_required": True,
    "missing_for_runtime": ["full PE and Unix DLL tree", "FEX translator",
        "graphics/display/input", "fresh Windows prefix and on-device testing"],
    "components": {},
}
for name in ("kernelbase", "kernel32"):
    p = d / f"{name}-arm64ec.dll"
    content = p.read_bytes()
    manifest["components"][name] = {"file": p.name, "size": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "pe_machine": "0xA641"}
(d / "kernel-bridge-manifest.json").write_text(
    json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("CHAROITE_ARM64EC_KERNEL_DLL_ABI=PASS")
print("LAUNCH_READY=false")
PY
echo "CHAROITE_WINE_ARM64EC_KERNEL_MODULES_COMPILED"
