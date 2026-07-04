#!/usr/bin/env bash
# Scrape Gramps Mantis issue threads into each issue's bundle as notes.json
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
# All modes write results/issue_<id>/notes.json per id. Env override:
# MANTIS_DEBUG_PORT (default 9222). HOST-SIDE tool — NOT run in the Docker image.
#
#   ./engine/scripts/scrape-mantis.sh --setup
#       One-time dependency setup: creates a repo-local .venv-mantis and pip-installs
#       the Playwright wheel (which bundles its own Node driver). After this, scrape
#       with NO PATH prefix — the script auto-detects the venv. Needs python3-venv
#       (`sudo apt install -y python3-venv`), plus a system Google Chrome/Chromium.
#
# Interpreter resolution (first with a working Playwright): $MANTIS_PYTHON →
# .venv-mantis → ~/.venvs/mantis → system python3. Ubuntu's apt python3-playwright
# is driverless (no node-playwright-core in the archive) and its ensurepip is
# disabled, so the --setup venv+wheel is the reliable path.

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
PW_VENV="$REPO_ROOT/.venv-mantis"                # `--setup` venv; gitignored (Playwright wheel)
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
usage() { echo "usage: $0 --setup | [--attach [<cdp-url>]] <id> [<id> ...]" >&2; }

# The interpreter that runs mantis_notes.py needs a WORKING Playwright — the Python
# binding AND a runnable Node driver. `--version` exercises both (the missing binding
# fails on import; a missing/broken Node driver fails only when it runs).
_py_works() {  # $1 = interpreter path/name; true if it has a runnable Playwright driver
  [ -n "${1:-}" ] || return 1
  { command -v "$1" >/dev/null 2>&1 || [ -x "$1" ]; } && "$1" -m playwright --version >/dev/null 2>&1
}
_resolve_python() {  # echo the first interpreter with a working Playwright, else nothing
  local c
  for c in ${MANTIS_PYTHON:+"$MANTIS_PYTHON"} \
           "$PW_VENV/bin/python3" \
           "$HOME/.venvs/mantis/bin/python3" \
           python3; do
    if _py_works "$c"; then printf '%s\n' "$c"; return 0; fi
  done
  return 1
}

# --setup: provision $PW_VENV with the Playwright wheel (bundled Node driver) — the
# reliable path on Ubuntu, where the apt python3-playwright ships no driver and system
# ensurepip is disabled. Idempotent; safe to re-run. Leaves the script prefix-free after.
_setup_venv() {
  if _py_works "$PW_VENV/bin/python3"; then
    echo "→ $PW_VENV already has a working $("$PW_VENV/bin/python3" -m playwright --version)"
    return 0
  fi
  if ! python3 -c 'import venv' 2>/dev/null; then
    echo "scrape-mantis.sh --setup: python3 venv module missing — run: sudo apt install -y python3-venv" >&2
    return 1
  fi
  echo "→ creating venv at $PW_VENV"
  python3 -m venv "$PW_VENV" || {
    echo "scrape-mantis.sh --setup: venv creation failed (pip seed?) — run: sudo apt install -y python3-venv" >&2
    return 1; }
  echo "→ installing playwright (pip wheel, with bundled Node driver)"
  "$PW_VENV/bin/pip" install --quiet --upgrade pip \
    && "$PW_VENV/bin/pip" install --quiet playwright || {
      echo "scrape-mantis.sh --setup: pip install playwright failed" >&2; return 1; }
  if _py_works "$PW_VENV/bin/python3"; then
    echo "→ ok — $("$PW_VENV/bin/python3" -m playwright --version) in $PW_VENV"
    echo "  Scrape now runs with NO prefix:  $0 --attach <id> [<id> ...]"
    return 0
  fi
  echo "scrape-mantis.sh --setup: playwright installed but its driver still won't start" >&2
  return 1
}

# Preflight — resolve a working interpreter into $MANTIS_PY, or fail with guidance.
MANTIS_PY=""
_preflight_deps() {
  MANTIS_PY="$(_resolve_python || true)"
  [ -n "$MANTIS_PY" ] && return 0
  cat >&2 <<EOF
scrape-mantis.sh: no python3 with a working Playwright found (tried: \${MANTIS_PYTHON:-unset},
  $PW_VENV, ~/.venvs/mantis, system python3).
  Provision one (recommended):  $0 --setup
    → creates $PW_VENV and pip-installs the Playwright wheel (bundled Node driver).
      Needs python3-venv:  sudo apt install -y python3-venv
  Ubuntu's apt python3-playwright is driverless (no node-playwright-core in the archive)
  and its ensurepip is disabled — the --setup venv is the fix. Override with
  MANTIS_PYTHON=/path/to/python3 if you manage your own interpreter.
EOF
  return 1
}

# --setup provisions the venv and exits (no issue ids needed).
if [ "${1:-}" = "--setup" ]; then _setup_venv; exit $?; fi

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

# Fail on missing prerequisites BEFORE launching Chrome / prompting for a login.
_preflight_deps || exit 1

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
  "$MANTIS_PY" "$NOTES_PY" --attach "$ATTACH" --yes --ids "$csv_ids" --out "$tmp"
else
  echo "→ scraping (a Chrome window opens; log in once if asked): $csv_ids"
  "$MANTIS_PY" "$NOTES_PY" --channel chrome --ids "$csv_ids" --out "$tmp"
fi

for id in "${ids[@]}"; do
  src="$tmp/issue_${id}.json"
  dest_dir="$REPO_ROOT/results/issue_${id}"
  if [ -f "$src" ]; then
    mkdir -p "$dest_dir"
    cp "$src" "$dest_dir/notes.json"
    echo "→ wrote $dest_dir/notes.json"
    # Image attachments (issue #319): mantis_notes.py drops them under
    # <tmp>/issue_<id>_attachments/; place them beside notes.json so the planner can
    # open them (notes.json links each as attachments/<name>).
    att_src="$tmp/issue_${id}_attachments"
    if [ -d "$att_src" ] && [ -n "$(ls -A "$att_src" 2>/dev/null)" ]; then
      mkdir -p "$dest_dir/attachments"
      cp "$att_src"/* "$dest_dir/attachments/"
      echo "→ wrote $(ls -1 "$att_src" | wc -l | tr -d ' ') attachment(s) to $dest_dir/attachments/"
    fi
  else
    echo "WARN: no scrape output for #$id (blocked / access-restricted? see log above)" >&2
  fi
done
