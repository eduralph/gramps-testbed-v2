#!/usr/bin/env bash
# Run per-addon unit test suites (addons-source/<addon>/tests/test_*.py) locally
# on the Ubuntu Docker base, using the same commands as CI. No display, no dbus,
# no AT-SPI — these tests construct in-memory fixtures / exercise pure-logic helpers.
#
# After the per-addon suites, two extra gates run when their tests are present:
# a translation-catalog gate (msgfmt over every addon's po/) and a system-dep
# drift gate. Those tests are not yet ported into this instance, so they SKIP.
#
# Companion to engine/scripts/ubuntu/run-unit.sh (gramps core unit suite).
# Addon tests follow Python stdlib convention (test_*.py).
#
# Usage:
#   ./engine/scripts/ubuntu/run-addon-unit.sh                 # all addons with tests/
#   ./engine/scripts/ubuntu/run-addon-unit.sh TMGimporter     # one addon
#   ./engine/scripts/ubuntu/run-addon-unit.sh TMGimporter Form  # several

set -euo pipefail

# Repo root = nearest ancestor with pdca.toml (depth- and git-independent; see
# engine/tests/test_root_resolution.py). ENGINE = build context; WORKSPACE holds
# the sibling gramps/ + addons-source/ checkouts; TESTBED_NAME = in-container path.
_find_repo_root() {
  local d
  d="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  while [ "$d" != "/" ]; do
    if [ -f "$d/pdca.toml" ]; then printf '%s\n' "$d"; return 0; fi
    d="$(dirname "$d")"
  done
  echo "run-addon-unit.sh: could not locate pdca.toml above ${BASH_SOURCE[0]}" >&2
  return 1
}
REPO_ROOT="$(_find_repo_root)"
ENGINE="$REPO_ROOT/engine"
WORKSPACE="$(cd "$REPO_ROOT/.." && pwd)"
TESTBED_NAME="$(basename "$REPO_ROOT")"
cd "$WORKSPACE"

if [[ ! -d "$WORKSPACE/addons-source" ]]; then
  echo "addons-source/ is missing — run ./engine/scripts/bootstrap-forks.sh first." >&2
  exit 1
fi

GRAMPS_VERSION="$(sed -nE 's/^VERSION_TUPLE *= *\(([0-9]+), *([0-9]+), *([0-9]+)\).*$/\1.\2.\3/p' "$WORKSPACE/gramps/gramps/version.py")"
: "${GRAMPS_VERSION:?could not detect Gramps version from gramps/version.py}"
IMAGE="${GRAMPS_TESTBED_IMAGE:-gramps-testbed:ubuntu-$GRAMPS_VERSION}"

if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "→ building $IMAGE"
  docker build -f "$ENGINE/docker/Dockerfile.ubuntu" -t "$IMAGE" "$ENGINE"
fi

# Auto-clean stale gramps/build/ before the in-container pip install (uid-mismatch
# PermissionError from gramps' build_hook rmtree; clean-build.sh picks host-side
# rm or container-as-root rm based on actual permissions).
build_dir="$WORKSPACE/gramps/build"
if [[ -d "$build_dir" ]] && [[ "$(stat -c %u "$build_dir" 2>/dev/null || echo 0)" != "$(id -u)" ]]; then
  echo "→ stale gramps/build/ detected (uid mismatch); calling clean-build.sh"
  "$ENGINE/scripts/ubuntu/clean-build.sh"
fi

# Positional args → container as a whitespace list. Empty = discover all addons.
TARGET_ADDONS="$*"

docker run --rm \
  -v "$WORKSPACE":/workspace \
  -w /workspace \
  -e "TARGET_ADDONS=$TARGET_ADDONS" \
  -e "TESTBED_NAME=$TESTBED_NAME" \
  "$IMAGE" \
  bash -c '
    set -e
    results_dir="/workspace/$TESTBED_NAME/test-results"
    install_logs="$results_dir/install-logs"
    rm -rf "$results_dir"
    mkdir -p "$install_logs"

    # [testing] extras pulls in jsonschema/mock/lxml; pip rejects the extras
    # syntax against absolute paths, so resolve via a relative path.
    gramps_log="$install_logs/gramps-testing.log"
    if ! (cd /workspace && pip install --break-system-packages --user \
            --progress-bar off -q --no-warn-script-location \
            -e "./gramps[testing]") \
            >"$gramps_log" 2>&1; then
      echo "× gramps[testing] install failed — last 40 lines of $gramps_log:" >&2
      tail -n 40 "$gramps_log" >&2
      exit 1
    fi
    export PATH="$HOME/.local/bin:$PATH"

    # Auto-derive addon Python deps (requires_mod) from every .gpr.py and pip
    # install the union — mirrors what the Gramps Addon Manager installs.
    echo "→ discovering addon deps from requires_mod declarations"
    addon_mods=$(python3 "/workspace/$TESTBED_NAME/engine/scripts/lib/addon_python_deps.py" /workspace/addons-source)
    pip_failures=()
    if [ -n "$addon_mods" ]; then
      echo "→ addon deps: $addon_mods"
      # One at a time so a single failing build does not abort the batch.
      for mod in $addon_mods; do
        mod_log="$install_logs/$mod.log"
        if pip install --break-system-packages --user \
             --progress-bar off -q --no-warn-script-location \
             "$mod" >"$mod_log" 2>&1; then
          :
        else
          pip_failures+=( "$mod" )
          echo "  × $mod failed — see install-logs/$mod.log"
        fi
      done
    fi
    find "$install_logs" -type f -empty -delete 2>/dev/null || true

    # Compile .mo translations so gramps.gen imports do not emit localedir
    # warnings. A single malformed catalog (e.g. po/mn.po) must not abort the
    # run under set -e — skip it and carry on.
    if [ ! -f /workspace/gramps/build/mo/de/LC_MESSAGES/gramps.mo ]; then
      echo "→ compiling translations"
      for po in /workspace/gramps/po/*.po; do
        lang=$(basename "$po" .po)
        dest="/workspace/gramps/build/mo/$lang/LC_MESSAGES"
        mkdir -p "$dest"
        if ! msgfmt "$po" -o "$dest/gramps.mo" 2>/dev/null; then
          echo "  ⚠ skipping $lang — msgfmt rejected $po (malformed catalog)"
          rm -f "$dest/gramps.mo"
        fi
      done
    fi

    # Resolve target addon list.
    if [ -n "${TARGET_ADDONS:-}" ]; then
      addons=( $TARGET_ADDONS )
    else
      addons=()
      for d in /workspace/addons-source/*/tests; do
        [ -d "$d" ] || continue
        parent_name=$(basename "$(dirname "$d")")
        [ "$parent_name" = "addons-source" ] && continue
        compgen -G "$d/test_*.py" >/dev/null || continue
        addons+=( "$parent_name" )
      done
    fi

    if [ ${#addons[@]} -eq 0 ]; then
      echo "no addons with tests/test_*.py were found" >&2
      exit 1
    fi

    echo "→ addon unit tests: ${addons[*]}"

    fail=0
    summary_lines=()
    for addon in "${addons[@]}"; do
      test_dir="/workspace/addons-source/$addon/tests"
      if [ ! -d "$test_dir" ]; then
        echo "× $addon: addons-source/$addon/tests/ not found" >&2
        summary_lines+=( "$(printf "  %-30s  SKIP (tests/ not found)" "$addon")" )
        fail=1
        continue
      fi
      echo
      echo "=== $addon ==="
      out_dir="$results_dir/$addon"
      mkdir -p "$out_dir"
      # Dotted module paths (<Addon>.tests.<module>) run from addons-source/ —
      # mirrors addons-source CI and surfaces package-shadowing bugs that a
      # discover-from-tests/ run would hide. test_windows_* excluded (Ubuntu).
      modules=()
      for f in /workspace/addons-source/"$addon"/tests/test_*.py; do
        [ -f "$f" ] || continue
        case "$(basename "$f")" in
          test_windows_*) continue ;;
        esac
        rel="${f#/workspace/addons-source/}"
        mod="${rel%.py}"
        mod="${mod//\//.}"
        modules+=( "$mod" )
      done
      if [ ${#modules[@]} -eq 0 ]; then
        echo "× $addon: no test_*.py in tests/" >&2
        summary_lines+=( "$(printf "  %-30s  SKIP (no test_*.py)" "$addon")" )
        fail=1
        continue
      fi
      run_log="$out_dir/_run.log"
      (
        cd /workspace/addons-source
        # Under Xvfb (some addons create a Gtk style context at import). The
        # gi_bootstrap sitecustomize on PYTHONPATH pins the GI versions the
        # gramps GUI launcher does, so gramps.gui.* imports load the GTK 3 stack.
        GRAMPS_RESOURCES=/workspace/gramps \
          PYTHONPATH="/workspace/$TESTBED_NAME/engine/scripts/lib/gi_bootstrap${PYTHONPATH:+:$PYTHONPATH}" \
          xvfb-run -a --server-args="-screen 0 1920x1080x24" \
            python3 -m xmlrunner "${modules[@]}" \
              -o "$out_dir" \
              -v
      ) 2>&1 | tee "$run_log"
      rc=${PIPESTATUS[0]}
      # Coverage from the JUnit XML, not the exit code: an all-skipped run also
      # exits 0, so treat wholly-skipped as a failure (usually a missing dep).
      coverage=$(python3 "/workspace/$TESTBED_NAME/engine/scripts/lib/junit_coverage.py" "$out_dir")
      ran="${coverage% *}"; skipped="${coverage#* }"
      ran="${ran:-0}"; skipped="${skipped:-0}"
      if [ "$rc" -ne 0 ]; then
        fail=1
        detail=$(grep -oE "FAILED \([^)]*\)" "$run_log" | tail -n 1 || true)
        detail="${detail:-crashed}"
        summary_lines+=( "$(printf "  %-30s  FAIL  (%s tests, %s)" "$addon" "$ran" "$detail")" )
      elif [ "$ran" -gt 0 ] && [ "$skipped" -eq "$ran" ]; then
        fail=1
        summary_lines+=( "$(printf "  %-30s  FAIL  (all %s tests skipped)" "$addon" "$ran")" )
      elif [ "$skipped" -gt 0 ]; then
        summary_lines+=( "$(printf "  %-30s  PASS  (%s tests, %s skipped)" "$addon" "$ran" "$skipped")" )
      else
        summary_lines+=( "$(printf "  %-30s  PASS  (%s tests)" "$addon" "$ran")" )
      fi
    done

    # Extra gates — run only if their tests are ported into this instance.
    run_extra_gate() {
      # $1 = label, $2 = test module, $3 = results subdir name
      local label="$1" module="$2" sub="$3"
      local tf="/workspace/$TESTBED_NAME/tests/${module#tests.}.py"
      echo
      echo "=== $label ==="
      if [ ! -f "$tf" ]; then
        echo "  (skipped — $tf not ported into this instance yet)"
        summary_lines+=( "$(printf "  %-30s  SKIP (gate not ported)" "$label")" )
        return
      fi
      local out="$results_dir/$sub"; mkdir -p "$out"
      ( cd "/workspace/$TESTBED_NAME"; ADDONS_SOURCE=/workspace/addons-source \
          python3 -m xmlrunner "$module" -o "$out" -v ) 2>&1 | tee "$out/_run.log"
      if [ "${PIPESTATUS[0]}" -eq 0 ]; then
        summary_lines+=( "$(printf "  %-30s  PASS" "$label")" )
      else
        fail=1
        summary_lines+=( "$(printf "  %-30s  FAIL  (see %s/_run.log)" "$label" "$sub")" )
      fi
    }
    run_extra_gate "addon translation catalogs" "tests.test_addon_po_catalogs" "_po-catalogs"
    run_extra_gate "addon system dependencies"  "tests.test_addon_system_deps"  "_system-deps"

    echo
    echo "=== Summary ==="
    for line in "${summary_lines[@]}"; do
      echo "$line"
    done
    echo
    echo "→ JUnit XMLs + per-addon _run.log: $TESTBED_NAME/test-results/<addon>/"
    if [ ${#pip_failures[@]} -gt 0 ]; then
      echo "→ pip install logs (${#pip_failures[@]} failure(s)): $TESTBED_NAME/test-results/install-logs/"
    fi
    exit $fail
  '
