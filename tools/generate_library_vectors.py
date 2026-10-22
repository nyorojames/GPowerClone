"""Generates 500+ library vectors using scipy / statsmodels and compares against gpower-clone engine.

Outputs are written to tests/data/library_vectors.csv.
"""

import csv
import math
import os
import sys
import warnings

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.engine.anova_oneway import compute_a_priori
from statsmodels.stats.power import FTestAnovaPower
from scipy.stats import f as central_f, ncf
from scipy.optimize import brentq

# Suppress statsmodels convergence warnings during grid search
warnings.filterwarnings("ignore")

pwr_model = FTestAnovaPower()


def solve_library_fractional_n(k, f, alpha, target_power):
    """Solves for continuous N using statsmodels with robust scipy brentq fallback."""
    try:
        val = pwr_model.solve_power(effect_size=f, nobs=None, alpha=alpha, power=target_power, k_groups=k)
        if isinstance(val, (int, float)) and not math.isnan(val) and val > k:
            return float(val)
    except Exception:
        pass

    # Robust scipy brentq solver
    def obj(N):
        df1 = k - 1
        df2 = N - k
        if df2 <= 1e-4:
            return -1.0
        lam = (f ** 2) * N
        crit = central_f.ppf(1.0 - alpha, df1, df2)
        return float(1.0 - ncf.cdf(crit, df1, df2, lam)) - target_power

    low = k + 0.05
    high = max(100.0, float(k) * 10.0)
    step = 0
    while obj(high) < 0 and step < 50:
        high *= 2.0
        step += 1

    try:
        sol = brentq(obj, low, high, xtol=1e-7, maxiter=100)
        return float(sol)
    except Exception:
        # Robust bisection fallback
        l, r = low, high
        for _ in range(80):
            mid = (l + r) / 2.0
            if obj(mid) >= 0:
                r = mid
            else:
                l = mid
        return float((l + r) / 2.0)


def generate_parameter_grid():
    grid = []

    # 1. Broad combinations across standard, small, large effect sizes
    # Curated sampling to ensure rich coverage > 500 valid inputs
    for k in [2, 3, 4, 5, 6, 8, 10, 12, 15, 20]:
        for f in [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50, 0.60, 0.80]:
            for alpha in [0.01, 0.05, 0.10]:
                for power in [0.70, 0.80, 0.85, 0.90, 0.95]:
                    if power >= alpha + 0.02:
                        grid.append((k, f, alpha, power, "grid_main"))

    # 2. Boundary: Near alpha (power ~ alpha)
    for k in [2, 3, 4, 5, 8, 10]:
        for f in [0.10, 0.20, 0.25, 0.40]:
            for alpha in [0.01, 0.05, 0.10]:
                p_near = round(alpha + 0.02, 4)
                grid.append((k, f, alpha, p_near, "boundary_near_alpha"))

    # 3. Boundary: Massive effect sizes (f = 1.0 .. 5.0) checking floor N = 2k
    for k in [2, 3, 4, 5, 6, 8, 10, 15, 20]:
        for f in [1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]:
            for alpha in [0.01, 0.05]:
                for power in [0.80, 0.95]:
                    grid.append((k, f, alpha, power, "boundary_large_f_floor"))

    # 4. Boundary: Very small effect sizes (f = 0.01 .. 0.04) checking large N convergence
    for k in [2, 3, 4, 5]:
        for f in [0.015, 0.02, 0.03, 0.04]:
            for alpha in [0.01, 0.05]:
                for power in [0.80, 0.90]:
                    grid.append((k, f, alpha, power, "boundary_small_f_large_N"))

    # 5. Boundary: Very large group counts (k = 25, 50, 75, 100)
    for k in [25, 50, 75, 100]:
        for f in [0.15, 0.25, 0.40]:
            for alpha in [0.01, 0.05]:
                for power in [0.80, 0.95]:
                    grid.append((k, f, alpha, power, "boundary_large_k"))

    # 6. Boundary: Extreme high power (power = 0.99, 0.995, 0.999)
    for k in [2, 3, 4, 5]:
        for f in [0.20, 0.25, 0.35]:
            for alpha in [0.01, 0.05]:
                for power in [0.99, 0.995, 0.999]:
                    grid.append((k, f, alpha, power, "boundary_extreme_high_power"))

    # 7. Boundary: Extreme small alpha (alpha = 0.0001, 0.001)
    for k in [2, 3, 5]:
        for f in [0.20, 0.25, 0.40]:
            for alpha in [0.0001, 0.001]:
                for power in [0.80, 0.95]:
                    grid.append((k, f, alpha, power, "boundary_extreme_small_alpha"))

    # Deduplicate while preserving order
    seen = set()
    unique_grid = []
    for item in grid:
        key = (item[0], item[1], item[2], item[3])
        if key not in seen:
            seen.add(key)
            unique_grid.append(item)

    return unique_grid


def generate_library_vectors(output_csv="tests/data/library_vectors.csv"):
    param_grid = generate_parameter_grid()
    print(f"Total parameter combinations generated: {len(param_grid)}")

    rows = []
    for idx, (k, f, alpha, power, category) in enumerate(param_grid, start=1):
        vec_id = f"lib_{idx:04d}"

        # 1. Compute continuous N from library (scipy / statsmodels mathematical formulation)
        n_frac = solve_library_fractional_n(k, f, alpha, power)
        n_ceil = math.ceil(n_frac)
        n_group_ceil = k * math.ceil(n_frac / k)

        # 2. Compute G*Power / gpower-clone discrete engine output
        res = compute_a_priori(
            effect_size_f=f,
            alpha=alpha,
            target_power=power,
            groups=k,
        )

        exact_match_ceil = (res.n_total == n_ceil)
        exact_match_group_ceil = (res.n_total == n_group_ceil)
        gap = res.n_total - n_frac

        row = {
            "id": vec_id,
            "category": category,
            "groups": k,
            "effect_size_f": f,
            "alpha": alpha,
            "power": power,
            "library_fractional_N": f"{n_frac:.6f}",
            "library_ceil_N": n_ceil,
            "library_group_ceil_N": n_group_ceil,
            "gpower_n_total": res.n_total,
            "gpower_n_per_group": res.n_per_group,
            "gpower_actual_power": f"{res.actual_power:.7f}",
            "gpower_critical_F": f"{res.critical_f:.7f}",
            "df1": res.df_num,
            "df2": res.df_denom,
            "noncentrality": f"{res.ncp:.7f}",
            "n_gap": f"{gap:.6f}",
            "matches_simple_ceil": exact_match_ceil,
            "matches_group_ceil": exact_match_group_ceil,
        }
        rows.append(row)

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    fieldnames = list(rows[0].keys())
    with open(output_csv, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Successfully generated {len(rows)} vectors in {output_csv}.")
    return rows


if __name__ == "__main__":
    generate_library_vectors()
