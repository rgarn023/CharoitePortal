#!/usr/bin/env bash
# Charoite Wine: build ARM64EC Windows ntdll.dll plus Android ARM64 Unix ntdll.so.
# Experimental CI-only build, never installs to either Android app or Wine prefix.
set -euo pipefail
if [[ $# -ne 3 || "${1:-}" != /* || "${2:-}" != /* || "${3:-}" != /* ]]; then
  echo "Usage: bash build-arm64ec-ntdll.sh ABS_PREPARED_WINE ABS_NDK_R27D ABS_LLVM_MINGW" >&2
  exit 2
fi
source_dir="$1"
ndk="$2"
mingw="$3"
ndk_bin="$ndk/toolchains/llvm/prebuilt/linux-x86_64/bin"
llvm_bin="$mingw/bin"
test -f "$source_dir/charoite-source-validation.txt" || {
  echo "Refusing unvalidated patched Wine source" >&2; exit 3;
}
test -x "$ndk_bin/aarch64-linux-android35-clang" || exit 3
test -x "$llvm_bin/clang" || exit 3
test -x "$llvm_bin/aarch64-w64-mingw32-clang" || exit 3
test -x "$llvm_bin/x86_64-w64-mingw32-clang" || exit 3
test -x "$llvm_bin/llvm-readobj" || exit 3
for path in charoite-arm64ec-host-tools charoite-arm64ec-android charoite-arm64ec-toolwrap charoite-arm64ec-artifact; do
  test ! -e "$source_dir/$path" || {
    echo "Refusing to replace existing ARM64EC build output: $path" >&2; exit 4;
  }
done

# Wine's ARM64EC architecture is a hybrid PE machine, different from ARM64.
# This wrapper chooses the hybrid target explicitly, never relying on default
# aarch64-w64-mingw32-clang behavior or a PE file extension.
mkdir "$source_dir/charoite-arm64ec-toolwrap"
cat > "$source_dir/charoite-arm64ec-toolwrap/arm64ec-w64-mingw32-clang" <<EOF
#!/usr/bin/env bash
exec "$llvm_bin/clang" --target=arm64ec-w64-windows-gnu --sysroot="$mingw" "\$@"
EOF
chmod +x "$source_dir/charoite-arm64ec-toolwrap/arm64ec-w64-mingw32-clang"
export PATH="$source_dir/charoite-arm64ec-toolwrap:$llvm_bin:$ndk_bin:$PATH"

# Clang must produce ARM64EC COFF, rather than regular AArch64 COFF.
printf 'int charoite_arm64ec_probe(void) { return 42; }\n' > "$source_dir/charoite-arm64ec-probe.c"
"$source_dir/charoite-arm64ec-toolwrap/arm64ec-w64-mingw32-clang" \
  -c "$source_dir/charoite-arm64ec-probe.c" -o "$source_dir/charoite-arm64ec-probe.obj"
"$llvm_bin/llvm-readobj" --file-headers "$source_dir/charoite-arm64ec-probe.obj" \
  > "$source_dir/charoite-arm64ec-probe-header.txt"
grep -Ei 'Machine: IMAGE_FILE_MACHINE_ARM64EC|Machine: ARM64EC|Machine: 0xA641' \
  "$source_dir/charoite-arm64ec-probe-header.txt"

# The pinned DirectAudio submodule is part of Wine's generated make graph.
git -C "$source_dir" submodule update --init --depth 1 dlls/winedirectaudio.drv
test -s "$source_dir/dlls/winedirectaudio.drv/Makefile.in"
( cd "$source_dir" && ./autogen.sh )
test -f "$source_dir/configure"

mkdir "$source_dir/charoite-arm64ec-host-tools"
cd "$source_dir/charoite-arm64ec-host-tools"
../configure --enable-win64 --disable-tests --without-x \
  --without-freetype --without-fontconfig --without-opengl --without-vulkan \
  --without-gstreamer --without-alsa --without-pulse --without-sdl --without-gnutls
make -j2 __tooldeps__

mkdir "$source_dir/charoite-arm64ec-android"
cd "$source_dir/charoite-arm64ec-android"
export CC="$ndk_bin/aarch64-linux-android35-clang"
export CXX="$ndk_bin/aarch64-linux-android35-clang++"
export AR="$ndk_bin/llvm-ar"
export RANLIB="$ndk_bin/llvm-ranlib"
export CFLAGS="-O2 -g0 -DANDROID_SUPPORT_FLEXIBLE_PAGE_SIZES"
export CXXFLAGS="$CFLAGS"
export LDFLAGS="-Wl,-z,max-page-size=16384"
export CROSSCFLAGS="-O2 -g0"
export PKG_CONFIG_LIBDIR="/nonexistent/charoite-mingw-pkgconfig"
# Wine may probe both aarch64 and x86_64 due to ARM64EC's hybrid ABI.
export arm64ec_CC="$source_dir/charoite-arm64ec-toolwrap/arm64ec-w64-mingw32-clang"
export aarch64_CC="$llvm_bin/aarch64-w64-mingw32-clang"
export x86_64_CC="$llvm_bin/x86_64-w64-mingw32-clang"

../configure \
  --host=aarch64-linux-android35 --enable-win64 --disable-tests \
  --enable-archs=arm64ec,aarch64 --with-mingw=yes \
  --with-wine-tools=../charoite-arm64ec-host-tools \
  --prefix=/data/data/com.charoitx/files/rootfs/usr/opt/charoite-wine \
  --bindir=/data/data/com.charoitx/files/rootfs/usr/opt/charoite-wine/bin \
  --libdir=/data/data/com.charoitx/files/rootfs/usr/opt/charoite-wine/lib \
  --exec-prefix=/data/data/com.charoitx/files/rootfs/usr/opt/charoite-wine \
  --without-x --without-freetype --without-fontconfig \
  --without-opengl --without-vulkan --without-gstreamer \
  --without-alsa --without-pulse --without-sdl --without-gnutls \
  --without-inotify --without-unwind --without-gettext \
  --without-cups --without-dbus --without-gssapi --without-opencl \
  --without-sane --without-pcap --without-usb --without-udev

# Windows ARM64EC PE and Unix Android loader must come from THE SAME source.
# Wine 10's ARM64EC PE install directory uses aarch64-windows.
make -j2 dlls/ntdll/arm64ec-windows/ntdll.dll dlls/ntdll/ntdll.so

pe="$PWD/dlls/ntdll/arm64ec-windows/ntdll.dll"
elf="$PWD/dlls/ntdll/ntdll.so"
[[ -s "$pe" && -s "$elf" ]] || {
  echo "Both Wine ntdll components must be nonempty" >&2; exit 5;
}
mkdir "$source_dir/charoite-arm64ec-artifact"
"$llvm_bin/llvm-readobj" --file-headers "$pe" \
  > "$source_dir/charoite-arm64ec-artifact/ntdll-pe-header.txt"
grep -Ei 'Machine: IMAGE_FILE_MACHINE_ARM64EC|Machine: ARM64EC|Machine: 0xA641' \
  "$source_dir/charoite-arm64ec-artifact/ntdll-pe-header.txt"
"$ndk_bin/llvm-readelf" -h "$elf" > "$source_dir/charoite-arm64ec-artifact/ntdll-elf-header.txt"
"$ndk_bin/llvm-readelf" -h "$elf" | grep -F 'AArch64'
"$ndk_bin/llvm-readelf" -lW "$elf" > "$source_dir/charoite-arm64ec-artifact/ntdll-elf-program-headers.txt"
python3 - "$source_dir/charoite-arm64ec-artifact/ntdll-elf-program-headers.txt" <<'PY'
from pathlib import Path
import re
import sys
loads = []
for line in Path(sys.argv[1]).read_text().splitlines():
    if re.match(r'^\s*LOAD\s', line):
        match = re.search(r'(0x[0-9A-Fa-f]+)\s*$', line)
        if not match:
            raise SystemExit('Unparseable ARM64 ntdll.so PT_LOAD alignment')
        loads.append(int(match.group(1), 16))
if not loads or any(align < 16384 for align in loads):
    raise SystemExit(f'Android ntdll.so PT_LOAD not 16KiB-compatible: {loads}')
print('Android ntdll.so PT_LOAD alignments:', loads)
PY
cp "$pe" "$source_dir/charoite-arm64ec-artifact/ntdll-arm64ec.dll"
cp "$elf" "$source_dir/charoite-arm64ec-artifact/ntdll-arm64-android.so"
{
  echo "Charoite Wine ntdll dual-architecture experimental cross-build"
  echo "Source SHA: c74acb09d51b447f5d5ac56c87608d3ec565a767"
  echo "PE: ARM64EC; Unix: Android AArch64; 16KiB PT_LOAD"
  echo "NOT an executable Android runner; NOT installed in either Charoite edition"
  sha256sum "$pe" "$elf"
} > "$source_dir/charoite-arm64ec-artifact/build-report.txt"
echo "CHAROITE WINE ARM64EC NTDLL PE + ANDROID NTDLL SO BUILT"
