"""Contract tests verifying the CLI interface format against SPEC.md.

SPEC.md References:
- Section 2: Inputs, Ranges, Defaults, and Units (including aliases --effect-size and --k).
- Section 5: Exact output definitions (n_per_group, n_total, actual_power, critical, df1, df2, ncp).
- Section 6: Error handling and admissible ranges ({"error": "<description>"}, non-zero exit code).
- Section 7: Provisional CLI contract (invocation syntax, single-line JSON on stdout).
"""

import json
import subprocess
import sys
import unittest

from src.cli.contract_map import (
    KEY_N_PER_GROUP,
    KEY_N_TOTAL,
    KEY_ACTUAL_POWER,
    KEY_CRITICAL,
    KEY_DF1,
    KEY_DF2,
    KEY_NCP,
    KEY_ERROR,
)


def run_cli(*args):
    """Invokes the CLI and returns (returncode, stdout, stderr)."""
    cmd = [sys.executable, "-m", "src.cli.main"] + list(args)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def test_cli_success_format_and_keys():
    """Verifies that successful execution outputs strict single-line JSON with exact SPEC.md Section 5 keys."""
    ret, stdout, _ = run_cli(
        "--test", "anova-oneway",
        "--mode", "a-priori",
        "--f", "0.25",
        "--alpha", "0.05",
        "--power", "0.95",
        "--groups", "3",
    )
    assert ret == 0, f"Expected 0, got {ret}"
    assert "\n" not in stdout, "Output must be strictly single-line JSON"

    data = json.loads(stdout)
    expected_keys = {
        KEY_N_PER_GROUP,
        KEY_N_TOTAL,
        KEY_ACTUAL_POWER,
        KEY_CRITICAL,
        KEY_DF1,
        KEY_DF2,
        KEY_NCP,
    }
    assert set(data.keys()) == expected_keys, f"Keys mismatch. Expected {expected_keys}, got {set(data.keys())}"

    # Check SPEC.md Section 7 benchmark values
    assert data[KEY_N_PER_GROUP] == 84
    assert data[KEY_N_TOTAL] == 252
    assert data[KEY_DF1] == 2
    assert data[KEY_DF2] == 249
    assert abs(data[KEY_NCP] - 15.75) <= 1e-4
    assert abs(data[KEY_CRITICAL] - 3.0320649) <= 1e-4
    assert abs(data[KEY_ACTUAL_POWER] - 0.9514888) <= 1e-4


def test_cli_aliases_invocation():
    """Verifies that flag aliases (--effect-size and --k) work identically per SPEC.md Section 2 & 7."""
    ret, stdout, _ = run_cli(
        "--test", "anova-oneway",
        "--mode", "a-priori",
        "--effect-size", "0.25",
        "--alpha", "0.05",
        "--power", "0.95",
        "--k", "3",
    )
    assert ret == 0
    assert "\n" not in stdout
    data = json.loads(stdout)
    assert data[KEY_N_TOTAL] == 252
    assert data[KEY_N_PER_GROUP] == 84


def test_cli_missing_required_flag_returns_error_json():
    """Verifies that missing required arguments trigger non-zero exit and single-line JSON error."""
    ret, stdout, _ = run_cli(
        "--test", "anova-oneway",
        "--mode", "a-priori",
        "--f", "0.25",
    )
    assert ret != 0
    assert "\n" not in stdout
    data = json.loads(stdout)
    assert KEY_ERROR in data
    assert "Missing required argument" in data[KEY_ERROR]


def test_cli_error_power_below_alpha():
    """SPEC.md Section 6.4: Power strictly below alpha triggers error."""
    ret, stdout, _ = run_cli(
        "--test", "anova-oneway",
        "--mode", "a-priori",
        "--f", "0.25",
        "--alpha", "0.05",
        "--power", "0.04",
        "--groups", "3",
    )
    assert ret != 0
    assert "\n" not in stdout
    data = json.loads(stdout)
    assert KEY_ERROR in data
    assert data[KEY_ERROR] == "Power must be greater than or equal to alpha"


def test_cli_error_effect_size_out_of_range():
    """SPEC.md Section 6.1: Out of range effect size triggers error."""
    ret, stdout, _ = run_cli(
        "--test", "anova-oneway",
        "--mode", "a-priori",
        "--f", "-0.25",
        "--alpha", "0.05",
        "--power", "0.95",
        "--groups", "3",
    )
    assert ret != 0
    assert "\n" not in stdout
    data = json.loads(stdout)
    assert KEY_ERROR in data
    assert "Effect size f is outside the admissible range (1e-06, 50)" in data[KEY_ERROR]


def test_cli_error_non_numeric_effect_size():
    """SPEC.md Section 6.1: Non-numeric effect size text triggers error."""
    ret, stdout, _ = run_cli(
        "--test", "anova-oneway",
        "--mode", "a-priori",
        "--f", "not-a-number",
        "--alpha", "0.05",
        "--power", "0.95",
        "--groups", "3",
    )
    assert ret != 0
    assert "\n" not in stdout
    data = json.loads(stdout)
    assert KEY_ERROR in data
    assert "Effect size f is outside the admissible range (1e-06, 50)" in data[KEY_ERROR]


def test_cli_error_alpha_out_of_range():
    """SPEC.md Section 6.2: Out of range alpha triggers error."""
    for invalid_alpha in ["0.0", "1.0", "-0.05"]:
        ret, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "a-priori",
            "--f", "0.25",
            "--alpha", invalid_alpha,
            "--power", "0.95",
            "--groups", "3",
        )
        assert ret != 0
        assert "\n" not in stdout
        data = json.loads(stdout)
        assert KEY_ERROR in data
        assert "Alpha is outside the admissible range (1e-07, 1)" in data[KEY_ERROR]


def test_cli_error_power_out_of_range():
    """SPEC.md Section 6.3: Out of range power triggers error."""
    for invalid_power in ["0.0", "1.0"]:
        ret, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "a-priori",
            "--f", "0.25",
            "--alpha", "0.05",
            "--power", invalid_power,
            "--groups", "3",
        )
        assert ret != 0
        assert "\n" not in stdout
        data = json.loads(stdout)
        assert KEY_ERROR in data
        assert "Power is outside the admissible range (1e-07, 1)" in data[KEY_ERROR]


def test_cli_error_insufficient_groups():
    """SPEC.md Section 6.5: Group count < 2 triggers error."""
    for invalid_groups in ["1", "0", "-2"]:
        ret, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "a-priori",
            "--f", "0.25",
            "--alpha", "0.05",
            "--power", "0.95",
            "--groups", invalid_groups,
        )
        assert ret != 0
        assert "\n" not in stdout
        data = json.loads(stdout)
        assert KEY_ERROR in data
        assert "There must be at least 2 groups" in data[KEY_ERROR]


def test_cli_error_unsupported_test():
    """SPEC.md Section 1: Unsupported test identifier triggers error."""
    ret, stdout, _ = run_cli(
        "--test", "unknown-test",
        "--mode", "a-priori",
        "--f", "0.25",
        "--alpha", "0.05",
        "--power", "0.95",
        "--groups", "3",
    )
    assert ret != 0
    assert "\n" not in stdout
    data = json.loads(stdout)
    assert KEY_ERROR in data
    assert "Unsupported test" in data[KEY_ERROR]


def test_cli_error_unsupported_mode():
    """SPEC.md Section 1: Unsupported mode triggers error."""
    ret, stdout, _ = run_cli(
        "--test", "anova-oneway",
        "--mode", "invalid-mode",
        "--f", "0.25",
        "--alpha", "0.05",
        "--power", "0.95",
        "--groups", "3",
    )
    assert ret != 0
    assert "\n" not in stdout
    data = json.loads(stdout)
    assert KEY_ERROR in data
    assert "Invalid mode" in data[KEY_ERROR]


def test_cli_determinism():
    """Verifies that multiple runs produce bitwise identical single-line JSON outputs."""
    outputs = []
    for _ in range(3):
        ret, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "a-priori",
            "--f", "0.25",
            "--alpha", "0.05",
            "--power", "0.95",
            "--groups", "3",
        )
        assert ret == 0
        outputs.append(stdout)
    assert outputs[0] == outputs[1] == outputs[2]


class TestCliContract(unittest.TestCase):
    """TestCase wrapper enabling standard unittest test discovery."""
    def test_cli_success_format_and_keys(self):
        test_cli_success_format_and_keys()

    def test_cli_aliases_invocation(self):
        test_cli_aliases_invocation()

    def test_cli_missing_required_flag_returns_error_json(self):
        test_cli_missing_required_flag_returns_error_json()

    def test_cli_error_power_below_alpha(self):
        test_cli_error_power_below_alpha()

    def test_cli_error_effect_size_out_of_range(self):
        test_cli_error_effect_size_out_of_range()

    def test_cli_error_non_numeric_effect_size(self):
        test_cli_error_non_numeric_effect_size()

    def test_cli_error_alpha_out_of_range(self):
        test_cli_error_alpha_out_of_range()

    def test_cli_error_power_out_of_range(self):
        test_cli_error_power_out_of_range()

    def test_cli_error_insufficient_groups(self):
        test_cli_error_insufficient_groups()

    def test_cli_error_unsupported_test(self):
        test_cli_error_unsupported_test()

    def test_cli_error_unsupported_mode(self):
        test_cli_error_unsupported_mode()

    def test_cli_determinism(self):
        test_cli_determinism()


if __name__ == "__main__":
    unittest.main()
