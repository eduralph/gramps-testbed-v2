#!/usr/bin/env bash
# Thin shim → the single-sourced `pdca doctor` (pdca_harness.doctor). All checks
# now live there: config-derived (leaf CLIs + auth, gh, bundle root, notes_cmd,
# python/ensurepip/make/git) plus this instance's engine/workspace/scraper rows
# declared in `pdca.toml [[doctor.checks]]` (Docker, siblings, base + per-lane
# worktrees, Chrome). One doctor, reported identically by `pdca doctor`,
# `make doctor`, and `scripts/bootstrap.sh`.
#
#   ./scripts/doctor.sh            # human-readable report, exit 0 iff required OK
#   ./scripts/doctor.sh --strict   # exit 1 on ANY non-OK row (CI)
#
# Runnable on a clean machine BEFORE `make install`: pdca_harness is stdlib-only,
# so it imports straight from src/ with no venv.

set -euo pipefail

case "${1:-}" in
  -h | --help)
    awk 'NR==1{next} /^#/{sub(/^# ?/,""); print; next} {exit}' "$0"
    exit 0
    ;;
esac

# Repo root = nearest ancestor containing pdca.toml (matches the driver's own root
# convention), so the shim works whatever the caller's cwd.
_find_repo_root() {
  local d
  d="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  while [ "$d" != "/" ]; do
    if [ -f "$d/pdca.toml" ]; then printf '%s\n' "$d"; return 0; fi
    d="$(dirname "$d")"
  done
  echo "doctor.sh: could not locate pdca.toml above ${BASH_SOURCE[0]}" >&2
  return 1
}
REPO_ROOT="$(_find_repo_root)"

# Prefer the installed console script; fall back to the source module (no venv needed).
if [ -x "$REPO_ROOT/.venv/bin/gramps-pdca" ]; then
  exec "$REPO_ROOT/.venv/bin/gramps-pdca" doctor "$@"
fi
cd "$REPO_ROOT"
exec env PYTHONPATH="src${PYTHONPATH:+:$PYTHONPATH}" python3 -m pdca_harness.cli doctor "$@"
