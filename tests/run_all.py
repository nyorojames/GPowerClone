"""Complete test runner for gpower-clone using Python standard library.

SPEC.md References:
- Section 2: CLI formatting, single-line JSON, numeric representations.
- Section 3: The seven error codes.
- Section 4: Pure engine distributions and algorithms.
- Section 6.1: Acceptance criteria scenarios.
- Section 6.2: Official instructor public reference vectors.
"""

import os
import sys
import unittest

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.unit.test_distributions import TestDistributions
from tests.unit.test_engine import TestEngine
from tests.unit.test_gherkin_scenarios import TestGherkinScenarios
from tests.contract.test_cli_contract import TestCliContract


def main():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestDistributions))
    suite.addTests(loader.loadTestsFromTestCase(TestEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestGherkinScenarios))
    suite.addTests(loader.loadTestsFromTestCase(TestCliContract))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if not result.wasSuccessful():
        sys.exit(1)


if __name__ == "__main__":
    main()
