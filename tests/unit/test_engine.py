"""Unit tests for the one-way ANOVA calculation engine.

SPEC.md References:
- Section 2: Input ranges and defaults.
- Section 3: Distribution and degrees of freedom formulas.
- Section 4: Search and stopping rules.
- Section 5: Exact output definitions.
- Section 6: Error handling and admissible ranges.
"""

import unittest

from src.engine.anova_oneway import (
    compute_a_priori,
    compute_post_hoc,
    calculate_a_priori,
    validate_anova_inputs,
    CalculationError,
)


def test_input_validation_negative_f():
    # SPEC.md Section 6.1
    try:
        validate_anova_inputs(effect_size_f=-0.25, alpha=0.05, groups=3, power=0.8)
        assert False, "Should raise on negative f"
    except CalculationError as e:
        assert "outside the admissible range" in e.error


def test_input_validation_zero_f():
    # SPEC.md Section 6.1
    try:
        validate_anova_inputs(effect_size_f=0.0, alpha=0.05, groups=3, power=0.8)
        assert False, "Should raise on zero f"
    except CalculationError as e:
        assert "outside the admissible range" in e.error


def test_input_validation_invalid_alpha():
    # SPEC.md Section 6.2
    try:
        validate_anova_inputs(effect_size_f=0.25, alpha=0.0, groups=3, power=0.8)
        assert False, "Should raise on zero alpha"
    except CalculationError as e:
        assert "outside the admissible range" in e.error

    try:
        validate_anova_inputs(effect_size_f=0.25, alpha=1.0, groups=3, power=0.8)
        assert False, "Should raise on alpha = 1.0"
    except CalculationError as e:
        assert "outside the admissible range" in e.error


def test_input_validation_invalid_groups():
    # SPEC.md Section 6.5
    try:
        validate_anova_inputs(effect_size_f=0.25, alpha=0.05, groups=1, power=0.8)
        assert False, "Should raise on groups < 2"
    except CalculationError as e:
        assert "There must be at least 2 groups" in e.error


def test_a_priori_sample_size_divisibility():
    # SPEC.md Section 4: N is a multiple of k
    for k in [2, 3, 4, 5, 6]:
        res = compute_a_priori(effect_size_f=0.25, alpha=0.05, target_power=0.80, groups=k)
        assert res.n_total % k == 0
        assert res.n_per_group == res.n_total // k
        assert res.actual_power >= 0.80
        assert res.df1 == k - 1
        assert res.df2 == res.n_total - k
        assert abs(res.ncp - (0.25 ** 2) * res.n_total) < 1e-9


def test_post_hoc_power():
    # SPEC.md Section 3 formulas
    res = compute_post_hoc(effect_size_f=0.25, alpha=0.05, n_total=305, groups=5)
    assert res.df1 == 4
    assert res.df2 == 300
    assert abs(res.ncp - 19.0625) < 1e-9
    assert abs(res.critical - 2.4017397) < 1e-5
    assert abs(res.actual_power - 0.9521313) < 1e-5


def test_calculate_a_priori_pure_interface():
    # Pure interface returning structured result or error
    res = calculate_a_priori(effect_size_f=0.25, alpha=0.05, target_power=0.80, groups=3)
    assert res.is_success is True
    assert res.n_total == 159

    err = calculate_a_priori(effect_size_f=-0.25, alpha=0.05, target_power=0.80, groups=3)
    assert err.is_success is False
    assert "outside the admissible range" in err.error


class TestEngine(unittest.TestCase):
    """TestCase wrapper enabling standard unittest test discovery."""
    def test_input_validation_negative_f(self):
        test_input_validation_negative_f()

    def test_input_validation_zero_f(self):
        test_input_validation_zero_f()

    def test_input_validation_invalid_alpha(self):
        test_input_validation_invalid_alpha()

    def test_input_validation_invalid_groups(self):
        test_input_validation_invalid_groups()

    def test_a_priori_sample_size_divisibility(self):
        test_a_priori_sample_size_divisibility()

    def test_post_hoc_power(self):
        test_post_hoc_power()

    def test_calculate_a_priori_pure_interface(self):
        test_calculate_a_priori_pure_interface()


if __name__ == "__main__":
    unittest.main()
