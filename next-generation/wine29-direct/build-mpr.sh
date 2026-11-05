#!/usr/bin/env bash
# Source-only MPR DLL follow-on; never execute Wine, Wineboot, Windows PE or touch Android data.
set -euo pipefail
if [[ $# -ne 7 || "$1" != /* || "$2" != /* || "$3" != /* ||
      "$4" != /* || "$5" != /* || "$6" != /* || "$7" != /* ]]; then
  echo "Usage: build-mpr.sh ABS_FRESH_SOURCE ABS_READOBJ ABS_BASELINE_TAR ABS_SIX ABS_TWO ABS_DIRECT ABS_NEW_MPR" >&2
  exit 2
fi
source="$1";readobj="$2";archive="$3";six="$4";two="$5";direct="$6";out="$7"
scripts="$(cd "$(dirname "$0")" && pwd)"
build="$source/charoite-arm64ec-android"
[[ -d "$build" && -x "$readobj" && -s "$archive" && -d "$six" &&
   -d "$two" && -d "$direct" && -d "$(dirname "$out")" &&
   ! -e "$out" && ! -L "$out" ]] || {
  echo "Missing coherent Wine29 proof or output already exists" >&2; exit 3;
}
case " $source $readobj $archive $six $two $direct $out " in
  *"/data/data/"*|*"/data/user/"*|*"/storage/emulated/"*|*"/sdcard/"*)
    echo "Refusing app/phone user-data paths" >&2; exit 4 ;;
esac
[[ -s "$source/dlls/mpr/Makefile.in" && ! -L "$source/dlls/mpr/Makefile.in" ]] || {
  echo "No pinned MPR Wine source" >&2; exit 5;
}
# Verify actual previous source-built direct dependencies before candidate compile.
python3 "$scripts/verify-direct.py" verify "$archive" "$six" "$two" "$direct" "$readobj"
cd "$build"
make -j2 "dlls/mpr/aarch64-windows/mpr.dll"
[[ -s "$build/dlls/mpr/aarch64-windows/mpr.dll" ]] || exit 6
mkdir "$out"
cp "$build/dlls/mpr/aarch64-windows/mpr.dll" "$out/mpr-arm64ec.dll"
"$readobj" --file-headers "$out/mpr-arm64ec.dll" > "$out/mpr-pe-header.txt"
"$readobj" --coff-imports "$out/mpr-arm64ec.dll" > "$out/mpr-pe-imports.txt"
grep -Fq 'Machine: IMAGE_FILE_MACHINE_ARM64EC (0xA641)' "$out/mpr-pe-header.txt" || exit 7
cd "$GITHUB_WORKSPACE"
python3 "$scripts/verify-mpr.py" create "$archive" "$six" "$two" "$direct" "$out" "$readobj"
python3 "$scripts/verify-mpr.py" verify "$archive" "$six" "$two" "$direct" "$out" "$readobj"
echo WINE29_07_SOURCE_ONLY_MPR_CANDIDATE_BUILD=PASS
echo WINE29_07_NO_ANDROID_APK_WINDOWS_EXECUTION=PASS
