"""Unit tests for statistical distribution primitives in src.engine.distributions.

SPEC.md References:
- Section 4.1: Central and noncentral F distributions.
"""

import math
import unittest
from src.engine.distributions import log_gamma, betai, f_cdf, f_sf, f_inv_sf, ncf_power


class TestDistributions(unittest.TestCase):
    """Distribution primitive tests."""

    def test_log_gamma_known_values(self):
        self.assertLess(abs(log_gamma(1.0)), 1e-14)
        self.assertLess(abs(log_gamma(2.0)), 1e-14)
        self.assertLess(abs(log_gamma(5.0) - math.log(24.0)), 1e-13)
        self.assertLess(abs(log_gamma(0.5) - 0.5 * math.log(math.pi)), 1e-13)

    def test_betai_boundary_conditions(self):
        self.assertEqual(betai(2.0, 3.0, 0.0), 0.0)
        self.assertEqual(betai(2.0, 3.0, 1.0), 1.0)
        with self.assertRaises(ValueError):
            betai(2.0, 3.0, -0.1)
        with self.assertRaises(ValueError):
            betai(2.0, 3.0, 1.1)

    def test_central_f_distribution_consistency(self):
        df1, df2 = 4, 300
        f_val = 2.4017397
        cdf = f_cdf(f_val, df1, df2)
        sf = f_sf(f_val, df1, df2)
        self.assertLess(abs(cdf + sf - 1.0), 1e-14)
        self.assertLess(abs(sf - 0.05), 1e-6)

    def test_f_inv_sf_inverts_sf(self):
        df1, df2 = 4, 300
        alpha = 0.05
        crit_f = f_inv_sf(alpha, df1, df2)
        recalculated_sf = f_sf(crit_f, df1, df2)
        self.assertLess(abs(recalculated_sf - alpha), 1e-10)

    def test_ncf_power_reduces_to_central_f_when_lambda_zero(self):
        df1, df2 = 4, 300
        f_crit = 2.4017397
        central_sf = f_sf(f_crit, df1, df2)
        ncf_at_zero = ncf_power(f_crit, df1, df2, lambda_nc=0.0)
        self.assertLess(abs(central_sf - ncf_at_zero), 1e-7)


if __name__ == "__main__":
    unittest.main()
