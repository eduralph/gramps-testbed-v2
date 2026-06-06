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

# --- patch classification helpers (unit-tested by engine/tests/test_verify_classification.py) ---
# Files the patch ADDS: a `--- /dev/null` header line immediately precedes their
# `+++ b/<path>` (unified-diff headers come in adjacent pairs). A `git apply`
# leaves an added file UNTRACKED, so it must be `rm`-ed — not `git checkout`-ed —
# to revert it for the red pass, and cleaned from the checkout after the run.
_added_files() {
  awk '
    /^--- / { prev = $0; next }
    /^\+\+\+ b\// { p = $0; sub(/^\+\+\+ b\//, "", p); if (prev == "--- /dev/null") print p }
  ' "$1"
}
# Is $1 an element of the remaining args? (empty arg list -> not a member)
_in_list() { local x="$1"; shift; local e; for e in "$@"; do [ "$e" = "$x" ] && return 0; done; return 1; }
# --- end patch classification helpers ---

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
mapfile -t ADDED < <(_added_files "$PATCH")   # files the patch creates (test and/or prod)
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

# Split the production change for the red pass: a brand-new prod file must be
# REMOVED (it is untracked after `git apply`; `git checkout` would error and, under
# `set -e`, abort the whole revert), a modified prod file `git checkout`-ed.
PROD_MOD=()
PROD_NEW=()
for f in "${PROD[@]}"; do
  if _in_list "$f" "${ADDED[@]}"; then PROD_NEW+=("$f"); else PROD_MOD+=("$f"); fi
done

# What to verify against. A core fix runs ONCE against the primary gramps checkout.
# An addon fix runs the version MATRIX — each addons-source maintenance branch against
# its MATCHING core, in the pinned worktrees (`make worktrees`): a gramps60 fix is
# cherry-picked to gramps61, so the fix must hold red→green on BOTH cores. (Addon mode
# needs a display via xvfb so a @skipUnless(_HAS_GTK_DISPLAY) RUNS; core mode is plain.)
if [ "$MODE" = addon ]; then LEGS=(6.0 6.1); else LEGS=(core); fi
TIMEOUT="${GRAMPS_TEST_TIMEOUT:-900}"

# The container body — install core, apply the patch, assert green-with-fix then
# red-without-the-production-change. Identical per leg; the mounts/env/image differ.
read -r -d '' INNER <<'INNER_EOF' || true
    set -e
    cleanup() { git checkout -- . 2>/dev/null || true; }
    trap cleanup EXIT
    (cd /workspace && pip install --break-system-packages --user -e "./gramps[testing]" >/dev/null 2>&1)
    export PATH="$HOME/.local/bin:$PATH"

    git apply "$PATCH"
    echo "→ green check (fix applied):"
    if env $RUNENV $XVFB python3 -m unittest "$MODULE" 2>&1; then green=0; else green=1; fi

    echo "→ red check (production change reverted, test kept):"
    [ -n "$PROD_MOD" ] && git checkout -- $PROD_MOD   # revert modified prod files
    [ -n "$PROD_NEW" ] && rm -f -- $PROD_NEW           # remove prod files the patch added
    if env $RUNENV $XVFB python3 -m unittest "$MODULE" 2>&1; then red=0; else red=1; fi

    echo "C4-verify: green-with-fix=$([ $green -eq 0 ] && echo PASS || echo FAIL)" \
         "/ red-without-fix=$([ $red -ne 0 ] && echo PASS || echo FAIL)"
    [ "$green" -eq 0 ] && [ "$red" -ne 0 ]
INNER_EOF

# Restore every checkout we patch (revert tracked + remove patch-added files) even on
# interrupt, and kill any leg's container. Host-side git works on worktrees fine.
_TOUCHED=()
_restore_one() {  # $1 = repo dir
  git -C "$1" checkout -- . 2>/dev/null || true
  [ "${#ADDED[@]}" -gt 0 ] && (cd "$1" && rm -f -- "${ADDED[@]}") 2>/dev/null || true
}
_restore_all() {
  local r; for r in "${_TOUCHED[@]:-}"; do [ -n "$r" ] && _restore_one "$r"; done
  docker ps -aq --filter "name=grampstest-$$" | xargs -r docker rm -f >/dev/null 2>&1 || true
}
trap _restore_all EXIT

# Verify one leg; return 0 iff the red→green contract held. $1 = core | 6.0 | 6.1.
_verify_leg() {
  local leg="$1" gramps_dir repo cwd runenv xvfb image gv cname d gd label rc=0
  local mounts=()
  if [ "$leg" = core ]; then
    gramps_dir="$WORKSPACE/gramps"; repo="$WORKSPACE/gramps"; cwd=/workspace/gramps
    runenv="GRAMPS_RESOURCES=."; xvfb=""
    mounts=( -v "$WORKSPACE":/workspace )         # core mode unchanged: whole-workspace mount
  else
    gramps_dir="$WORKSPACE/gramps-$leg"; repo="$WORKSPACE/addons-source-$leg"
    cwd=/workspace/addons-source
    runenv="GRAMPS_RESOURCES=/workspace/gramps PYTHONPATH=/workspace/$TESTBED_NAME/engine/scripts/lib/gi_bootstrap"
    xvfb="xvfb-run -a"
    for d in "$gramps_dir" "$repo"; do
      [ -d "$d" ] || { echo "run-verify.sh: worktree $d missing — run 'make worktrees'." >&2; return 1; }
    done
    mounts=( -v "$gramps_dir":/workspace/gramps -v "$repo":/workspace/addons-source \
             -v "$REPO_ROOT":/workspace/"$TESTBED_NAME" )
    # A worktree's .git is a file pointing at the primary gitdir — bind-mount it so
    # in-container `git apply`/`checkout` resolve (a primary .git dir needs no mount).
    for d in "$gramps_dir" "$repo"; do
      if [ -f "$d/.git" ]; then gd="$(git -C "$d" rev-parse --path-format=absolute --git-common-dir)"; mounts+=( -v "$gd":"$gd" ); fi
    done
  fi
  [ -d "$repo/.git" ] || [ -f "$repo/.git" ] || { echo "run-verify.sh: no checkout at $repo" >&2; return 1; }
  git -C "$repo" diff --quiet || { echo "run-verify.sh: $repo has uncommitted changes — refusing to patch it" >&2; return 1; }
  _TOUCHED+=( "$repo" )

  gv="$(sed -nE 's/^VERSION_TUPLE *= *\(([0-9]+), *([0-9]+), *([0-9]+)\).*$/\1.\2.\3/p' "$gramps_dir/gramps/version.py")"
  : "${gv:?could not detect Gramps version from $gramps_dir}"
  image="${GRAMPS_TESTBED_IMAGE:-gramps-testbed:ubuntu-$gv}"
  if ! docker image inspect "$image" >/dev/null 2>&1; then
    echo "→ building $image"; docker build -f "$ENGINE/docker/Dockerfile.ubuntu" -t "$image" "$ENGINE"
  fi
  cname="grampstest-$$-$leg"
  label="$MODE"; [ "$leg" != core ] && label="$MODE, core $gv"
  echo "→ C4-verify ($label): $MODULE  (test: $TEST_REL ; reverting: ${PROD_MOD[*]:-—} ; removing: ${PROD_NEW[*]:-—})"
  timeout --kill-after=30 "$TIMEOUT" docker run --rm --name "$cname" \
    "${mounts[@]}" -w "$cwd" \
    -e PATCH="/workspace/${BUNDLE#"$WORKSPACE"/}/patch.diff" \
    -e MODULE="$MODULE" -e PROD_MOD="${PROD_MOD[*]}" -e PROD_NEW="${PROD_NEW[*]}" \
    -e RUNENV="$runenv" -e XVFB="$xvfb" \
    "$image" bash -c "$INNER" || rc=$?
  if [ "$rc" = 124 ] || [ "$rc" = 137 ]; then
    echo "$(basename "$0"): leg $leg exceeded ${TIMEOUT}s — killed it (raise GRAMPS_TEST_TIMEOUT)." >&2
    docker kill "$cname" >/dev/null 2>&1 || true
  fi
  _restore_one "$repo"   # leave this leg clean for the next (EXIT trap is the backstop)
  return "$rc"
}

overall=0
for leg in "${LEGS[@]}"; do
  _verify_leg "$leg" || overall=1
done
exit "$overall"
