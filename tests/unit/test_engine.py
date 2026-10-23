"""Unit tests for the one-way ANOVA pure calculation engine.

SPEC.md References:
- Section 1.1: Mode classification.
- Section 2.3: Inputs and admissible ranges.
- Section 4.1: Mathematical algorithm (df1, df2, noncentrality, critical_f, power).
- Section 4.2: A-priori search algorithm and divisibility rule.
- Section 4.3: Post-hoc power evaluation and average group size.
- Section 5.1 & 5.2: Error handling, refusal mappings, and integer rules.
"""

import math
import time
import unittest

from src.engine.anova_oneway import (
    compute_a_priori,
    compute_post_hoc,
    compute_compromise,
    compute_criterion,
    compute_sensitivity,
    calculate_a_priori,
    validate_effect_size,
    validate_alpha,
    validate_power,
    validate_groups,
    validate_n_total,
    EngineError,
)


def assert_numeric_close(actual: float, expected: float, tol: float = 1e-6):
    """SPEC.md tolerance rule: |a - b| <= 1e-6 OR relative difference <= 1e-6."""
    diff = abs(actual - expected)
    if diff <= tol:
        return
    rel = diff / max(abs(expected), 1e-15)
    if rel <= tol:
        return
    raise AssertionError(
        f"Numeric mismatch: actual={actual}, expected={expected}, abs_diff={diff}, rel_diff={rel}"
    )


class TestEngine(unittest.TestCase):
    """Pure engine unit tests."""

    def test_input_validation_negative_f(self):
        """SPEC.md Section 5.1 v042."""
        with self.assertRaises(EngineError) as ctx:
            validate_effect_size(-0.25)
        self.assertEqual(ctx.exception.code, "OUT_OF_RANGE")
        self.assertEqual(ctx.exception.field, "f")

    def test_input_validation_zero_f(self):
        """SPEC.md Section 5.1 v041."""
        with self.assertRaises(EngineError) as ctx:
            validate_effect_size(0.0)
        self.assertEqual(ctx.exception.code, "OUT_OF_RANGE")
        self.assertEqual(ctx.exception.field, "f")

    def test_input_validation_invalid_alpha(self):
        """SPEC.md Section 5.1 v039/v040."""
        for invalid_alpha in [0.0, 1.0, -0.05]:
            with self.assertRaises(EngineError) as ctx:
                validate_alpha(invalid_alpha)
            self.assertEqual(ctx.exception.code, "OUT_OF_RANGE")
            self.assertEqual(ctx.exception.field, "alpha")

    def test_input_validation_invalid_groups(self):
        """SPEC.md Section 5.1 v043/v044."""
        for invalid_groups in [1, 0, -2]:
            with self.assertRaises(EngineError) as ctx:
                validate_groups(invalid_groups)
            self.assertEqual(ctx.exception.code, "OUT_OF_RANGE")
            self.assertEqual(ctx.exception.field, "groups")

    def test_input_validation_non_integer_groups(self):
        """SPEC.md Section 5.2 item 1."""
        with self.assertRaises(EngineError) as ctx:
            validate_groups("3.5")
        self.assertEqual(ctx.exception.code, "INVALID_VALUE")
        self.assertEqual(ctx.exception.field, "groups")

    def test_a_priori_sample_size_divisibility(self):
        """SPEC.md Section 4.2: N_total is a multiple of group count k."""
        for k in [2, 3, 4, 5, 6]:
            res = compute_a_priori(effect_size_f=0.25, alpha=0.05, target_power=0.80, groups=k)
            self.assertEqual(res.n_total % k, 0)
            self.assertEqual(res.n_per_group, res.n_total // k)
            self.assertGreaterEqual(res.actual_power, 0.80)
            self.assertEqual(res.df1, k - 1)
            self.assertEqual(res.df2, res.n_total - k)
            assert_numeric_close(res.ncp, (0.25 ** 2) * res.n_total)

    def test_post_hoc_power(self):
        """SPEC.md Section 4.1 & 4.3 formulas."""
        res = compute_post_hoc(effect_size_f=0.25, alpha=0.05, n_total=305, groups=5)
        self.assertEqual(res.df1, 4)
        self.assertEqual(res.df2, 300)
        assert_numeric_close(res.ncp, 19.0625)
        assert_numeric_close(res.critical_f, 2.4017397)
        assert_numeric_close(res.power, 0.9521313)

    def test_post_hoc_inconsistent_sample_size(self):
        """SPEC.md Section 4.3 & 5.1: N_total <= k produces INCONSISTENT."""
        with self.assertRaises(EngineError) as ctx:
            compute_post_hoc(effect_size_f=0.25, alpha=0.05, n_total=5, groups=5)
        self.assertEqual(ctx.exception.code, "INCONSISTENT")
        self.assertEqual(ctx.exception.field, "n_total")

    def test_calculate_a_priori_pure_functional_interface(self):
        """Pure functional interface returning structured result or error."""
        res = calculate_a_priori(effect_size_f=0.25, alpha=0.05, target_power=0.80, groups=3)
        self.assertTrue(res.is_success)
        self.assertEqual(res.n_total, 159)
        self.assertEqual(res.df1, 2)
        self.assertEqual(res.df2, 156)

        err = calculate_a_priori(effect_size_f=-0.25, alpha=0.05, target_power=0.80, groups=3)
        self.assertFalse(err.is_success)
        self.assertEqual(err.code, "OUT_OF_RANGE")
        self.assertEqual(err.field, "f")

    # ========================================================================
    # Extremes, Stability, Monotonicity & Timing Tests (Prompt Item 2)
    # ========================================================================

    def test_boundary_inclusive_values_accepted(self):
        """SPEC.md Section 2.3 & 5.2 item 2: Exact boundary inclusivity."""
        # f = 1e-6 and f = 50.0 are accepted
        self.assertEqual(validate_effect_size(1e-6), 1e-6)
        self.assertEqual(validate_effect_size("1e-6"), 1e-6)
        self.assertEqual(validate_effect_size(50.0), 50.0)
        self.assertEqual(validate_effect_size("50.0"), 50.0)

        # alpha = 1e-7 is accepted
        self.assertEqual(validate_alpha(1e-7), 1e-7)
        self.assertEqual(validate_alpha("1e-7"), 1e-7)

        # power = 1e-7 is accepted
        self.assertEqual(validate_power(1e-7), 1e-7)
        self.assertEqual(validate_power("1e-7"), 1e-7)

        # groups = 2 is accepted
        self.assertEqual(validate_groups(2), 2)

        # n_total = 2147483647 is accepted
        self.assertEqual(validate_n_total(2147483647, 5), 2147483647)

    def test_boundary_exclusive_values_rejected(self):
        """SPEC.md Section 2.3 & 5.2: Values outside inclusive bounds rejected."""
        # f outside [1e-6, 50]
        with self.assertRaises(EngineError) as ctx:
            validate_effect_size(0.999e-6)
        self.assertEqual(ctx.exception.code, "OUT_OF_RANGE")

        with self.assertRaises(EngineError) as ctx:
            validate_effect_size(50.0001)
        self.assertEqual(ctx.exception.code, "OUT_OF_RANGE")

        # alpha outside [1e-7, 1)
        with self.assertRaises(EngineError) as ctx:
            validate_alpha(0.999e-7)
        self.assertEqual(ctx.exception.code, "OUT_OF_RANGE")

        with self.assertRaises(EngineError) as ctx:
            validate_alpha(1.0)
        self.assertEqual(ctx.exception.code, "OUT_OF_RANGE")

        # power outside [1e-7, 1)
        with self.assertRaises(EngineError) as ctx:
            validate_power(0.999e-7)
        self.assertEqual(ctx.exception.code, "OUT_OF_RANGE")

        with self.assertRaises(EngineError) as ctx:
            validate_power(1.0)
        self.assertEqual(ctx.exception.code, "OUT_OF_RANGE")

        # n_total > 2147483647
        with self.assertRaises(EngineError) as ctx:
            validate_n_total(2147483648, 5)
        self.assertEqual(ctx.exception.code, "OUT_OF_RANGE")

    def test_extremes_post_hoc_values(self):
        """Extremes: N = 2147483647, k = 100, f = 50, f = 1e-6, alpha = 1e-7, power near 1."""
        extreme_cases = [
            ("N=max, k=100, f=0.25, alpha=0.05", 0.25, 0.05, 2147483647, 100),
            ("N=max, k=100, f=50.0, alpha=0.05", 50.0, 0.05, 2147483647, 100),
            ("N=max, k=100, f=1e-6, alpha=0.05", 1e-6, 0.05, 2147483647, 100),
            ("N=max, k=100, f=0.25, alpha=1e-7", 0.25, 1e-7, 2147483647, 100),
            ("N=max, k=2, f=1e-6, alpha=1e-7", 1e-6, 1e-7, 2147483647, 2),
            ("power near 1 (N=1e6, f=0.5, alpha=0.05, k=5)", 0.5, 0.05, 1000000, 5),
            ("power near 1 (N=100000, f=50.0, alpha=0.05, k=100)", 50.0, 0.05, 100000, 100),
        ]

        for label, f_val, a_val, n_val, k_val in extreme_cases:
            t0 = time.time()
            res = compute_post_hoc(effect_size_f=f_val, alpha=a_val, n_total=n_val, groups=k_val)
            elapsed = time.time() - t0

            self.assertLess(elapsed, 2.0, f"Case {label} took {elapsed:.4f}s >= 2.0s")
            self.assertFalse(math.isnan(res.power), f"Case {label} produced NaN power")
            self.assertFalse(math.isinf(res.power), f"Case {label} produced inf power")
            self.assertFalse(math.isnan(res.critical_f), f"Case {label} produced NaN critical_f")
            self.assertFalse(math.isinf(res.critical_f), f"Case {label} produced inf critical_f")
            self.assertGreaterEqual(res.power, 0.0, f"Case {label} power < 0")
            self.assertLessEqual(res.power, 1.0, f"Case {label} power > 1")

    def test_extremes_a_priori_tiny_f(self):
        """Tiny f in a-priori mode: should either find solution or raise NO_SOLUTION."""
        # 1. Unachievable within 32-bit: power = 0.95 with f = 1e-6
        t0 = time.time()
        with self.assertRaises(EngineError) as ctx:
            compute_a_priori(effect_size_f=1e-6, alpha=0.05, target_power=0.95, groups=5)
        elapsed = time.time() - t0
        self.assertLess(elapsed, 2.0)
        self.assertEqual(ctx.exception.code, "NO_SOLUTION")

        # 2. Achievable within 32-bit: power = 0.05001 with f = 1e-6
        t0 = time.time()
        res = compute_a_priori(effect_size_f=1e-6, alpha=0.05, target_power=0.05001, groups=5)
        elapsed = time.time() - t0
        self.assertLess(elapsed, 2.0)
        self.assertLessEqual(res.n_total, 2147483647)
        self.assertGreaterEqual(res.actual_power, 0.05001)
        self.assertFalse(math.isnan(res.actual_power))
        self.assertFalse(math.isinf(res.actual_power))
        self.assertGreaterEqual(res.actual_power, 0.0)
        self.assertLessEqual(res.actual_power, 1.0)

        # 3. Large f = 50.0: should return minimal n = 2 per group (N = 10)
        t0 = time.time()
        res_large = compute_a_priori(effect_size_f=50.0, alpha=0.05, target_power=0.95, groups=5)
        elapsed = time.time() - t0
        self.assertLess(elapsed, 2.0)
        self.assertEqual(res_large.n_total, 10)
        self.assertEqual(res_large.n_per_group, 2)
        assert_numeric_close(res_large.actual_power, 1.0)

    def test_power_monotone_in_sample_size(self):
        """Statistical power must be non-decreasing with respect to total sample size N."""
        configs = [
            (0.25, 0.05, 5),
            (0.1, 0.01, 3),
            (0.5, 0.05, 10),
            (1e-4, 0.05, 4),
        ]
        n_sequence = [15, 30, 60, 100, 300, 1000, 5000, 20000, 100000, 1000000, 2147483647]

        for f_val, a_val, k_val in configs:
            prev_power = -1.0
            for n_val in n_sequence:
                if n_val <= k_val:
                    continue
                t0 = time.time()
                res = compute_post_hoc(effect_size_f=f_val, alpha=a_val, n_total=n_val, groups=k_val)
                elapsed = time.time() - t0
                self.assertLess(elapsed, 2.0)
                self.assertFalse(math.isnan(res.power))
                self.assertFalse(math.isinf(res.power))
                self.assertGreaterEqual(res.power, 0.0)
                self.assertLessEqual(res.power, 1.0)
                self.assertGreaterEqual(
                    res.power,
                    prev_power - 1e-12,
                    f"Monotonicity failed for ({f_val}, {a_val}, {k_val}) at N={n_val}: {res.power} < {prev_power}"
                )
                prev_power = res.power


if __name__ == "__main__":
    unittest.main()
