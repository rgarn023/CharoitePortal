#!/usr/bin/env bash
# Independent, source-only Wine29 urlmon/windowscodecs candidate expansion.
# Does not run Windows binaries, Wine, Wineboot, Android, or touch prefixes.
set -euo pipefail
if [[ $# -ne 5 || "$1" != /* || "$2" != /* || "$3" != /* || "$4" != /* || "$5" != /* ]]; then
  echo "Usage: build-followups.sh ABS_WINE_SOURCE ABS_LLVM_READOBJ ABS_PINNED_ARCHIVE ABS_VERIFIED_SIX_DIR ABS_FRESH_OUTPUT" >&2
  exit 2
fi
source="$1"; readobj="$2"; archive="$3"; six="$4"; out="$5"
scripts="$(cd "$(dirname "$0")" && pwd)"
root="$(cd "$scripts/.." && pwd)"
build="$source/charoite-arm64ec-android"
[[ -x "$readobj" && -f "$archive" && -d "$six" && -d "$build" &&
   -d "$(dirname "$out")" && ! -e "$out" && ! -L "$out" ]] || {
  echo "Missing pinned source or verified six candidates, or output not fresh" >&2; exit 3;
}
case " $source $readobj $archive $six $out " in
  *"/data/data/"*|*"/data/user/"*|*"/storage/emulated/"*|*"/sdcard/"*)
    echo "Never use Android/user storage" >&2; exit 4 ;;
esac
# This validates every existing copied six-DLL artifact, ABI log, source
# generation and the experimental oleaut32 currency portability attestation.
python3 "$root/wine29-deps/verify-wine29-deps.py" verify "$six" "$readobj"
python3 - "$archive" "$six/wine29-07-six-candidates.json" <<'PY'
from pathlib import Path
import hashlib,json,sys
if hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest() != "66068032bd2203c8e53fddc92ce46b84086eb293306b2bd12bb741bf9a5e035e":
    raise ValueError("Mismatch in pinned .0.7 source archive")
report=json.loads(Path(sys.argv[2]).read_text())
if (report["generation"]!="wine10-arm64ec-dependencies.0.8-candidate" or
    report["component_count"]!=6 or report["source_commit"]!="c74acb09d51b447f5d5ac56c87608d3ec565a767" or
    report["baseline_source_archive_sha256"]!="66068032bd2203c8e53fddc92ce46b84086eb293306b2bd12bb741bf9a5e035e" or
    report["launch_ready"] is not False):
    raise ValueError("Six-DLL source provenance mismatch")
PY
for name in urlmon windowscodecs; do
  [[ -s "$source/dlls/$name/Makefile.in" && ! -L "$source/dlls/$name/Makefile.in" ]] || {
    echo "Missing pinned follow-up source: $name" >&2; exit 5;
  }
done
cd "$build"
for name in urlmon windowscodecs; do
  # Host make and LLVM inspection only; cross-built PE is never executed.
  make -j2 "dlls/$name/aarch64-windows/$name.dll"
  pe="$build/dlls/$name/aarch64-windows/$name.dll"
  [[ -s "$pe" && ! -L "$pe" ]] || { echo "No PE for $name" >&2; exit 6; }
done
mkdir "$out"
for name in urlmon windowscodecs; do
  cp "$build/dlls/$name/aarch64-windows/$name.dll" "$out/$name-arm64ec.dll"
  "$readobj" --file-headers "$out/$name-arm64ec.dll" > "$out/$name-pe-header.txt"
  "$readobj" --coff-imports "$out/$name-arm64ec.dll" > "$out/$name-pe-imports.txt"
  grep -Fq 'Machine: IMAGE_FILE_MACHINE_ARM64EC (0xA641)' "$out/$name-pe-header.txt" || {
    echo "Missing ARM64EC nested view: $name" >&2; exit 7;
  }
done
cd "$GITHUB_WORKSPACE"
python3 "$scripts/verify-followups.py" create "$archive" "$six" "$out" "$readobj"
python3 "$scripts/verify-followups.py" verify "$archive" "$six" "$out" "$readobj"
echo WINE29_07_SOURCE_ONLY_2_TRANSITIVE_CANDIDATES=PASS
echo WINE29_07_PE_WINEBOOT_PHONE_PREFIX=NOT_EXECUTED_OR_TOUCHED
