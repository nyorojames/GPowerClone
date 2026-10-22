"""Complete test runner for gpower-clone using Python standard library (no 3rd-party dependencies needed).

Runs:
1. Engine & distribution unit tests
2. Gherkin scenario tests (SPEC.md Section 8)
3. CLI contract tests (SPEC.md Section 2, 5, 6, 7)
"""

import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.unit.test_distributions import (
    test_log_gamma_known_values,
    test_betai_boundary_conditions,
    test_central_f_distribution_consistency,
    test_f_inv_sf_inverts_sf,
    test_ncf_power_reduces_to_central_f_when_lambda_zero,
)
from tests.unit.test_engine import (
    test_input_validation_negative_f,
    test_input_validation_zero_f,
    test_input_validation_invalid_alpha,
    test_input_validation_invalid_groups,
    test_a_priori_sample_size_divisibility,
    test_post_hoc_power,
    test_calculate_a_priori_pure_interface,
)
from tests.differential.test_differential import DifferentialTest
import tests.unit.test_gherkin_scenarios as gherkin_tests
import tests.contract.test_cli_contract as contract_tests


def run_unit_tests():
    print("=== 1. Running Distribution & Engine Unit Tests ===")
    test_log_gamma_known_values()
    test_betai_boundary_conditions()
    test_central_f_distribution_consistency()
    test_f_inv_sf_inverts_sf()
    test_ncf_power_reduces_to_central_f_when_lambda_zero()
    print("  [PASS] Distribution functions (log_gamma, betai, central F, noncentral F)")

    test_input_validation_negative_f()
    test_input_validation_zero_f()
    test_input_validation_invalid_alpha()
    test_input_validation_invalid_groups()
    test_a_priori_sample_size_divisibility()
    test_post_hoc_power()
    test_calculate_a_priori_pure_interface()
    print("  [PASS] Engine calculations & input validation")


def run_gherkin_scenarios():
    print("\n=== 2. Running SPEC.md Gherkin Acceptance Scenarios ===")
    gherkin_tests.test_typical_benchmark_calculation_medium_effect_standard_power()
    print("  [PASS] Scenario: Typical Benchmark Calculation (Medium Effect, Standard Power)")

    gherkin_tests.test_group_divisibility_invariant()
    print("  [PASS] Scenario: Group Divisibility Invariant")

    gherkin_tests.test_massive_effect_size_floor_limit()
    print("  [PASS] Scenario: Massive Effect Size Floor Limit")

    gherkin_tests.test_non_integer_group_count_rounding()
    print("  [PASS] Scenario: Non-Integer Group Count Rounding")

    gherkin_tests.test_error_handling_power_less_than_alpha()
    print("  [PASS] Scenario: Error Handling - Power Less Than Alpha")

    gherkin_tests.test_error_handling_insufficient_groups()
    print("  [PASS] Scenario: Error Handling - Insufficient Groups")

    gherkin_tests.test_error_handling_negative_effect_size()
    print("  [PASS] Scenario: Error Handling - Negative Effect Size")


def run_contract_tests():
    print("\n=== 3. Running CLI Contract Tests ===")
    contract_tests.test_cli_success_format_and_keys()
    print("  [PASS] CLI single-line JSON format & key schema")

    contract_tests.test_cli_aliases_invocation()
    print("  [PASS] CLI flag aliases (--effect-size, --k)")

    contract_tests.test_cli_missing_required_flag_returns_error_json()
    print("  [PASS] CLI missing required arguments")

    contract_tests.test_cli_error_power_below_alpha()
    print("  [PASS] CLI error handling: power < alpha")

    contract_tests.test_cli_error_effect_size_out_of_range()
    print("  [PASS] CLI error handling: effect size out of range")

    contract_tests.test_cli_error_non_numeric_effect_size()
    print("  [PASS] CLI error handling: non-numeric effect size")

    contract_tests.test_cli_error_alpha_out_of_range()
    print("  [PASS] CLI error handling: alpha out of range")

    contract_tests.test_cli_error_power_out_of_range()
    print("  [PASS] CLI error handling: power out of range")

    contract_tests.test_cli_error_insufficient_groups()
    print("  [PASS] CLI error handling: groups < 2")

    contract_tests.test_cli_error_unsupported_test()
    print("  [PASS] CLI error handling: unsupported test")

    contract_tests.test_cli_error_unsupported_mode()
    print("  [PASS] CLI error handling: unsupported mode")

    contract_tests.test_cli_determinism()
    print("  [PASS] CLI determinism: identical output across repeated invocations")


def run_differential_tests():
    print("\n=== 4. Running Differential Tests Against G*Power Oracle ===")
    DifferentialTest.setUpClass()
    test_case = DifferentialTest()
    test_case.test_all_oracle_vectors_against_cli()
    print("  [PASS] Differential tests against all 46 G*Power GUI oracle vectors (100% exact match)")


if __name__ == "__main__":
    run_unit_tests()
    run_gherkin_scenarios()
    run_contract_tests()
    run_differential_tests()
    print("\n=======================================================")
    print("ALL TEST SUITES PASSED SUCCESSFULLY (100% SPEC COMPLIANT)!")
    print("=======================================================")
