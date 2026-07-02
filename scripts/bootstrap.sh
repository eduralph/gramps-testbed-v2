#!/usr/bin/env bash
# One-command bootstrap of this testbed on a clean machine — idempotent and
# re-runnable; every phase prints what it does and skips work already done.
#
#   ./scripts/bootstrap.sh              full bootstrap (needs network; docker for the image)
#   ./scripts/bootstrap.sh --minimal    core only: venv + setup + offline smoke test
#                                       (no forks/worktrees/docker/scraper — CI mode)
#   ./scripts/bootstrap.sh --ssh        clone the sibling forks over SSH
#   ./scripts/bootstrap.sh --apt        allow `sudo apt-get install` of missing core
#                                       tools; default only PRINTS the command
#   make bootstrap [MINIMAL=1]          same entry point
#
# Phases:
#   1. doctor (pass 1)      hard-stop only if the REQUIRED core toolchain is missing
#   2. make install + setup venv + console script + Claude workspace permissions
#   3. sibling forks        ./engine/scripts/bootstrap-forks.sh   [skipped by --minimal]
#   4. worktrees + image    make preflight NO_CAPTURE=1           [skipped by --minimal / no docker]
#   5. Mantis scraper       ./engine/scripts/scrape-mantis.sh --setup, best-effort
#   6. smoke test           make check, then make rehearse ID=9999 (offline stubs)
#   7. doctor (pass 2)      final report + the manual next steps (auth stays manual)
#
# Credentials are NEVER scripted: claude login, `gh auth login`, `codex login`
# and the docker group membership are printed as next steps, not performed.

set -uo pipefail

case "${1:-}" in
  -h | --help)
    awk 'NR==1{next} /^#/{sub(/^# ?/,""); print; next} {exit}' "$0"
    exit 0
    ;;
esac

MINIMAL=0 APT=0 SSH_FLAG=""
for arg in "$@"; do
  case "$arg" in
    --minimal) MINIMAL=1 ;;
    --apt) APT=1 ;;
    --ssh) SSH_FLAG="--ssh" ;;
    *) echo "bootstrap.sh: unknown flag $arg (see --help)" >&2; exit 2 ;;
  esac
done

_find_repo_root() {
  local d
  d="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  while [ "$d" != "/" ]; do
    if [ -f "$d/pdca.toml" ]; then printf '%s\n' "$d"; return 0; fi
    d="$(dirname "$d")"
  done
  echo "bootstrap.sh: could not locate pdca.toml above ${BASH_SOURCE[0]}" >&2
  return 1
}
REPO_ROOT="$(_find_repo_root)"
cd "$REPO_ROOT"

step() { printf '\n\033[1;34m== bootstrap: %s ==\033[0m\n' "$*"; }
have() { command -v "$1" >/dev/null 2>&1; }

# --- 1. doctor pass 1: core toolchain is the only hard gate ------------------
step "doctor (pass 1)"
if ! ./scripts/doctor.sh; then
  # Core failed. Optionally repair via apt, else print the one command and stop.
  pyv="$(python3 -c 'import sys;print(f"{sys.version_info[0]}.{sys.version_info[1]}")' 2>/dev/null || echo 3)"
  APT_CMD="sudo apt-get update && sudo apt-get install -y git make python3 python3-venv python${pyv}-venv"
  if [ "$APT" -eq 1 ]; then
    step "installing missing core tools (--apt)"
    eval "$APT_CMD" || { echo "bootstrap.sh: apt install failed" >&2; exit 1; }
    ./scripts/doctor.sh || { echo "bootstrap.sh: core still failing after apt" >&2; exit 1; }
  else
    echo
    echo "bootstrap.sh: the REQUIRED core toolchain is incomplete. Install it with:"
    echo "    $APT_CMD"
    echo "or re-run with --apt to let bootstrap run that command."
    exit 1
  fi
fi

# --- 2. harness install + Claude permission setup ----------------------------
step "make install (venv + console script)"
make --no-print-directory install
step "make setup (Claude workspace permissions)"
make --no-print-directory setup

# --- 3. sibling forks ---------------------------------------------------------
if [ "$MINIMAL" -eq 1 ]; then
  step "sibling forks — skipped (--minimal)"
else
  step "sibling forks (bootstrap-forks.sh)"
  if ! ./engine/scripts/bootstrap-forks.sh $SSH_FLAG; then
    echo "bootstrap.sh: fork bootstrap failed — continuing. To retry with explicit sources:"
    echo "    FORK_OWNER=<you> ./engine/scripts/bootstrap-forks.sh"
    echo "    GRAMPS_FORK_URL=… ADDONS_SRC_FORK_URL=… ./engine/scripts/bootstrap-forks.sh"
  fi
fi

# --- 4. worktrees + engine image ----------------------------------------------
if [ "$MINIMAL" -eq 1 ]; then
  step "worktrees + engine image — skipped (--minimal)"
elif ! have docker || ! docker info >/dev/null 2>&1; then
  step "worktrees + engine image — skipped (docker unavailable)"
  echo "install docker (https://docs.docker.com/engine/install/ubuntu/), then: make preflight NO_CAPTURE=1"
else
  step "worktrees + engine image (make preflight NO_CAPTURE=1)"
  make --no-print-directory preflight NO_CAPTURE=1 \
    || echo "bootstrap.sh: preflight reported problems — continuing (re-run 'make preflight' after fixing)"
fi

# --- 5. Mantis scraper (best-effort) -------------------------------------------
if [ "$MINIMAL" -eq 1 ]; then
  step "Mantis scraper — skipped (--minimal)"
else
  CHROME=""
  for c in google-chrome google-chrome-stable chromium chromium-browser; do
    have "$c" && { CHROME="$c"; break; }
  done
  if [ -n "$CHROME" ]; then
    step "Mantis scraper (scrape-mantis.sh --setup)"
    ./engine/scripts/scrape-mantis.sh --setup \
      || echo "bootstrap.sh: scraper setup failed — optional; retry with ./engine/scripts/scrape-mantis.sh --setup"
  else
    step "Mantis scraper — skipped (no system Chrome/Chromium; install the Chrome .deb, not the snap)"
  fi
fi

# --- 6. offline smoke test -----------------------------------------------------
step "smoke test: make check (driver + engine guards, offline)"
make --no-print-directory check || { echo "bootstrap.sh: make check FAILED" >&2; exit 1; }
step "smoke test: make rehearse ID=9999 (full control flow, stub leaves + gates)"
make --no-print-directory rehearse ID=9999 || { echo "bootstrap.sh: rehearsal FAILED" >&2; exit 1; }

# --- 7. doctor pass 2 + next steps ---------------------------------------------
step "doctor (pass 2)"
./scripts/doctor.sh || true

step "done — manual next steps (credentials are never scripted)"
cat <<'EOF'
  1. claude          run once interactively: log in + accept the folder-trust prompt
  2. gh auth login   needed by publish / merge / revert
  3. codex login     optional: restores the cross-vendor reviewer
  4. docker group    if `docker info` failed: sudo usermod -aG docker $USER, then re-login
Then run a cycle:   make flow ID=<mantis-id>   (or `make rehearse ID=…` offline)
EOF
