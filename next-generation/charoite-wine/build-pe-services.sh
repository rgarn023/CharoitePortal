#!/usr/bin/env bash
# Source-locked ARM64EC Wine PE security/runtime dependency expansion.
# This is a CI cross-build only: no phone, Wine prefix or executable startup.
set -euo pipefail
if [[ $# -ne 4 || "${1:-}" != /* || "${2:-}" != /* || "${3:-}" != /* || "${4:-}" != /* ]]; then
  echo "Usage: build-pe-services.sh ABS_BUILD ABS_LLVM_READOBJ ABS_22_REVIEW ABS_OUTPUT" >&2
  exit 2
fi
build="$1"; readobj="$2"; review="$3"; out="$4"
script_dir="$(cd "$(dirname "$0")" && pwd)"
[[ -x "$readobj" && -s "$review" && -f "$build/../charoite-source-validation.txt" ]] || {
  echo "Missing audited source build, LLVM inspector or dependency review" >&2; exit 3;
}
[[ ! -e "$out" && -d "$(dirname "$out")" ]] || {
  echo "Refusing existing or unsafe output directory" >&2; exit 4;
}
case " $build $review $out " in
  *"/data/data/"*|*"/data/user/"*|*"/storage/emulated/"*)
    echo "Refusing installed Android or shared game paths" >&2; exit 4 ;;
esac
python3 - "$review" <<'PY'
import json,sys
from pathlib import Path
d=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
expected={"bcrypt.dll","secur32.dll","sechost.dll","msvcrt.dll"}
assert d.get("schema_version")==1
assert d.get("purpose")=="Exact imports in sampled compiled bootstrap; not full runtime dependency closure"
assert expected.issubset(set(d.get("windows_imports_not_bundled",[])))
assert not (expected & set(d.get("bundled_windows_dlls",[])))
print("CHAROITE_SERVICES_AUDIT_22_INPUT_VERIFIED=PASS")
PY
cd "$build"
# The generated Wine Makefile hardcodes ARM64EC compiler invocations and
# ignores CROSSCFLAGS overrides. ARM64EC's hybrid defines select LibTomCrypt's
# x86 inline rotates, which are invalid for an ARM64EC compiler ('c' register).
# Gate the supported -DLTC_NO_ASM portable rotates in the ephemeral compiler
# wrapper ONLY while compiling bcrypt inputs. This does not modify the pinned
# Wine/LibTomCrypt source or loosen output ABI and SHA verification.
wrapper="$build/../charoite-arm64ec-toolwrap/arm64ec-w64-mingw32-clang"
[[ -x "$wrapper" && ! -L "$wrapper" ]] || {
  echo "Missing source-built ARM64EC tool wrapper" >&2; exit 5;
}
python3 - "$wrapper" <<'PY'
from pathlib import Path
import sys
wrapper=Path(sys.argv[1])
data=wrapper.read_text(encoding="utf-8")
lines=data.splitlines()
if (len(lines)!=2 or lines[0]!="#!/usr/bin/env bash"
        or not lines[1].startswith("exec ") or
        lines[1].count('"$@"')!=1 or
        "arm64ec-w64-windows-gnu" not in lines[1] or
        "-DLTC_NO_ASM" in lines[1]):
    raise SystemExit("Unexpected generated ARM64EC tool wrapper; fail closed")
cmd=lines[1]
portable=cmd.replace('"$@"','-DLTC_NO_ASM "$@"')
wrapper.write_text(
    "#!/usr/bin/env bash\\n"
    "case \" $* \" in\\n"
    "  *\"dlls/bcrypt/\"*)\\n"
    f"    {portable}\\n"
    "    ;;\\n"
    "  *)\\n"
    f"    {cmd}\\n"
    "    ;;\\n"
    "esac\\n",
    encoding="utf-8")
print("CHAROITE_ARM64EC_BCRYPT_PORTABLE_ROTATES_WRAPPER=PASS")
PY
make -j2 "dlls/bcrypt/aarch64-windows/bcrypt.dll"
for name in secur32 sechost msvcrt; do
  make -j2 "dlls/$name/aarch64-windows/$name.dll"
done
mkdir "$out"
for name in bcrypt secur32 sechost msvcrt; do
  file="$PWD/dlls/$name/aarch64-windows/$name.dll"
  [[ -f "$file" && -s "$file" && ! -L "$file" ]] || {
    echo "Missing same-build Windows ARM64EC module: $name" >&2; exit 5;
  }
  "$readobj" --file-headers "$file" > "$out/$name-pe-header.txt"
  grep -F 'Machine: IMAGE_FILE_MACHINE_ARM64EC (0xA641)' "$out/$name-pe-header.txt" >/dev/null || {
    echo "Not an independently confirmed ARM64EC view: $name" >&2; exit 5;
  }
  "$readobj" --coff-imports "$file" > "$out/$name-pe-imports.txt"
  cp "$file" "$out/$name-arm64ec.dll"
done
python3 - "$review" "$out" <<'PY'
from pathlib import Path
import hashlib,json,sys
audit=Path(sys.argv[1])
out=Path(sys.argv[2])
components={}
for name in ("bcrypt","secur32","sechost","msvcrt"):
    file=out/f"{name}-arm64ec.dll"
    components[name]={
        "file":file.name,"size":file.stat().st_size,
        "sha256":hashlib.sha256(file.read_bytes()).hexdigest(),
        "pe_machine":"0xA641","raw_arm64x_carrier":"0xAA64"
    }
manifest={
    "schema_version":1,
    "project":"Charoite Wine ARM64EC security/service CRT dependency expansion",
    "source_commit":"c74acb09d51b447f5d5ac56c87608d3ec565a767",
    "android_package":"com.charoitx",
    "dependency_review_sha256":hashlib.sha256(audit.read_bytes()).hexdigest(),
    "status":"compiled-not-executed",
    "launch_ready":False,"installable":False,"prefix_created":False,
    "device_tested":False,"anti_cheat_supported":False,
    "components":components,
    "remaining":"Additional Windows PE/Unix dependency closure, FEX, graphics and isolated Wineboot",
}
(out/"pe-services-manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n",encoding="utf-8")
PY
python3 "$script_dir/verify-pe-services.py" "$out" "$review"
echo "CHAROITE_PE_SERVICES_COMPILED_NOT_EXECUTED"
