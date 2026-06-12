#!/usr/bin/env bash
# Scrape Gramps Mantis issue threads into each issue's bundle as mantis-notes.json
# — the file the Plan leaf reads for full context beyond the CSV row. Wraps
# engine/scripts/mantis_notes.py (Playwright + a system Google Chrome).
#
# Modes:
#   ./engine/scripts/scrape-mantis.sh <id> [<id> ...]
#       Launch mode — Playwright opens Chrome; clear Cloudflare / log in once.
#
#   ./engine/scripts/scrape-mantis.sh --attach <id> [<id> ...]
#       Robust mode (the Cloudflare-LOOP fix), one command: it starts a normal
#       Chrome with remote debugging on the first issue, PAUSES so you clear
#       Cloudflare + log in, then attaches to that same browser and scrapes. A
#       re-run detects the still-running Chrome and attaches straight away — and
#       the profile persists — so you usually log in only once.
#
#   ./engine/scripts/scrape-mantis.sh --attach <cdp-url> <id> [<id> ...]
#       Attach to a Chrome YOU already started at <cdp-url> (skip the start/pause).
#
# All modes write results/issue_<id>/mantis-notes.json per id. Env override:
# MANTIS_DEBUG_PORT (default 9222). HOST-SIDE tool — NOT run in the Docker image.
# One-time setup:
#   pip install --break-system-packages playwright   # + a system Google Chrome .deb

set -euo pipefail

# -h / --help: print this script's header comment block and exit.
case "${1:-}" in
  -h | --help)
    awk 'NR==1{next} /^#/{sub(/^# ?/,""); print; next} {exit}' "$0"
    exit 0
    ;;
esac

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

PORT="${MANTIS_DEBUG_PORT:-9222}"
PROFILE="$REPO_ROOT/.cf-chrome-profile"          # persistent; gitignored (holds login)
BASE_URL="https://gramps-project.org/bugs"
NOTES_PY="$REPO_ROOT/engine/scripts/mantis_notes.py"

_chrome() {  # first system Chrome/Chromium on PATH (NOT the snap chromium)
  local c
  for c in google-chrome google-chrome-stable chromium chromium-browser; do
    command -v "$c" >/dev/null 2>&1 && { printf '%s\n' "$c"; return 0; }
  done
  return 1
}
_debugger_up() { timeout 1 bash -c "exec 3<>/dev/tcp/127.0.0.1/$PORT" 2>/dev/null; }
usage() { echo "usage: $0 [--attach [<cdp-url>]] <id> [<id> ...]" >&2; }

# --- Mode dispatch -----------------------------------------------------------
ATTACH=""          # non-empty → attach to this CDP url
OWN_BROWSER=0      # 1 → if no debugger is up, we start one + pause for login
case "${1:-}" in
  --attach)
    shift
    if [[ "${1:-}" == http://* || "${1:-}" == https://* ]]; then
      ATTACH="$1"; shift                              # attach to an EXISTING debugger
    else
      ATTACH="http://127.0.0.1:$PORT"; OWN_BROWSER=1  # start+pause+attach (one command)
    fi
    ;;
  --*)
    echo "scrape-mantis.sh: unknown option '$1'" >&2; usage; exit 2 ;;
esac

if [ "$#" -eq 0 ]; then usage; exit 2; fi

# Normalize ids (strip leading zeros) so they match the issue_<id> bundle naming.
# Validate each id is digits-only BEFORE the arithmetic expansion: $((10#$raw))
# evaluates $raw as a bash arithmetic expression, so a non-numeric id such as
# '1+a[$(cmd)]' would execute cmd via array-subscript evaluation (CWE-95
# arithmetic-eval command injection — the 10# prefix binds only the first token).
ids=()
for raw in "$@"; do
  if [[ ! "$raw" =~ ^[0-9]+$ ]]; then
    echo "scrape-mantis.sh: invalid issue id '$raw' (must be digits only)" >&2
    exit 2
  fi
  ids+=("$((10#$raw))")
done
csv_ids="$(IFS=,; echo "${ids[*]}")"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# Combined attach: start Chrome + pause for login, unless a debugger is already up.
if [ "$OWN_BROWSER" = 1 ]; then
  if _debugger_up; then
    echo "→ found a debug Chrome on :$PORT — attaching to it (no re-login)."
  else
    chrome="$(_chrome)" || { echo "no Google Chrome / Chromium found on PATH" >&2; exit 1; }
    mkdir -p "$PROFILE"
    echo "→ starting $chrome (remote debugging :$PORT, profile $PROFILE)"
    nohup "$chrome" --remote-debugging-port="$PORT" --user-data-dir="$PROFILE" \
      "$BASE_URL/view.php?id=${ids[0]}" >/dev/null 2>&1 &
    echo
    echo "A Chrome window is opening on issue ${ids[0]} (pid $!)."
    echo "  Clear the Cloudflare \"verify you are human\" check, and log in if you"
    echo "  need private/developer-only issues."
    read -r -p "  Press Enter once the issue page is loaded and you're past Cloudflare… " _ || true
  fi
fi

if [ -n "$ATTACH" ]; then
  echo "→ scraping (attach $ATTACH): $csv_ids"
  python3 "$NOTES_PY" --attach "$ATTACH" --yes --ids "$csv_ids" --out "$tmp"
else
  echo "→ scraping (a Chrome window opens; log in once if asked): $csv_ids"
  python3 "$NOTES_PY" --channel chrome --ids "$csv_ids" --out "$tmp"
fi

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
