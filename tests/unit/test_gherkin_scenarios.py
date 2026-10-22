"""Unit tests directly implementing the Gherkin scenarios defined in SPEC.md Section 8.

Each test is named after the corresponding scenario in SPEC.md Section 8:
1. Scenario: Typical Benchmark Calculation (Medium Effect, Standard Power)
2. Scenario: Group Divisibility Invariant
3. Scenario: Massive Effect Size Floor Limit
4. Scenario: Non-Integer Group Count Rounding
5. Scenario: Error Handling - Power Less Than Alpha
6. Scenario: Error Handling - Insufficient Groups
7. Scenario: Error Handling - Negative Effect Size
"""

import json
import subprocess
import sys
import unittest

from src.engine.anova_oneway import compute_a_priori, calculate_a_priori
from src.cli.contract_map import (
    KEY_N_TOTAL,
    KEY_N_PER_GROUP,
    KEY_DF1,
    KEY_DF2,
    KEY_NCP,
    KEY_CRITICAL,
    KEY_ACTUAL_POWER,
    KEY_ERROR,
)


def run_cli(*args):
    """Executes the CLI process and returns (returncode, stdout_str, stderr_str)."""
    cmd = [sys.executable, "-m", "src.cli.main"] + list(args)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def test_typical_benchmark_calculation_medium_effect_standard_power():
    """Scenario: Typical Benchmark Calculation (Medium Effect, Standard Power)

    Given test is "anova-oneway"
    And mode is "a-priori"
    And effect size f is 0.25
    And alpha is 0.05
    And desired power is 0.80
    And number of groups is 3
    When the analysis engine executes
    Then the response must be valid single-line JSON
    And exit code must be 0
    And "n_total" must equal 159
    And "n_per_group" must equal 53
    And "df1" must equal 2
    And "df2" must equal 156
    And "ncp" must equal 9.9375000 within 1e-4
    And "critical" must equal 3.0540042 within 1e-4
    And "actual_power" must equal 0.8048873 within 1e-4
    """
    # 1. Engine verification
    res = compute_a_priori(effect_size_f=0.25, alpha=0.05, target_power=0.80, groups=3)
    assert res.n_total == 159
    assert res.n_per_group == 53
    assert res.df1 == 2
    assert res.df2 == 156
    assert abs(res.ncp - 9.9375000) <= 1e-4
    assert abs(res.critical - 3.0540042) <= 1e-4
    assert abs(res.actual_power - 0.8048873) <= 1e-4

    # 2. CLI verification
    code, stdout, _ = run_cli(
        "--test", "anova-oneway",
        "--mode", "a-priori",
        "--f", "0.25",
        "--alpha", "0.05",
        "--power", "0.80",
        "--groups", "3",
    )
    assert code == 0
    assert "\n" not in stdout, "Response must be valid single-line JSON"
    data = json.loads(stdout)
    assert data[KEY_N_TOTAL] == 159
    assert data[KEY_N_PER_GROUP] == 53
    assert data[KEY_DF1] == 2
    assert data[KEY_DF2] == 156
    assert abs(data[KEY_NCP] - 9.9375000) <= 1e-4
    assert abs(data[KEY_CRITICAL] - 3.0540042) <= 1e-4
    assert abs(data[KEY_ACTUAL_POWER] - 0.8048873) <= 1e-4


def test_group_divisibility_invariant():
    """Scenario: Group Divisibility Invariant

    Given test is "anova-oneway"
    And mode is "a-priori"
    And number of groups is 5
    When sample size is computed for target power 0.95, alpha 0.05, f 0.25
    Then "n_total" must equal 305
    And "n_total" modulo 5 must equal 0
    And "actual_power" must be strictly greater than 0.95
    """
    res = compute_a_priori(effect_size_f=0.25, alpha=0.05, target_power=0.95, groups=5)
    assert res.n_total == 305
    assert res.n_total % 5 == 0
    assert res.actual_power > 0.95


def test_massive_effect_size_floor_limit():
    """Scenario: Massive Effect Size Floor Limit

    Given test is "anova-oneway"
    And mode is "a-priori"
    And effect size f is 5.0
    And alpha is 0.05
    And desired power is 0.95
    And number of groups is 3
    When the analysis engine executes
    Then "n_total" must not be less than 6
    And "n_per_group" must equal 2
    """
    res = compute_a_priori(effect_size_f=5.0, alpha=0.05, target_power=0.95, groups=3)
    assert res.n_total >= 6
    assert res.n_per_group == 2


def test_non_integer_group_count_rounding():
    """Scenario: Non-Integer Group Count Rounding

    Given test is "anova-oneway"
    And mode is "a-priori"
    And number of groups is 3.5
    And effect size f is 0.25
    And alpha is 0.05
    And desired power is 0.80
    When the analysis engine executes
    Then the engine must round groups to 4
    And "df1" must equal 3
    And "n_total" must equal 180
    """
    res = compute_a_priori(effect_size_f=0.25, alpha=0.05, target_power=0.80, groups=3.5)
    assert res.df1 == 3
    assert res.n_total == 180
    assert res.n_per_group == 45


def test_error_handling_power_less_than_alpha():
    """Scenario: Error Handling - Power Less Than Alpha

    Given test is "anova-oneway"
    And mode is "a-priori"
    And alpha is 0.05
    And desired power is 0.04
    When the CLI executes
    Then exit code must be non-zero
    And stdout must be single-line JSON
    And "error" must contain "Power must be greater than or equal to alpha"
    """
    code, stdout, _ = run_cli(
        "--test", "anova-oneway",
        "--mode", "a-priori",
        "--f", "0.25",
        "--alpha", "0.05",
        "--power", "0.04",
        "--groups", "3",
    )
    assert code != 0
    assert "\n" not in stdout, "Stdout must be single-line JSON"
    data = json.loads(stdout)
    assert KEY_ERROR in data
    assert "Power must be greater than or equal to alpha" in data[KEY_ERROR]


def test_error_handling_insufficient_groups():
    """Scenario: Error Handling - Insufficient Groups

    Given test is "anova-oneway"
    And number of groups is 1
    When the CLI executes
    Then exit code must be non-zero
    And stdout must be single-line JSON
    And "error" must contain "There must be at least 2 groups"
    """
    code, stdout, _ = run_cli(
        "--test", "anova-oneway",
        "--mode", "a-priori",
        "--f", "0.25",
        "--alpha", "0.05",
        "--power", "0.80",
        "--groups", "1",
    )
    assert code != 0
    assert "\n" not in stdout, "Stdout must be single-line JSON"
    data = json.loads(stdout)
    assert KEY_ERROR in data
    assert "There must be at least 2 groups" in data[KEY_ERROR]


def test_error_handling_negative_effect_size():
    """Scenario: Error Handling - Negative Effect Size

    Given test is "anova-oneway"
    And effect size f is -0.25
    When the CLI executes
    Then exit code must be non-zero
    And stdout must be single-line JSON
    And "error" must contain "outside the admissible range"
    """
    code, stdout, _ = run_cli(
        "--test", "anova-oneway",
        "--mode", "a-priori",
        "--f", "-0.25",
        "--alpha", "0.05",
        "--power", "0.80",
        "--groups", "3",
    )
    assert code != 0
    assert "\n" not in stdout, "Stdout must be single-line JSON"
    data = json.loads(stdout)
    assert KEY_ERROR in data
    assert "outside the admissible range" in data[KEY_ERROR]


class TestGherkinScenarios(unittest.TestCase):
    """TestCase wrapper enabling standard unittest test discovery."""
    def test_typical_benchmark_calculation_medium_effect_standard_power(self):
        test_typical_benchmark_calculation_medium_effect_standard_power()

    def test_group_divisibility_invariant(self):
        test_group_divisibility_invariant()

    def test_massive_effect_size_floor_limit(self):
        test_massive_effect_size_floor_limit()

    def test_non_integer_group_count_rounding(self):
        test_non_integer_group_count_rounding()

    def test_error_handling_power_less_than_alpha(self):
        test_error_handling_power_less_than_alpha()

    def test_error_handling_insufficient_groups(self):
        test_error_handling_insufficient_groups()

    def test_error_handling_negative_effect_size(self):
        test_error_handling_negative_effect_size()


if __name__ == "__main__":
    unittest.main()
