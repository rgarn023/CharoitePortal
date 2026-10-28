#!/usr/bin/env bash
# CI-only, same-source ARM64EC Wine DLL build; no prefix or app mutation.
set -euo pipefail
if [[ $# -ne 4 || "$1" != /* || "$2" != /* || "$3" != /* || "$4" != /* ]]; then
  echo "Usage: build-pe-foundation.sh ABS_BUILD ABS_READOBJ ABS_AUDIT_JSON ABS_OUTPUT" >&2
  exit 2
fi
build="$1"
readobj="$2"
audit="$3"
output="$4"
script_dir="$(cd "$(dirname "$0")" && pwd)"
[[ -x "$readobj" && -s "$audit" && -f "$build/../charoite-source-validation.txt" ]] || {
  echo "Missing validated Wine build, audit or PE inspector" >&2; exit 3;
}
for required in dlls/ntdll/aarch64-windows/ntdll.dll dlls/kernelbase/aarch64-windows/kernelbase.dll dlls/kernel32/aarch64-windows/kernel32.dll programs/wineboot/aarch64-windows/wineboot.exe; do
  [[ -s "$build/$required" ]] || { echo "Missing same-build prerequisite $required" >&2; exit 3; }
done
[[ ! -e "$output" && -d "$(dirname "$output")" ]] || { echo "Refusing to overwrite output" >&2; exit 4; }
case "$build $output" in
  *"/data/data/com.charoite/"*|*"/data/data/com.charoitx/"*|*"/data/user/"*|*"/storage/emulated/"*)
    echo "Device/app data paths are forbidden" >&2; exit 4 ;;
esac
python3 - "$audit" <<'PY'
import json,sys
from pathlib import Path
d=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert d.get("schema_version")==1 and d.get("android_package")=="com.charoitx"
for k in ("launch_ready","installable","prefix_created","device_tested"):
    assert d.get(k) is False
assert {"advapi32.dll","user32.dll","ws2_32.dll"}.issubset(set(d.get("imports_not_in_sampled_pe_dlls",[])))
print("CHAROITE_PE_FOUNDATION_AUDIT_INPUT_VERIFIED=PASS")
PY
cd "$build"
for name in advapi32 user32 ws2_32; do
  make -j2 "dlls/$name/aarch64-windows/$name.dll"
done
mkdir "$output"
for name in advapi32 user32 ws2_32; do
  dll="$PWD/dlls/$name/aarch64-windows/$name.dll"
  [[ -s "$dll" && ! -L "$dll" ]] || { echo "Missing compiled $name" >&2; exit 5; }
  "$readobj" --file-headers "$dll" > "$output/$name-pe-header.txt"
  grep -E 'Machine: IMAGE_FILE_MACHINE_ARM64EC \(0xA641\)|Machine: ARM64EC \(0xA641\)' \
    "$output/$name-pe-header.txt" || { echo "Unexpected PE ABI for $name" >&2; exit 5; }
  cp "$dll" "$output/$name-arm64ec.dll"
done
python3 - "$output" <<'PY'
import hashlib,json,sys
from pathlib import Path
out=Path(sys.argv[1]); parts={}
for name in ("advapi32","user32","ws2_32"):
    p=out/f"{name}-arm64ec.dll"
    parts[name]={"file":p.name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
                 "size":p.stat().st_size,"pe_machine":"0xA641"}
manifest={"schema_version":1,"name":"Charoite Wine ARM64EC PE Foundation",
          "source_commit":"c74acb09d51b447f5d5ac56c87608d3ec565a767",
          "android_package":"com.charoitx","launch_ready":False,"installable":False,
          "prefix_created":False,"device_tested":False,
          "status":"compile-verified-not-executed","components":parts,
          "remaining":"Full Wine PE/Unix/NLS closure, FEX, graphics and device testing"}
(out/"pe-foundation-manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n",encoding="utf-8")
PY
python3 "$script_dir/verify-pe-foundation.py" "$output"
echo "CHAROITE_PE_FOUNDATION_COMPILED_NOT_EXECUTED"
