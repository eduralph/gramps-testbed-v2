#!/usr/bin/env bash
# Doctor check (issue #303): verify the engine image CONTAINS the indirect
# toolchain the gate scripts exec INSIDE it — not merely that the image exists.
# `pdca doctor` already confirms the image is built; this closes the "image
# contents never verified" gap: a stale / misbuilt image (missing e.g. xvfb-run
# or msgfmt) otherwise dies mid-gate with a confusing runtime error, exactly
# what doctor is meant to pre-empt.
#
# Two layers are attested:
#   1. BAKED tools the interface / unit / translation gates exec in-container:
#      xvfb-run, dbus-run-session, gsettings, msgfmt, python3, pip, the AT-SPI
#      launcher at /usr/libexec/at-spi-bus-launcher (run-interface.sh:179), and
#      the xmlrunner JUnit module (run-unit.sh).
#   2. The RUNTIME linters the T2-lint gate (#307) pip-installs at gate time —
#      black + mypy + types-requests (run-lint.sh) — so a broken index / pip in
#      the image is caught up front, not when the lint gate fails.
#
# Read-only, fixes nothing (like every doctor check). WARN-level: it needs the
# engine image, which `make preflight` builds. Runs from the repo root (doctor's
# cwd); the pip cache volume mirrors the gate runners so the linter probe is fast
# after the first run.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ver="$(python3 "$here/lib/gramps_version.py" ../gramps-6.1 2>/dev/null || true)"
[ -n "$ver" ] || { echo "cannot detect gramps version (is ../gramps-6.1 present?)"; exit 1; }
img="gramps-testbed:ubuntu-$ver"
docker image inspect "$img" >/dev/null 2>&1 || { echo "engine image $img is not built"; exit 1; }

# 1. baked in-container toolchain
docker run --rm "$img" sh -c '
  for t in xvfb-run dbus-run-session gsettings msgfmt python3 pip; do
    command -v "$t" >/dev/null || { echo "missing baked tool: $t"; exit 1; }
  done
  test -x /usr/libexec/at-spi-bus-launcher || { echo "missing: /usr/libexec/at-spi-bus-launcher"; exit 1; }
  python3 -c "import xmlrunner" 2>/dev/null || { echo "missing python module: xmlrunner"; exit 1; }
' || { echo "engine image $img is missing a baked gate tool — rebuild it (make preflight)"; exit 1; }

# 2. runtime linters (the T2-lint gate pip-installs these at gate time)
docker run --rm -v gramps-testbed-pipcache:/home/runner/.cache/pip "$img" sh -c '
  pip install --break-system-packages --user -q black mypy types-requests >/dev/null 2>&1 \
    && python3 -m black --version >/dev/null 2>&1 \
    && python3 -m mypy --version >/dev/null 2>&1
' || { echo "black/mypy not installable in the image (T2-lint gate would fail) — check the image has pip + PyPI access"; exit 1; }

echo "engine image toolchain OK ($img: baked tools + black/mypy)"
