#!/usr/bin/env bash
# Source-only Wine29 ordinary-import expansion: wininet.dll and propsys.dll.
# Keeps original 27+6+2 cohorts immutable; never runs Wine, Wineboot or PE.
set -euo pipefail
if [[ $# -ne 6 || "$1" != /* || "$2" != /* || "$3" != /* ||
      "$4" != /* || "$5" != /* || "$6" != /* ]]; then
  echo "Usage: build-regular-next.sh ABS_SOURCE ABS_LLVM ABS_ARCHIVE ABS_SIX ABS_TWO ABS_NEW_DIR" >&2
  exit 2
fi
source="$1"; readobj="$2"; archive="$3"; six="$4"; two="$5"; out="$6"
scripts="$(cd "$(dirname "$0")" && pwd)"
build="$source/charoite-arm64ec-android"
[[ -d "$build" && -x "$readobj" && -f "$archive" &&
   -d "$six" && -d "$two" && -d "$(dirname "$out")" &&
   ! -e "$out" && ! -L "$out" ]] || {
  echo "Missing/unsafe Wine29 candidates or new output already exists" >&2; exit 3;
}
case " $source $readobj $archive $six $two $out " in
 *"/data/data/"*|*"/data/user/"*|*"/storage/emulated/"*|*"/sdcard/"*)
   echo "Refusing Android/user-data paths" >&2; exit 4 ;;
esac
# Verify ALL already built cohorts and exact immutable source archive first.
python3 "$scripts/verify-followups.py" verify "$archive" "$six" "$two" "$readobj"
python3 - "$source" "$archive" <<'PY'
from pathlib import Path
import hashlib,importlib.util,json,subprocess,sys
source=Path(sys.argv[1]); archive=Path(sys.argv[2])
spec=importlib.util.spec_from_file_location("wine29_pinned_bundle",
  Path("next-generation/charoite-wine/verify-bootstrap-bundle.py").resolve())
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
if hashlib.sha256(archive.read_bytes()).hexdigest()!="66068032bd2203c8e53fddc92ce46b84086eb293306b2bd12bb741bf9a5e035e":
  raise ValueError("Pinned Wine29 original source archive hash mismatch")
manifest,_=module.verify(archive)
proof=json.loads((source/"charoite-wine29-native-source-validation.json").read_text())
head=subprocess.check_output(["git","-C",str(source),"rev-parse","HEAD"],text=True).strip()
if (head!="c74acb09d51b447f5d5ac56c87608d3ec565a767" or
    manifest.get("version")!="wine10-arm64ec-bootstrap.0.7" or
    manifest.get("source_commit")!=head or
    proof.get("delta_sha256")!=manifest.get("wine29_native_source_delta_sha256")):
  raise ValueError("Wrong Wine29 source cohort, PE/native patch or generation")
print("WINE29_NEXT_REGULAR_SOURCE_ARCHIVE_AND_PATCH=PASS")
PY
for name in wininet propsys; do
  [[ -s "$source/dlls/$name/Makefile.in" && ! -L "$source/dlls/$name/Makefile.in" ]] || {
    echo "Pinned Wine source missing dependency module: $name" >&2; exit 5;
  }
done
cd "$build"
for name in wininet propsys; do
  # Compile host tools and PE data ONLY; no target Windows application run.
  make -j2 "dlls/$name/aarch64-windows/$name.dll"
  pe="$build/dlls/$name/aarch64-windows/$name.dll"
  [[ -s "$pe" && ! -L "$pe" ]] || { echo "No compiled candidate PE: $name" >&2; exit 6; }
done
mkdir "$out"
for name in wininet propsys; do
  cp "$build/dlls/$name/aarch64-windows/$name.dll" "$out/$name-arm64ec.dll"
  "$readobj" --file-headers "$out/$name-arm64ec.dll" > "$out/$name-pe-header.txt"
  "$readobj" --coff-imports "$out/$name-arm64ec.dll" > "$out/$name-pe-imports.txt"
  grep -Fq 'Machine: IMAGE_FILE_MACHINE_ARM64EC (0xA641)' \
    "$out/$name-pe-header.txt" || {
    echo "No independently verified ARM64EC PE view: $name" >&2; exit 7;
  }
done
cd "$GITHUB_WORKSPACE"
python3 "$scripts/verify-regular-next.py" create "$archive" "$six" "$two" "$out" "$readobj"
python3 "$scripts/verify-regular-next.py" verify "$archive" "$six" "$two" "$out" "$readobj"
echo WINE29_NEXT_2_REGULAR_SOURCE_PE_CANDIDATES=PASS
echo WINE29_NEXT_NO_PHONE_WINEBOOT_OR_PREFIX_EXECUTION=PASS
