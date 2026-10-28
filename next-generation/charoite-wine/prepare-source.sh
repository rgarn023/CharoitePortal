#!/usr/bin/env bash
# Charoite Wine: deterministic source preparation only, not a runnable Wine build.
# Never invokes upstream build scripts that delete/overwrite installed runtimes.
set -euo pipefail

if [[ $# -ne 1 || "$1" != /* ]]; then
  echo "Usage: bash prepare-source.sh ABSOLUTE_NEW_WORKSPACE" >&2
  exit 2
fi
workspace="$1"
if [[ -e "$workspace" ]]; then
  echo "Refusing existing destination (no overwrite): $workspace" >&2
  exit 3
fi
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
base_sha="c74acb09d51b447f5d5ac56c87608d3ec565a767"

git clone --filter=blob:none --no-checkout https://github.com/The412Banner/proton-wine.git "$workspace"
cd "$workspace"
git fetch --depth=1 origin "$base_sha"
git checkout --detach "$base_sha"
[[ "$(git rev-parse HEAD)" == "$base_sha" ]]
echo "CHAROITE_WINE_SOURCE_BASE=$base_sha"

# The pinned original ARM64EC build script specifies the exact order of Bionic,
# FEX, thread-suspension and GE prerequisite patches. Parse the literal entries;
# never execute its --configure / --install / cleanup branches.
python3 - "$workspace" <<'PY'
from pathlib import Path
import re
import sys
root=Path(sys.argv[1])
build=(root/"build-scripts/build-step-arm64ec.sh").read_text()
start=build.find("    PATCHES=(")
end=build.find("    for patch in \"${PATCHES[@]}\";", start)
if start<0 or end<=start:
    raise SystemExit("Upstream patch list changed; review before proceeding")
section=build[start:end]
patches=re.findall(r'^\s+"((?:common|arm64ec|test-bylaws)/[A-Za-z0-9_.-]+\.patch)"\s*$',section,re.M)
if len(patches)<55 or len(patches)>100 or len(set(patches))!=len(patches):
    raise SystemExit(f"Unexpected upstream patch count or duplicate: {len(patches)}")
for path in patches:
    if not (root/"android/patches"/path).is_file():
        raise SystemExit(f"Missing pinned prerequisite patch: {path}")
(root/"charoite-prerequisite-order.txt").write_text("\n".join(patches)+"\n")
print(f"Validating {len(patches)} pinned Android/Bionic/FEX prerequisite patches")
PY

count=0
while IFS= read -r rel; do
  [[ -n "$rel" ]] || continue
  patch="android/patches/$rel"
  if ! git apply --check "$patch"; then
    echo "Prerequisite patch does not apply: $rel" >&2
    exit 10
  fi
  git apply --whitespace=error "$patch"
  count=$((count+1))
done < charoite-prerequisite-order.txt
echo "CHAROITE_WINE_PREREQUISITES_APPLIED=$count"

# Upstream GE-Proton game-fixes tier follows Android patches, as documented by
# its own pinned build. Fail on rejected hunks and detect patch trash.
bash build-scripts/apply-ge-patches.sh
if find . -type f \( -name '*.rej' -o -name '*.orig' \) -print -quit | grep -q .; then
  echo "Refusing GE patch rejects/original backup files" >&2
  exit 11
fi

# Imported Charoite patches are applied only after the upstream prerequisites.
# Never use --3way, --reject or a force flag; report incompatible deltas instead.
count=0
while IFS= read -r rel; do
  [[ -n "$rel" && "$rel" != \#* ]] || continue
  [[ "$rel" =~ ^[0-9]{4}-[A-Za-z0-9-]+\.patch$ ]] || {
    echo "Invalid Charoite patch series entry" >&2; exit 12;
  }
  patch="$script_dir/patches/$rel"
  [[ -f "$patch" ]] || { echo "Missing Charoite patch in series: $rel" >&2; exit 12; }
  if ! git apply --check "$patch"; then
    echo "Charoite Wine source patch needs rebase: $rel" >&2
    exit 13
  fi
  git apply --whitespace=error "$patch"
  count=$((count+1))
done < "$script_dir/patches/SERIES"
[[ "$count" -eq 7 ]] || { echo "Unexpected active Charoite patch count: $count" >&2; exit 12; }
git diff --check
printf 'Charoite Wine imported patches applied: %s\n' "$count"
for symbol in 'syscall_dispatcher' 'RtlExitUserThread' 'security_unix_uid_to_sid'; do
  grep -R -F -q "$symbol" dlls/ntdll/thread.c dlls/ntdll/unix/signal_arm64.c server/token.c || {
    echo "Required source symbol missing: $symbol" >&2; exit 14;
  }
done
# Produce a provenance record, not an executable or another Wine installation.
{
  echo "Charoite Wine source base: $base_sha"
  echo "Android prerequisite patches: $(wc -l < charoite-prerequisite-order.txt)"
  echo "Charoite source patches: $count"
  echo "This is patched SOURCE; native executable/Android integration NOT VERIFIED."
  git diff --stat
} > charoite-source-validation.txt
git diff --binary > charoite-source-delta.patch
echo "SOURCE VALIDATED; binaries have NOT been built or installed."
