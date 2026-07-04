#!/usr/bin/env bash
# `pdca try <id>` launcher — open the PATCHED gramps build on the host desktop for
# hands-on manual verification of the visual / GUI §6 NEEDS-HUMAN rows at sign-off.
#
# Invoked by the driver (src/pdca_harness/manual_test.py) from $PDCA_WORKTREE — the
# per-cycle worktree Do populated with this bundle's patch — with PDCA_WORKTREE /
# PDCA_BUNDLE / PDCA_TARGET exported. The host is a Wayland + XWayland session
# (DISPLAY=:0, socket /tmp/.X11-unix); the host has no GTK, so gramps runs in the
# gramps-testbed image with the X socket forwarded and the display set — the window
# opens on your desktop. Mirrors engine/scripts/ubuntu/run-verify.sh's mounts +
# editable install, minus the gate machinery, and launches gramps INTERACTIVELY
# (no xvfb). Advisory: edits made here are reset on the next Do. Quit gramps to return.
set -euo pipefail

WT="${PDCA_WORKTREE:?run via 'gramps-pdca try <id>' — PDCA_WORKTREE is unset}"
IMAGE="${GRAMPS_TESTBED_IMAGE:-gramps-testbed:ubuntu-6.1.0}"
DISP="${DISPLAY:-:0}"

# Launcher-side patch banner: a sitecustomize (outside the target checkout, so it never
# pollutes the worktree/patch) appends this tag to gramps' window titles, so the running GUI
# visibly confirms it is the PATCHED build and which bundle. See engine/scripts/lib/try_banner.
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BANNER="$REPO/engine/scripts/lib/try_banner"
BUNDLE_ID="$(basename "${PDCA_BUNDLE:-unknown}")"
TAG="⚑ PDCA try: ${BUNDLE_ID} — PATCHED build"

# Mounts mirror run-verify.sh: patched tree -> /workspace/gramps, the shared pip cache
# (so the editable install is a cache hit after the first run), and the X socket. A
# worktree's .git is a FILE pointing at the primary gitdir; bind-mount the common dir so
# an in-container `pip install -e` that shells out to git can resolve it.
mounts=( -v "$WT":/workspace/gramps -w /workspace/gramps
         -v "${GRAMPS_TESTBED_PIPCACHE:-gramps-testbed-pipcache}":/home/runner/.cache/pip
         -e "DISPLAY=$DISP" -v /tmp/.X11-unix:/tmp/.X11-unix )
# Mount the banner dir read-only and put it on PYTHONPATH so its sitecustomize.py runs at
# interpreter startup (it only carries sitecustomize.py — no `gramps`, so nothing is shadowed).
if [ -d "$BANNER" ]; then
  mounts+=( -v "$BANNER":/pdca_try_banner:ro -e "PYTHONPATH=/pdca_try_banner" -e "PDCA_TRY_TAG=$TAG" )
fi
if [ -f "$WT/.git" ]; then
  gd="$(git -C "$WT" rev-parse --path-format=absolute --git-common-dir)"
  mounts+=( -v "$gd":"$gd" )
fi

# Let the container (a different uid than you) reach the local X server; restore on exit.
_xhosted=0
if command -v xhost >/dev/null 2>&1; then
  xhost +local: >/dev/null 2>&1 && _xhosted=1 || true
fi
cleanup() { [ "$_xhosted" = 1 ] && xhost -local: >/dev/null 2>&1 || true; }
trap cleanup EXIT

echo "→ launching patched gramps from $WT" >&2
echo "  image $IMAGE, display $DISP — quit the app to return to the shell." >&2

# A GUI launch needs no stdin/TTY, but attach them when present (a human in a terminal) so
# console output/^C behave; omit when absent (backgrounded / non-interactive) so `docker
# run` doesn't fail with "the input device is not a TTY".
tty=()
[ -t 0 ] && tty+=( -i )
[ -t 1 ] && tty+=( -t )

# The gramps-testbed image already carries gramps' runtime deps, so run straight from the
# mounted source tree (cwd is on sys.path; GRAMPS_RESOURCES=. points at the in-tree data),
# no install step. Runs in English (uncompiled .mo) — fine for a visual/GUI check.
inner='
  set -e
  export GRAMPS_RESOURCES=.
  exec python3 -m gramps
'
docker run --rm "${tty[@]}" "${mounts[@]}" "$IMAGE" bash -lc "$inner"
