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

# Tag the image with platform + Gramps version so multiple versions can
# coexist on the same machine (e.g. switching branches between 6.0.x and
# a future 6.1.x). Read VERSION_TUPLE from gramps' own source-of-truth.
GRAMPS_VERSION="$(sed -nE 's/^VERSION_TUPLE *= *\(([0-9]+), *([0-9]+), *([0-9]+)\).*$/\1.\2.\3/p' "$WORKSPACE/gramps/gramps/version.py")"
: "${GRAMPS_VERSION:?could not detect Gramps version from gramps/version.py}"
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
  -v "$WORKSPACE":/workspace \
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
