#!/usr/bin/env bash
# Force-rebuild the testbed Docker image.
#
# The run-*.sh runners only build when the image is MISSING, so edits to
# engine/docker/Dockerfile.ubuntu (new apt packages, locale tweaks) aren't picked
# up automatically. Run this after editing the Dockerfile.
#
# Usage:
#   ./engine/scripts/ubuntu/rebuild-image.sh            # remove + rebuild
#   ./engine/scripts/ubuntu/rebuild-image.sh --no-cache # also bust the layer cache

set -euo pipefail

# -h / --help: print this script's header comment block and exit.
case "${1:-}" in
  -h | --help)
    awk 'NR==1{next} /^#/{sub(/^# ?/,""); print; next} {exit}' "$0"
    exit 0
    ;;
esac

# Repo root = nearest ancestor with pdca.toml (matches pdca_harness.config._find_root;
# depth- and git-independent — see engine/tests/test_root_resolution.py). ENGINE is
# the docker build context; WORKSPACE holds the sibling gramps/ checkout.
_find_repo_root() {
  local d
  d="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  while [ "$d" != "/" ]; do
    if [ -f "$d/pdca.toml" ]; then printf '%s\n' "$d"; return 0; fi
    d="$(dirname "$d")"
  done
  echo "rebuild-image.sh: could not locate pdca.toml above ${BASH_SOURCE[0]}" >&2
  return 1
}
REPO_ROOT="$(_find_repo_root)"
ENGINE="$REPO_ROOT/engine"
WORKSPACE="$(cd "$REPO_ROOT/.." && pwd)"

GRAMPS_VERSION="$(sed -nE 's/^VERSION_TUPLE *= *\(([0-9]+), *([0-9]+), *([0-9]+)\).*$/\1.\2.\3/p' "$WORKSPACE/gramps/gramps/version.py")"
: "${GRAMPS_VERSION:?could not detect Gramps version from gramps/version.py}"
IMAGE="${GRAMPS_TESTBED_IMAGE:-gramps-testbed:ubuntu-$GRAMPS_VERSION}"

BUILD_ARGS=()
case "${1:-}" in
  "")          ;;
  --no-cache)  BUILD_ARGS+=(--no-cache) ;;
  *)
    echo "unknown argument: $1" >&2
    echo "usage: $0 [--no-cache]" >&2
    exit 2
    ;;
esac

if docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "→ removing $IMAGE"
  docker rmi -f "$IMAGE" >/dev/null
fi

echo "→ building $IMAGE"
docker build "${BUILD_ARGS[@]}" -f "$ENGINE/docker/Dockerfile.ubuntu" -t "$IMAGE" "$ENGINE"

echo
echo "Done. Re-run ./engine/scripts/ubuntu/run-{unit,addon-unit}.sh."
