#!/usr/bin/env bash
# Source-only: construct Wine10 ARM64 API-set PE. Never executes Wine or phone code.
set -euo pipefail
[[ $# == 3 && "$1" == /* && "$2" == /* && "$3" == /* ]] || exit 2
build="$1"; tool="$2"; out="$3"; src="$(dirname "$build")"
[[ -x "$tool" && -s "$src/charoite-source-validation.txt" && -s "$src/charoite-source-delta.patch" ]] || exit 3
[[ -s "$src/dlls/apisetschema/apisetschema.spec" && -s "$src/dlls/apisetschema/Makefile.in" && -s "$src/COPYING.LIB" ]] || exit 3
grep -Fxq 'MODULE    = apisetschema.dll' "$src/dlls/apisetschema/Makefile.in"
grep -Fxq 'EXTRADLLFLAGS = -Wb,--data-only' "$src/dlls/apisetschema/Makefile.in"
[[ ! -e "$out" && -d "$(dirname "$out")" ]] || exit 4
case " $build $out " in
  *"/data/user/"*|*"/data/data/"*|*"/storage/emulated/"*) exit 4;;
esac
cd "$build"
make -j2 dlls/apisetschema/aarch64-windows/apisetschema.dll
module="$PWD/dlls/apisetschema/aarch64-windows/apisetschema.dll"
[[ -s "$module" && ! -L "$module" ]] || exit 5
mkdir "$out"
cp "$module" "$out/apisetschema.dll"
cp "$src/dlls/apisetschema/apisetschema.spec" "$out/apisetschema.spec"
cp "$src/dlls/apisetschema/Makefile.in" "$out/Makefile.in"
cp "$src/COPYING.LIB" "$out/COPYING.LIB"
"$tool" --file-headers "$module" > "$out/pe-file-header.txt"
echo 'WINE_APISET_COMPILED_NOT_EXECUTED=PASS'
