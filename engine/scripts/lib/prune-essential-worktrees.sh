#!/usr/bin/env bash
# Remove essential worktrees whose target version no longer appears in the manifest.
#
# `make essential-worktrees` derives the versions it (re)builds FROM the manifest, so a
# dropped row is simply never visited again — not even under REBUILD=1. The worktree an
# earlier run created lives on: a stale line carrying a fix that is no longer essential,
# on a base nothing refreshes. run-verify.sh must not fall back to it (it now requires a
# manifest row), and it should not sit on disk pretending to be a verification base.
#
# Usage: prune-essential-worktrees.sh <workspace> <manifest>
#   <workspace>  the dir holding gramps/ and the gramps-<ver>-essential* worktrees
#   <manifest>   engine/essential-fixes.tsv
#
# Idempotent: a workspace with no stale worktrees is a no-op. Unit-tested by
# engine/tests/test_prune_essential_worktrees.py.

set -euo pipefail

ws="${1:?usage: prune-essential-worktrees.sh <workspace> <manifest>}"
manifest="${2:?usage: prune-essential-worktrees.sh <workspace> <manifest>}"
[ -f "$manifest" ] || { echo "prune-essential-worktrees.sh: no $manifest" >&2; exit 1; }

# Versions the manifest still declares. Empty is legitimate: every row dropped.
vers=" $(awk -F'\t' '!/^#/ && NF>=3 {print $1}' "$manifest" | sort -u | tr '\n' ' ')"

for wt in "$ws"/gramps-*-essential*; do
  [ -d "$wt" ] || continue                      # unmatched glob, or a stray file
  base="$(basename "$wt")"
  v="${base#gramps-}"
  v="${v%%-essential*}"                         # gramps-6.1-essential-lane0 -> 6.1
  case "$vers" in *" $v "*) continue ;; esac    # still declared: keep

  # gramps-6.1-essential-lane0 -> testbed/essential-gramps61-lane0
  sfx="$(printf '%s' "$base" | sed -e "s/^gramps-$v-essential//")"
  br="testbed/essential-gramps$(printf '%s' "$v" | tr -d .)$sfx"

  echo "pruning stale essential worktree $wt (no '$v' row in $(basename "$manifest"))"
  git -C "$ws/gramps" worktree remove --force "$wt" 2>/dev/null || rm -rf "$wt"
  git -C "$ws/gramps" branch -D "$br" >/dev/null 2>&1 || true
done
