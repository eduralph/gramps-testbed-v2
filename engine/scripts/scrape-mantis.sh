#!/usr/bin/env bash
# Scrape Gramps Mantis issue threads into each issue's bundle as mantis-notes.json
# — the file the Plan leaf reads for full context beyond the CSV row. Wraps
# engine/scripts/mantis_notes.py (Playwright + system Chrome; one-time manual
# login — see that script's header for setup).
#
# Usage:
#   ./engine/scripts/scrape-mantis.sh 13636 [14051 ...]
# Writes results/issue_<id>/mantis-notes.json per id (bundle dir created if absent).
#
# HOST-SIDE tool: it is NOT run in the Docker image. One-time setup:
#   pip install --break-system-packages playwright   # + a system Google Chrome .deb

set -euo pipefail

# Repo root = nearest ancestor with pdca.toml (the engine's standard resolver).
_find_repo_root() {
  local d
  d="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  while [ "$d" != "/" ]; do
    if [ -f "$d/pdca.toml" ]; then printf '%s\n' "$d"; return 0; fi
    d="$(dirname "$d")"
  done
  echo "scrape-mantis.sh: could not locate pdca.toml above ${BASH_SOURCE[0]}" >&2
  return 1
}
REPO_ROOT="$(_find_repo_root)"
cd "$REPO_ROOT"

if [ "$#" -eq 0 ]; then
  echo "usage: $0 <issue-id> [<issue-id> ...]" >&2
  exit 2
fi

# Normalize ids (strip leading zeros) so they match the issue_<id> bundle naming.
ids=()
for raw in "$@"; do
  ids+=("$((10#$raw))")
done
csv_ids="$(IFS=,; echo "${ids[*]}")"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

echo "→ scraping Mantis issues: $csv_ids (a Chrome window opens; log in once if asked)"
python3 "$REPO_ROOT/engine/scripts/mantis_notes.py" --channel chrome --ids "$csv_ids" --out "$tmp"

for id in "${ids[@]}"; do
  src="$tmp/issue_${id}.json"
  dest_dir="$REPO_ROOT/results/issue_${id}"
  if [ -f "$src" ]; then
    mkdir -p "$dest_dir"
    cp "$src" "$dest_dir/mantis-notes.json"
    echo "→ wrote $dest_dir/mantis-notes.json"
  else
    echo "WARN: no scrape output for #$id (blocked / access-restricted? see log above)" >&2
  fi
done
