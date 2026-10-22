"""Differential tests comparing gpower-clone CLI against ground-truth G*Power GUI oracle vectors."""

import csv
import json
import os
import subprocess
import sys
import unittest

ORACLE_CSV = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "oracle", "gpower_vectors.csv"))


def load_oracle_vectors():
    vectors = []
    if not os.path.exists(ORACLE_CSV):
        return vectors

    with open(ORACLE_CSV, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            vectors.append(row)
    return vectors


class DifferentialTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vectors = load_oracle_vectors()
        cls.cli_path = [sys.executable, "-m", "src.cli.main"]

    def run_cli(self, args):
        cmd = self.cli_path + args
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return proc

    def test_all_oracle_vectors_against_cli(self):
        passed = 0
        failed = 0
        mismatches = []

        for row in self.vectors:
            vid = row["id"]
            k = row["k_groups"]
            f_val = row["effect_size_f"]
            alpha = row["alpha"]
            power = row["power"]
            total_n_str = row.get("total_N", "").strip()
            is_valid = bool(total_n_str)

            cmd_args = [
                "--test", "anova-oneway",
                "--mode", "a-priori",
                "--groups", str(k),
                "--f", str(f_val),
                "--alpha", str(alpha),
                "--power", str(power),
            ]

            proc = self.run_cli(cmd_args)

            if is_valid:
                expected_total_N = int(total_n_str)
                k_float = float(k)
                k_int = int(round(k_float + 1e-9))
                expected_n_per_group = expected_total_N // k_int
                expected_actual_power = float(row["actual_power"])
                expected_critical_F = float(row["critical_F"])
                expected_df1 = int(row["df1"])
                expected_df2 = int(row["df2"])
                expected_ncp = float(row["noncentrality"])

                if proc.returncode != 0:
                    failed += 1
                    mismatches.append(f"{vid}: CLI failed with exit code {proc.returncode}, stdout: {proc.stdout.strip()}")
                    continue

                try:
                    out = json.loads(proc.stdout.strip())
                except Exception as e:
                    failed += 1
                    mismatches.append(f"{vid}: Failed to parse JSON stdout: {e}, text: {proc.stdout.strip()}")
                    continue

                # Compare n_total exactly
                diffs = []
                if out.get("n_total") != expected_total_N:
                    diffs.append(f"n_total {out.get('n_total')} != {expected_total_N}")

                # Compare n_per_group exactly
                if out.get("n_per_group") != expected_n_per_group:
                    diffs.append(f"n_per_group {out.get('n_per_group')} != {expected_n_per_group}")

                # Compare df1 and df2 exactly
                if out.get("df1") != expected_df1:
                    diffs.append(f"df1 {out.get('df1')} != {expected_df1}")
                if out.get("df2") != expected_df2:
                    diffs.append(f"df2 {out.get('df2')} != {expected_df2}")

                # Compare other floating point outputs to the number of digits G*Power displays (7 decimal places)
                if abs(out.get("critical", 0.0) - expected_critical_F) > 1e-4:
                    diffs.append(f"critical {out.get('critical')} != {expected_critical_F}")
                if abs(out.get("actual_power", 0.0) - expected_actual_power) > 1e-4:
                    diffs.append(f"actual_power {out.get('actual_power')} != {expected_actual_power}")
                if abs(out.get("ncp", 0.0) - expected_ncp) > 1e-4:
                    diffs.append(f"ncp {out.get('ncp')} != {expected_ncp}")

                if diffs:
                    failed += 1
                    mismatches.append(f"{vid}: " + ", ".join(diffs))
                else:
                    passed += 1
            else:
                # Expect error / dialog rejection
                if proc.returncode == 0:
                    failed += 1
                    mismatches.append(f"{vid}: Expected rejection, got exit code 0, stdout: {proc.stdout.strip()}")
                else:
                    try:
                        err_out = json.loads(proc.stdout.strip())
                        if "error" in err_out:
                            passed += 1
                        else:
                            failed += 1
                            mismatches.append(f"{vid}: Non-zero exit but JSON missing 'error' key: {proc.stdout.strip()}")
                    except Exception as e:
                        failed += 1
                        mismatches.append(f"{vid}: Non-zero exit but invalid JSON: {e}")

        total = len(self.vectors)
        valid_count = sum(1 for v in self.vectors if v.get("total_N", "").strip())
        print(f"\nDifferential Verification Results:")
        print(f"  Total oracle rows evaluated: {total}")
        print(f"  Valid calculation rows: {valid_count}")
        print(f"  Error / boundary rejection rows: {total - valid_count}")
        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")
        if total > 0:
            print(f"  Overall Match Rate: {passed / total * 100:.2f}%")
        if mismatches:
            print(f"  Mismatches:\n    " + "\n    ".join(mismatches))

        self.assertEqual(failed, 0, f"{failed} vector(s) mismatched oracle ground truth.")


if __name__ == "__main__":
    unittest.main()
