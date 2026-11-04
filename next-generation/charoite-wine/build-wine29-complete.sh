#!/usr/bin/env bash
# CI-only: 27 Windows/ELF components + 76 Wine NLS, same isolated Wine29 tree.
# This is an archive build, NEVER an APK, phone install, Wineboot execution,
# user prefix, Winlator data, or a Windows game runtime.
set -euo pipefail
if [[ $# -ne 5 || "$1" != /* || "$2" != /* || "$3" != /* || "$4" != /* || "$5" != /* ]]; then
  echo "Usage: build-wine29-complete.sh ABS_FRESH_WINE29_SOURCE ABS_NDK_READELF ABS_LLVM_READOBJ ABS_NATIVE_PROOF_JSON ABS_NEW_OUTDIR" >&2
  exit 2
fi
source_dir="$1"
readelf="$2"
readobj="$3"
native_proof="$4"
output="$5"
scripts="$(cd "$(dirname "$0")" && pwd)"
build="$source_dir/charoite-arm64ec-android"
[[ -d "$build" && -f "$source_dir/charoite-source-validation.txt" ]] || {
  echo "Refusing nonexistent source-matched Wine29 build" >&2; exit 3;
}
[[ -s "$source_dir/charoite-wine29-native-source-validation.json" &&
   -s "$source_dir/charoite-wine29-native-source-delta.patch" &&
   -s "$native_proof" &&
   -x "$readelf" && -x "$readobj" ]] || {
  echo "Missing source-verified Wine29 inputs or trusted ABI inspectors" >&2; exit 3;
}
[[ -d "$(dirname "$output")" && ! -e "$output" && ! -L "$output" ]] || {
  echo "Refusing existing/new Wine29 output destination" >&2; exit 4;
}
case " $source_dir $output $native_proof " in
  *"/data/data/"*|*"/data/user/"*|*"/storage/emulated/"*|*"/sdcard/"*)
    echo "Refusing Android installed or shared user data path" >&2; exit 4 ;;
esac
python3 - "$source_dir" "$native_proof" <<'PY'
import json,sys
from pathlib import Path
root=Path(sys.argv[1]); proof=json.loads(Path(sys.argv[2]).read_text())
src=json.loads((root/"charoite-wine29-native-source-validation.json").read_text())
assert src["generation"]=="wine10-arm64ec-bootstrap.0.7"
assert proof["source_generation"]==src["generation"]
assert proof["source_patch_sha256"]==src["delta_sha256"]
assert set(proof["components"])=={"wine","wineserver","ntdll_unix","ntdll_windows"}
assert proof["native_elf_count"]==3 and proof["windows_ntdll_pe_count"]==1
assert proof["launch_ready"] is False and proof["native_elf_installed"] is False
assert proof["new_27_component_archive_verified"] is False
print("WINE29_NATIVE_INPUT_SOURCE_GENERATION=PASS")
PY

# Rebuild every audited PE and NLS component FROM THE SAME PATCHED SOURCE.
# These existing scripts recheck prerequisites and refuse preexisting outputs.
bash "$scripts/build-kernel-bridge.sh" "$build" "$readobj" \
  "$source_dir/charoite-kernel-bridge"
python3 "$scripts/verify-kernel-bridge.py" \
  "$source_dir/charoite-kernel-bridge"

bash "$scripts/build-wineboot.sh" "$build" "$readobj" \
  "$source_dir/charoite-wineboot"
python3 "$scripts/verify-wineboot.py" "$source_dir/charoite-wineboot"

python3 "$scripts/audit-runtime-deps.py" "$build" "$readelf" "$readobj" \
  "$source_dir/charoite-dependency-inventory"
grep -Fxq 'CHAROITE_WINE_DEPENDENCY_AUDIT=PASS' \
  "$source_dir/charoite-dependency-inventory/runtime-dependency-inventory.txt"

bash "$scripts/build-pe-foundation.sh" "$build" "$readobj" \
  "$source_dir/charoite-dependency-inventory/runtime-dependency-inventory.json" \
  "$source_dir/charoite-pe-foundation"
python3 "$scripts/verify-pe-foundation.py" "$source_dir/charoite-pe-foundation"

bash "$scripts/build-pe-expansion.sh" "$build" "$readobj" \
  "$source_dir/charoite-dependency-inventory/runtime-dependency-inventory.json" \
  "$source_dir/charoite-pe-foundation" "$source_dir/charoite-pe-expansion"
python3 "$scripts/verify-pe-expansion.py" "$source_dir/charoite-pe-expansion" \
  "$source_dir/charoite-pe-foundation"

python3 "$scripts/assemble-bootstrap-bundle.py" "$build" "$readelf" "$readobj" \
  "$source_dir/charoite-bootstrap-bundle"
python3 "$scripts/verify-bootstrap-bundle.py" \
  "$source_dir/charoite-bootstrap-bundle/charoite-wine-bootstrap-bundle.tar.gz"

bash "$scripts/build-pe-startup.sh" "$build" "$readobj" \
  "$source_dir/charoite-bootstrap-bundle/dependency-review.json" \
  "$source_dir/charoite-pe-startup"
python3 "$scripts/verify-pe-startup.py" "$source_dir/charoite-pe-startup" \
  "$source_dir/charoite-bootstrap-bundle/dependency-review.json"

python3 "$scripts/assemble-bootstrap-bundle.py" "$build" "$readelf" "$readobj" \
  "$source_dir/charoite-bootstrap-extended" --include-startup
python3 "$scripts/verify-bootstrap-bundle.py" \
  "$source_dir/charoite-bootstrap-extended/charoite-wine-bootstrap-bundle.tar.gz"

bash "$scripts/build-pe-com.sh" "$build" "$readobj" \
  "$source_dir/charoite-bootstrap-extended/dependency-review.json" \
  "$source_dir/charoite-pe-com"
python3 "$scripts/verify-pe-com.py" "$source_dir/charoite-pe-com" \
  "$source_dir/charoite-bootstrap-extended/dependency-review.json"

python3 "$scripts/assemble-bootstrap-bundle.py" "$build" "$readelf" "$readobj" \
  "$source_dir/charoite-bootstrap-com-extended" --include-com
python3 "$scripts/verify-bootstrap-bundle.py" \
  "$source_dir/charoite-bootstrap-com-extended/charoite-wine-bootstrap-bundle.tar.gz"

bash "$scripts/build-pe-services.sh" "$build" "$readobj" \
  "$source_dir/charoite-bootstrap-com-extended/dependency-review.json" \
  "$source_dir/charoite-pe-services"
python3 "$scripts/verify-pe-services.py" "$source_dir/charoite-pe-services" \
  "$source_dir/charoite-bootstrap-com-extended/dependency-review.json"

python3 "$scripts/assemble-bootstrap-bundle.py" "$build" "$readelf" "$readobj" \
  "$source_dir/charoite-bootstrap-services-extended" --include-services
python3 "$scripts/verify-bootstrap-bundle.py" \
  "$source_dir/charoite-bootstrap-services-extended/charoite-wine-bootstrap-bundle.tar.gz"

bash "$scripts/build-apiset-bootstrap.sh" "$build" "$readobj" \
  "$source_dir/charoite-apiset-schema"
python3 "$scripts/verify-apiset-bootstrap.py" "$source_dir/charoite-apiset-schema"

# ONLY the final sealed .0.7 output is published. Earlier archives above are
# internal audit prerequisites, never substituted for this native generation.
python3 "$scripts/assemble-bootstrap-bundle.py" "$build" "$readelf" "$readobj" \
  "$output" --include-wine29
archive="$output/charoite-wine-bootstrap-bundle.tar.gz"
python3 "$scripts/verify-bootstrap-bundle.py" "$archive"
python3 "$scripts/verify-wine29-native-isolation.py" "$archive"

# Independent link to the earlier separate verified native build, so that
# a stale ELF copy or older NTDLL cannot be inserted after native verification.
python3 - "$archive" "$native_proof" <<'PY'
import importlib.util,json,sys
from pathlib import Path
file=Path("next-generation/charoite-wine/verify-bootstrap-bundle.py").resolve()
spec=importlib.util.spec_from_file_location("wine29_source_abi",file)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
manifest,review=mod.verify(Path(sys.argv[1]))
prior=json.loads(Path(sys.argv[2]).read_text())
assert manifest["version"]=="wine10-arm64ec-bootstrap.0.7"
assert manifest["component_count"]==27 and manifest["nls_count"]==76
assert prior["source_patch_sha256"]==manifest["wine29_native_source_delta_sha256"]
for name in ("wine","wineserver","ntdll_unix"):
    assert manifest["components"][name]["sha256"]==prior["components"][name]["sha256"]
assert manifest["components"]["ntdll"]["sha256"]==prior["components"]["ntdll_windows"]["sha256"]
assert manifest["launch_ready"] is False and manifest["installable"] is False
print("WINE29_FULL_27_COMPONENT_NATIVE_PROOF_MATCH=PASS")
print("WINE29_NLS_COUNT=76")
print("WINE29_PHONE_EXECUTION=NOT_ATTEMPTED")
PY
grep -Fxq 'COMPONENTS=27' "$output/bundle-report.txt"
grep -Fxq 'NLS_COUNT=76' "$output/bundle-report.txt"
grep -Fxq 'LAUNCH_READY=false' "$output/bundle-report.txt"
echo "WINE29_COHERENT_SOURCE_MATCHED_FULL_BUNDLE=PASS"
