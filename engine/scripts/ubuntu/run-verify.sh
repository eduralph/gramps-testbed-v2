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
cd "$WORKSPACE"

BUNDLE="${PDCA_BUNDLE:?run-verify.sh is bundle-scoped — \$PDCA_BUNDLE must be set}"
PATCH="$BUNDLE/patch.diff"
[ -f "$PATCH" ] || { echo "run-verify.sh: no patch.diff in $BUNDLE" >&2; exit 1; }

# Classify the files the patch touches: the *_test.py is the test; the rest are
# the production change reverted for the red check.
mapfile -t FILES < <(grep -E '^\+\+\+ b/' "$PATCH" | sed -E 's|^\+\+\+ b/||')
TEST_REL=""
PROD=()
for f in "${FILES[@]}"; do
  case "$f" in
    *_test.py) TEST_REL="$f" ;;
    *)         PROD+=("$f") ;;
  esac
done
[ -n "$TEST_REL" ] || { echo "run-verify.sh: patch ships no *_test.py to verify" >&2; exit 1; }
[ "${#PROD[@]}" -gt 0 ] || { echo "run-verify.sh: patch has no production change to revert" >&2; exit 1; }
MODULE="$(printf '%s' "${TEST_REL%.py}" | tr '/' '.')"   # gramps/gui/test/x_test.py → gramps.gui.test.x_test

GRAMPS="$WORKSPACE/gramps"
[ -d "$GRAMPS/.git" ] || { echo "run-verify.sh: no gramps checkout at $GRAMPS" >&2; exit 1; }
git -C "$GRAMPS" diff --quiet || {
  echo "run-verify.sh: gramps checkout has uncommitted changes — refusing to patch it" >&2; exit 1; }
# Always restore the checkout, even if the container is interrupted.
trap 'git -C "$GRAMPS" checkout -- . 2>/dev/null || true' EXIT

GRAMPS_VERSION="$(sed -nE 's/^VERSION_TUPLE *= *\(([0-9]+), *([0-9]+), *([0-9]+)\).*$/\1.\2.\3/p' "$GRAMPS/gramps/version.py")"
: "${GRAMPS_VERSION:?could not detect Gramps version}"
IMAGE="${GRAMPS_TESTBED_IMAGE:-gramps-testbed:ubuntu-$GRAMPS_VERSION}"
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "→ building $IMAGE"
  docker build -f "$ENGINE/docker/Dockerfile.ubuntu" -t "$IMAGE" "$ENGINE"
fi

echo "→ C4-verify: $MODULE  (test: $TEST_REL ; reverting: ${PROD[*]})"
docker run --rm \
  -v "$WORKSPACE":/workspace \
  -w /workspace/gramps \
  -e PATCH="/workspace/${BUNDLE#"$WORKSPACE"/}/patch.diff" \
  -e MODULE="$MODULE" \
  -e PROD="${PROD[*]}" \
  "$IMAGE" \
  bash -c '
    set -e
    cleanup() { git checkout -- . 2>/dev/null || true; }
    trap cleanup EXIT
    (cd /workspace && pip install --break-system-packages --user -e "./gramps[testing]" >/dev/null 2>&1)
    export PATH="$HOME/.local/bin:$PATH"

    git apply "$PATCH"
    echo "→ green check (fix applied):"
    if GRAMPS_RESOURCES=. python3 -m unittest "$MODULE" 2>&1; then green=0; else green=1; fi

    echo "→ red check (production change reverted, test kept):"
    git checkout -- $PROD
    if GRAMPS_RESOURCES=. python3 -m unittest "$MODULE" 2>&1; then red=0; else red=1; fi

    echo "C4-verify: green-with-fix=$([ $green -eq 0 ] && echo PASS || echo FAIL)" \
         "/ red-without-fix=$([ $red -ne 0 ] && echo PASS || echo FAIL)"
    [ "$green" -eq 0 ] && [ "$red" -ne 0 ]
  '
