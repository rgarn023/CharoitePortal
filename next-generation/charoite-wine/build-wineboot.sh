#!/usr/bin/env bash
# Experimental Charoite Wine regular Windows ARM64 startup utility (not ARM64EC).
# This is NOT proof that a Windows prefix can be initialized on Android.
set -euo pipefail
if [[ $# -ne 3 || "${1:-}" != /* || "${2:-}" != /* || "${3:-}" != /* ]]; then
  echo "Usage: build-wineboot.sh ABS_ANDROID_WINE_BUILD ABS_LLVM_READOBJ ABS_REPORT_DIR" >&2
  exit 2
fi
build_dir="$1"
readobj="$2"
report="$3"
[[ -x "$readobj" && -f "$build_dir/../charoite-source-validation.txt" ]] || {
  echo "Refusing unvalidated source/toolchain" >&2; exit 3;
}
[[ -s "$build_dir/dlls/kernel32/aarch64-windows/kernel32.dll" ]] || {
  echo "ARM64EC kernel32 from same Wine build tree required" >&2; exit 3;
}
[[ -s "$build_dir/dlls/kernelbase/aarch64-windows/kernelbase.dll" ]] || {
  echo "ARM64EC kernelbase from same Wine build tree required" >&2; exit 3;
}
[[ ! -e "$report" ]] || { echo "Refusing overwrite of Charoite wineboot output" >&2; exit 4; }
cd "$build_dir"

# Wine's boot utility brings in advapi32, ws2_32 and delayed imports.
# Let Wine generate its actual dependencies from the pinned make graph.
make -j2 programs/wineboot/aarch64-windows/wineboot.exe
boot="$PWD/programs/wineboot/aarch64-windows/wineboot.exe"
[[ -s "$boot" && ! -L "$boot" ]] || { echo "wineboot PE missing" >&2; exit 5; }
mkdir "$report"
"$readobj" --file-headers "$boot" > "$report/wineboot-pe-header.txt"
grep -E 'Machine: IMAGE_FILE_MACHINE_ARM64 \\(0xAA64\\)|Machine: ARM64 \\(0xAA64\\)' \
  "$report/wineboot-pe-header.txt" || {
    echo "Wineboot is not Windows ARM64 (0xAA64)" >&2; exit 5;
  }
cp "$boot" "$report/wineboot-arm64.exe"
python3 - "$report" <<'PY'
from pathlib import Path
import hashlib, json, sys
out = Path(sys.argv[1])
pe = out / "wineboot-arm64.exe"
payload = {
    "schema_version": 1,
    "project": "Charoite Wine Windows ARM64 wineboot experiment",
    "source_commit": "c74acb09d51b447f5d5ac56c87608d3ec565a767",
    "android_package": "com.charoitx",
    "pe_machine": "0xAA64",
    "status": "compiled-not-executed",
    "launch_ready": False,
    "installable": False,
    "prefix_created": False,
    "needs": ["Complete Windows DLL and Unix tree", "FEX and graphics",
              "isolated staging/prefix", "Android device smoke test"],
    "file": pe.name,
    "size": pe.stat().st_size,
    "sha256": hashlib.sha256(pe.read_bytes()).hexdigest()
}
(out / "wineboot-manifest.json").write_text(
    json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("CHAROITE_ARM64EC_WINEBOOT_PE=PASS")
print("LAUNCH_READY=false")
PY
echo "CHAROITE_WINEBOOT_COMPILED_NOT_RUN"
