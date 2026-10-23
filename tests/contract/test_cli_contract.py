"""Contract tests verifying the CLI interface format against SPEC.md.

SPEC.md References:
- Section 2.1: Command line invocation, formatting, single-line JSON on stdout, exit codes.
- Section 2.2: Version query.
- Section 2.3: Inputs, output field definitions for anova-oneway.
- Section 2.4: Numeric data representation (raw double precision, exact integers).
- Section 3.1 & 3.2: Error JSON format and the seven error codes.
"""

import json
import subprocess
import sys
import time
import unittest


def run_cli(*args):
    """Invokes the CLI and returns (returncode, stdout, stderr)."""
    cmd = [sys.executable, "-m", "src.cli.main"] + list(args)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


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


class TestCliContract(unittest.TestCase):
    """Comprehensive contract tests for gpower-clone CLI."""

    def test_version_query(self):
        """SPEC.md Section 2.2: Version query returns exact single-line JSON, exit code 0."""
        ret, stdout, stderr = run_cli("--version")
        self.assertEqual(ret, 0)
        self.assertNotIn("\n", stdout)
        self.assertEqual(stderr, "")
        data = json.loads(stdout)
        self.assertEqual(data.get("contract_version"), "1.0.0")
        self.assertIn("name", data)
        self.assertIn("engine", data)

    def test_stdout_single_line_json_and_exit_code_zero_on_success(self):
        """SPEC.md Section 2.1: Exactly one line of JSON on stdout, nothing else, exit code 0."""
        ret, stdout, stderr = run_cli(
            "--test", "anova-oneway",
            "--mode", "a-priori",
            "--f", "0.25",
            "--alpha", "0.05",
            "--power", "0.95",
            "--groups", "5",
        )
        self.assertEqual(ret, 0)
        self.assertNotIn("\n", stdout)
        # Parse stdout as valid JSON
        data = json.loads(stdout)
        self.assertIsInstance(data, dict)

    def test_output_key_names_and_integer_types_a_priori(self):
        """SPEC.md Section 2.3 & 2.4: Exact key names and exact integer types."""
        ret, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "a-priori",
            "--f", "0.25",
            "--alpha", "0.05",
            "--power", "0.95",
            "--groups", "5",
        )
        self.assertEqual(ret, 0)
        data = json.loads(stdout)

        # SPEC.md Section 2.3 keys
        required_keys = {"ncp", "critical_f", "df1", "df2", "n_total", "actual_power"}
        self.assertTrue(required_keys.issubset(set(data.keys())))

        # SPEC.md Section 2.4: Integer fields must be exact JSON integers
        self.assertIsInstance(data["df1"], int)
        self.assertNotIsInstance(data["df1"], bool)
        self.assertIsInstance(data["df2"], int)
        self.assertNotIsInstance(data["df2"], bool)
        self.assertIsInstance(data["n_total"], int)
        self.assertNotIsInstance(data["n_total"], bool)

        # SPEC.md Section 2.4: Full double precision floats
        self.assertIsInstance(data["critical_f"], float)
        self.assertIsInstance(data["actual_power"], float)
        self.assertIsInstance(data["ncp"], float)

    def test_output_key_names_and_integer_types_post_hoc(self):
        """SPEC.md Section 2.3 & 2.4: Post-hoc key names and exact integer types."""
        ret, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "post-hoc",
            "--f", "0.25",
            "--alpha", "0.05",
            "--n_total", "100",
            "--groups", "5",
        )
        self.assertEqual(ret, 0)
        data = json.loads(stdout)

        required_keys = {"ncp", "critical_f", "df1", "df2", "power"}
        self.assertTrue(required_keys.issubset(set(data.keys())))

        self.assertIsInstance(data["df1"], int)
        self.assertIsInstance(data["df2"], int)
        self.assertIsInstance(data["power"], float)

    def test_missing_required_param_returns_exit_code_2(self):
        """SPEC.md Section 3.2: Missing required field produces MISSING_PARAM and exit code 2."""
        ret, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "a-priori",
            "--f", "0.25",
            "--alpha", "0.05",
            "--groups", "5",
        )
        self.assertEqual(ret, 2)
        self.assertNotIn("\n", stdout)
        data = json.loads(stdout)
        self.assertEqual(data.get("code"), "MISSING_PARAM")
        self.assertEqual(data.get("field"), "power")
        self.assertIn("error", data)

    def test_unknown_or_mode_irrelevant_param_returns_exit_code_2(self):
        """SPEC.md Section 3.2: Mode-irrelevant parameter produces UNKNOWN_PARAM and exit code 2."""
        ret, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "post-hoc",
            "--f", "0.25",
            "--alpha", "0.05",
            "--n_total", "100",
            "--groups", "5",
            "--power", "0.95",
        )
        self.assertEqual(ret, 2)
        self.assertNotIn("\n", stdout)
        data = json.loads(stdout)
        self.assertEqual(data.get("code"), "UNKNOWN_PARAM")
        self.assertEqual(data.get("field"), "power")
        self.assertIn("error", data)

    def test_invalid_value_non_integer_group_returns_exit_code_2(self):
        """SPEC.md Section 3.2 & 5.2 item 1: Float for integer field produces INVALID_VALUE."""
        ret, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "a-priori",
            "--f", "0.25",
            "--alpha", "0.05",
            "--power", "0.95",
            "--groups", "3.5",
        )
        self.assertEqual(ret, 2)
        self.assertNotIn("\n", stdout)
        data = json.loads(stdout)
        self.assertEqual(data.get("code"), "INVALID_VALUE")
        self.assertEqual(data.get("field"), "groups")

    def test_invalid_value_non_numeric_f_returns_exit_code_2(self):
        """SPEC.md Section 3.2 & 5.1 v045: Non-numeric string produces INVALID_VALUE."""
        ret, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "a-priori",
            "--f", "abc",
            "--alpha", "0.05",
            "--power", "0.95",
            "--groups", "5",
        )
        self.assertEqual(ret, 2)
        self.assertNotIn("\n", stdout)
        data = json.loads(stdout)
        self.assertEqual(data.get("code"), "INVALID_VALUE")
        self.assertEqual(data.get("field"), "f")

    def test_out_of_range_effect_size_returns_exit_code_2(self):
        """SPEC.md Section 3.2 & 5.1 v041/v042: f outside (1e-6, 50] produces OUT_OF_RANGE."""
        for invalid_f in ["-0.25", "0.0", "60.0"]:
            ret, stdout, _ = run_cli(
                "--test", "anova-oneway",
                "--mode", "a-priori",
                "--f", invalid_f,
                "--alpha", "0.05",
                "--power", "0.95",
                "--groups", "5",
            )
            self.assertEqual(ret, 2)
            data = json.loads(stdout)
            self.assertEqual(data.get("code"), "OUT_OF_RANGE")
            self.assertEqual(data.get("field"), "f")

    def test_out_of_range_alpha_returns_exit_code_2(self):
        """SPEC.md Section 3.2 & 5.1 v039/v040: alpha outside (1e-7, 1) produces OUT_OF_RANGE."""
        for invalid_alpha in ["0.0", "1.0", "-0.05"]:
            ret, stdout, _ = run_cli(
                "--test", "anova-oneway",
                "--mode", "a-priori",
                "--f", "0.25",
                "--alpha", invalid_alpha,
                "--power", "0.95",
                "--groups", "5",
            )
            self.assertEqual(ret, 2)
            data = json.loads(stdout)
            self.assertEqual(data.get("code"), "OUT_OF_RANGE")
            self.assertEqual(data.get("field"), "alpha")

    def test_out_of_range_groups_returns_exit_code_2(self):
        """SPEC.md Section 3.2 & 5.1 v043/v044: groups < 2 produces OUT_OF_RANGE."""
        for invalid_groups in ["1", "0", "-2"]:
            ret, stdout, _ = run_cli(
                "--test", "anova-oneway",
                "--mode", "a-priori",
                "--f", "0.25",
                "--alpha", "0.05",
                "--power", "0.95",
                "--groups", invalid_groups,
            )
            self.assertEqual(ret, 2)
            data = json.loads(stdout)
            self.assertEqual(data.get("code"), "OUT_OF_RANGE")
            self.assertEqual(data.get("field"), "groups")

    def test_inconsistent_power_less_than_alpha_returns_exit_code_2(self):
        """SPEC.md Section 3.2 & 5.1 v035: power < alpha produces INCONSISTENT."""
        ret, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "a-priori",
            "--f", "0.25",
            "--alpha", "0.05",
            "--power", "0.04",
            "--groups", "5",
        )
        self.assertEqual(ret, 2)
        data = json.loads(stdout)
        self.assertEqual(data.get("code"), "INCONSISTENT")
        self.assertEqual(data.get("field"), "power")

    def test_inconsistent_post_hoc_sample_size_returns_exit_code_2(self):
        """SPEC.md Section 3.2 & 4.3: n_total <= groups produces INCONSISTENT."""
        ret, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "post-hoc",
            "--f", "0.25",
            "--alpha", "0.05",
            "--n_total", "5",
            "--groups", "5",
        )
        self.assertEqual(ret, 2)
        data = json.loads(stdout)
        self.assertEqual(data.get("code"), "INCONSISTENT")
        self.assertEqual(data.get("field"), "n_total")

    def test_unsupported_test_family_returns_exit_code_2(self):
        """SPEC.md Section 3.2 & 6.1 Scenario 9: Unsupported test produces UNSUPPORTED."""
        ret, stdout, _ = run_cli(
            "--test", "unsupported-test",
            "--mode", "a-priori",
            "--f", "0.25",
            "--alpha", "0.05",
            "--power", "0.95",
            "--groups", "5",
        )
        self.assertEqual(ret, 2)
        data = json.loads(stdout)
        self.assertEqual(data.get("code"), "UNSUPPORTED")
        self.assertEqual(data.get("field"), "test")

    def test_unsupported_mode_returns_exit_code_2(self):
        """SPEC.md Section 3.2 Table: Unknown mode produces UNSUPPORTED."""
        ret, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "bootstrap",
            "--f", "0.25",
            "--alpha", "0.05",
            "--power", "0.95",
            "--groups", "5",
        )
        self.assertEqual(ret, 2)
        data = json.loads(stdout)
        self.assertEqual(data.get("code"), "UNSUPPORTED")
        self.assertEqual(data.get("field"), "mode")

    def test_determinism(self):
        """SPEC.md Section 2.1: Identical inputs unconditionally produce bitwise identical output."""
        outputs = []
        for _ in range(3):
            ret, stdout, _ = run_cli(
                "--test", "anova-oneway",
                "--mode", "a-priori",
                "--f", "0.25",
                "--alpha", "0.05",
                "--power", "0.95",
                "--groups", "5",
            )
            self.assertEqual(ret, 0)
            outputs.append(stdout)
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(outputs[1], outputs[2])

    def test_timing_worst_cases_under_two_seconds(self):
        """SPEC.md Section 2.1: Execution must finish within 2.0 seconds per invocation."""
        worst_cases = [
            # Process start & version query
            (["--version"], "process_start"),
            # Typical a-priori benchmark
            (["--test", "anova-oneway", "--mode", "a-priori", "--f", "0.25", "--alpha", "0.05", "--power", "0.95", "--groups", "5"], "a_priori_typical"),
            # Very large N (1e7) in post-hoc
            (["--test", "anova-oneway", "--mode", "post-hoc", "--f", "0.001", "--alpha", "0.05", "--n_total", "10000000", "--groups", "5"], "large_n_post_hoc"),
            # Very small effects (f = 1e-5) in post-hoc
            (["--test", "anova-oneway", "--mode", "post-hoc", "--f", "0.00001", "--alpha", "0.05", "--n_total", "1000000", "--groups", "5"], "small_f_post_hoc"),
            # Large group counts (k = 100)
            (["--test", "anova-oneway", "--mode", "a-priori", "--f", "0.25", "--alpha", "0.05", "--power", "0.95", "--groups", "100"], "large_groups"),
            # Extreme alpha (alpha = 1e-6)
            (["--test", "anova-oneway", "--mode", "a-priori", "--f", "0.25", "--alpha", "0.000001", "--power", "0.95", "--groups", "5"], "extreme_alpha"),
            # Extreme boundaries: N = 2147483647, k = 100, f = 50.0
            (["--test", "anova-oneway", "--mode", "post-hoc", "--f", "50.0", "--alpha", "0.05", "--n_total", "2147483647", "--groups", "100"], "max_n_max_k_max_f"),
            # Extreme boundaries: N = 2147483647, k = 100, f = 1e-6
            (["--test", "anova-oneway", "--mode", "post-hoc", "--f", "0.000001", "--alpha", "0.05", "--n_total", "2147483647", "--groups", "100"], "max_n_min_f"),
            # Extreme boundaries: N = 2147483647, k = 100, alpha = 1e-7
            (["--test", "anova-oneway", "--mode", "post-hoc", "--f", "0.25", "--alpha", "0.0000001", "--n_total", "2147483647", "--groups", "100"], "max_n_min_alpha"),
        ]

        for args, label in worst_cases:
            t0 = time.time()
            ret, stdout, _ = run_cli(*args)
            elapsed = time.time() - t0
            self.assertEqual(ret, 0, f"Case {label} failed with exit code {ret}: {stdout}")
            self.assertLess(elapsed, 2.0, f"Case {label} exceeded 2.0 seconds: {elapsed:.4f}s")

    def test_cli_boundary_admissibility_and_rejections(self):
        """SPEC.md Section 2.3 & 5.2: Admissible boundary values and out-of-range rejections."""
        # Accepted: f = 1e-6, alpha = 1e-7, n_total = 2147483647
        ret, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "post-hoc",
            "--f", "0.000001",
            "--alpha", "0.0000001",
            "--n_total", "2147483647",
            "--groups", "5",
        )
        self.assertEqual(ret, 0)
        data = json.loads(stdout)
        self.assertIn("power", data)

        # Rejected: n_total > 2147483647
        ret, stdout, _ = run_cli(
            "--test", "anova-oneway",
            "--mode", "post-hoc",
            "--f", "0.25",
            "--alpha", "0.05",
            "--n_total", "2147483648",
            "--groups", "5",
        )
        self.assertEqual(ret, 2)
        data = json.loads(stdout)
        self.assertEqual(data.get("code"), "OUT_OF_RANGE")
        self.assertEqual(data.get("field"), "n_total")


if __name__ == "__main__":
    unittest.main()
