#!/usr/bin/env bash
# Run the GUI / interface test suite (engine/interface/test_*.py, driven via
# AT-SPI + dogtail) locally on the Ubuntu Docker base, using the same commands
# as CI. The suite runs HEADLESS — Xvfb provides the display, dbus-run-session
# the session bus, at-spi-bus-launcher the accessibility bridge — so no host
# display is required (unlike run-manual.sh, which forwards a live display).
#
# Ported from the gramps-testbed reference repo (agent-work/scripts/ubuntu/
# run-interface.sh) into this PDCA harness under engine/. The interface test
# suite itself was ported to engine/interface/ (self-contained: base.py + the
# test_*.py + data/ fixtures).
#
# Usage:
#   ./engine/scripts/ubuntu/run-interface.sh                 # whole suite
#   ./engine/scripts/ubuntu/run-interface.sh test_smoke.py   # one pattern (the
#                                                            # vertical-slice gate)
#
# NOTE: several tests in the suite are reproductions of UNMERGED upstream bugs
# (e.g. test_bug_0014100_* repros Mantis 14100, fix gramps#2322 not yet merged),
# so the full suite is NOT uniformly green on a clean checkout — it is an
# advisory baseline, like the unit/addon-unit runners. The smoke test
# (test_smoke.py) is the per-checkout health gate: if it is red, nothing else
# in the suite can pass.

set -euo pipefail

# -h / --help: print this script's header comment block and exit.
case "${1:-}" in
  -h | --help)
    awk 'NR==1{next} /^#/{sub(/^# ?/,""); print; next} {exit}' "$0"
    exit 0
    ;;
esac

# Repo root = nearest ancestor of this script containing pdca.toml (the driver's
# own convention, pdca_harness.config._find_root): depth-independent and
# git-independent. See engine/tests/test_root_resolution.py.
#   ENGINE        = the docker build context (holds docker/ + scripts/lib/)
#   WORKSPACE     = the repo's parent, holding the sibling gramps/ + addons-source/
#   TESTBED_NAME  = the repo dir name, for paths inside the mounted container
_find_repo_root() {
  local d
  d="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  while [ "$d" != "/" ]; do
    if [ -f "$d/pdca.toml" ]; then printf '%s\n' "$d"; return 0; fi
    d="$(dirname "$d")"
  done
  echo "run-interface.sh: could not locate pdca.toml above ${BASH_SOURCE[0]}" >&2
  return 1
}
REPO_ROOT="$(_find_repo_root)"
ENGINE="$REPO_ROOT/engine"
WORKSPACE="$(cd "$REPO_ROOT/.." && pwd)"
TESTBED_NAME="$(basename "$REPO_ROOT")"
cd "$WORKSPACE"

# Optional first arg: a unittest discovery -p pattern (default: all test_*.py).
PATTERN="${1:-test_*.py}"

# Which checkouts to test against. Default: the primary ../gramps + ../addons-source.
# With CORE_VERSION set (the T3-interface gate passes 6.1), the pinned, realigned
# per-version worktrees ../gramps-<ver> + ../addons-source-<ver> — the real
# contribution target, kept current by `make worktrees` / `make preflight` — so the
# baseline diff runs against a deterministic upstream tree, not the dev clone's
# branch. The smoke installs QuiltView/CombinedView from addons-source, so it needs
# the matching addon worktree too. $PDCA_LANE scopes to a lane copy. Mirrors
# run-addon-unit.sh.
GRAMPS_DIR="$WORKSPACE/gramps"
ADDONS_DIR="$WORKSPACE/addons-source"
LANE_SFX="${PDCA_LANE:+-lane$PDCA_LANE}"
if [ -n "${CORE_VERSION:-}" ]; then
  case "$CORE_VERSION" in
    6.0 | 6.1)
      GRAMPS_DIR="$WORKSPACE/gramps-$CORE_VERSION$LANE_SFX"
      ADDONS_DIR="$WORKSPACE/addons-source-$CORE_VERSION$LANE_SFX" ;;
    *) echo "$(basename "$0"): unknown CORE_VERSION '$CORE_VERSION' (expected 6.0 or 6.1)" >&2; exit 2 ;;
  esac
  for wt in "$GRAMPS_DIR" "$ADDONS_DIR"; do
    [ -d "$wt" ] || { echo "$(basename "$0"): worktree $wt is missing — run 'make worktrees${LANE_SFX:+ LANES=N}'." >&2; exit 1; }
  done
fi

# A git worktree's `.git` is a FILE pointing at the primary repo's gitdir, which does
# not resolve inside the container; bind-mount that gitdir at its own absolute path so
# the git-aware editable pip build works (mirrors run-addon-unit.sh).
GIT_MOUNTS=()
for dir in "$GRAMPS_DIR" "$ADDONS_DIR"; do
  if [ -f "$dir/.git" ]; then
    gd="$(git -C "$dir" rev-parse --path-format=absolute --git-common-dir)"
    GIT_MOUNTS+=( -v "$gd":"$gd" )
  fi
done

# Tag the image with platform + Gramps version (read from gramps' source of
# truth) so multiple versions coexist on one machine.
GRAMPS_VERSION="$(sed -nE 's/^VERSION_TUPLE *= *\(([0-9]+), *([0-9]+), *([0-9]+)\).*$/\1.\2.\3/p' "$GRAMPS_DIR/gramps/version.py")"
: "${GRAMPS_VERSION:?could not detect Gramps version from $GRAMPS_DIR/gramps/version.py}"
IMAGE="${GRAMPS_TESTBED_IMAGE:-gramps-testbed:ubuntu-$GRAMPS_VERSION}"

if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "→ building $IMAGE"
  docker build -f "$ENGINE/docker/Dockerfile.ubuntu" -t "$IMAGE" "$ENGINE"
fi

# A hung test must FAIL the run, not block the cycle forever (the no-timeout gap that
# let a GUI-import test hang the batch flow). Tunable via GRAMPS_TEST_TIMEOUT (seconds).
TIMEOUT="${GRAMPS_TEST_TIMEOUT:-1200}"
CNAME="grampstest-$$"
trap 'docker rm -f "$CNAME" >/dev/null 2>&1 || true' EXIT
rc=0
timeout --kill-after=30 "$TIMEOUT" docker run --rm --name "$CNAME" \
  -v "$GRAMPS_DIR":/workspace/gramps \
  -v "$ADDONS_DIR":/workspace/addons-source \
  -v "$REPO_ROOT":/workspace/"$TESTBED_NAME" \
  "${GIT_MOUNTS[@]}" \
  -w "/workspace/$TESTBED_NAME" \
  -e TESTBED_NAME="$TESTBED_NAME" \
  -e PATTERN="$PATTERN" \
  "$IMAGE" \
  bash -c '
    set -e
    # Extras syntax rejects absolute paths — resolve via a relative path.
    (cd /workspace && pip install --break-system-packages --user -e "./gramps[testing]")
    export PATH="$HOME/.local/bin:$PATH"
    # Compile .mo translations into gramps/build/mo (gitignored in the fork).
    # pip install -e skips setup.py build, so without this Gramps logs
    # "Missing or invalid localedir" on every launch and UI strings never get
    # translated. Idempotent — a single malformed .po is warned and skipped
    # (cosmetic; not what the interface suite tests).
    if [ ! -f /workspace/gramps/build/mo/de/LC_MESSAGES/gramps.mo ]; then
      echo "→ compiling translations"
      for po in /workspace/gramps/po/*.po; do
        lang=$(basename "$po" .po)
        dest="/workspace/gramps/build/mo/$lang/LC_MESSAGES"
        mkdir -p "$dest"
        msgfmt "$po" -o "$dest/gramps.mo" 2>/dev/null \
          || echo "  warn: skipping malformed translation $lang.po (cosmetic; not under test)"
      done
    fi
    # Install ONLY the addons the bundled interface tests need, by copying the
    # source straight into USER_PLUGINS — no make.py (it mutates tracked
    # .gpr.py version fields and would dirty the addons-source mirror), and no
    # bulk install (149 addons blocks GUI startup during registration).
    USER_PLUGINS="$(python3 -c "from gramps.gen.const import USER_PLUGINS; print(USER_PLUGINS)")"
    mkdir -p "$USER_PLUGINS"
    for addon in QuiltView CombinedView; do
      src="/workspace/addons-source/$addon"
      if [ -d "$src" ]; then
        rm -rf "$USER_PLUGINS/$addon"
        cp -a "$src" "$USER_PLUGINS/$addon"
        echo "→ installed addon: $addon"
      else
        echo "WARN: addon source not found: $src (skipping install)"
      fi
    done
    # Seed the trees the suite opens (TestTree = the canonical example fixture;
    # the two minimal trees back the QuiltView / bug-14100 tests).
    gramps -C TestTree -i /workspace/gramps/example/gramps/example.gramps
    gramps -C QuiltViewTree \
           -i "/workspace/$TESTBED_NAME/engine/interface/data/quiltview_minimal.gramps"
    gramps -C Bug14100Tree \
           -i "/workspace/$TESTBED_NAME/engine/interface/data/bug_0014100_minimal.gramps"
    # Clear stale XMLs so accumulated runs do not pollute JUnit summaries.
    rm -rf "/workspace/$TESTBED_NAME/test-results"
    mkdir -p "/workspace/$TESTBED_NAME/test-results"
    export ARTIFACTS_DIR="/workspace/$TESTBED_NAME/artifacts"
    # Run the interface suite under Xvfb + dbus + AT-SPI. Discovery treats
    # engine/ as the top-level dir, so the package is "interface" and the
    # tests'\'' "from .base import ..." resolves (engine/ has no __init__.py).
    cd "/workspace/$TESTBED_NAME"
    xvfb-run -a --server-args="-screen 0 1920x1080x24" \
      dbus-run-session -- bash -c "
        gsettings set org.gnome.desktop.interface toolkit-accessibility true
        /usr/libexec/at-spi-bus-launcher --launch-immediately &
        sleep 2
        python3 -m xmlrunner discover -s engine/interface -t engine \
          -p \"$PATTERN\" -o test-results/ -v
      "
  ' || rc=$?
if [ "$rc" = 124 ] || [ "$rc" = 137 ]; then
  echo "$(basename "$0"): test run exceeded ${TIMEOUT}s — killed it (raise GRAMPS_TEST_TIMEOUT for longer runs)." >&2
  docker kill "$CNAME" >/dev/null 2>&1 || true
fi
exit "$rc"
