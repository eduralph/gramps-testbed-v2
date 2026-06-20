"""The gramps Docker-deps generator + a drift guard for the committed layer (issue #132).

``engine/scripts/lib/gramps_python_deps.py`` derives the deps baked into the image
(``engine/docker/gramps-requirements.txt``) from gramps' own ``pyproject.toml`` —
``[project].dependencies`` + the ``[testing]`` extra, the exact set the per-gate
``pip install -e ./gramps[testing]`` resolves. These tests pin the extraction (on a
fixture, always offline) and guard the committed file against drift vs the live
``../gramps`` (skipped when the sibling isn't checked out, e.g. in CI).
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

LIB = Path(__file__).resolve().parents[1] / "scripts" / "lib"
sys.path.insert(0, str(LIB))

import gramps_python_deps as gpd  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
GRAMPS_PYPROJECT = REPO.parent / "gramps" / "pyproject.toml"
COMMITTED = REPO / "engine" / "docker" / "gramps-requirements.txt"

# Mirrors gramps' pyproject shape: base deps + several extras, of which only `testing`
# is what the gates install and thus what we bake.
_FIXTURE = """\
[project]
name = "gramps"
dependencies = ["orjson", "requests", "certifi"]

[project.optional-dependencies]
image = ["Pillow"]
gui = ["PyGObject", "pycairo"]
testing = ["jsonschema", "mock", "lxml"]
"""


class Generator(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.pp = self.tmp / "pyproject.toml"
        self.pp.write_text(_FIXTURE, encoding="utf-8")

    def test_extracts_base_deps_plus_testing_extra_sorted(self) -> None:
        self.assertEqual(
            gpd.requirements(self.pp),
            ["certifi", "jsonschema", "lxml", "mock", "orjson", "requests"],
        )

    def test_excludes_non_testing_extras(self) -> None:
        reqs = gpd.requirements(self.pp)
        self.assertNotIn("Pillow", reqs)      # image extra not baked
        self.assertNotIn("PyGObject", reqs)   # gui extra not baked (apt-provided)

    def test_dedupes_verbatim_specs(self) -> None:
        pp = self.tmp / "dup.toml"
        pp.write_text(
            '[project]\ndependencies = ["requests", "requests", "orjson"]\n',
            encoding="utf-8",
        )
        self.assertEqual(gpd.requirements(pp), ["orjson", "requests"])

    def test_render_carries_header_and_one_dep_per_line(self) -> None:
        out = gpd.render(self.pp)
        self.assertIn("GENERATED", out)
        self.assertIn("issue #132", out)
        body = [ln for ln in out.splitlines() if ln and not ln.startswith("#")]
        self.assertEqual(body, ["certifi", "jsonschema", "lxml", "mock", "orjson", "requests"])


class CommittedFileInSync(unittest.TestCase):
    """The committed gramps-requirements.txt must equal what the live ../gramps produces,
    or the baked Docker layer is stale. Skips when ../gramps isn't a sibling (CI checks
    out only the testbed); on a dev box it catches a gramps dep bump that wasn't followed
    by `make gramps-requirements`."""

    @unittest.skipUnless(GRAMPS_PYPROJECT.is_file(), "../gramps/pyproject.toml not present")
    def test_committed_matches_live_gramps(self) -> None:
        expected = gpd.render(GRAMPS_PYPROJECT)
        actual = COMMITTED.read_text(encoding="utf-8")
        self.assertEqual(
            actual, expected,
            "engine/docker/gramps-requirements.txt is stale vs ../gramps — "
            "run `make gramps-requirements` and commit the result.",
        )


if __name__ == "__main__":
    unittest.main()
