#!/usr/bin/env bash
# CI-only extension of a NEW, already sealed Wine29 six-DLL candidate build.
# Never touches installed Android apps, prefixes, Wine28 scratch, games or saves.
set -euo pipefail
if [[ $# -ne 5 || "$1" != /* || "$2" != /* || "$3" != /* ||
      "$4" != /* || "$5" != /* ]]; then
  echo "Usage: build-wine29-followups.sh ABS_WINE29_SOURCE ABS_READOBJ ABS_SEALED_SIX ABS_NEW_OUTPUT ABS_PINNED_ARCHIVE" >&2
  exit 2
fi
source="$1"; readobj="$2"; six="$3"; out="$4"; baseline="$5"
scripts="$(cd "$(dirname "$0")" && pwd)"
build="$source/charoite-arm64ec-android"
[[ -d "$build" && -x "$readobj" && -d "$six" && ! -L "$six" &&
   -s "$six/wine29-07-six-candidates.json" && -s "$baseline" &&
   -s "$source/charoite-wine29-native-source-validation.json" &&
   -d "$(dirname "$out")" && ! -e "$out" && ! -L "$out" ]] || {
  echo "Refusing missing/unsafe source generation or nonempty extension output" >&2; exit 3;
}
case " $source $readobj $six $out $baseline " in
  *"/data/data/"*|*"/data/user/"*|*"/storage/emulated/"*|*"/sdcard/"*)
    echo "Refusing Android and user-data paths" >&2; exit 4 ;;
esac
# Repeat all six proofs, and demand the exact original .0.7 archive identity.
python3 "$scripts/verify-wine29-deps.py" verify "$six" "$readobj"
python3 - "$source" "$baseline" <<'PY'
import hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
root=Path(sys.argv[1]); archive=Path(sys.argv[2])
path=Path("next-generation/charoite-wine/verify-bootstrap-bundle.py").resolve()
spec=importlib.util.spec_from_file_location("wine29_followup_base",path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
if hashlib.sha256(archive.read_bytes()).hexdigest()!="66068032bd2203c8e53fddc92ce46b84086eb293306b2bd12bb741bf9a5e035e":
    raise ValueError("Original Wine29 .0.7 archive hash differs")
manifest,_=module.verify(archive)
proof=json.loads((root/"charoite-wine29-native-source-validation.json").read_text())
head=subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()
if (head!="c74acb09d51b447f5d5ac56c87608d3ec565a767" or
    manifest.get("version")!="wine10-arm64ec-bootstrap.0.7" or
    proof.get("delta_sha256")!=manifest.get("wine29_native_source_delta_sha256") or
    manifest.get("component_count")!=27 or manifest.get("nls_count")!=76):
    raise ValueError("Unapproved mixed Wine29 ARM64EC source or manifest")
print("WINE29_07_FOLLOWUP_SOURCE_AND_BASELINE_HASH_VERIFIED=PASS")
PY
for name in urlmon windowscodecs; do
  [[ -s "$source/dlls/$name/Makefile.in" && ! -L "$source/dlls/$name/Makefile.in" ]] || {
    echo "Original pinned Wine source lacks candidate Makefile: $name" >&2; exit 5;
  }
done
cd "$build"
for name in urlmon windowscodecs; do
  # Compiles PE only; no Wine, Wineboot or target Windows executable is run.
  make -j2 "dlls/$name/aarch64-windows/$name.dll"
  pe="$build/dlls/$name/aarch64-windows/$name.dll"
  [[ -s "$pe" && ! -L "$pe" ]] || {
    echo "Source-built candidate missing: $name" >&2; exit 6;
  }
done
mkdir "$out"
for name in urlmon windowscodecs; do
  pe="$build/dlls/$name/aarch64-windows/$name.dll"
  cp "$pe" "$out/$name-arm64ec.dll"
  inspected="$out/$name-arm64ec.dll"
  "$readobj" --file-headers "$inspected" > "$out/$name-pe-header.txt"
  "$readobj" --coff-imports "$inspected" > "$out/$name-pe-imports.txt"
  grep -Fq 'Machine: IMAGE_FILE_MACHINE_ARM64EC (0xA641)' \
    "$out/$name-pe-header.txt" || {
    echo "Candidate lacks expected ARM64EC view: $name" >&2; exit 7;
  }
done
python3 "$scripts/verify-wine29-followups.py" create "$out" "$readobj" "$six" "$baseline"
python3 "$scripts/verify-wine29-followups.py" verify "$out" "$readobj" "$six" "$baseline"
echo "WINE29_07_TWO_FOLLOWUP_SOURCE_PE_HASHES_VERIFIED=PASS"
echo "WINE29_07_NO_PHONE_STAGING_OR_WINDOWS_EXECUTION=PASS"
