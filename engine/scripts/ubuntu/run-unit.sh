#!/usr/bin/env bash
# Run gramps' own unit test suite (*_test.py under gramps/**/test/) locally
# on the Ubuntu Docker base, using the same commands as CI. No display,
# no dbus, no AT-SPI — unit tests construct in-memory fixtures only.
#
# Ported from the gramps-testbed reference repo (agent-work/scripts/ubuntu/)
# into this PDCA harness under engine/. Companion runners (addon-unit,
# interface, manual) and other platforms land under engine/scripts/<platform>/
# as those slices are wired.

set -euo pipefail

# -h / --help: print this script's header comment block and exit.
case "${1:-}" in
  -h | --help)
    awk 'NR==1{next} /^#/{sub(/^# ?/,""); print; next} {exit}' "$0"
    exit 0
    ;;
esac

# Repo root = nearest ancestor of this script containing pdca.toml. This matches
# the driver's own root convention (pdca_harness.config._find_root): it is
# depth-independent (NOT a fragile fixed-depth ../.. walk — see the reference
# repo's test_runner_workspace_root.py for why that breaks on directory moves)
# and git-independent (this harness instance need not be a git repo; the
# reference repo, which was always git, used `git rev-parse --show-toplevel`).
#   ENGINE        = the docker build context (holds docker/ + scripts/lib/)
#   WORKSPACE     = the repo's parent, holding the sibling gramps/ checkout
#   TESTBED_NAME  = the repo dir name, for paths inside the mounted container
_find_repo_root() {
  local d
  d="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  while [ "$d" != "/" ]; do
    if [ -f "$d/pdca.toml" ]; then printf '%s\n' "$d"; return 0; fi
    d="$(dirname "$d")"
  done
  echo "run-unit.sh: could not locate pdca.toml above ${BASH_SOURCE[0]}" >&2
  return 1
}
REPO_ROOT="$(_find_repo_root)"
ENGINE="$REPO_ROOT/engine"
WORKSPACE="$(cd "$REPO_ROOT/.." && pwd)"
TESTBED_NAME="$(basename "$REPO_ROOT")"
cd "$WORKSPACE"

# Which gramps checkout to test. Default: the primary ../gramps. With CORE_VERSION
# set (the T3-unit gate passes 6.1), the pinned, realigned per-version worktree
# ../gramps-<ver> — the real contribution target, kept current by `make worktrees`
# / `make preflight` — so the baseline diff runs against a deterministic upstream
# tree, not whatever branch the dev clone happens to be on. $PDCA_LANE scopes to a
# lane copy under the worker pool. Mirrors run-addon-unit.sh.
GRAMPS_DIR="$WORKSPACE/gramps"
LANE_SFX="${PDCA_LANE:+-lane$PDCA_LANE}"
if [ -n "${CORE_VERSION:-}" ]; then
  case "$CORE_VERSION" in
    6.0 | 6.1) GRAMPS_DIR="$WORKSPACE/gramps-$CORE_VERSION$LANE_SFX" ;;
    *) echo "$(basename "$0"): unknown CORE_VERSION '$CORE_VERSION' (expected 6.0 or 6.1)" >&2; exit 2 ;;
  esac
  [ -d "$GRAMPS_DIR" ] || { echo "$(basename "$0"): worktree $GRAMPS_DIR is missing — run 'make worktrees${LANE_SFX:+ LANES=N}'." >&2; exit 1; }
fi

# A git worktree's `.git` is a FILE pointing at the primary repo's gitdir, which does
# not resolve inside the container; bind-mount that gitdir at its own absolute path so
# the git-aware editable pip build works (mirrors run-addon-unit.sh).
GIT_MOUNTS=()
if [ -f "$GRAMPS_DIR/.git" ]; then
  gd="$(git -C "$GRAMPS_DIR" rev-parse --path-format=absolute --git-common-dir)"
  GIT_MOUNTS+=( -v "$gd":"$gd" )
fi

# Tag the image with platform + Gramps version so multiple versions can
# coexist on the same machine (e.g. switching branches between 6.0.x and
# a future 6.1.x). Read VERSION_TUPLE from gramps' own source-of-truth.
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
  -v "$REPO_ROOT":/workspace/"$TESTBED_NAME" \
  "${GIT_MOUNTS[@]}" \
  -w /workspace/gramps \
  -e TESTBED_NAME="$TESTBED_NAME" \
  "$IMAGE" \
  bash -c '
    set -e
    # [testing] extras pulls in jsonschema/mock/lxml from gramps setup.py,
    # which some of the upstream *_test.py files import. pip rejects the
    # extras syntax against absolute paths, so resolve via a relative path.
    (cd /workspace && pip install --break-system-packages --user -e "./gramps[testing]")
    export PATH="$HOME/.local/bin:$PATH"
    # Compile .mo translations so gramps.gen imports do not emit
    # "Missing or invalid localedir" warnings during collection. This is a
    # cosmetic prerequisite — the .mo catalogs are NOT what the unit suite
    # tests — so a single malformed .po (e.g. a plural-form newline mismatch in
    # an upstream translation) must not abort the run. Per-file failures are
    # warned and skipped rather than killing the script under `set -e`. (This
    # differs from the reference runner, which let msgfmt be fatal and so
    # could not get past a broken translation in the checked-out gramps tree.)
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
    # Mirrors the canonical command from ../gramps/AGENTS.md:
    #   GRAMPS_RESOURCES=. python3 -m unittest discover -p "*_test.py"
    # We swap unittest for xmlrunner (drop-in replacement) so CI gets
    # JUnit XML for reporting. GRAMPS_RESOURCES=. is load-bearing —
    # without it, several plugin tests fail to locate resource files.
    # $TESTBED_NAME comes from the container env (-e above); test-results
    # lands under the mounted repo. Clear stale XMLs first.
    rm -rf "/workspace/$TESTBED_NAME/test-results"
    mkdir -p "/workspace/$TESTBED_NAME/test-results"
    cd /workspace/gramps
    GRAMPS_RESOURCES=. python3 -m xmlrunner discover \
      -p "*_test.py" \
      -o "/workspace/$TESTBED_NAME/test-results/" \
      -v
  ' || rc=$?
if [ "$rc" = 124 ] || [ "$rc" = 137 ]; then
  echo "$(basename "$0"): test run exceeded ${TIMEOUT}s — killed it (raise GRAMPS_TEST_TIMEOUT for longer runs)." >&2
  docker kill "$CNAME" >/dev/null 2>&1 || true
fi
exit "$rc"
