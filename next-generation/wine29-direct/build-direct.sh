#!/usr/bin/env bash
# Same-source Wine29 .0.7 direct-import candidates; compile only in CI.
# No Wine, Wineboot, Windows execution, phone, prefix or prior scratch.
set -euo pipefail
if [[ $# -ne 6 || "$1" != /* || "$2" != /* || "$3" != /* ||
      "$4" != /* || "$5" != /* || "$6" != /* ]]; then
  echo "Usage: build-direct.sh ABS_FRESH_SOURCE ABS_LLVM_READOBJ ABS_BASELINE_TAR ABS_SIX ABS_TWO ABS_NEW_OUT" >&2
  exit 2
fi
source="$1"; readobj="$2"; archive="$3"; six="$4"; two="$5"; out="$6"
scripts="$(cd "$(dirname "$0")" && pwd)"
build="$source/charoite-arm64ec-android"
[[ -x "$readobj" && -s "$archive" && -d "$six" && -d "$two" &&
   -d "$build" && -d "$(dirname "$out")" && ! -e "$out" && ! -L "$out" ]] || {
  echo "Missing fresh build or source evidence; never overwrite output" >&2; exit 3;
}
case " $source $readobj $archive $six $two $out " in
  *"/data/data/"*|*"/data/user/"*|*"/storage/emulated/"*|*"/sdcard/"*)
    echo "Refuse Android app/user storage paths" >&2; exit 4 ;;
esac
python3 - "$source" "$archive" "$six" "$two" <<'PY'
from pathlib import Path
import hashlib,importlib.util,json,subprocess,sys
root,archive,six,two=map(Path,sys.argv[1:])
script=Path("next-generation/wine29-imports/classify.py").resolve()
spec=importlib.util.spec_from_file_location("wine29_boot_direct_preflight",script)
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
report=v.analyze(archive,six,two)
if (report["next_regular_import_candidates"]!=["propsys.dll","wininet.dll"] or
    report["baseline_phone_regression"]["regular_descriptors"]!=111 or
    report["provider_dll_count"]!=31):
    raise ValueError("Real PE regular-import preflight differs")
native=json.loads((root/"charoite-wine29-native-source-validation.json").read_text())
head=subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()
if (head!=v.SOURCE_SHA or native.get("generation")!="wine10-arm64ec-bootstrap.0.7" or
    not (root/"charoite-wine29-native-source-delta.patch").is_file() or
    hashlib.sha256((root/"charoite-wine29-native-source-delta.patch").read_bytes()).hexdigest()!=native.get("delta_sha256")):
    raise ValueError("Mismatch in source-pinned native tree or patch")
print("WINE29_07_ORIGINAL_23_PLUS_6_PLUS_2_PE_SOURCE_COHERENCE=PASS")
print("WINE29_07_REAL_PE_REGULAR_IMPORT_GAP_ONLY_PROPSYS_WININET=PASS")
PY
for name in propsys wininet; do
  [[ -s "$source/dlls/$name/Makefile.in" && ! -L "$source/dlls/$name/Makefile.in" ]] || {
    echo "No pinned Wine29 source Makefile: $name" >&2; exit 5;
  }
done
cd "$build"
for name in propsys wininet; do
  # Only cross-compilation host processes. Windows targets are never run.
  make -j2 "dlls/$name/aarch64-windows/$name.dll"
  [[ -s "$build/dlls/$name/aarch64-windows/$name.dll" ]] || exit 6
done
mkdir "$out"
for name in propsys wininet; do
  cp "$build/dlls/$name/aarch64-windows/$name.dll" "$out/$name-arm64ec.dll"
  "$readobj" --file-headers "$out/$name-arm64ec.dll" > "$out/$name-pe-header.txt"
  "$readobj" --coff-imports "$out/$name-arm64ec.dll" > "$out/$name-pe-imports.txt"
  grep -Fq 'Machine: IMAGE_FILE_MACHINE_ARM64EC (0xA641)' "$out/$name-pe-header.txt" || {
    echo "Missing source-backed ARM64EC view" >&2; exit 7;
  }
done
cd "$GITHUB_WORKSPACE"
python3 "$scripts/verify-direct.py" create "$archive" "$six" "$two" "$out" "$readobj"
python3 "$scripts/verify-direct.py" verify "$archive" "$six" "$two" "$out" "$readobj"
echo WINE29_07_PROPSYS_WININET_SOURCE_BUILT_ONLY=PASS
echo WINE29_07_NO_PE_EXECUTION_NO_APK_INSTALLATION=PASS
