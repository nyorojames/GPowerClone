"""Unit tests for statistical distribution primitives in src.engine.distributions."""

import math
from src.engine.distributions import log_gamma, betai, f_cdf, f_sf, f_inv_sf, ncf_power


def test_log_gamma_known_values():
    # Gamma(1) = 1 -> log_gamma(1) = 0
    assert abs(log_gamma(1.0)) < 1e-14
    # Gamma(2) = 1 -> log_gamma(2) = 0
    assert abs(log_gamma(2.0)) < 1e-14
    # Gamma(5) = 24 -> log(24)
    assert abs(log_gamma(5.0) - math.log(24.0)) < 1e-13
    # Gamma(0.5) = sqrt(pi) -> log(sqrt(pi))
    assert abs(log_gamma(0.5) - 0.5 * math.log(math.pi)) < 1e-13


def test_betai_boundary_conditions():
    assert betai(2.0, 3.0, 0.0) == 0.0
    assert betai(2.0, 3.0, 1.0) == 1.0
    try:
        betai(2.0, 3.0, -0.1)
        assert False, "Should raise ValueError on x < 0"
    except ValueError:
        pass

    try:
        betai(2.0, 3.0, 1.1)
        assert False, "Should raise ValueError on x > 1"
    except ValueError:
        pass


def test_central_f_distribution_consistency():
    # Symmetry and CDF + SF == 1
    df1, df2 = 4, 300
    f_val = 2.4017397
    cdf = f_cdf(f_val, df1, df2)
    sf = f_sf(f_val, df1, df2)
    assert abs(cdf + sf - 1.0) < 1e-14
    assert abs(sf - 0.05) < 1e-6


def test_f_inv_sf_inverts_sf():
    df1, df2 = 4, 300
    alpha = 0.05
    crit_f = f_inv_sf(alpha, df1, df2)
    recalculated_sf = f_sf(crit_f, df1, df2)
    assert abs(recalculated_sf - alpha) < 1e-10


def test_ncf_power_reduces_to_central_f_when_lambda_zero():
    df1, df2 = 4, 300
    f_crit = 2.4017397
    central_sf = f_sf(f_crit, df1, df2)
    ncf_at_zero = ncf_power(f_crit, df1, df2, lambda_nc=0.0)
    assert abs(central_sf - ncf_at_zero) < 1e-7
