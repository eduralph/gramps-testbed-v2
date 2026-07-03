#!/usr/bin/env bash
# Doctor check (issue #303): verify the engine image(s) CONTAIN the indirect
# toolchain the gate scripts exec INSIDE them — not merely that an image exists.
# `pdca doctor` already confirms the image is built; this closes the "image
# contents never verified" gap: a stale / misbuilt image (missing e.g. git,
# xvfb-run or msgfmt) otherwise dies mid-gate with a confusing runtime error,
# exactly what doctor is meant to pre-empt.
#
# Covers EVERY version image the configured gates use — the core C4/T3 gates run
# 6.1 and the addon matrix runs 6.0 (pdca.toml `CORE_VERSION=6.{0,1}`), each
# selecting gramps-testbed:ubuntu-<ver> from its own gramps-6.<ver> worktree. A
# version whose worktree is absent is skipped (the base-worktrees doctor row
# already flags that); a present worktree whose image is unbuilt or thin fails.
#
# Two layers per image are attested:
#   1. BAKED tools the interface / unit / lint / verify gates exec in-container:
#      git (T2-lint + C4 verify run git checkout/clean/apply inside the image),
#      xvfb-run, dbus-run-session, gsettings, the AT-SPI launcher at
#      /usr/libexec/at-spi-bus-launcher (run-interface.sh:179), msgfmt, and the
#      xmlrunner JUnit module (run-unit.sh).
#   2. The RUNTIME linters the T2-lint gate (#307) pip-installs at gate time —
#      black + mypy + types-requests (run-lint.sh) — so a broken index / pip in
#      the image is caught up front, not when the lint gate fails.
#
# Read-only, fixes nothing (like every doctor check). WARN-level: it needs the
# engine image(s), which `make preflight` builds. Runs from the repo root
# (doctor's cwd); the pip cache volume mirrors the gate runners so the linter
# probe is fast after the first run.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Probe one built image: baked toolchain, then the runtime linters. Returns
# non-zero (with a reason) on the first gap so doctor can point at the rebuild.
probe_image() {
    local img="$1"
    docker run --rm "$img" sh -c '
        for t in git xvfb-run dbus-run-session gsettings msgfmt python3 pip; do
            command -v "$t" >/dev/null || { echo "missing baked tool: $t"; exit 1; }
        done
        test -x /usr/libexec/at-spi-bus-launcher || { echo "missing: /usr/libexec/at-spi-bus-launcher"; exit 1; }
        python3 -c "import xmlrunner" 2>/dev/null || { echo "missing python module: xmlrunner"; exit 1; }
    ' || { echo "engine image $img is missing a baked gate tool — rebuild it (make preflight)"; return 1; }
    docker run --rm -v gramps-testbed-pipcache:/home/runner/.cache/pip "$img" sh -c '
        pip install --break-system-packages --user -q black mypy types-requests >/dev/null 2>&1 \
            && python3 -m black --version >/dev/null 2>&1 \
            && python3 -m mypy --version >/dev/null 2>&1
    ' || { echo "black/mypy not installable in $img (T2-lint gate would fail) — check the image has pip + PyPI access"; return 1; }
}

probed=0
for d in ../gramps-6.0 ../gramps-6.1; do
    [ -e "$d/.git" ] || continue  # absent version worktree — base-worktrees row covers it
    ver="$(python3 "$here/lib/gramps_version.py" "$d" 2>/dev/null || true)"
    [ -n "$ver" ] || { echo "cannot detect gramps version from $d"; exit 1; }
    img="gramps-testbed:ubuntu-$ver"
    docker image inspect "$img" >/dev/null 2>&1 \
        || { echo "engine image $img (for the $d gate) is not built — make preflight"; exit 1; }
    probe_image "$img" || exit 1
    echo "  OK $img ($d): baked tools + git + black/mypy"
    probed=$((probed + 1))
done

[ "$probed" -gt 0 ] || { echo "no gramps-6.{0,1} worktree present to resolve an engine image from"; exit 1; }
echo "engine image toolchain OK ($probed image(s) probed)"
