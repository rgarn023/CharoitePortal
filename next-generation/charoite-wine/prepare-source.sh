#!/usr/bin/env bash
# Materialize Charoite Wine's pinned source tree in an isolated workspace.
# This is a SOURCE PREPARATION tool, not a binary build or APK installer.
set -euo pipefail
if [ "$#" -ne 1 ]; then
  echo "Usage: bash next-generation/charoite-wine/prepare-source.sh ABSOLUTE_EMPTY_WORKDIR" >&2
  exit 2
fi
workspace="$1"
case "$workspace" in
  /*) ;;
  *) echo "Destination must be absolute" >&2; exit 2;;
esac
if [ -e "$workspace" ]; then
  echo "Refusing an existing destination; no files will be overwritten: $workspace" >&2
  exit 3
fi
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
base_sha="c74acb09d51b447f5d5ac56c87608d3ec565a767"
git clone --filter=blob:none --no-checkout https://github.com/The412Banner/proton-wine.git "$workspace"
cd "$workspace"
git fetch --depth 1 origin "$base_sha"
git checkout --detach "$base_sha"
test "$(git rev-parse HEAD)" = "$base_sha"
# GE / Bionic / ARM64EC prerequisite patches must be reviewed and applied
# from the pinned build tree before the following Wine fixes; do not apply
# fuzzed patches or claim success when the base is not ready.
if [ "${CHAROITE_WINE_PREREQUISITES_PREPARED:-0}" != "1" ]; then
  echo "Pinned source cloned. Prerequisite GE+ARM64EC patch preparation not yet validated." >&2
  echo "Stopping BEFORE applying Charoite patch queue; no binaries produced." >&2
  exit 4
fi
for patch in "$script_dir"/patches/*.patch; do
  git apply --check "$patch"
  git apply --whitespace=error "$patch"
done
echo "Charoite Wine source patch queue applied. Compile and smoke tests still required."
git diff --stat
