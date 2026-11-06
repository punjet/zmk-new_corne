#!/usr/bin/env bash
# Flash one half of the Eyelash Corne with a firmware build from GitHub Actions.
#
#   scripts/flash.sh left            # newest successful build of mac-aerospace
#   scripts/flash.sh left 75e3add    # build of a specific commit (rollback)
#   scripts/flash.sh right
#   scripts/flash.sh reset           # settings_reset: wipes BLE pairings, re-pair afterwards
#
# Needs the GitHub CLI (gh) logged in. Builds are cached in ~/.cache/corne-firmware/<sha>.
set -euo pipefail

REPO="punjet/zmk-new_corne"
BRANCH="mac-aerospace"
WORKFLOW="Build ZMK firmware"
VOLUME="/Volumes/NICENANO"
CACHE="${HOME}/.cache/corne-firmware"

side="${1:-}"
ref="${2:-}"
case "$side" in
  left)  file="eyelash_corne_studio_left.uf2" ;;
  right) file="eyelash_corne_right nice_view_doom-nice_nano_v2-zmk.uf2" ;;
  reset) file="settings_reset-nice_nano_v2-zmk.uf2" ;;
  *) sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 1 ;;
esac

runs=$(gh run list -R "$REPO" --branch "$BRANCH" --workflow "$WORKFLOW" -L 50 \
  --json databaseId,headSha,conclusion \
  -q '.[] | select(.conclusion=="success") | "\(.databaseId) \(.headSha)"')
if [ -n "$ref" ]; then
  line=$(printf '%s\n' "$runs" | awk -v r="$ref" 'index($2, r) == 1 {print; exit}')
else
  line=$(printf '%s\n' "$runs" | head -n 1)
fi
[ -n "$line" ] || { echo "No successful build found for '${ref:-latest}' on $BRANCH."; exit 1; }
run_id=${line%% *}
sha=${line#* }
short=${sha:0:7}

dir="$CACHE/$short"
if [ ! -f "$dir/firmware/$file" ]; then
  echo "Downloading build $short (run $run_id)..."
  rm -rf "$dir"; mkdir -p "$dir"
  gh run download "$run_id" -R "$REPO" -D "$dir"
fi
src="$dir/firmware/$file"
[ -f "$src" ] || { echo "Missing $file in build $short."; exit 1; }

echo "Firmware: $short -> $side"
if [ ! -d "$VOLUME" ]; then
  echo "Connect the $side half by USB and double-tap its reset button..."
  for _ in $(seq 1 120); do [ -d "$VOLUME" ] && break; sleep 1; done
  [ -d "$VOLUME" ] || { echo "NICENANO did not appear within 2 minutes."; exit 1; }
fi

# The board reboots as soon as the file is written, so cp often reports
# "Device not configured" / "fchmod failed". That is harmless.
cp -X "$src" "$VOLUME/" 2>/dev/null || true

for _ in $(seq 1 10); do [ -d "$VOLUME" ] || break; sleep 1; done
if [ -d "$VOLUME" ]; then
  echo "NICENANO is still mounted: the firmware was probably not accepted. Try again."
  exit 1
fi
echo "Done: the $side half rebooted with $short."
