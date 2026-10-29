#!/usr/bin/env bash
# Compile four measured Wine startup dependencies from the SAME pinned Android
# ARM64EC build. This does not run Wine, install engines or create prefixes.
set -euo pipefail
if [[ $# -ne 4 || "$1" != /* || "$2" != /* || "$3" != /* || "$4" != /* ]]; then
  echo "Usage: build-pe-startup.sh ABS_BUILD ABS_LLVM_READOBJ ABS_BASE_MANIFEST ABS_OUTPUT" >&2
  exit 2
fi
build="$1"; readobj="$2"; base="$3"; output="$4"
script_dir="$(cd "$(dirname "$0")" && pwd)"
[[ -x "$readobj" && -s "$base" && -f "$build/../charoite-source-validation.txt" ]] || {
  echo "Missing source, readobj or same-run dependency inventory" >&2; exit 3;
}
[[ ! -e "$output" && -d "$(dirname "$output")" ]] || {
  echo "Refusing to replace PE startup output" >&2; exit 4;
}
case " $build $base $output " in
  *"/data/data/"*|*"/data/user/"*|*"/storage/emulated/"*)
    echo "App data / shared phone storage is forbidden" >&2; exit 4 ;;
esac
for prerequisite in \
  dlls/ntdll/aarch64-windows/ntdll.dll \
  dlls/kernel32/aarch64-windows/kernel32.dll \
  dlls/kernelbase/aarch64-windows/kernelbase.dll \
  dlls/advapi32/aarch64-windows/advapi32.dll \
  dlls/user32/aarch64-windows/user32.dll \
  dlls/crypt32/aarch64-windows/crypt32.dll; do
  [[ -s "$build/$prerequisite" ]] || { echo "Missing $prerequisite" >&2; exit 4; }
done
python3 - "$base" <<'PY'
import json,sys
from pathlib import Path
a=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert a.get("schema_version")==1
assert a.get("purpose")=="Exact imports in sampled compiled bootstrap; not full runtime dependency closure"
required={"win32u.dll","gdi32.dll","ucrtbase.dll","shell32.dll"}
assert required.issubset(set(a.get("windows_imports_not_bundled",[])))
print("CHAROITE_PE_STARTUP_IMPORT_EVIDENCE=PASS")
PY

cd "$build"
for name in win32u gdi32 ucrtbase shell32; do
  make -j2 "dlls/$name/aarch64-windows/$name.dll"
done
mkdir "$output"
for name in win32u gdi32 ucrtbase shell32; do
  pe="$PWD/dlls/$name/aarch64-windows/$name.dll"
  [[ -s "$pe" && ! -L "$pe" ]] || { echo "$name not source-built" >&2; exit 5; }
  "$readobj" --file-headers "$pe" > "$output/$name-pe-header.txt"
  grep -F 'Machine: IMAGE_FILE_MACHINE_ARM64EC (0xA641)' "$output/$name-pe-header.txt" || {
    echo "$name missing ARM64EC hybrid view" >&2; exit 5;
  }
  "$readobj" --coff-imports "$pe" > "$output/$name-pe-imports.txt"
  cp "$pe" "$output/$name-arm64ec.dll"
done
python3 - "$output" "$base" <<'PY'
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]);base=Path(sys.argv[2])
parts={}
for name in ("win32u","gdi32","ucrtbase","shell32"):
    p=root/f"{name}-arm64ec.dll"
    parts[name]={"file":p.name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
                 "size":p.stat().st_size,"pe_machine":"0xA641",
                 "raw_arm64x_carrier":"0xAA64"}
manifest={
    "schema_version":1,
    "name":"Charoite Wine ARM64EC startup API modules",
    "source_commit":"c74acb09d51b447f5d5ac56c87608d3ec565a767",
    "android_package":"com.charoitx",
    "base_dependency_review_sha256":hashlib.sha256(base.read_bytes()).hexdigest(),
    "status":"compiled-not-executed",
    "launch_ready":False,"installable":False,"prefix_created":False,
    "device_tested":False,"anti_cheat_supported":False,
    "components":parts,
    "needs":"Remaining Windows PE/Unix imports, FEX, Vulkan, fresh prefix and device test",
}
(root/"pe-startup-manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n",encoding="utf-8")
PY
python3 "$script_dir/verify-pe-startup.py" "$output" "$base"
echo "CHAROITE_PE_STARTUP_COMPILED_NOT_EXECUTED"
