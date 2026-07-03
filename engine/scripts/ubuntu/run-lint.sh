#!/usr/bin/env bash
# T2-lint (bundle-scoped): prove the bundle's patch is black- and mypy-clean,
# reproducing the two static-analysis gates upstream Gramps CI enforces:
#   * black  — .github/workflows/black.yml runs `psf/black@stable` (= `black
#     --check --diff .`, default line length 88, unpinned).
#   * mypy   — .github/workflows/gramps-ci.yml runs `pip install mypy
#     types-requests` then bare `mypy`, which reads the repo's mypy.ini
#     (files = ./gramps, ./test; exclude = *gpr.py; per-module ignores).
# A patch can pass C4 (red->green) and the T3 suite yet still trip these, opening
# an upstream PR that fails CI (pdca-harness lint gap). This gate catches it at
# Check so a lint-dirty bundle never reaches a clean COMPLETE.
#
# Passes iff BOTH black and mypy are clean with the patch applied. Bundle-scoped:
# the driver exports $PDCA_BUNDLE (the absolute bundle dir). Runs in the same
# Docker image as run-unit.sh / run-verify.sh, against the pinned per-version
# UPSTREAM worktree (the contribution target), which upstream keeps lint-clean.
#
# Exit codes (so callers can tell a real lint failure from a setup problem — the
# publish pre-push guard blocks on the former, warns-and-proceeds on the latter):
#   0  — black AND mypy clean.
#   1  — a linter reported issues (the patch is lint-dirty).       [BLOCK]
#   2  — setup/infra problem (missing/dirty worktree, no patch,    [couldn't run]
#        bad CORE_VERSION, git-apply / install failure).
#   77 — PDCA-UNVERIFIABLE: patch has no core .py to lint (§6).
#
# Core-only: mypy.ini and the black defaults belong to the gramps core repo, so
# the T2-lint gate is wired `target = "core"`. An addon fix skips it (its patch
# carries no core .py) via the PDCA-UNVERIFIABLE exit below.

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
  echo "run-lint.sh: could not locate pdca.toml above ${BASH_SOURCE[0]}" >&2
  return 1
}
REPO_ROOT="$(_find_repo_root)"
ENGINE="$REPO_ROOT/engine"
WORKSPACE="$(cd "$REPO_ROOT/.." && pwd)"
TESTBED_NAME="$(basename "$REPO_ROOT")"
INVOCATION_CWD="$PWD"   # for resolving a relative $PDCA_BUNDLE before the cd below
cd "$WORKSPACE"

# Lane concurrency: a worker patches its OWN per-version worktree
# (gramps-6.1-lane0). Unset (serial driver) -> the bare gramps-6.1 worktree.
LANE_SFX="${PDCA_LANE:+-lane$PDCA_LANE}"

BUNDLE="${PDCA_BUNDLE:?run-lint.sh is bundle-scoped — \$PDCA_BUNDLE must be set}"
# The driver exports an absolute bundle dir, but hand-runs often pass a path
# relative to the invocation CWD. Resolve it against that CWD (we already cd'd to
# $WORKSPACE) so both work, and so the ${BUNDLE#"$WORKSPACE"/} container-path
# strip below sees an absolute path.
[ "${BUNDLE#/}" != "$BUNDLE" ] || BUNDLE="$(cd "$INVOCATION_CWD" && cd "$(dirname "$BUNDLE")" && pwd)/$(basename "$BUNDLE")"
PATCH="$BUNDLE/patch.diff"
[ -f "$PATCH" ] || { echo "run-lint.sh: no patch.diff in $BUNDLE" >&2; exit 2; }

# Core target version -> which UPSTREAM worktree to lint against. Passed as a
# literal prefix from pdca.toml (CORE_VERSION=6.1 …); default 6.1.
TARGET_VER="${CORE_VERSION:-6.1}"
case "$TARGET_VER" in
  6.0 | 6.1) ;;
  *) echo "run-lint.sh: unknown CORE_VERSION '$TARGET_VER' (expected 6.0 or 6.1)" >&2; exit 2 ;;
esac

# The changed core .py files (added or modified; a deleted file's +++ is
# /dev/null, so `+++ b/` already excludes it). These are what black checks; the
# base worktree is upstream-gated black-clean, so this is equivalent to
# upstream's whole-repo `black .` and gives sharper per-file errors. mypy always
# runs whole-tree (bare `mypy`), exactly as upstream.
mapfile -t CHANGED_PY < <(grep -E '^\+\+\+ b/' "$PATCH" | sed -E 's|^\+\+\+ b/||' | grep -E '\.py$' || true)
if [ "${#CHANGED_PY[@]}" -eq 0 ]; then
  # No core .py in the patch — nothing for black/mypy to judge (e.g. a prose /
  # POTFILES-only / addon patch). Declare unverifiable (exit 77 -> SUMMARY §6,
  # non-fatal) rather than a hard pass or fail, mirroring run-verify.sh.
  echo "PDCA-UNVERIFIABLE: patch has no core .py file — black/mypy have nothing to check (addon / prose / manifest-only change); the human accepts T2-lint at sign-off."
  exit 77
fi

GRAMPS_DIR="$WORKSPACE/gramps-$TARGET_VER$LANE_SFX"
[ -d "$GRAMPS_DIR" ] || { echo "run-lint.sh: core worktree $GRAMPS_DIR missing — run 'make worktrees${LANE_SFX:+ LANES=N}'." >&2; exit 2; }
[ -d "$GRAMPS_DIR/.git" ] || [ -f "$GRAMPS_DIR/.git" ] || { echo "run-lint.sh: no checkout at $GRAMPS_DIR" >&2; exit 2; }
# status --porcelain (not diff --quiet): the restore path runs `git clean -fd`,
# so the guard must also catch staged and UNTRACKED files the restore would
# destroy, and guarantees black/mypy judge the patch alone, not stray residue.
[ -z "$(git -C "$GRAMPS_DIR" status --porcelain)" ] || { echo "run-lint.sh: $GRAMPS_DIR has uncommitted or untracked changes — refusing to patch it" >&2; exit 2; }

# Restore the worktree (revert tracked + drop patch-added files) even on
# interrupt, and kill the container. Host-side git works on worktrees fine.
_restore() {
  git -C "$GRAMPS_DIR" checkout -- . 2>/dev/null || true
  git -C "$GRAMPS_DIR" clean -fdq 2>/dev/null || true
  docker ps -aq --filter "name=grampslint-$$" | xargs -r docker rm -f >/dev/null 2>&1 || true
}
trap _restore EXIT

# Bind-mount the worktree's real gitdir (its .git is a file pointing at the
# primary gitdir) so in-container `git apply`/`checkout` resolve.
GIT_MOUNTS=()
if [ -f "$GRAMPS_DIR/.git" ]; then
  gd="$(git -C "$GRAMPS_DIR" rev-parse --path-format=absolute --git-common-dir)"
  GIT_MOUNTS+=( -v "$gd":"$gd" )
fi

GRAMPS_VERSION="$(python3 "$ENGINE/scripts/lib/gramps_version.py" "$GRAMPS_DIR")"
: "${GRAMPS_VERSION:?could not detect Gramps version from $GRAMPS_DIR}"
IMAGE="${GRAMPS_TESTBED_IMAGE:-gramps-testbed:ubuntu-$GRAMPS_VERSION}"
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "→ building $IMAGE"; docker build -f "$ENGINE/docker/Dockerfile.ubuntu" -t "$IMAGE" "$ENGINE"
fi

TIMEOUT="${GRAMPS_TEST_TIMEOUT:-900}"
CNAME="grampslint-$$"

# The container body — install core + the linters, apply the patch, run black
# on the changed files and mypy on the whole tree, and pass iff both are clean.
# A cleanup trap reverts even if a step aborts under `set -e`.
read -r -d '' INNER <<'INNER_EOF' || true
    set +e
    cleanup() { git checkout -- . 2>/dev/null || true; git clean -fdq 2>/dev/null || true; }
    trap cleanup EXIT
    (cd /workspace && pip install --break-system-packages --user -e "./gramps[testing]" >/dev/null 2>&1) \
      || { echo "run-lint (container): gramps install failed" >&2; exit 2; }
    # Unpinned, matching upstream (psf/black@stable + `pip install mypy types-requests`).
    pip install --break-system-packages --user black mypy types-requests >/dev/null 2>&1 \
      || { echo "run-lint (container): black/mypy install failed" >&2; exit 2; }
    export PATH="$HOME/.local/bin:$PATH"

    if ! git apply "$PATCH"; then echo "run-lint (container): git apply failed (base drifted?)" >&2; exit 2; fi

    echo "→ black --check --diff (changed .py):"
    black --check --diff $CHANGED_PY; blackrc=$?

    echo "→ mypy (whole tree, mypy.ini):"
    mypy; myrc=$?

    echo "T2-lint: black=$([ $blackrc -eq 0 ] && echo PASS || echo FAIL)" \
         "/ mypy=$([ $myrc -eq 0 ] && echo PASS || echo FAIL)"
    [ "$blackrc" -eq 0 ] && [ "$myrc" -eq 0 ]
INNER_EOF

echo "→ T2-lint (core $GRAMPS_VERSION): black on ${#CHANGED_PY[@]} changed .py + mypy whole-tree, patch applied to $GRAMPS_DIR"
rc=0
timeout --kill-after=30 "$TIMEOUT" docker run --rm --name "$CNAME" \
  -v "${GRAMPS_TESTBED_PIPCACHE:-gramps-testbed-pipcache}":/home/runner/.cache/pip \
  -v "$GRAMPS_DIR":/workspace/gramps \
  -v "$REPO_ROOT":/workspace/"$TESTBED_NAME" \
  "${GIT_MOUNTS[@]}" -w /workspace/gramps \
  -e PATCH="/workspace/${BUNDLE#"$WORKSPACE"/}/patch.diff" \
  -e CHANGED_PY="${CHANGED_PY[*]}" \
  "$IMAGE" bash -c "$INNER" || rc=$?
if [ "$rc" = 124 ] || [ "$rc" = 137 ]; then
  echo "$(basename "$0"): lint run exceeded ${TIMEOUT}s — killed it (raise GRAMPS_TEST_TIMEOUT)." >&2
  docker kill "$CNAME" >/dev/null 2>&1 || true
fi
exit "$rc"
