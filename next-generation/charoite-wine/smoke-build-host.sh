#!/usr/bin/env bash
# Host-only compile smoke test for pinned, patched Charoite Wine.
# Output is a Linux x86-64 wineserver for validating modified source linking.
# NEVER install or ship this as an Android ARM64EC runner.
set -euo pipefail
if [[ $# -ne 1 || "$1" != /* ]]; then
  echo "Usage: bash smoke-build-host.sh ABSOLUTE_PREPARED_SOURCE_DIR" >&2
  exit 2
fi
source_dir="$1"
[[ -f "$source_dir/charoite-source-validation.txt" ]] || {
  echo "Refusing unvalidated Wine source tree" >&2; exit 3;
}
[[ -f "$source_dir/server/token.c" ]] || exit 3
grep -F -q 'Android runs each app as its own uid' "$source_dir/server/token.c" || {
  echo "Missing patched Android file-owner handling" >&2; exit 3;
}
test ! -e "$source_dir/charoite-host-build" || {
  echo "Refusing to overwrite an existing host build directory" >&2; exit 3;
}
mkdir "$source_dir/charoite-host-build"
# This Wine source commit intentionally tracks configure.ac rather than a
# generated configure script. Regenerate in the isolated checkout first.
( cd "$source_dir" && ./autogen.sh )
[[ -f "$source_dir/configure" ]] || { echo "Wine configure generation failed" >&2; exit 4; }
cd "$source_dir/charoite-host-build"

# This deliberately configures a minimal Linux/host Wine server toolchain.
# No APK prefix is opened and no device/existing game files are touched.
../configure --enable-win64 --disable-tests \
  --without-x --without-freetype --without-fontconfig \
  --without-opengl --without-vulkan --without-gstreamer \
  --without-alsa --without-pulse --without-sdl --without-gnutls

make -j2 server/wineserver
binary="$PWD/server/wineserver"
[[ -x "$binary" ]] || { echo "No host wineserver output" >&2; exit 4; }
file "$binary"
readelf -h "$binary" | grep -F 'ELF64'
"$binary" --version
{
  echo "Charoite Wine host smoke-build (NOT Galaxy ARM64EC)"
  echo "Upstream source: c74acb09d51b447f5d5ac56c87608d3ec565a767"
  echo "Executable: server/wineserver (host Linux)"
  echo "Android native binaries: NOT COMPILED"
  echo "Battle.net / Steam / anti-cheat: NOT TESTED"
  file "$binary"
  sha256sum "$binary"
} > "$source_dir/charoite-host-build-validation.txt"
echo "HOST WINE SERVER COMPILE VERIFIED (not Android)"
