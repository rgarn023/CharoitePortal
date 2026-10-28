#!/usr/bin/env bash
# Compile Charoite Wine's Android ARM64 wineserver from already-validated source.
# This is a native toolchain milestone: NOT a runnable ARM64EC Wine installation.
# Requires: pinned Android NDK r27d, generated Wine sources, host autotools.
set -euo pipefail

if [[ $# -ne 2 || "$1" != /* || "$2" != /* ]]; then
  echo "Usage: bash build-android-arm64.sh ABSOLUTE_PREPARED_WINE ABSOLUTE_ANDROID_NDK" >&2
  exit 2
fi
source_dir="$1"
ndk="$2"
bin="$ndk/toolchains/llvm/prebuilt/linux-x86_64/bin"
cc="$bin/aarch64-linux-android35-clang"
cxx="$bin/aarch64-linux-android35-clang++"
ar="$bin/llvm-ar"
strip="$bin/llvm-strip"
readelf="$bin/llvm-readelf"
[[ -f "$source_dir/charoite-source-validation.txt" ]] || {
  echo "Unvalidated Wine source: refusing native compilation" >&2
  exit 3
}
for tool in "$cc" "$cxx" "$ar" "$strip" "$readelf"; do
  [[ -x "$tool" ]] || { echo "Missing pinned Android tool: $tool" >&2; exit 3; }
done
for directory in charoite-host-tools charoite-arm64-android; do
  [[ ! -e "$source_dir/$directory" ]] || {
    echo "Refusing to overwrite existing Wine build: $directory" >&2; exit 4;
  }
done
# The pinned DirectAudio submodule provides Makefile.in, even in builds
# that disable audio. This does not modify an installed runtime or prefix.
git -C "$source_dir" submodule update --init --depth 1 dlls/winedirectaudio.drv
[[ -f "$source_dir/dlls/winedirectaudio.drv/Makefile.in" ]]
( cd "$source_dir" && ./autogen.sh )
[[ -f "$source_dir/configure" ]] || exit 4

# Build native host tools (makedep, winebuild etc.) needed by cross Wine.
mkdir "$source_dir/charoite-host-tools"
cd "$source_dir/charoite-host-tools"
../configure --enable-win64 --disable-tests \
  --without-x --without-freetype --without-fontconfig \
  --without-opengl --without-vulkan --without-gstreamer \
  --without-alsa --without-pulse --without-sdl --without-gnutls
make -j2 __tooldeps__

# Wine's unix-host architecture is aarch64-linux-android35. The ARM64EC
# Windows PE DLLs are deliberately NOT attempted in this milestone.
mkdir "$source_dir/charoite-arm64-android"
cd "$source_dir/charoite-arm64-android"
export PATH="$bin:$PATH"
export CC="$cc"
export CXX="$cxx"
export AR="$ar"
export RANLIB="$bin/llvm-ranlib"
export STRIP="$strip"
export CFLAGS="-O2 -g0 -DANDROID_SUPPORT_FLEXIBLE_PAGE_SIZES"
export CXXFLAGS="$CFLAGS"
export LDFLAGS="-Wl,-z,max-page-size=16384"
export PKG_CONFIG_LIBDIR="/nonexistent/charoite-host-pkgconfig"

# Explicit bindir/libdir keep Wine's locale/NLS lookup adjacent to its own
# binary instead of letting an Android ABI triplet change runtime resolution.
../configure \
  --host=aarch64-linux-android35 \
  --enable-win64 --disable-tests \
  --with-wine-tools=../charoite-host-tools \
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

make -j2 server/wineserver
out="$PWD/server/wineserver"
[[ -s "$out" ]] || { echo "Android wineserver missing" >&2; exit 5; }
"$readelf" -h "$out" | grep -F 'AArch64'
"$readelf" -lW "$out" > "$source_dir/charoite-android-program-headers.txt"
"$readelf" -h "$out" > "$source_dir/charoite-android-elf-header.txt"
# Fail unless every ELF LOAD p_align is at least 16 KiB.
python3 - "$source_dir/charoite-android-program-headers.txt" <<'PY'
from pathlib import Path
import re,sys
text=Path(sys.argv[1]).read_text()
alignments=[]
for line in text.splitlines():
    if re.search(r'^\s+LOAD\s',line):
        match=re.search(r'(0x[0-9a-fA-F]+)\s*$',line)
        if not match:
            raise SystemExit("Unable to check Android ELF LOAD alignment")
        alignments.append(int(match.group(1),16))
if not alignments or any(a<16384 for a in alignments):
    raise SystemExit(f"Android 16 KiB page alignment failed: {alignments}")
print("Android ARM64 LOAD alignments:",alignments)
PY
mkdir "$source_dir/charoite-android-native-artifact"
cp "$out" "$source_dir/charoite-android-native-artifact/wineserver-arm64-android"
cp "$source_dir/charoite-android-program-headers.txt" "$source_dir/charoite-android-native-artifact/"
cp "$source_dir/charoite-android-elf-header.txt" "$source_dir/charoite-android-native-artifact/"
{
  echo "Charoite Wine Android ARM64 server native cross-build"
  echo "Upstream source: c74acb09d51b447f5d5ac56c87608d3ec565a767"
  echo "Target: Android API 35, aarch64, 16 KiB ELF LOAD"
  echo "Built binary: wineserver-arm64-android (NOT yet integrated)"
  echo "ARM64EC ntdll/FEX/Steam/Battle.net: NOT BUILT OR TESTED"
  file "$out"
  sha256sum "$out"
} > "$source_dir/charoite-android-native-artifact/build-report.txt"
echo "ANDROID ARM64 WINESERVER CROSS-COMPILED (not an installable runner)"
