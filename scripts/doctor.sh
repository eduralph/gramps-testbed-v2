#!/usr/bin/env bash
# Preflight diagnostic: report every prerequisite of a real `make flow` run as
#   OK / MISSING / UNAUTH / WARN     (one line each, with a fix hint)
# without installing or changing anything (read-only, no sudo, idempotent).
#
# Exit status: 0 when every REQUIRED check passes (core toolchain), even if
# optional pieces (claude, docker, gh, siblings, scraper) are missing — those
# print as MISSING/WARN with the command that fixes them. `--strict` escalates
# every non-OK line to a failure (for CI).
#
# Usage:
#   ./scripts/doctor.sh            # human-readable report, exit 0 iff core OK
#   ./scripts/doctor.sh --strict   # exit 1 on ANY non-OK line
#   make doctor                    # same as the first form
#
# Check groups:
#   core      python3 >= 3.11, ensurepip (python3-venv), git + identity, make   [REQUIRED]
#   leaves    claude CLI (+ credential heuristic), codex CLI (reviewer decorrelation)
#   github    gh CLI + gh auth status (publish/merge need it)
#   engine    docker daemon reachable, gramps-testbed:ubuntu-<ver> image
#   workspace sibling checkouts (../gramps, ../addons-source, ../addons) +
#             per-version validation worktrees (../gramps-6.*, ../addons-source-6.*)
#   scraper   system Chrome/Chromium + .venv-mantis Playwright (Mantis scraping)

set -uo pipefail

case "${1:-}" in
  -h | --help)
    awk 'NR==1{next} /^#/{sub(/^# ?/,""); print; next} {exit}' "$0"
    exit 0
    ;;
esac

STRICT=0
[ "${1:-}" = "--strict" ] && STRICT=1

# Repo root = nearest ancestor containing pdca.toml — matches the driver's own
# root convention (pdca_harness.config._find_root).
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
WORKSPACE="$(cd "$REPO_ROOT/.." && pwd)"

CORE_FAIL=0
NONOK=0

_row() { # _row <STATE> <check> <detail/hint>
  printf '%-7s %-34s %s\n' "$1" "$2" "$3"
  [ "$1" = "OK" ] || NONOK=1
}
_core_fail() { CORE_FAIL=1; }
have() { command -v "$1" >/dev/null 2>&1; }

echo "== core (required) =="
if have python3 && python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' 2>/dev/null; then
  _row OK "python3 >= 3.11" "$(python3 --version 2>&1)"
else
  _row MISSING "python3 >= 3.11" "sudo apt-get install -y python3"; _core_fail
fi
if python3 -c 'import ensurepip' >/dev/null 2>&1; then
  _row OK "python ensurepip (venv)" ""
else
  pyv="$(python3 -c 'import sys;print(f"{sys.version_info[0]}.{sys.version_info[1]}")' 2>/dev/null || echo 3)"
  _row MISSING "python ensurepip (venv)" "sudo apt-get install -y python3-venv python${pyv}-venv"; _core_fail
fi
if have git; then
  if [ -n "$(git config --get user.name 2>/dev/null)" ] && [ -n "$(git config --get user.email 2>/dev/null)" ]; then
    _row OK "git + identity" "$(git --version 2>&1)"
  else
    _row WARN "git + identity" "set: git config --global user.name/user.email (DCO sign-off needs them)"
  fi
else
  _row MISSING "git" "sudo apt-get install -y git"; _core_fail
fi
if have make; then _row OK "make" ""; else _row MISSING "make" "sudo apt-get install -y make"; _core_fail; fi

echo
echo "== model CLIs (leaves) =="
if have claude; then
  # No reliable non-interactive auth probe exists; report the credential
  # heuristic and leave the verdict soft.
  if [ -e "$HOME/.claude/.credentials.json" ] || [ -e "$HOME/.claude.json" ]; then
    _row OK "claude CLI" "$(claude --version 2>&1 | head -1)"
  else
    _row WARN "claude CLI (auth?)" "installed, but no credentials found — run 'claude' once interactively"
  fi
else
  _row MISSING "claude CLI" "curl -fsSL https://claude.ai/install.sh | bash — then run 'claude' once to log in"
fi
if have codex; then
  if codex login status >/dev/null 2>&1; then
    _row OK "codex CLI (reviewer)" "$(codex --version 2>&1 | head -1)"
  else
    _row UNAUTH "codex CLI (reviewer)" "run 'codex login' (or export OPENAI_API_KEY)"
  fi
else
  _row WARN "codex CLI (reviewer)" "optional: cross-vendor reviewer; pdca.toml documents the same-vendor fallback"
fi

echo
echo "== github =="
if have gh; then
  if gh auth status >/dev/null 2>&1; then
    _row OK "gh CLI + auth" ""
  else
    _row UNAUTH "gh CLI" "run 'gh auth login' (publish/merge/revert need it; building does not)"
  fi
else
  _row MISSING "gh CLI" "https://github.com/cli/cli/blob/trunk/docs/install_linux.md — then: gh auth login"
fi

echo
echo "== engine (docker) =="
GV=""
if have docker; then
  if docker info >/dev/null 2>&1; then
    _row OK "docker daemon" ""
    GV="$(python3 "$REPO_ROOT/engine/scripts/lib/gramps_version.py" "$WORKSPACE/gramps-6.1" 2>/dev/null || true)"
    if [ -n "$GV" ]; then
      img="gramps-testbed:ubuntu-$GV"
      if docker image inspect "$img" >/dev/null 2>&1; then
        _row OK "engine image $img" ""
      else
        _row WARN "engine image $img" "build it: make preflight NO_CAPTURE=1"
      fi
    else
      _row WARN "engine image" "cannot detect gramps version (worktree ../gramps-6.1 missing?)"
    fi
  else
    _row WARN "docker daemon" "installed but unreachable — daemon down, or add yourself: sudo usermod -aG docker \$USER (re-login)"
  fi
else
  _row MISSING "docker" "https://docs.docker.com/engine/install/ubuntu/ — all real gates run in a container"
fi

echo
echo "== workspace layout =="
for sib in gramps addons-source addons; do
  d="$WORKSPACE/$sib"
  if [ -e "$d/.git" ]; then
    if [ "$sib" = addons ] || git -C "$d" remote get-url upstream >/dev/null 2>&1; then
      _row OK "sibling ../$sib" ""
    else
      _row WARN "sibling ../$sib" "no 'upstream' remote — re-run ./engine/scripts/bootstrap-forks.sh"
    fi
  else
    _row MISSING "sibling ../$sib" "./engine/scripts/bootstrap-forks.sh"
  fi
done
for wt in gramps-6.0 gramps-6.1 addons-source-6.0 addons-source-6.1; do
  if [ -e "$WORKSPACE/$wt/.git" ]; then
    _row OK "worktree ../$wt" ""
  else
    _row WARN "worktree ../$wt" "make worktrees   (or the full: make preflight)"
  fi
done
# Per-lane worktrees: a batch `flow` fans out across [driver].lanes workers, and lane
# K patches its OWN gramps-6.x-laneK / addons-source-6.x-laneK worktree (docs 09). If
# lanes > 1 those copies MUST exist or every gate landing on a missing lane fails with
# "worktree … missing" — the batch-flow failure this check exists to pre-empt.
LANES="$(python3 -c "import tomllib,sys; print(tomllib.load(open('$REPO_ROOT/pdca.toml','rb')).get('driver',{}).get('lanes',1))" 2>/dev/null || echo 1)"
if [ "${LANES:-1}" -gt 1 ] 2>/dev/null; then
  missing=""
  k=0
  while [ "$k" -lt "$LANES" ]; do
    for base in gramps-6.0 gramps-6.1 addons-source-6.0 addons-source-6.1; do
      [ -e "$WORKSPACE/$base-lane$k/.git" ] || missing="$missing $base-lane$k"
    done
    k=$((k + 1))
  done
  if [ -z "$missing" ]; then
    _row OK "lane worktrees (lanes=$LANES)" "gramps-6.{0,1}-lane{0..$((LANES - 1))} + addon copies"
  else
    _row WARN "lane worktrees (lanes=$LANES)" "make worktrees LANES=$LANES   (missing:$missing)"
  fi
fi

echo
echo "== scraper (optional) =="
CHROME=""
for c in google-chrome google-chrome-stable chromium chromium-browser; do
  if have "$c"; then CHROME="$c"; break; fi
done
if [ -n "$CHROME" ]; then
  _row OK "system Chrome/Chromium" "$CHROME"
else
  _row WARN "system Chrome/Chromium" "needed only for Mantis scraping — install the Chrome .deb (not snap)"
fi
if [ -x "$REPO_ROOT/.venv-mantis/bin/python" ] \
   && "$REPO_ROOT/.venv-mantis/bin/python" -m playwright --version >/dev/null 2>&1; then
  _row OK ".venv-mantis (playwright)" ""
else
  _row WARN ".venv-mantis (playwright)" "./engine/scripts/scrape-mantis.sh --setup"
fi

echo
echo "== harness =="
if [ -x "$REPO_ROOT/.venv/bin/gramps-pdca" ]; then
  _row OK "console script (.venv)" ""
else
  _row WARN "console script (.venv)" "optional: make install   (make targets work without it)"
fi

echo
if [ "$CORE_FAIL" -ne 0 ]; then
  echo "doctor: REQUIRED core checks failed — fix the MISSING lines above first."
  exit 1
fi
if [ "$STRICT" -eq 1 ] && [ "$NONOK" -ne 0 ]; then
  echo "doctor (--strict): non-OK lines present."
  exit 1
fi
echo "doctor: core toolchain OK$( [ "$NONOK" -ne 0 ] && printf ' — some optional pieces need attention (see above)' )."
exit 0
