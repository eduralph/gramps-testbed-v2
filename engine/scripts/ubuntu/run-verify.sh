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

# In-driver lane concurrency (docs 09): when the driver runs a worker pool it pins each
# worker to a slot and exposes it as $PDCA_LANE, so a lane patches its OWN per-version
# worktree (gramps-6.1-lane0) instead of the shared one. Unset (serial driver) → empty
# suffix → the bare gramps-6.1 worktrees, exactly as before. `make worktrees LANES=N`
# creates the lane copies.
LANE_SFX="${PDCA_LANE:+-lane$PDCA_LANE}"

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

# Core target version → which UPSTREAM worktree to verify against (gramps-6.0 / gramps-6.1).
# Default validation is against clean upstream/maintenance/gramps<ver> (the contribution
# target), NOT the developer's working clone. Addon mode runs both versions as a matrix.
TARGET_VER=6.1
if grep -iqE 'repo \+ branch( target)?:.*(gramps60|maintenance/gramps60)' "$BUNDLE/brief.md" 2>/dev/null; then
  TARGET_VER=6.0
fi

# --- fork base selection (issue #96) ---
# An addon fix whose change lives on a FORK's open PR branch (e.g. .github/ CI infra the
# clean upstream base does not carry, so the patch can't even apply there) declares a
# `- **Verification base:** <remote>/<branch>` field. With it set, FORK_REF drives the
# matrix to verify the single TARGET_VER leg against the DEDICATED addons-source-<ver>-fork
# worktree `make fork-worktrees` built at that branch; empty ⇒ today's full clean matrix
# against the shared per-version worktrees, unchanged. Self-contained so the unit test can
# source + evaluate it without Docker (reads MODE/TARGET_VER/FORK_REF/WORKSPACE/LANE_SFX).
_parse_fork_ref() {  # $1 = brief.md path → echo the <remote>/<branch> from the Verification base field (empty if none)
  grep -iE 'verification base:' "$1" 2>/dev/null | head -1 \
    | sed -E 's/.*[Vv]erification [Bb]ase:[[:space:]]*//; s/[*`]//g; s/^[[:space:]]+//; s/[[:space:]].*//'
}
_fork_legs() {  # echo the version legs to verify, space-separated
  if [ -n "${FORK_REF:-}" ]; then echo "$TARGET_VER"
  elif [ "$MODE" = addon ]; then echo "6.0 6.1"
  else echo "$TARGET_VER"; fi
}
_addon_repo() {  # $1 = version leg → the addons-source worktree to patch for that leg
  if [ -n "${FORK_REF:-}" ]; then echo "$WORKSPACE/addons-source-$1-fork$LANE_SFX"
  else echo "$WORKSPACE/addons-source-$1$LANE_SFX"; fi
}
# --- end fork base selection ---

# A fork base applies to addon fixes only (the field formalises the #820 series' prose).
FORK_REF=""
[ "$MODE" = addon ] && FORK_REF="$(_parse_fork_ref "$BUNDLE/brief.md")"

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

# What to verify against. A core fix runs ONCE against its target-version UPSTREAM
# worktree (gramps-6.0 / gramps-6.1 from `make worktrees`). An addon fix runs the
# version MATRIX — each addons-source maintenance branch against its MATCHING core,
# in the pinned worktrees: a gramps60 fix is cherry-picked to gramps61, so the fix must
# hold red→green on BOTH cores. (Addon mode needs a display via xvfb so a
# @skipUnless(_HAS_GTK_DISPLAY) RUNS; core mode is plain.)
read -ra LEGS <<< "$(_fork_legs)"
[ -n "$FORK_REF" ] && echo "→ fork verification base: $FORK_REF → addons-source-$TARGET_VER-fork (single leg $TARGET_VER)"
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
  # Scrub run-created untracked residue (e.g. test-dir __init__.py the runner leaves)
  # so the next leg/run starts pristine — these are throwaway upstream worktrees, and
  # leftover residue can otherwise flip a result. (-fd, not -x: keep ignored caches.)
  git -C "$1" clean -fdq 2>/dev/null || true
}
_restore_all() {
  local r; for r in "${_TOUCHED[@]:-}"; do [ -n "$r" ] && _restore_one "$r"; done
  docker ps -aq --filter "name=grampstest-$$" | xargs -r docker rm -f >/dev/null 2>&1 || true
}
trap _restore_all EXIT

# Verify one leg; return 0 iff the red→green contract held. $1 = version (6.0|6.1).
# $2 (optional, core only) = an explicit gramps checkout to verify against — used to
# retry on the *essential* worktree after the upstream leg fails.
_verify_leg() {
  local leg="$1" gramps_override="${2:-}" gramps_dir repo cwd runenv xvfb image gv cname d gd label rc=0
  local mounts=()
  if [ "$MODE" = core ]; then
    # Default: the target-version UPSTREAM worktree (the contribution target), NOT the
    # developer's working clone. Overridable to the essential worktree for the retry.
    gramps_dir="${gramps_override:-$WORKSPACE/gramps-$leg$LANE_SFX}"; repo="$gramps_dir"; cwd=/workspace/gramps
    runenv="GRAMPS_RESOURCES=."; xvfb=""
    [ -d "$gramps_dir" ] || { echo "run-verify.sh: core worktree $gramps_dir missing — run 'make worktrees${LANE_SFX:+ LANES=N}'." >&2; return 1; }
    mounts=( -v "$gramps_dir":/workspace/gramps -v "$REPO_ROOT":/workspace/"$TESTBED_NAME" )
    # A worktree's .git is a file pointing at the primary gitdir — bind-mount it so
    # in-container `git apply`/`checkout` resolve.
    if [ -f "$gramps_dir/.git" ]; then gd="$(git -C "$gramps_dir" rev-parse --path-format=absolute --git-common-dir)"; mounts+=( -v "$gd":"$gd" ); fi
  else
    gramps_dir="$WORKSPACE/gramps-$leg$LANE_SFX"; repo="$(_addon_repo "$leg")"
    cwd=/workspace/addons-source
    runenv="GRAMPS_RESOURCES=/workspace/gramps PYTHONPATH=/workspace/$TESTBED_NAME/engine/scripts/lib/gi_bootstrap"
    xvfb="xvfb-run -a"
    for d in "$gramps_dir" "$repo"; do
      if [ ! -d "$d" ]; then
        case "$d" in
          *-fork) echo "run-verify.sh: fork worktree $d missing — run 'make fork-worktrees' (declared via the brief's 'Verification base')." >&2 ;;
          *)      echo "run-verify.sh: worktree $d missing — run 'make worktrees${LANE_SFX:+ LANES=N}'." >&2 ;;
        esac
        return 1
      fi
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
  cname="grampstest-$$-$leg-$(basename "$gramps_dir")"
  label="$MODE, core $gv"; [ -n "$gramps_override" ] && label="$label, ESSENTIAL line"
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

# Write the dependency stamp when a bundle passes ONLY on the essential line.
_stamp_essential_dependency() {  # $1 = version leg
  local leg="$1" manifest="$ENGINE/essential-fixes.tsv" slugs date
  date="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  # Candidate dependencies = the essential fixes this version's line carries (by slug).
  slugs="$(awk -F'\t' -v v="$leg" '!/^#/ && $1==v {printf "%s\"%s\"", (n++?", ":""), $3}' "$manifest" 2>/dev/null)"
  cat > "$BUNDLE/essential-dependency.json" <<JSON
{
  "target_version": "$leg",
  "upstream_result": "fail",
  "essential_result": "pass",
  "essential_worktree": "gramps-$leg-essential",
  "depends_on": [$slugs],
  "date": "$date",
  "note": "C4-verify FAILS on clean upstream/maintenance/gramps$leg and PASSES on the essential line. Merge-order dependency: the listed essential fix(es) must land on the target branch first (or this fix's test must adopt equivalent import-safety). See engine/essential-fixes.tsv and process/validate-numbered-bundles.md."
}
JSON
  echo "  · wrote $BUNDLE/essential-dependency.json (depends_on: [$slugs])"
}

overall=0
stamped=0
for leg in "${LEGS[@]}"; do
  if _verify_leg "$leg"; then continue; fi
  # Upstream leg failed. For a CORE fix, retry on the essential line (upstream +
  # harness-enabling fixes). If it passes there, the fix is correct but carries a
  # dependency — stamp it and do NOT fail the gate on a known-essential prerequisite.
  ess="$WORKSPACE/gramps-$leg-essential$LANE_SFX"
  if [ "$MODE" = core ] && [ -d "$ess" ]; then
    echo "→ upstream leg $leg FAILED — retrying on the essential line ($ess)…"
    if _verify_leg "$leg" "$ess"; then
      _stamp_essential_dependency "$leg"; stamped=1
      echo "C4-verify[$leg]: PASS-ON-ESSENTIAL — fix is correct but depends on an essential fix (see essential-dependency.json)"
      continue
    fi
    echo "→ essential-line retry for $leg also FAILED — a real failure, not a missing prerequisite."
  fi
  overall=1
done

# Clear a stale dependency stamp if this run passed cleanly on upstream (no fallback) —
# e.g. once the essential fix has been merged upstream, the bundle no longer depends on it.
if [ "$overall" -eq 0 ] && [ "$stamped" -eq 0 ] && [ -f "$BUNDLE/essential-dependency.json" ]; then
  rm -f "$BUNDLE/essential-dependency.json"
  echo "  · cleared stale essential-dependency.json (now passes on clean upstream)"
fi
exit "$overall"
