#!/usr/bin/env bash
# C4-verify-interface (bundle-scoped, ADVISORY): prove the bundle's fix at the GUI level.
#
# The BEHAVIORAL sibling of run-verify.sh (the unit-level C4). Where run-verify runs the
# patch's OWN unit test, this runs the bug's headless AT-SPI/dogtail repro — committed at
# engine/interface/test_bug_<id>_<slug>.py, NOT shipped in patch.diff — against:
#   * the UNPATCHED gramps/addon worktree (red: the bug reproduces → the repro FAILS), and
#   * the PATCHED worktree (green: the repro PASSES).
# Passes iff green-with-fix AND red-without-fix — the same predicate as run-verify, but the
# red↔green axis is simply patch-applied-vs-not: the repro lives in the TESTBED mount, a
# separate checkout from gramps/addons-source, so a gramps-side revert never touches it and
# no test-vs-production split is needed.
#
# Bundle-scoped: the driver exports $PDCA_BUNDLE. Advisory (gating=false) — a GUI repro is
# flakier than a unit test; promote to gating once stable. v1 covers a single TARGET_VER leg
# (no version matrix) for both core GUI fixes and frontend-addon E2E (the addon is installed
# into the running GUI). No committed repro for the bundle id → PDCA-UNVERIFIABLE (exit 77):
# the human verifies the GUI at sign-off.

set -euo pipefail

# -h / --help: print this script's header comment block and exit.
case "${1:-}" in
  -h | --help)
    awk 'NR==1{next} /^#/{sub(/^# ?/,""); print; next} {exit}' "$0"
    exit 0
    ;;
esac

# Repo root via the pdca.toml marker (depth- and git-independent; matches the other runners).
_find_repo_root() {
  local d
  d="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  while [ "$d" != "/" ]; do
    if [ -f "$d/pdca.toml" ]; then printf '%s\n' "$d"; return 0; fi
    d="$(dirname "$d")"
  done
  echo "run-verify-interface.sh: could not locate pdca.toml above ${BASH_SOURCE[0]}" >&2
  return 1
}
REPO_ROOT="$(_find_repo_root)"
ENGINE="$REPO_ROOT/engine"
WORKSPACE="$(cd "$REPO_ROOT/.." && pwd)"
TESTBED_NAME="$(basename "$REPO_ROOT")"
cd "$WORKSPACE"

# In-driver lane concurrency (docs 09): $PDCA_LANE pins a lane to its own per-version
# worktree (gramps-6.1-lane0); unset (serial) → the bare worktrees, unchanged.
LANE_SFX="${PDCA_LANE:+-lane$PDCA_LANE}"

BUNDLE="${PDCA_BUNDLE:?run-verify-interface.sh is bundle-scoped — \$PDCA_BUNDLE must be set}"
PATCH="$BUNDLE/patch.diff"
[ -f "$PATCH" ] || { echo "run-verify-interface.sh: no patch.diff in $BUNDLE" >&2; exit 1; }

# Detect target from the brief (same parsing as run-verify.sh): an addons-source fix is an
# E2E (install the addon into the GUI); else a gramps-core GUI fix. Default core.
MODE=core
if grep -iqE 'repo \+ branch( target)?:.*addons-source' "$BUNDLE/brief.md" 2>/dev/null; then
  MODE=addon
fi
# Core target version → which UPSTREAM per-version worktree to verify against. v1 runs a
# SINGLE leg = TARGET_VER (no 6.0×6.1 matrix — two GUI launches per leg is already heavy).
TARGET_VER=6.1
if grep -iqE 'repo \+ branch( target)?:.*(gramps60|maintenance/gramps60)' "$BUNDLE/brief.md" 2>/dev/null; then
  TARGET_VER=6.0
fi

# --- interface repro discovery helpers (unit-tested by engine/tests/test_verify_interface_discovery.py) ---
# The per-fix repro is committed at engine/interface/test_bug_<id>_<slug>.py. The driver's
# bundle dir is results/issue_<id>, so the id is the dir basename minus the `issue_` prefix.
# The filename's bug number is ZERO-PADDED (test_bug_0014100_*) while the bundle id is not
# (14100), so match with a leading `*` and a trailing `_` to bound the numeric run.
_bundle_id() { basename "$1" | sed -E 's/^issue_//'; }   # $1 = bundle dir → id
_find_repro() {                                          # $1 = id, $2 = ENGINE dir → 0..n repro paths
  shopt -s nullglob
  local m=( "$2"/interface/test_bug_*"$1"_*.py )
  [ "${#m[@]}" -gt 0 ] && printf '%s\n' "${m[@]}"   # no match → no output (not one blank line)
  return 0
}
# --- end interface repro discovery helpers ---

id="$(_bundle_id "$BUNDLE")"
[ -n "$id" ] && [ "$id" != "$(basename "$BUNDLE")" ] || {
  echo "PDCA-UNVERIFIABLE: bundle dir $(basename "$BUNDLE") is not issue_<id> — cannot derive the interface repro; the human verifies the GUI at sign-off."; exit 77; }
mapfile -t REPROS < <(_find_repro "$id" "$ENGINE")
case "${#REPROS[@]}" in
  0) echo "PDCA-UNVERIFIABLE: no interface repro engine/interface/test_bug_*${id}_*.py for bundle $(basename "$BUNDLE") — the per-fix GUI red→green cannot run; the human verifies the GUI at sign-off (or a repro should be added)."; exit 77 ;;
  1) PATTERN="$(basename "${REPROS[0]}")" ;;
  *) echo "PDCA-UNVERIFIABLE: multiple interface repros for bundle id ${id}: ${REPROS[*]} — ambiguous; keep exactly one (or rename)."; exit 77 ;;
esac

# For an addon E2E the patch targets addons-source/<Addon>/…; the addon to (re)install into
# the GUI is the top-level path component the patch touches.
ADDON=""
if [ "$MODE" = addon ]; then
  ADDON="$(grep -E '^\+\+\+ b/' "$PATCH" | sed -E 's|^\+\+\+ b/||; s|/.*||' | sort -u | head -1)"
  [ -n "$ADDON" ] || { echo "run-verify-interface.sh: could not infer the addon name from $PATCH" >&2; exit 1; }
fi

# Worktrees: gramps always (to run the GUI); addons-source too in addon mode (the patch
# target). A fork/stack base (#96/#54) is not supported in v1 — fail loudly rather than
# silently verify the wrong tree.
[ -z "${PDCA_BASE:-}" ] || { echo "run-verify-interface.sh: PDCA_BASE (stack/fork base) is not supported by the interface-verify gate yet — drop the brief's 'Onto branch'/'Verification base' for this gate, or use the unit C4." >&2; exit 1; }
if grep -iqE 'verification base:' "$BUNDLE/brief.md" 2>/dev/null; then
  echo "run-verify-interface.sh: a 'Verification base' (fork worktree) is not supported by the interface-verify gate yet." >&2; exit 1
fi

GRAMPS_DIR="$WORKSPACE/gramps-$TARGET_VER$LANE_SFX"
[ -d "$GRAMPS_DIR" ] || { echo "run-verify-interface.sh: core worktree $GRAMPS_DIR missing — run 'make worktrees${LANE_SFX:+ LANES=N}'." >&2; exit 1; }
PATCH_REPO="$GRAMPS_DIR"
MOUNTS=( -v "$GRAMPS_DIR":/workspace/gramps -v "$REPO_ROOT":/workspace/"$TESTBED_NAME" )
if [ "$MODE" = addon ]; then
  ADDONS_DIR="$WORKSPACE/addons-source-$TARGET_VER$LANE_SFX"
  [ -d "$ADDONS_DIR" ] || { echo "run-verify-interface.sh: addon worktree $ADDONS_DIR missing — run 'make worktrees${LANE_SFX:+ LANES=N}'." >&2; exit 1; }
  PATCH_REPO="$ADDONS_DIR"
  MOUNTS+=( -v "$ADDONS_DIR":/workspace/addons-source )
fi
# A worktree's .git is a FILE pointing at the primary gitdir — bind-mount it so in-container
# `git apply`/`checkout` resolve (a primary .git dir needs no mount).
GITDIR_REPOS=( "$GRAMPS_DIR" )
[ "$MODE" = addon ] && GITDIR_REPOS+=( "$ADDONS_DIR" )
for d in "${GITDIR_REPOS[@]}"; do
  if [ -f "$d/.git" ]; then gd="$(git -C "$d" rev-parse --path-format=absolute --git-common-dir)"; MOUNTS+=( -v "$gd":"$gd" ); fi
done

# Refuse to patch a dirty checkout (loud-failure backstop against tangling). Register the
# patch-target repo for restore even on interrupt.
git -C "$PATCH_REPO" diff --quiet || { echo "run-verify-interface.sh: $PATCH_REPO has uncommitted changes — refusing to patch it" >&2; exit 1; }
_TOUCHED=( "$PATCH_REPO" )
CNAME="grampstest-$$-ifaceverify-$(basename "$GRAMPS_DIR")"
_restore_all() {
  local r; for r in "${_TOUCHED[@]:-}"; do
    [ -n "$r" ] || continue
    git -C "$r" checkout -- . 2>/dev/null || true
    git -C "$r" clean -fdq 2>/dev/null || true
  done
  docker rm -f "$CNAME" >/dev/null 2>&1 || true
}
trap _restore_all EXIT

gv="$(sed -nE 's/^VERSION_TUPLE *= *\(([0-9]+), *([0-9]+), *([0-9]+)\).*$/\1.\2.\3/p' "$GRAMPS_DIR/gramps/version.py")"
: "${gv:?could not detect Gramps version from $GRAMPS_DIR}"
IMAGE="${GRAMPS_TESTBED_IMAGE:-gramps-testbed:ubuntu-$gv}"
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "→ building $IMAGE"; docker build -f "$ENGINE/docker/Dockerfile.ubuntu" -t "$IMAGE" "$ENGINE"
fi

# Two GUI launches (red + green), so a higher default than the suite's 1200s.
TIMEOUT="${GRAMPS_TEST_TIMEOUT:-1500}"
echo "→ C4-verify-interface ($MODE, core $gv${ADDON:+, addon $ADDON}): repro $PATTERN (red unpatched → green patched)"

# The container body: install gramps once (editable → live for both legs), seed trees, then
# run the repro RED on the pristine tree (refuse-on-dirty held before any git mutation), apply
# the fix, run GREEN. Green is the LAST leg so the host EXIT trap cleans up — no mid-run revert.
read -r -d '' INNER <<'INNER_EOF' || true
    set -e
    cleanup() {
      git -C /workspace/gramps checkout -- . 2>/dev/null || true
      [ "$MODE" = addon ] && git -C /workspace/addons-source checkout -- . 2>/dev/null || true
    }
    trap cleanup EXIT

    (cd /workspace && pip install --break-system-packages --user -e "./gramps[testing]" >/dev/null 2>&1)
    export PATH="$HOME/.local/bin:$PATH"

    # Compile .mo translations (idempotent). KEEP: a repro that launches under a non-English
    # LANGUAGE skipTests itself without its .mo — which the red-leg skip-guard would then
    # (correctly) flag as unverifiable rather than red-PASS, so a missing .mo must not be the
    # cause. Cheap with the warm pip/image cache.
    if [ ! -f /workspace/gramps/build/mo/de/LC_MESSAGES/gramps.mo ]; then
      for po in /workspace/gramps/po/*.po; do
        lang=$(basename "$po" .po); dest="/workspace/gramps/build/mo/$lang/LC_MESSAGES"
        mkdir -p "$dest"; msgfmt "$po" -o "$dest/gramps.mo" 2>/dev/null || true
      done
    fi

    USER_PLUGINS="$(python3 -c 'from gramps.gen.const import USER_PLUGINS; print(USER_PLUGINS)')"
    mkdir -p "$USER_PLUGINS"
    # Seed the canonical example tree (base.py default TREE_NAME=TestTree) plus a tree per
    # committed fixture, named by its file (a repro needing a fixture ships
    # engine/interface/data/<TREE_NAME>.gramps and sets TREE_NAME to that basename).
    gramps -C TestTree -i /workspace/gramps/example/gramps/example.gramps
    for data in "/workspace/$TESTBED_NAME/engine/interface/data/"*.gramps; do
      [ -e "$data" ] || continue
      gramps -C "$(basename "$data" .gramps)" -i "$data"
    done
    export ARTIFACTS_DIR="/workspace/$TESTBED_NAME/artifacts"
    # engine/ resolves `from .base import ...`; gi_bootstrap pins GI versions before any
    # addon import (mirrors the addon runners).
    export PYTHONPATH="/workspace/$TESTBED_NAME/engine/scripts/lib/gi_bootstrap${PYTHONPATH:+:$PYTHONPATH}"

    install_addon() {  # copy the (current on-disk) addon source into USER_PLUGINS
      [ "$MODE" = addon ] || return 0
      rm -rf "$USER_PLUGINS/$ADDON"; cp -a "/workspace/addons-source/$ADDON" "$USER_PLUGINS/$ADDON"
    }
    # Run the repro once; own dbus/at-spi bus per leg so a stale gramps app from one leg can't
    # confuse the next leg's root.application("gramps") wait. $1 = output subdir (red|green).
    run_repro() {
      local out="$1"
      rm -rf "/workspace/$TESTBED_NAME/test-results/$out"; mkdir -p "/workspace/$TESTBED_NAME/test-results/$out"
      cd "/workspace/$TESTBED_NAME"
      xvfb-run -a --server-args="-screen 0 1920x1080x24" \
        dbus-run-session -- bash -c "
          gsettings set org.gnome.desktop.interface toolkit-accessibility true
          /usr/libexec/at-spi-bus-launcher --launch-immediately &
          sleep 2
          python3 -m xmlrunner discover -s engine/interface -t engine -p \"$PATTERN\" -o \"test-results/$out/\" -v
        "
    }
    # The red leg is UNSOUND if the repro merely SKIPPED (e.g. a missing locale): a skip exits
    # 0, which would read as red-PASS and fail a correct fix. Treat an all-skipped / no-test
    # red leg as PDCA-UNVERIFIABLE, never as red-PASS. (Counts JUnit testsuite attributes.)
    red_is_unverifiable() {
      python3 - "/workspace/$TESTBED_NAME/test-results/red" <<'PY'
import sys, glob, xml.etree.ElementTree as ET
tests = skipped = 0
for f in glob.glob(sys.argv[1] + "/*.xml"):
    for ts in ET.parse(f).iter("testsuite"):
        tests += int(ts.get("tests", 0)); skipped += int(ts.get("skipped", 0))
# unverifiable iff no test actually exercised the bug (none ran, or every one skipped)
sys.exit(0 if tests == 0 or skipped >= tests else 1)
PY
    }

    # RED — UNPATCHED tree / UNPATCHED addon. The bug must reproduce → the repro FAILS.
    install_addon
    if run_repro red; then red=0; else red=1; fi
    if red_is_unverifiable; then
      echo "PDCA-UNVERIFIABLE: the interface repro was SKIPPED (or ran no test) on the UNPATCHED tree — the env could not exercise the bug (e.g. a missing locale/.mo), so red cannot be established; the human verifies the GUI at sign-off."
      exit 77
    fi

    # Apply the fix (core: gramps; addon: addons-source, then reinstall the patched addon).
    if [ "$MODE" = addon ]; then git -C /workspace/addons-source apply "$PATCH"; install_addon
    else git -C /workspace/gramps apply "$PATCH"; fi

    # GREEN — PATCHED. The repro must PASS.
    if run_repro green; then green=0; else green=1; fi

    echo "C4-verify-interface: green-with-fix=$([ $green -eq 0 ] && echo PASS || echo FAIL)" \
         "/ red-without-fix=$([ $red -ne 0 ] && echo PASS || echo FAIL)"
    [ "$green" -eq 0 ] && [ "$red" -ne 0 ]
INNER_EOF

# Persistent pip cache (issue #68): reuse wheels across gate runs. Pass the patch at its
# container-relative path (the bundle lives under $WORKSPACE, mounted via the testbed dir).
rc=0
timeout --kill-after=30 "$TIMEOUT" docker run --rm --name "$CNAME" \
  -v "${GRAMPS_TESTBED_PIPCACHE:-gramps-testbed-pipcache}":/home/runner/.cache/pip \
  "${MOUNTS[@]}" -w /workspace/gramps \
  -e PATCH="/workspace/${BUNDLE#"$WORKSPACE"/}/patch.diff" \
  -e MODE="$MODE" -e ADDON="$ADDON" -e PATTERN="$PATTERN" -e TESTBED_NAME="$TESTBED_NAME" \
  "$IMAGE" bash -c "$INNER" || rc=$?
if [ "$rc" = 124 ] || [ "$rc" = 137 ]; then
  echo "$(basename "$0"): interface verify exceeded ${TIMEOUT}s — killed it (raise GRAMPS_TEST_TIMEOUT)." >&2
  docker kill "$CNAME" >/dev/null 2>&1 || true
fi
exit "$rc"
