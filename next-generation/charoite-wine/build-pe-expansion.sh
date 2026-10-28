#!/usr/bin/env bash
# Compile the next audited ARM64EC Windows API DLLs from the SAME Wine build tree.
# CI-only, no installation, app data access or Wine prefix migration.
set -euo pipefail
if [[ $# -ne 5 || "$1" != /* || "$2" != /* || "$3" != /* || "$4" != /* || "$5" != /* ]]; then
  echo "Usage: build-pe-expansion.sh ABS_BUILD ABS_READOBJ ABS_AUDIT_JSON ABS_FOUNDATION_DIR ABS_OUTPUT" >&2
  exit 2
fi
build="$1"; readobj="$2"; audit="$3"; foundation="$4"; output="$5"
script_dir="$(cd "$(dirname "$0")" && pwd)"
[[ -x "$readobj" && -s "$audit" && -f "$build/../charoite-source-validation.txt" ]] || {
  echo "Missing pinned tools, audit or source validation" >&2; exit 3;
}
[[ -d "$foundation" && ! -e "$output" && -d "$(dirname "$output")" ]] || {
  echo "Refusing missing foundation or existing output" >&2; exit 4;
}
case " $build $foundation $output " in
  *"/data/data/"*|*"/data/user/"*|*"/storage/emulated/"*)
    echo "Refusing to operate on installed app or phone storage" >&2; exit 4 ;;
esac
for required in \
  dlls/ntdll/aarch64-windows/ntdll.dll \
  dlls/kernelbase/aarch64-windows/kernelbase.dll \
  dlls/kernel32/aarch64-windows/kernel32.dll; do
  [[ -s "$build/$required" ]] || { echo "Missing same-tree $required" >&2; exit 4; }
done
python3 "$script_dir/verify-pe-foundation.py" "$foundation"
python3 - "$audit" <<'PY'
import json,sys
from pathlib import Path
audit=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert audit.get("schema_version")==1 and audit.get("android_package")=="com.charoitx"
for key in ("launch_ready","installable","prefix_created","device_tested"):
    assert audit.get(key) is False
expected={"crypt32.dll","setupapi.dll","shlwapi.dll","version.dll"}
assert expected.issubset(set(audit.get("imports_not_in_sampled_pe_dlls",[])))
print("CHAROITE_PE_EXPANSION_AUDIT_INPUT_VERIFIED=PASS")
PY

cd "$build"
for name in crypt32 setupapi shlwapi version; do
  make -j2 "dlls/$name/aarch64-windows/$name.dll"
done
mkdir "$output"
for name in crypt32 setupapi shlwapi version; do
  dll="$PWD/dlls/$name/aarch64-windows/$name.dll"
  [[ -s "$dll" && ! -L "$dll" ]] || { echo "Missing compiled $name" >&2; exit 5; }
  "$readobj" --file-headers "$dll" > "$output/$name-pe-header.txt"
  grep -E 'Machine: IMAGE_FILE_MACHINE_ARM64EC \(0xA641\)' "$output/$name-pe-header.txt" || {
    echo "No ARM64EC view for $name" >&2; exit 5;
  }
  cp "$dll" "$output/$name-arm64ec.dll"
done
python3 - "$foundation" "$output" <<'PY'
import hashlib,json,sys
from pathlib import Path
foundation=Path(sys.argv[1]); root=Path(sys.argv[2])
fmanifest=foundation/"pe-foundation-manifest.json"
components={}
for name in ("crypt32","setupapi","shlwapi","version"):
    p=root/f"{name}-arm64ec.dll"
    components[name]={
        "file":p.name, "size":p.stat().st_size,
        "sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
        "pe_machine":"0xA641", "raw_arm64x_carrier":"0xAA64",
    }
manifest={
    "schema_version":1,
    "name":"Charoite Wine ARM64EC PE expansion (audited APIs)",
    "source_commit":"c74acb09d51b447f5d5ac56c87608d3ec565a767",
    "android_package":"com.charoitx",
    "depends_on_foundation_manifest_sha256":hashlib.sha256(fmanifest.read_bytes()).hexdigest(),
    "status":"compiled-not-executed",
    "launch_ready":False,"installable":False,
    "prefix_created":False,"device_tested":False,
    "anti_cheat_supported":False,
    "components":components,
    "remaining":"Complete Wine PE/Unix/NLS closure, FEX, graphics, fresh prefix and device smoke tests",
}
(root/"pe-expansion-manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n",encoding="utf-8")
PY
python3 "$script_dir/verify-pe-expansion.py" "$output" "$foundation"
echo "CHAROITE_PE_EXPANSION_COMPILED_NOT_EXECUTED"
