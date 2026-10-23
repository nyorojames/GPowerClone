"""Differential tests comparing gpower-clone CLI against ground-truth G*Power GUI oracle vectors."""

import csv
import json
import os
import subprocess
import sys
import unittest

ORACLE_CSV = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "oracle", "gpower_vectors.csv"))
POSTHOC_CSV = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "oracle", "posthoc_vectors.csv"))


def load_oracle_vectors():
    vectors = []
    if not os.path.exists(ORACLE_CSV):
        return vectors

    with open(ORACLE_CSV, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            vectors.append(row)
    return vectors


def load_posthoc_vectors():
    vectors = []
    if not os.path.exists(POSTHOC_CSV):
        return vectors

    with open(POSTHOC_CSV, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            vectors.append(row)
    return vectors


class DifferentialTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vectors = load_oracle_vectors()
        cls.posthoc_vectors = load_posthoc_vectors()
        cls.cli_path = [sys.executable, "-m", "src.cli.main"]

    def run_cli(self, args):
        cmd = self.cli_path + args
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return proc

    def test_all_oracle_vectors_against_cli(self):
        passed = 0
        failed = 0
        v046_divergence_verified = False
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

            if vid == "v046":
                # Under CONTRACT.md v1.0.0 Section 5, 'groups' must be integer >= 2.
                # In G*Power GUI, 3.5 was rounded half-up to 4. Under contract v1.0.0,
                # non-integer inputs are rejected with exit code 2 and code 'INVALID_VALUE'.
                if proc.returncode == 2:
                    try:
                        err_out = json.loads(proc.stdout.strip())
                        if err_out.get("code") == "INVALID_VALUE":
                            v046_divergence_verified = True
                            continue
                    except Exception:
                        pass
                failed += 1
                mismatches.append(f"v046: Expected exit code 2 with INVALID_VALUE, got {proc.returncode}, stdout: {proc.stdout.strip()}")
                continue

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

                # Compare floating point outputs according to contract numeric rule (|a-b| <= 1e-6 or relative diff <= 1e-6)
                def check_num(a, b, tol=1e-6):
                    d = abs(a - b)
                    if d <= tol:
                        return True
                    if abs(b) > 0 and (d / abs(b)) <= tol:
                        return True
                    return False

                crit_val = out.get("critical_f", out.get("critical", 0.0))
                if not check_num(crit_val, expected_critical_F):
                    diffs.append(f"critical_f {crit_val} != {expected_critical_F}")
                if not check_num(out.get("actual_power", 0.0), expected_actual_power):
                    diffs.append(f"actual_power {out.get('actual_power')} != {expected_actual_power}")
                if not check_num(out.get("ncp", 0.0), expected_ncp):
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
        print(f"  Rows matching G*Power values: {passed}/{total}")
        print(f"  Intentional contract divergence: v046 (G*Power rounds groups=3.5 to 4; contract requires INVALID_VALUE)")
        print(f"  Failed: {failed}")
        if mismatches:
            print(f"  Mismatches:\n    " + "\n    ".join(mismatches))

        self.assertTrue(v046_divergence_verified, "v046 must be rejected with exit code 2 and code INVALID_VALUE")
        self.assertEqual(failed, 0, f"{failed} vector(s) mismatched oracle ground truth.")

    def test_all_posthoc_vectors_against_cli(self):
        passed = 0
        failed = 0
        mismatches = []

        for row in self.posthoc_vectors:
            vid = row["id"]
            f_val = row["f"]
            alpha = row["alpha"]
            n_total = row["n_total"]
            groups = row["groups"]
            pwr_str = row.get("power", "").strip()
            is_calc = bool(pwr_str)

            cmd_args = [
                "--test", "anova-oneway",
                "--mode", "post-hoc",
                "--f", str(f_val),
                "--alpha", str(alpha),
                "--n_total", str(n_total),
                "--groups", str(groups),
            ]

            proc = self.run_cli(cmd_args)

            if is_calc:
                expected_df1 = int(row["df1"])
                expected_df2 = int(row["df2"])
                expected_ncp = float(row["ncp"])
                expected_critical_F = float(row["critical_F"])
                expected_power = float(pwr_str)

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

                diffs = []
                if out.get("df1") != expected_df1:
                    diffs.append(f"df1 {out.get('df1')} != {expected_df1}")
                if out.get("df2") != expected_df2:
                    diffs.append(f"df2 {out.get('df2')} != {expected_df2}")

                def check_num(a, b, tol=1e-6):
                    d = abs(a - b)
                    if d <= tol:
                        return True
                    if abs(b) > 0 and (d / abs(b)) <= tol:
                        return True
                    return False

                crit_val = out.get("critical_f", out.get("critical", 0.0))
                if not check_num(crit_val, expected_critical_F):
                    diffs.append(f"critical_f {crit_val} != {expected_critical_F}")
                if not check_num(out.get("power", 0.0), expected_power):
                    diffs.append(f"power {out.get('power')} != {expected_power}")
                if not check_num(out.get("ncp", 0.0), expected_ncp):
                    diffs.append(f"ncp {out.get('ncp')} != {expected_ncp}")

                if diffs:
                    failed += 1
                    mismatches.append(f"{vid}: " + ", ".join(diffs))
                else:
                    passed += 1
            else:
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

        total = len(self.posthoc_vectors)
        valid_count = sum(1 for v in self.posthoc_vectors if v.get("power", "").strip())
        print(f"\nDifferential Verification Results (Post-Hoc):")
        print(f"  Total oracle rows evaluated: {total}")
        print(f"  Valid calculation rows: {valid_count}")
        print(f"  Error / boundary rejection rows: {total - valid_count}")
        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")
        if total > 0:
            print(f"  Overall Match Rate: {passed / total * 100:.2f}%")
        if mismatches:
            print(f"  Mismatches ({len(mismatches)}):\n    " + "\n    ".join(mismatches))

        self.assertEqual(failed, 0, f"{failed} vector(s) mismatched oracle ground truth.")



if __name__ == "__main__":
    unittest.main()
