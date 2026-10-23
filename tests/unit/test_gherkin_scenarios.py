"""Gherkin acceptance scenarios from SPEC.md Section 6.

SPEC.md References:
- Section 6.1: General Contract & CLI Rule Scenarios (10 scenarios).
- Section 6.2: Public Reference Vectors for anova-oneway (5 scenarios).
"""

import json
import subprocess
import sys
import unittest


def run_cli(*args):
    """Executes the CLI process and returns (returncode, stdout_str, stderr_str)."""
    cmd = [sys.executable, "-m", "src.cli.main"] + list(args)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def assert_numeric_close(actual: float, expected: float, tol: float = 1e-6):
    """SPEC.md tolerance: |a - b| <= 1e-6 OR relative difference <= 1e-6."""
    diff = abs(actual - expected)
    if diff <= tol:
        return
    rel = diff / max(abs(expected), 1e-15)
    if rel <= tol:
        return
    raise AssertionError(
        f"Numeric mismatch: actual={actual}, expected={expected}, abs_diff={diff}, rel_diff={rel}"
    )


def assert_integer(val: Any):
    """SPEC.md Section 2.4: Exact integer type."""
    assert isinstance(val, int) and not isinstance(val, bool), f"Expected int, got {type(val)}: {val}"


class TestGherkinScenarios(unittest.TestCase):
    """One test per Gherkin scenario in SPEC.md, named after the scenario."""

    # ========================================================================
    # SPEC.md Section 6.1: General Contract & CLI Rule Scenarios
    # ========================================================================

    def test_version_query(self):
        """Scenario: Version Query (SPEC.md Section 6.1)."""
        code, stdout, _ = run_cli("--version")
        self.assertEqual(code, 0)
        self.assertNotIn("\n", stdout)
        data = json.loads(stdout)
        self.assertEqual(data.get("contract_version"), "1.0.0")
        self.assertIn("name", data)
        self.assertIn("engine", data)

    def test_error_handling_missing_required_parameter(self):
        """Scenario: Error Handling - Missing Required Parameter (SPEC.md Section 6.1)."""
        code, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "a-priori",
            "--f", "0.25",
            "--alpha", "0.05",
            "--groups", "5",
        )
        self.assertEqual(code, 2)
        self.assertNotIn("\n", stdout)
        data = json.loads(stdout)
        self.assertEqual(data.get("code"), "MISSING_PARAM")
        self.assertEqual(data.get("field"), "power")
        self.assertIn("error", data)

    def test_error_handling_unknown_irrelevant_parameter_in_post_hoc(self):
        """Scenario: Error Handling - Unknown / Irrelevant Parameter in Post-Hoc (SPEC.md Section 6.1)."""
        code, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "post-hoc",
            "--f", "0.25",
            "--alpha", "0.05",
            "--n_total", "100",
            "--groups", "5",
            "--power", "0.95",
        )
        self.assertEqual(code, 2)
        self.assertNotIn("\n", stdout)
        data = json.loads(stdout)
        self.assertEqual(data.get("code"), "UNKNOWN_PARAM")
        self.assertEqual(data.get("field"), "power")
        self.assertIn("error", data)

    def test_error_handling_invalid_value_float_for_integer_group_count(self):
        """Scenario: Error Handling - Invalid Value (Float for Integer Group Count) (SPEC.md Section 6.1)."""
        code, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "a-priori",
            "--f", "0.25",
            "--alpha", "0.05",
            "--power", "0.95",
            "--groups", "3.5",
        )
        self.assertEqual(code, 2)
        self.assertNotIn("\n", stdout)
        data = json.loads(stdout)
        self.assertEqual(data.get("code"), "INVALID_VALUE")
        self.assertEqual(data.get("field"), "groups")
        self.assertIn("error", data)

    def test_error_handling_out_of_range_effect_size(self):
        """Scenario: Error Handling - Out of Range Effect Size (SPEC.md Section 6.1)."""
        code, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "a-priori",
            "--f", "-0.25",
            "--alpha", "0.05",
            "--power", "0.95",
            "--groups", "5",
        )
        self.assertEqual(code, 2)
        self.assertNotIn("\n", stdout)
        data = json.loads(stdout)
        self.assertEqual(data.get("code"), "OUT_OF_RANGE")
        self.assertEqual(data.get("field"), "f")

    def test_error_handling_out_of_range_alpha_boundary(self):
        """Scenario: Error Handling - Out of Range Alpha Boundary (SPEC.md Section 6.1)."""
        code, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "a-priori",
            "--f", "0.25",
            "--alpha", "0.0",
            "--power", "0.95",
            "--groups", "5",
        )
        self.assertEqual(code, 2)
        self.assertNotIn("\n", stdout)
        data = json.loads(stdout)
        self.assertEqual(data.get("code"), "OUT_OF_RANGE")
        self.assertEqual(data.get("field"), "alpha")

    def test_error_handling_inconsistent_parameters_power_less_than_alpha(self):
        """Scenario: Error Handling - Inconsistent Parameters (Power Less Than Alpha) (SPEC.md Section 6.1)."""
        code, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "a-priori",
            "--f", "0.25",
            "--alpha", "0.05",
            "--power", "0.04",
            "--groups", "5",
        )
        self.assertEqual(code, 2)
        self.assertNotIn("\n", stdout)
        data = json.loads(stdout)
        self.assertEqual(data.get("code"), "INCONSISTENT")
        self.assertEqual(data.get("field"), "power")

    def test_error_handling_post_hoc_sample_size_less_than_or_equal_to_groups(self):
        """Scenario: Error Handling - Post-Hoc Sample Size Less Than or Equal to Groups (SPEC.md Section 6.1)."""
        code, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "post-hoc",
            "--f", "0.25",
            "--alpha", "0.05",
            "--n_total", "5",
            "--groups", "5",
        )
        self.assertEqual(code, 2)
        self.assertNotIn("\n", stdout)
        data = json.loads(stdout)
        self.assertEqual(data.get("code"), "INCONSISTENT")
        self.assertEqual(data.get("field"), "n_total")

    def test_error_handling_unsupported_test_family(self):
        """Scenario: Error Handling - Unsupported Test Family (SPEC.md Section 6.1)."""
        code, stdout, _ = run_cli(
            "--test", "non-existent-test",
            "--mode", "a-priori",
            "--f", "0.25",
            "--alpha", "0.05",
            "--power", "0.95",
            "--groups", "5",
        )
        self.assertEqual(code, 2)
        self.assertNotIn("\n", stdout)
        data = json.loads(stdout)
        self.assertEqual(data.get("code"), "UNSUPPORTED")
        self.assertEqual(data.get("field"), "test")

    def test_post_hoc_calculation_with_sample_size_not_divisible_by_groups(self):
        """Scenario: Post-Hoc Calculation with Sample Size Not Divisible by Groups (SPEC.md Section 6.1)."""
        code, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "post-hoc",
            "--f", "0.25",
            "--alpha", "0.05",
            "--n_total", "61",
            "--groups", "5",
        )
        self.assertEqual(code, 0)
        self.assertNotIn("\n", stdout)
        data = json.loads(stdout)
        assert_integer(data["df1"])
        assert_integer(data["df2"])
        self.assertEqual(data["df1"], 4)
        self.assertEqual(data["df2"], 56)
        self.assertIn("power", data)

    # ========================================================================
    # SPEC.md Section 6.2: Official Instructor Public Reference Vectors
    # ========================================================================

    def test_official_vector_anova_oneway_a_priori(self):
        """Scenario: Official Vector - anova-oneway a-priori (SPEC.md Section 6.2)."""
        code, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "a-priori",
            "--f", "0.25",
            "--alpha", "0.05",
            "--power", "0.95",
            "--groups", "5",
        )
        self.assertEqual(code, 0)
        self.assertNotIn("\n", stdout)
        data = json.loads(stdout)
        assert_integer(data["df1"])
        assert_integer(data["df2"])
        assert_integer(data["n_total"])
        self.assertEqual(data["df1"], 4)
        self.assertEqual(data["df2"], 300)
        self.assertEqual(data["n_total"], 305)
        assert_numeric_close(data["ncp"], 19.0625000)
        assert_numeric_close(data["critical_f"], 2.4017397)
        assert_numeric_close(data["actual_power"], 0.9521313)

    def test_official_vector_anova_oneway_post_hoc(self):
        """Scenario: Official Vector - anova-oneway post-hoc (SPEC.md Section 6.2)."""
        code, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "post-hoc",
            "--f", "0.25",
            "--alpha", "0.05",
            "--n_total", "100",
            "--groups", "5",
        )
        self.assertEqual(code, 0)
        self.assertNotIn("\n", stdout)
        data = json.loads(stdout)
        assert_integer(data["df1"])
        assert_integer(data["df2"])
        self.assertEqual(data["df1"], 4)
        self.assertEqual(data["df2"], 95)
        assert_numeric_close(data["ncp"], 6.2500000)
        assert_numeric_close(data["critical_f"], 2.4674936)
        assert_numeric_close(data["power"], 0.4663312)

    def test_official_vector_anova_oneway_compromise_deferred_later(self):
        """Scenario: Official Vector - anova-oneway compromise (Deferred / Later) (SPEC.md Section 6.2)."""
        code, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "compromise",
            "--f", "0.25",
            "--beta_alpha_ratio", "1",
            "--n_total", "100",
            "--groups", "5",
        )
        self.assertEqual(code, 0)
        self.assertNotIn("\n", stdout)
        data = json.loads(stdout)
        assert_integer(data["df1"])
        assert_integer(data["df2"])
        self.assertEqual(data["df1"], 4)
        self.assertEqual(data["df2"], 95)
        assert_numeric_close(data["ncp"], 6.2500000)
        assert_numeric_close(data["critical_f"], 1.4272492)
        assert_numeric_close(data["alpha"], 0.2309247)
        assert_numeric_close(data["beta"], 0.2309247)
        assert_numeric_close(data["power"], 0.7690753)

    def test_official_vector_anova_oneway_criterion_deferred_later(self):
        """Scenario: Official Vector - anova-oneway criterion (Deferred / Later) (SPEC.md Section 6.2)."""
        code, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "criterion",
            "--f", "0.25",
            "--power", "0.95",
            "--n_total", "100",
            "--groups", "5",
        )
        self.assertEqual(code, 0)
        self.assertNotIn("\n", stdout)
        data = json.loads(stdout)
        assert_integer(data["df1"])
        assert_integer(data["df2"])
        self.assertEqual(data["df1"], 4)
        self.assertEqual(data["df2"], 95)
        assert_numeric_close(data["ncp"], 6.2500000)
        assert_numeric_close(data["critical_f"], 0.6552638)
        assert_numeric_close(data["alpha"], 0.6245994)

    def test_official_vector_anova_oneway_sensitivity_deferred_later(self):
        """Scenario: Official Vector - anova-oneway sensitivity (Deferred / Later) (SPEC.md Section 6.2)."""
        code, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "sensitivity",
            "--alpha", "0.05",
            "--power", "0.95",
            "--n_total", "100",
            "--groups", "5",
        )
        self.assertEqual(code, 0)
        self.assertNotIn("\n", stdout)
        data = json.loads(stdout)
        assert_integer(data["df1"])
        assert_integer(data["df2"])
        self.assertEqual(data["df1"], 4)
        self.assertEqual(data["df2"], 95)
        assert_numeric_close(data["ncp"], 19.5245874)
        assert_numeric_close(data["critical_f"], 2.4674936)
        assert_numeric_close(data["f"], 0.4418664)

    # ========================================================================
    # SPEC.md Section 6.3: Post-Hoc Boundary and Asymptotic Power Scenarios
    # ========================================================================

    def test_post_hoc_asymptotic_power_at_large_sample_size_n_100000(self):
        """Scenario: Post-Hoc Asymptotic Power at Large Sample Size N = 100000 (SPEC.md Section 6.3)."""
        code, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "post-hoc",
            "--f", "0.25",
            "--alpha", "0.05",
            "--n_total", "100000",
            "--groups", "5",
        )
        self.assertEqual(code, 0)
        self.assertNotIn("\n", stdout)
        data = json.loads(stdout)
        assert_integer(data["df1"])
        assert_integer(data["df2"])
        self.assertEqual(data["df1"], 4)
        self.assertEqual(data["df2"], 99995)
        assert_numeric_close(data["ncp"], 6250.0)
        assert_numeric_close(data["critical_f"], 2.3720211)
        assert_numeric_close(data["power"], 1.0000000)

    def test_post_hoc_asymptotic_power_at_large_sample_size_n_1000000(self):
        """Scenario: Post-Hoc Asymptotic Power at Large Sample Size N = 1000000 (SPEC.md Section 6.3)."""
        code, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "post-hoc",
            "--f", "0.25",
            "--alpha", "0.05",
            "--n_total", "1000000",
            "--groups", "5",
        )
        self.assertEqual(code, 0)
        self.assertNotIn("\n", stdout)
        data = json.loads(stdout)
        assert_integer(data["df1"])
        assert_integer(data["df2"])
        self.assertEqual(data["df1"], 4)
        self.assertEqual(data["df2"], 999995)
        assert_numeric_close(data["ncp"], 62500.0)
        assert_numeric_close(data["critical_f"], 2.3719411)
        assert_numeric_close(data["power"], 1.0000000)

    def test_post_hoc_asymptotic_power_at_large_sample_size_n_10000000(self):
        """Scenario: Post-Hoc Asymptotic Power at Large Sample Size N = 10000000 (SPEC.md Section 6.3)."""
        code, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "post-hoc",
            "--f", "0.25",
            "--alpha", "0.05",
            "--n_total", "10000000",
            "--groups", "5",
        )
        self.assertEqual(code, 0)
        self.assertNotIn("\n", stdout)
        data = json.loads(stdout)
        assert_integer(data["df1"])
        assert_integer(data["df2"])
        self.assertEqual(data["df1"], 4)
        self.assertEqual(data["df2"], 9999995)
        assert_numeric_close(data["ncp"], 625000.0)
        assert_numeric_close(data["critical_f"], 2.3719331)
        assert_numeric_close(data["power"], 1.0000000)

    def test_post_hoc_maximum_admissible_effect_size_boundary_f_50(self):
        """Scenario: Post-Hoc Maximum Admissible Effect Size Boundary f = 50.0 (SPEC.md Section 6.3)."""
        code, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "post-hoc",
            "--f", "50.0",
            "--alpha", "0.05",
            "--n_total", "10",
            "--groups", "5",
        )
        self.assertEqual(code, 0)
        self.assertNotIn("\n", stdout)
        data = json.loads(stdout)
        assert_integer(data["df1"])
        assert_integer(data["df2"])
        self.assertEqual(data["df1"], 4)
        self.assertEqual(data["df2"], 5)
        assert_numeric_close(data["ncp"], 25000.0)
        assert_numeric_close(data["critical_f"], 5.1921678)
        assert_numeric_close(data["power"], 1.0000000)

    def test_post_hoc_lower_significance_boundary_alpha_1e_7(self):
        """Scenario: Post-Hoc Lower Significance Boundary Alpha = 1e-7 (SPEC.md Section 6.3)."""
        code, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "post-hoc",
            "--f", "0.25",
            "--alpha", "0.0000001",
            "--n_total", "100",
            "--groups", "5",
        )
        self.assertEqual(code, 0)
        self.assertNotIn("\n", stdout)
        data = json.loads(stdout)
        assert_integer(data["df1"])
        assert_integer(data["df2"])
        self.assertEqual(data["df1"], 4)
        self.assertEqual(data["df2"], 95)
        assert_numeric_close(data["ncp"], 6.2500000)
        assert_numeric_close(data["critical_f"], 11.6273196)
        assert_numeric_close(data["power"], 0.0002068239)


if __name__ == "__main__":
    unittest.main()
