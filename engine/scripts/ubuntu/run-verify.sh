#!/usr/bin/env bash
# C4-verify (bundle-scoped): prove the bundle's patch is a real fix.
#
# Unlike the T3-unit gate (which runs the WHOLE gramps suite on an UNMODIFIED
# tree — so it is red on any pre-existing failure and never sees this change),
# this gate APPLIES the bundle's patch.diff to the gramps checkout and runs ONLY
# the test the patch ships, asserting the regression contract:
#   * GREEN with the fix applied, and
#   * RED with the production change reverted (test kept) — i.e. the test really
#     catches the bug the fix resolves.
# Passes iff green-with-fix AND red-without-fix.
#
# Bundle-scoped: the driver exports $PDCA_BUNDLE (the absolute bundle dir) for
# this check. Runs in the same Docker image as run-unit.sh.

set -euo pipefail

# -h / --help: print this script's header comment block and exit.
case "${1:-}" in
  -h | --help)
    awk 'NR==1{next} /^#/{sub(/^# ?/,""); print; next} {exit}' "$0"
    exit 0
    ;;
esac

# Repo root via the pdca.toml marker (depth- and git-independent; matches
# pdca_harness.config._find_root and the other engine runners).
_find_repo_root() {
  local d
  d="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  while [ "$d" != "/" ]; do
    if [ -f "$d/pdca.toml" ]; then printf '%s\n' "$d"; return 0; fi
    d="$(dirname "$d")"
  done
  echo "run-verify.sh: could not locate pdca.toml above ${BASH_SOURCE[0]}" >&2
  return 1
}
REPO_ROOT="$(_find_repo_root)"
ENGINE="$REPO_ROOT/engine"
WORKSPACE="$(cd "$REPO_ROOT/.." && pwd)"
TESTBED_NAME="$(basename "$REPO_ROOT")"
cd "$WORKSPACE"

BUNDLE="${PDCA_BUNDLE:?run-verify.sh is bundle-scoped — \$PDCA_BUNDLE must be set}"
PATCH="$BUNDLE/patch.diff"
[ -f "$PATCH" ] || { echo "run-verify.sh: no patch.diff in $BUNDLE" >&2; exit 1; }

# Detect the target from the brief: an addons-source fix verifies differently from a
# gramps-core fix — different checkout, test-name convention, and run env. Default core.
MODE=core
if grep -iqE 'repo \+ branch( target)?:.*addons-source' "$BUNDLE/brief.md" 2>/dev/null; then
  MODE=addon
fi

# Classify the patched files; the rest is the production change reverted for the red
# check. Core tests use the *_test.py SUFFIX (gramps/**/test/); addon tests use the
# test_*.py PREFIX (addons-source/<Addon>/tests/) — see INTEGRATION.md §3.
mapfile -t FILES < <(grep -E '^\+\+\+ b/' "$PATCH" | sed -E 's|^\+\+\+ b/||')
TEST_REL=""
PROD=()
for f in "${FILES[@]}"; do
  base="$(basename "$f")"
  if { [ "$MODE" = addon ] && [[ "$base" == test_*.py ]]; } \
     || { [ "$MODE" = core ] && [[ "$base" == *_test.py ]]; }; then
    TEST_REL="$f"
  else
    PROD+=("$f")
  fi
done
want_test=$([ "$MODE" = addon ] && echo 'test_*.py' || echo '*_test.py')
[ -n "$TEST_REL" ] || { echo "run-verify.sh: patch ships no $MODE test ($want_test) to verify" >&2; exit 1; }
[ "${#PROD[@]}" -gt 0 ] || { echo "run-verify.sh: patch has no production change to revert" >&2; exit 1; }
MODULE="$(printf '%s' "${TEST_REL%.py}" | tr '/' '.')"   # core: gramps.gui.test.x_test ; addon: Addon.tests.test_x

# Per-mode: which checkout we patch, the container cwd, and the run env. Addon tests
# need a display (xvfb) so a @skipUnless(_HAS_GTK_DISPLAY) actually RUNS instead of
# skipping, plus GRAMPS_RESOURCES + the gi_bootstrap shim (mirrors run-addon-unit.sh).
if [ "$MODE" = addon ]; then
  REPO="$WORKSPACE/addons-source"
  CWD=/workspace/addons-source
  RUNENV="GRAMPS_RESOURCES=/workspace/gramps PYTHONPATH=/workspace/$TESTBED_NAME/engine/scripts/lib/gi_bootstrap"
  XVFB="xvfb-run -a"
else
  REPO="$WORKSPACE/gramps"
  CWD=/workspace/gramps
  RUNENV="GRAMPS_RESOURCES=."
  XVFB=""
fi

[ -d "$REPO/.git" ] || { echo "run-verify.sh: no $MODE checkout at $REPO" >&2; exit 1; }
git -C "$REPO" diff --quiet || {
  echo "run-verify.sh: $REPO has uncommitted changes — refusing to patch it" >&2; exit 1; }
# Always restore the checkout, even if interrupted; and kill a hung container so a
# test can't block the cycle forever. Tunable via GRAMPS_TEST_TIMEOUT (seconds).
TIMEOUT="${GRAMPS_TEST_TIMEOUT:-900}"
CNAME="grampstest-$$"
trap 'git -C "$REPO" checkout -- . 2>/dev/null || true; docker rm -f "$CNAME" 2>/dev/null || true' EXIT

# The image tag tracks the gramps checkout's version regardless of mode (same base).
GRAMPS_VERSION="$(sed -nE 's/^VERSION_TUPLE *= *\(([0-9]+), *([0-9]+), *([0-9]+)\).*$/\1.\2.\3/p' "$WORKSPACE/gramps/gramps/version.py")"
: "${GRAMPS_VERSION:?could not detect Gramps version}"
IMAGE="${GRAMPS_TESTBED_IMAGE:-gramps-testbed:ubuntu-$GRAMPS_VERSION}"
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "→ building $IMAGE"
  docker build -f "$ENGINE/docker/Dockerfile.ubuntu" -t "$IMAGE" "$ENGINE"
fi

echo "→ C4-verify ($MODE): $MODULE  (test: $TEST_REL ; reverting: ${PROD[*]})"
rc=0
timeout --kill-after=30 "$TIMEOUT" docker run --rm --name "$CNAME" \
  -v "$WORKSPACE":/workspace \
  -w "$CWD" \
  -e PATCH="/workspace/${BUNDLE#"$WORKSPACE"/}/patch.diff" \
  -e MODULE="$MODULE" \
  -e PROD="${PROD[*]}" \
  -e RUNENV="$RUNENV" \
  -e XVFB="$XVFB" \
  "$IMAGE" \
  bash -c '
    set -e
    cleanup() { git checkout -- . 2>/dev/null || true; }
    trap cleanup EXIT
    (cd /workspace && pip install --break-system-packages --user -e "./gramps[testing]" >/dev/null 2>&1)
    export PATH="$HOME/.local/bin:$PATH"

    git apply "$PATCH"
    echo "→ green check (fix applied):"
    if env $RUNENV $XVFB python3 -m unittest "$MODULE" 2>&1; then green=0; else green=1; fi

    echo "→ red check (production change reverted, test kept):"
    git checkout -- $PROD
    if env $RUNENV $XVFB python3 -m unittest "$MODULE" 2>&1; then red=0; else red=1; fi

    echo "C4-verify: green-with-fix=$([ $green -eq 0 ] && echo PASS || echo FAIL)" \
         "/ red-without-fix=$([ $red -ne 0 ] && echo PASS || echo FAIL)"
    [ "$green" -eq 0 ] && [ "$red" -ne 0 ]
  ' || rc=$?
if [ "$rc" = 124 ] || [ "$rc" = 137 ]; then
  echo "$(basename "$0"): test run exceeded ${TIMEOUT}s — killed it (raise GRAMPS_TEST_TIMEOUT for longer runs)." >&2
  docker kill "$CNAME" >/dev/null 2>&1 || true
fi
exit "$rc"
