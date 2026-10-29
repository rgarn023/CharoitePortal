#!/usr/bin/env bash
# Experimental pinned Wine ARM64EC Windows RPC/COM/control API expansion.
# Compiles from the SAME audited tree; never installs to Android or Wine prefixes.
set -euo pipefail
if [[ $# -ne 4 || "$1" != /* || "$2" != /* || "$3" != /* || "$4" != /* ]]; then
  echo "Usage: build-pe-com.sh ABS_BUILD ABS_READOBJ ABS_18_DEPENDENCY_REVIEW ABS_NEW_OUTPUT" >&2
  exit 2
fi
build="$1"; readobj="$2"; audit="$3"; output="$4"
script_dir="$(cd "$(dirname "$0")" && pwd)"
[[ -x "$readobj" && -s "$audit" && -f "$build/../charoite-source-validation.txt" ]] || {
  echo "Missing audited Charoite Wine build/readobj/import inventory" >&2; exit 3;
}
[[ ! -e "$output" && -d "$(dirname "$output")" ]] || {
  echo "Refusing existing experimental COM output" >&2; exit 4;
}
case " $build $audit $output " in
  *"/data/data/"*|*"/data/user/"*|*"/storage/emulated/"*)
    echo "Never operate in an installed Android app or shared phone storage" >&2; exit 4 ;;
esac
for required in \
  dlls/ntdll/aarch64-windows/ntdll.dll \
  dlls/kernelbase/aarch64-windows/kernelbase.dll \
  dlls/kernel32/aarch64-windows/kernel32.dll \
  dlls/advapi32/aarch64-windows/advapi32.dll \
  dlls/user32/aarch64-windows/user32.dll \
  dlls/gdi32/aarch64-windows/gdi32.dll \
  dlls/shell32/aarch64-windows/shell32.dll; do
  [[ -s "$build/$required" ]] || { echo "Missing same-tree $required" >&2; exit 4; }
done
python3 - "$audit" <<'PY'
import json,sys
from pathlib import Path
review=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
required={"rpcrt4.dll","combase.dll","ole32.dll","comctl32.dll"}
assert review.get("schema_version")==1
assert review.get("purpose")=="Exact imports in sampled compiled bootstrap; not full runtime dependency closure"
assert required.issubset(set(review.get("windows_imports_not_bundled",[])))
print("CHAROITE_PE_COM_AUDIT_INPUT_VERIFIED=PASS")
PY

cd "$build"
# Wine Makefile build graph owns COM/RPC import-library dependencies.
# Do not modify DLLs or replace upstream Wine source at this step.
for name in rpcrt4 combase ole32 comctl32; do
  make -j2 "dlls/$name/aarch64-windows/$name.dll"
done
mkdir "$output"
for name in rpcrt4 combase ole32 comctl32; do
  dll="$PWD/dlls/$name/aarch64-windows/$name.dll"
  [[ -s "$dll" && ! -L "$dll" ]] || { echo "Missing compiled $name" >&2; exit 5; }
  "$readobj" --file-headers "$dll" > "$output/$name-pe-header.txt"
  grep -F 'Machine: IMAGE_FILE_MACHINE_ARM64EC (0xA641)' "$output/$name-pe-header.txt" || {
    echo "No ARM64EC view for $name" >&2; exit 5;
  }
  "$readobj" --coff-imports "$dll" > "$output/$name-pe-imports.txt"
  cp "$dll" "$output/$name-arm64ec.dll"
done
python3 - "$audit" "$output" <<'PY'
from pathlib import Path
import hashlib,json,sys
audit=Path(sys.argv[1]); root=Path(sys.argv[2]); components={}
for name in ("rpcrt4","combase","ole32","comctl32"):
    binary=root/f"{name}-arm64ec.dll"
    components[name]={
        "file":binary.name,"size":binary.stat().st_size,
        "sha256":hashlib.sha256(binary.read_bytes()).hexdigest(),
        "pe_machine":"0xA641","raw_arm64x_carrier":"0xAA64",
    }
manifest={
    "schema_version":1,
    "project":"Charoite Wine ARM64EC RPC/COM/control modules",
    "source_commit":"c74acb09d51b447f5d5ac56c87608d3ec565a767",
    "android_package":"com.charoitx",
    "dependency_review_sha256":hashlib.sha256(audit.read_bytes()).hexdigest(),
    "status":"compiled-not-executed",
    "launch_ready":False,"installable":False,"prefix_created":False,
    "device_tested":False,"anti_cheat_supported":False,
    "components":components,
    "remaining":"Additional PE/Unix dependency closure, FEX, display/input, Vulkan and isolated smoke test",
}
(root/"pe-com-manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n",encoding="utf-8")
PY
python3 "$script_dir/verify-pe-com.py" "$output" "$audit"
echo "CHAROITE_PE_COM_COMPILED_NOT_EXECUTED"
