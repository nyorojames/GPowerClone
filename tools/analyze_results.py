import csv
import json
import subprocess
import sys

def analyze():
    # 1. Oracle vectors analysis
    with open('oracle/gpower_vectors.csv', 'r', encoding='utf-8') as f:
        oracle_rows = list(csv.DictReader(f))

    total_oracle = len(oracle_rows)
    valid_oracle = [r for r in oracle_rows if r.get('total_N', '').strip()]
    error_oracle = [r for r in oracle_rows if not r.get('total_N', '').strip()]

    print(f"=== ORACLE GUI VECTORS ANALYSIS ===")
    print(f"Total oracle vectors: {total_oracle}")
    print(f"Valid calculation vectors: {len(valid_oracle)}")
    print(f"Error dialog vectors: {len(error_oracle)}")

    oracle_exact_n_matches = 0
    oracle_cli_passed = 0
    oracle_mismatches = []

    for r in oracle_rows:
        vid = r['id']
        k = r['k_groups']
        f_val = r['effect_size_f']
        alpha = r['alpha']
        power = r['power']
        is_valid = bool(r.get('total_N', '').strip())

        cmd = [sys.executable, '-m', 'src.cli.main', '--test', 'anova-oneway', '--mode', 'a-priori',
               '--groups', k, '--f', f_val, '--alpha', alpha, '--power', power]
        res = subprocess.run(cmd, capture_output=True, text=True)

        if is_valid:
            exp_n = int(r['total_N'])
            k_int = int(round(float(k) + 1e-9))
            exp_n_grp = exp_n // k_int
            exp_crit = float(r['critical_F'])
            exp_pwr = float(r['actual_power'])
            exp_df1 = int(r['df1'])
            exp_df2 = int(r['df2'])
            exp_ncp = float(r['noncentrality'])

            if res.returncode != 0:
                oracle_mismatches.append((vid, 'Exit code != 0 on valid input', res.stdout))
                continue
            data = json.loads(res.stdout.strip())
            diffs = []
            if data['n_total'] == exp_n:
                oracle_exact_n_matches += 1
            else:
                diffs.append(f"n_total {data['n_total']} != {exp_n}")
            if data['n_per_group'] != exp_n_grp:
                diffs.append(f"n_per_group {data['n_per_group']} != {exp_n_grp}")
            if data['df1'] != exp_df1:
                diffs.append(f"df1 {data['df1']} != {exp_df1}")
            if data['df2'] != exp_df2:
                diffs.append(f"df2 {data['df2']} != {exp_df2}")
            if abs(data['critical'] - exp_crit) > 1e-4:
                diffs.append(f"critical {data['critical']} != {exp_crit}")
            if abs(data['actual_power'] - exp_pwr) > 1e-4:
                diffs.append(f"actual_power {data['actual_power']} != {exp_pwr}")
            if abs(data['ncp'] - exp_ncp) > 1e-4:
                diffs.append(f"ncp {data['ncp']} != {exp_ncp}")

            if diffs:
                oracle_mismatches.append((vid, '; '.join(diffs), data))
            else:
                oracle_cli_passed += 1
        else:
            if res.returncode != 0:
                err_data = json.loads(res.stdout.strip())
                if 'error' in err_data:
                    oracle_cli_passed += 1
                else:
                    oracle_mismatches.append((vid, 'No error key in JSON', res.stdout))
            else:
                oracle_mismatches.append((vid, 'Expected error exit code, got 0', res.stdout))

    print(f"Oracle Exact-N Match Rate: {oracle_exact_n_matches}/{len(valid_oracle)} ({oracle_exact_n_matches/len(valid_oracle)*100:.2f}%)")
    print(f"Oracle Total CLI Pass Rate (including 10 error cases): {oracle_cli_passed}/{total_oracle} ({oracle_cli_passed/total_oracle*100:.2f}%)")

    # 2. Library vectors analysis
    with open('tests/data/library_vectors.csv', 'r', encoding='utf-8') as f:
        lib_rows = list(csv.DictReader(f))

    total_lib = len(lib_rows)
    simple_ceil_matches = sum(1 for r in lib_rows if r['matches_simple_ceil'] == 'True')
    group_ceil_matches = sum(1 for r in lib_rows if r['matches_group_ceil'] == 'True')
    group_ceil_diffs = [r for r in lib_rows if r['matches_group_ceil'] != 'True']

    print(f"\n=== LIBRARY VECTORS ANALYSIS (1200 Vectors) ===")
    print(f"Total library vectors: {total_lib}")
    print(f"Exact match with simple ceil(N_lib): {simple_ceil_matches}/{total_lib} ({simple_ceil_matches/total_lib*100:.2f}%)")
    print(f"Exact match with group-balanced ceil k*ceil(N_lib/k): {group_ceil_matches}/{total_lib} ({group_ceil_matches/total_lib*100:.2f}%)")
    print(f"Total discrepancies between gpower-clone and group-balanced ceil: {len(group_ceil_diffs)}")

    categories = {}
    for r in group_ceil_diffs:
        cat = r['category']
        categories[cat] = categories.get(cat, 0) + 1

    print("\nDiscrepancies by category:")
    for cat, count in categories.items():
        print(f"  {cat}: {count}")

    print("\nSample discrepancies:")
    for r in group_ceil_diffs[:15]:
        n_frac = float(r['library_fractional_N'])
        n_grp_ceil = int(r['library_group_ceil_N'])
        n_gp = int(r['gpower_n_total'])
        k = int(r['groups'])
        f_val = float(r['effect_size_f'])
        print(f"  {r['id']} ({r['category']}): k={k}, f={f_val}, a={r['alpha']}, p={r['power']} | Frac N={n_frac:.4f} -> GrpCeil={n_grp_ceil} vs GPower={n_gp} (Diff = {n_gp - n_grp_ceil})")

if __name__ == '__main__':
    analyze()
