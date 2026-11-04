#!/usr/bin/env bash
# Wine29 .0.7: source-matched experimental dependency DLLs, CI ONLY.
# No Android app, Wine/Wineboot, Windows EXE, prefix, games or old scratch.
set -euo pipefail
if [[ $# -ne 4 || "$1" != /* || "$2" != /* || "$3" != /* || "$4" != /* ]]; then
  echo "Usage: bash build-wine29-deps.sh ABS_VERIFIED_SOURCE ABS_LLVM_READOBJ ABS_PINNED_ARCHIVE ABS_NEW_OUTPUT" >&2
  exit 2
fi
source="$1"; readobj="$2"; baseline="$3"; out="$4"
scripts="$(cd "$(dirname "$0")" && pwd)"
build="$source/charoite-arm64ec-android"
[[ -x "$readobj" && -f "$baseline" && -f "$source/charoite-source-validation.txt" &&
   -s "$source/charoite-wine29-native-source-validation.json" &&
   -s "$source/charoite-wine29-native-source-delta.patch" &&
   -s "$source/charoite-wine29-full-coherent/charoite-wine-bootstrap-bundle.tar.gz" &&
   -d "$build" && -d "$(dirname "$out")" && ! -e "$out" && ! -L "$out" ]] || {
  echo "Missing source-verified Wine29 build or output not fresh" >&2; exit 3;
}
case " $source $readobj $baseline $out " in
  *"/data/data/"*|*"/data/user/"*|*"/storage/emulated/"*|*"/sdcard/"*)
    echo "Never compile or write inside installed Android/user storage" >&2; exit 4 ;;
esac
python3 - "$source" "$baseline" <<'PY'
from pathlib import Path
import hashlib,importlib.util,json,subprocess,sys
source=Path(sys.argv[1]); archive=Path(sys.argv[2])
p=Path("next-generation/charoite-wine/verify-bootstrap-bundle.py").resolve()
spec=importlib.util.spec_from_file_location("wine29_deps_pinned_archive",p)
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
if hashlib.sha256(archive.read_bytes()).hexdigest()!="66068032bd2203c8e53fddc92ce46b84086eb293306b2bd12bb741bf9a5e035e":
    raise ValueError("Original Wine29 .0.7 archive hash differs")
manifest,_=v.verify(archive)
proof=json.loads((source/"charoite-wine29-native-source-validation.json").read_text())
head=subprocess.check_output(["git","-C",str(source),"rev-parse","HEAD"],text=True).strip()
if (head!="c74acb09d51b447f5d5ac56c87608d3ec565a767"
    or proof.get("generation")!="wine10-arm64ec-bootstrap.0.7"
    or proof.get("delta_sha256")!=manifest.get("wine29_native_source_delta_sha256")
    or hashlib.sha256((source/"charoite-wine29-native-source-delta.patch").read_bytes()).hexdigest()!=proof["delta_sha256"]
    or manifest.get("component_count")!=27 or manifest.get("nls_count")!=76):
    raise ValueError("Mixed source generation, Wine29 patch or original archive")
print("WINE29_DEPENDENCY_CANDIDATE_SOURCE_PATCH_AND_ORIGINAL_ARCHIVE=PASS")
PY

for name in coml2 imm32 oleacc oleaut32 shcore newdev; do
  [[ -s "$source/dlls/$name/Makefile.in" && ! -L "$source/dlls/$name/Makefile.in" ]] || {
    echo "Missing pinned source definition for candidate: $name" >&2; exit 5;
  }
done
cd "$build"
for name in coml2 imm32 oleacc oleaut32 shcore newdev; do
  # make may run host build tools, never a target Windows application.
  make -j2 "dlls/$name/aarch64-windows/$name.dll"
  pe="$build/dlls/$name/aarch64-windows/$name.dll"
  [[ -s "$pe" && ! -L "$pe" ]] || {
    echo "Source build did not produce regular ARM64EC PE: $name" >&2; exit 6;
  }
done
mkdir "$out"
for name in coml2 imm32 oleacc oleaut32 shcore newdev; do
  pe="$build/dlls/$name/aarch64-windows/$name.dll"
  "$readobj" --file-headers "$pe" > "$out/$name-pe-header.txt"
  "$readobj" --coff-imports "$pe" > "$out/$name-pe-imports.txt"
  grep -Fq 'Machine: IMAGE_FILE_MACHINE_ARM64EC (0xA641)' \
    "$out/$name-pe-header.txt" || {
    echo "Source-built candidate lacks ARM64EC view: $name" >&2; exit 7;
  }
  cp "$pe" "$out/$name-arm64ec.dll"
done
python3 "$scripts/verify-wine29-deps.py" create "$out" "$readobj"
python3 "$scripts/verify-wine29-deps.py" verify "$out" "$readobj"
echo 'WINE29_07_SEPARATE_SAME_SOURCE_6_PE_DEPENDENCIES=PASS'
echo 'WINE29_07_DEPENDENCY_CANDIDATES=NOT_INSTALLED_OR_EXECUTED'
