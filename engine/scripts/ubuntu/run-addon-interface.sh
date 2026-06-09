#!/usr/bin/env bash
# Addon end-to-end (E2E) runner: install a frontend addon into a HEADLESS gramps GUI
# and run the addon's own interface tests against it (AT-SPI + dogtail under Xvfb).
# This is the "E2E that includes gramps core" a frontend-interacting addon needs — it
# exercises the addon loaded *inside* a running gramps, not in isolation.
#
# Reuses the run-interface.sh stack (same Docker image, Xvfb/dbus/at-spi launch, the
# USER_PLUGINS install path, and the engine/interface/base.py dogtail harness). The
# difference: it installs the NAMED addon(s) and discovers tests from each addon's own
# `addons-source/<Addon>/tests/interface/test_*.py` (the addon-side convention; see
# docs/INTEGRATION.md §3), with the testbed's engine/ on PYTHONPATH so those tests can
# `from interface.base import AddonInterfaceTestCase`.
#
# Usage:
#   ./engine/scripts/ubuntu/run-addon-interface.sh QuiltView [CombinedView ...]
#   CORE_VERSION=6.0 ./engine/scripts/ubuntu/run-addon-interface.sh QuiltView   # matrix leg
#
# Like the other T3 runners it is ADVISORY (baseline-diffed by t3_baseline.py): an addon
# with no tests/interface/ contributes nothing, so a project with no frontend addon tests
# yet sees an empty (green) run.

set -euo pipefail

case "${1:-}" in
  -h | --help)
    awk 'NR==1{next} /^#/{sub(/^# ?/,""); print; next} {exit}' "$0"
    exit 0
    ;;
esac

_find_repo_root() {
  local d
  d="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  while [ "$d" != "/" ]; do
    if [ -f "$d/pdca.toml" ]; then printf '%s\n' "$d"; return 0; fi
    d="$(dirname "$d")"
  done
  echo "run-addon-interface.sh: could not locate pdca.toml above ${BASH_SOURCE[0]}" >&2
  return 1
}
REPO_ROOT="$(_find_repo_root)"
ENGINE="$REPO_ROOT/engine"
WORKSPACE="$(cd "$REPO_ROOT/.." && pwd)"
TESTBED_NAME="$(basename "$REPO_ROOT")"
cd "$WORKSPACE"

ADDONS=("$@")   # explicit names (C4 per-fix); empty ⇒ auto-discover (the repo-scoped gate)

# Which gramps + addons-source checkout to use. Bare run uses the primary siblings;
# CORE_VERSION selects the pinned per-version worktrees (the addon matrix), matching
# run-addon-unit.sh / run-verify.sh.
GRAMPS_DIR="$WORKSPACE/gramps"
ADDONS_DIR="$WORKSPACE/addons-source"
# In-driver lane concurrency (docs 09): $PDCA_LANE (set by the worker pool) scopes the
# per-version worktrees to this lane; unset (serial) → the shared gramps-6.x, unchanged.
LANE_SFX="${PDCA_LANE:+-lane$PDCA_LANE}"
if [ -n "${CORE_VERSION:-}" ]; then
  case "$CORE_VERSION" in
    6.0) GRAMPS_DIR="$WORKSPACE/gramps-6.0$LANE_SFX"; ADDONS_DIR="$WORKSPACE/addons-source-6.0$LANE_SFX" ;;
    6.1) GRAMPS_DIR="$WORKSPACE/gramps-6.1$LANE_SFX"; ADDONS_DIR="$WORKSPACE/addons-source-6.1$LANE_SFX" ;;
    *) echo "run-addon-interface.sh: unknown CORE_VERSION '$CORE_VERSION' (expected 6.0 or 6.1)" >&2; exit 2 ;;
  esac
fi
for d in "$GRAMPS_DIR" "$ADDONS_DIR"; do
  [ -d "$d" ] || { echo "run-addon-interface.sh: checkout $d missing — run 'make worktrees${LANE_SFX:+ LANES=N}'." >&2; exit 1; }
done

# No explicit addon(s) ⇒ auto-discover every addon that ships a tests/interface/ suite
# (the repo-scoped gate runs them all; an empty result is a green no-op).
if [ "${#ADDONS[@]}" -eq 0 ]; then
  while IFS= read -r d; do ADDONS+=("$(basename "$(dirname "$(dirname "$d")")")"); done \
    < <(find "$ADDONS_DIR" -mindepth 3 -maxdepth 3 -type d -path '*/tests/interface' 2>/dev/null | sort)
  if [ "${#ADDONS[@]}" -eq 0 ]; then
    echo "run-addon-interface.sh: no addon ships tests/interface/ in $ADDONS_DIR — nothing to run."
    exit 0
  fi
  echo "→ auto-discovered addon interface suites: ${ADDONS[*]}"
fi

GRAMPS_VERSION="$(sed -nE 's/^VERSION_TUPLE *= *\(([0-9]+), *([0-9]+), *([0-9]+)\).*$/\1.\2.\3/p' "$GRAMPS_DIR/gramps/version.py")"
: "${GRAMPS_VERSION:?could not detect Gramps version from $GRAMPS_DIR/gramps/version.py}"
IMAGE="${GRAMPS_TESTBED_IMAGE:-gramps-testbed:ubuntu-$GRAMPS_VERSION}"
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "→ building $IMAGE"
  docker build -f "$ENGINE/docker/Dockerfile.ubuntu" -t "$IMAGE" "$ENGINE"
fi

TIMEOUT="${GRAMPS_TEST_TIMEOUT:-1200}"
CNAME="grampstest-$$"
trap 'docker rm -f "$CNAME" >/dev/null 2>&1 || true' EXIT
rc=0
timeout --kill-after=30 "$TIMEOUT" docker run --rm --name "$CNAME" \
  -v "$GRAMPS_DIR":/workspace/gramps \
  -v "$ADDONS_DIR":/workspace/addons-source \
  -v "$REPO_ROOT":/workspace/"$TESTBED_NAME" \
  -w /workspace/gramps \
  -e TESTBED_NAME="$TESTBED_NAME" \
  -e ADDONS="${ADDONS[*]}" \
  "$IMAGE" \
  bash -c '
    set -e
    (cd /workspace && pip install --break-system-packages --user -e "./gramps[testing]")
    export PATH="$HOME/.local/bin:$PATH"
    if [ ! -f /workspace/gramps/build/mo/de/LC_MESSAGES/gramps.mo ]; then
      for po in /workspace/gramps/po/*.po; do
        lang=$(basename "$po" .po); dest="/workspace/gramps/build/mo/$lang/LC_MESSAGES"
        mkdir -p "$dest"; msgfmt "$po" -o "$dest/gramps.mo" 2>/dev/null || true
      done
    fi
    USER_PLUGINS="$(python3 -c "from gramps.gen.const import USER_PLUGINS; print(USER_PLUGINS)")"
    mkdir -p "$USER_PLUGINS"
    # Seed the canonical example tree; install each named addon + seed any fixture trees
    # it ships (tests/interface/data/<name>.gramps -> tree "<name>").
    gramps -C TestTree -i /workspace/gramps/example/gramps/example.gramps
    suites=()
    for addon in $ADDONS; do
      src="/workspace/addons-source/$addon"
      [ -d "$src" ] || { echo "WARN: addon source not found: $src"; continue; }
      rm -rf "$USER_PLUGINS/$addon"; cp -a "$src" "$USER_PLUGINS/$addon"
      echo "→ installed addon: $addon"
      tdir="$src/tests/interface"
      if [ -d "$tdir" ] && ls "$tdir"/test_*.py >/dev/null 2>&1; then
        for data in "$tdir"/data/*.gramps; do
          [ -e "$data" ] || continue
          gramps -C "$(basename "$data" .gramps)" -i "$data"
        done
        suites+=("$tdir")
      else
        echo "  (no tests/interface/ in $addon — nothing to run)"
      fi
    done
    rm -rf "/workspace/$TESTBED_NAME/test-results"; mkdir -p "/workspace/$TESTBED_NAME/test-results"
    export ARTIFACTS_DIR="/workspace/$TESTBED_NAME/artifacts"
    # engine/ on PYTHONPATH so addon tests resolve `from interface.base import ...`;
    # gi_bootstrap pins GI versions before any addon import (same as the unit runner).
    export PYTHONPATH="/workspace/$TESTBED_NAME/engine:/workspace/$TESTBED_NAME/engine/scripts/lib/gi_bootstrap${PYTHONPATH:+:$PYTHONPATH}"
    [ "${#suites[@]}" -gt 0 ] || { echo "no addon interface suites to run"; exit 0; }
    cd "/workspace/$TESTBED_NAME"
    xvfb-run -a --server-args="-screen 0 1920x1080x24" \
      dbus-run-session -- bash -c "
        gsettings set org.gnome.desktop.interface toolkit-accessibility true
        /usr/libexec/at-spi-bus-launcher --launch-immediately &
        sleep 2
        rcc=0
        for s in ${suites[*]}; do
          python3 -m xmlrunner discover -s \"\$s\" -t \"\$s\" -p \"test_*.py\" -o test-results/ -v || rcc=1
        done
        exit \$rcc
      "
  ' || rc=$?
if [ "$rc" = 124 ] || [ "$rc" = 137 ]; then
  echo "$(basename "$0"): run exceeded ${TIMEOUT}s — killed it (raise GRAMPS_TEST_TIMEOUT)." >&2
  docker kill "$CNAME" >/dev/null 2>&1 || true
fi
exit "$rc"
