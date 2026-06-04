#!/usr/bin/env bash
# Clean the gramps/build/ dir left behind by docker-based test runs.
#
# The in-container `pip install -e ./gramps[testing]` the runners perform writes
# build artefacts under ./gramps/build/, which survive on the bind-mounted host
# dir. On the next run, gramps' build_hook rmtrees build/ and dies with
# PermissionError when those files are owned by a uid the host user can't write
# (the container's `runner` uid=1000 != the host uid, or an earlier `-u root` run).
#
# Removes the dir, preferring a host-side `rm -rf` and falling back to a
# container-as-root rm when permissions block it. Idempotent.
#
#   ./engine/scripts/ubuntu/clean-build.sh

set -euo pipefail

# Repo root = nearest ancestor with pdca.toml (depth- and git-independent; see
# engine/tests/test_root_resolution.py). WORKSPACE holds the sibling gramps/.
_find_repo_root() {
  local d
  d="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  while [ "$d" != "/" ]; do
    if [ -f "$d/pdca.toml" ]; then printf '%s\n' "$d"; return 0; fi
    d="$(dirname "$d")"
  done
  echo "clean-build.sh: could not locate pdca.toml above ${BASH_SOURCE[0]}" >&2
  return 1
}
REPO_ROOT="$(_find_repo_root)"
ENGINE="$REPO_ROOT/engine"
WORKSPACE="$(cd "$REPO_ROOT/.." && pwd)"
cd "$WORKSPACE"

build_dir="$WORKSPACE/gramps/build"

if [[ ! -d "$build_dir" ]]; then
  echo "→ no gramps/build/ — nothing to clean"
  exit 0
fi

# Fast path: host user owns the dir → plain rm, skip docker entirely.
if rm -rf "$build_dir" 2>/dev/null; then
  echo "→ removed gramps/build/ (host-side)"
  exit 0
fi

# Slow path: ownership blocks host-side removal — remove via the image as root.
GRAMPS_VERSION="$(sed -nE 's/^VERSION_TUPLE *= *\(([0-9]+), *([0-9]+), *([0-9]+)\).*$/\1.\2.\3/p' "$WORKSPACE/gramps/gramps/version.py")"
: "${GRAMPS_VERSION:?could not detect Gramps version from gramps/version.py}"
IMAGE="${GRAMPS_TESTBED_IMAGE:-gramps-testbed:ubuntu-$GRAMPS_VERSION}"

if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "→ building $IMAGE (needed for root-owned cleanup)"
  docker build -f "$ENGINE/docker/Dockerfile.ubuntu" -t "$IMAGE" "$ENGINE"
fi

owner_uid="$(stat -c %u "$build_dir" 2>/dev/null || echo "?")"
echo "→ gramps/build/ owned by uid=$owner_uid; removing via $IMAGE running as root"
docker run --rm -u root -v "$WORKSPACE/gramps:/g" "$IMAGE" rm -rf /g/build
echo "→ cleaned"
