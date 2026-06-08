"""Entry point for running the Blender integration tests inside Blender.

Usage (from the repository root)::

    blender --background --python portrait_mesh_generator/tests/run_blender_tests.py

The script ensures the repository root is importable, runs the integration
suite, and exits with a non-zero status on failure so it can be used in CI.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Repository root = parent of the portrait_mesh_generator package.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from portrait_mesh_generator.tests import test_integration_blender  # noqa: E402


def main() -> int:
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(test_integration_blender)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
