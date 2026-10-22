"""Calculation engine for one-way ANOVA omnibus F-test (clean-room implementation).

SPEC.md References:
- Section 1: Scope (anova-oneway, a-priori mode).
- Section 2: Inputs, Ranges, Defaults, and Units.
- Section 3: Algorithm in Plain Language & Mathematical Formulas.
- Section 4: Search and Stopping Rules, Rounding, Minimum and Maximum N.
- Section 5: Outputs and Exact Definitions.
- Section 6: Error Handling and Invalid Input Behavior.
"""

from dataclasses import dataclass
import math
from typing import Any, Dict, Optional, Tuple, Union

from src.engine.distributions import f_inv_sf, ncf_power


@dataclass(frozen=True)
class AnovaOneWayResult:
    """Statistical power analysis output parameters for one-way ANOVA.

    SPEC.md Section 5: Outputs and Exact Definitions:
    1. n_per_group (int): Number of observations per group (n = N / k).
    2. n_total (int): Total required sample size (N = n * k).
    3. actual_power (float): Achieved power evaluated at (df1, df2, lambda, F_crit).
    4. critical (float): Critical F ratio value (F_crit).
    5. df1 (int): Numerator degrees of freedom (k - 1).
    6. df2 (int): Denominator degrees of freedom (N - k).
    7. ncp (float): Noncentrality parameter (lambda = f^2 * N).
    """
    n_per_group: int
    n_total: int
    actual_power: float
    critical: float
    df1: int
    df2: int
    ncp: float
    is_success: bool = True
    error: Optional[str] = None

    # Backward-compatible property aliases
    @property
    def critical_f(self) -> float:
        """Alias for critical."""
        return self.critical

    @property
    def df_num(self) -> int:
        """Alias for df1."""
        return self.df1

    @property
    def df_denom(self) -> int:
        """Alias for df2."""
        return self.df2

    def to_dict(self) -> Dict[str, Any]:
        """Maps output to the contract dictionary format.

        SPEC.md Section 5 & Section 7:
        {"n_per_group": ..., "n_total": ..., "actual_power": ..., "critical": ..., "df1": ..., "df2": ..., "ncp": ...}
        SPEC.md Section 9.3: Rounded to 7 decimal places for numerical agreement.
        """
        return {
            "n_per_group": self.n_per_group,
            "n_total": self.n_total,
            "actual_power": round(self.actual_power, 7),
            "critical": round(self.critical, 7),
            "df1": self.df1,
            "df2": self.df2,
            "ncp": round(self.ncp, 7),
        }


class CalculationError(ValueError):
    """Structured error for invalid inputs or calculation boundaries.

    SPEC.md Section 6: Error Handling and Invalid Input Behavior.
    Inherits from ValueError for test compatibility while providing structured error access.
    """
    def __init__(self, error: str):
        super().__init__(error)
        self.error = error
        self.is_success = False

    def to_dict(self) -> Dict[str, Any]:
        """SPEC.md Section 6 & Section 7: {"error": "<description>"}"""
        return {"error": self.error}


def validate_anova_inputs(
    effect_size_f: Any,
    alpha: Any,
    groups: Any,
    power: Optional[Any] = None,
    n_total: Optional[Any] = None,
) -> Tuple[float, float, int, Optional[float], Optional[int]]:
    """Validates parameters for one-way ANOVA against SPEC.md admissible ranges.

    SPEC.md Section 2, Section 4 & Section 6:
    Raises CalculationError on validation failure.
    """
    # Parse effect size f
    # SPEC.md Section 6.1: f <= 10^-6 or f > 50 (or non-numeric text) triggers error
    try:
        f_val = float(effect_size_f)
    except (ValueError, TypeError):
        raise CalculationError("Effect size f is outside the admissible range (1e-06, 50)")

    # SPEC.md Section 2 & Section 6.1: Valid Range (10^-6, 50]
    if not (1e-6 < f_val <= 50.0):
        raise CalculationError("Effect size f is outside the admissible range (1e-06, 50)")

    # Parse significance level alpha
    # SPEC.md Section 6.2: alpha <= 10^-7 or alpha >= 1 (or non-numeric text) triggers error
    try:
        alpha_val = float(alpha)
    except (ValueError, TypeError):
        raise CalculationError("Alpha is outside the admissible range (1e-07, 1)")

    # SPEC.md Section 2 & Section 6.2: Valid Range (10^-7, 1)
    if not (1e-7 < alpha_val < 1.0):
        raise CalculationError("Alpha is outside the admissible range (1e-07, 1)")

    # Parse group count k
    # SPEC.md Section 6.5: If k < 2 (or non-numeric text), triggers error
    try:
        groups_raw = float(groups)
    except (ValueError, TypeError):
        raise CalculationError("There must be at least 2 groups")

    # SPEC.md Section 2 & Section 4: Floats rounded half-up (e.g. 3.5 -> 4)
    # math.floor(x + 0.5) implements deterministic half-up rounding for positive values
    groups_val = int(math.floor(groups_raw + 0.5))

    # SPEC.md Section 2 & Section 6.5: Valid Range [2, infinity)
    if groups_val < 2:
        raise CalculationError("There must be at least 2 groups")

    # Validate target power if provided (a-priori mode)
    power_val: Optional[float] = None
    if power is not None:
        # SPEC.md Section 6.3: power <= 10^-7 or power >= 1 triggers error
        try:
            power_val = float(power)
        except (ValueError, TypeError):
            raise CalculationError("Power is outside the admissible range (1e-07, 1)")

        # SPEC.md Section 2 & Section 6.3: Valid Range (10^-7, 1)
        if not (1e-7 < power_val < 1.0):
            raise CalculationError("Power is outside the admissible range (1e-07, 1)")

        # SPEC.md Section 2 & Section 6.4: Power must be greater than or equal to alpha
        if power_val < alpha_val:
            raise CalculationError("Power must be greater than or equal to alpha")

    # Validate n_total if provided (post-hoc mode)
    n_total_val: Optional[int] = None
    if n_total is not None:
        try:
            n_total_val = int(n_total)
        except (ValueError, TypeError):
            raise CalculationError(f"Total sample size N must be strictly greater than groups ({groups_val}), got {n_total}")

        # SPEC.md Section 4: df2 = N - k >= 1 => N > k
        if n_total_val <= groups_val:
            raise CalculationError(f"Total sample size N must be strictly greater than groups ({groups_val}), got {n_total_val}")

    return f_val, alpha_val, groups_val, power_val, n_total_val


def compute_a_priori(
    effect_size_f: Any,
    alpha: Any,
    target_power: Any,
    groups: Any,
    max_n: int = 100_000_000,
) -> AnovaOneWayResult:
    """Computes required total sample size N (a-priori analysis).

    SPEC.md Section 1: Mode a-priori.
    SPEC.md Section 3: Formulas:
      - df1 = k - 1 (Section 3.1)
      - df2 = N - k (Section 3.2)
      - lambda = f^2 * N (Section 3.3)
      - F_crit = F_central^-1(1 - alpha; df1, df2) (Section 3.4)
      - Power = 1 - F_nc(F_crit; df1, df2, lambda) (Section 3.5)
    SPEC.md Section 4:
      - Balanced design: N is searched in discrete increments of k: N = n * k
      - Minimum sample size per group: n >= 2 (N_min = 2k, df2 >= k >= 2)
      - Stopping condition: smallest integer n >= 2 achieving Power >= target_power
      - Max N cap: 100,000,000
    """
    f_val, alpha_val, groups_val, power_val, _ = validate_anova_inputs(
        effect_size_f=effect_size_f,
        alpha=alpha,
        groups=groups,
        power=target_power,
    )

    # SPEC.md Section 3.1: Numerator degrees of freedom df1 = k - 1
    df1 = groups_val - 1

    def evaluate_n_per_group(n_pg: int) -> Tuple[float, float, int, int, float]:
        # SPEC.md Section 4: N = n * k
        tot_n = n_pg * groups_val
        # SPEC.md Section 3.2: df2 = N - k
        df2 = tot_n - groups_val
        # SPEC.md Section 3.3: lambda = f^2 * N
        lambda_val = (f_val ** 2) * tot_n
        # SPEC.md Section 3.4: Critical value from central F distribution at 1 - alpha
        crit_f = f_inv_sf(alpha_val, df1, df2)
        # SPEC.md Section 3.5: Statistical power from noncentral F survival function
        pwr = ncf_power(crit_f, df1, df2, lambda_val)
        return pwr, crit_f, df2, tot_n, lambda_val

    # SPEC.md Section 4: Minimum sample size per group is n = 2 (N_min = 2k)
    low_n = 2
    pwr, crit_f, df2, tot_n, lambda_val = evaluate_n_per_group(low_n)
    # SPEC.md Section 4: Stopping condition Power >= target_power
    if pwr >= power_val:
        return AnovaOneWayResult(
            n_per_group=low_n,
            n_total=tot_n,
            actual_power=pwr,
            critical=crit_f,
            df1=df1,
            df2=df2,
            ncp=lambda_val,
        )

    # SPEC.md Section 4: O(log N) exponential bracketing to find upper bound
    high_n = 4
    # SPEC.md Section 4: Maximum N cap = 100,000,000
    while high_n * groups_val <= max_n:
        pwr, _, _, _, _ = evaluate_n_per_group(high_n)
        if pwr >= power_val:
            break
        low_n = high_n
        high_n *= 2

    # Check if max_n exceeded
    if high_n * groups_val > max_n:
        max_possible_n_per_group = max_n // groups_val
        pwr, _, _, _, _ = evaluate_n_per_group(max_possible_n_per_group)
        if pwr < power_val:
            raise CalculationError(
                f"A-priori search exceeded maximum sample size {max_n} without achieving target power {power_val}"
            )
        high_n = max_possible_n_per_group

    # SPEC.md Section 4: Binary search for exact smallest integer n >= 2 where Power >= target_power
    best_n = high_n
    while low_n <= high_n:
        mid = (low_n + high_n) // 2
        pwr, _, _, _, _ = evaluate_n_per_group(mid)
        if pwr >= power_val:
            best_n = mid
            high_n = mid - 1
        else:
            low_n = mid + 1

    pwr, crit_f, df2, tot_n, lambda_val = evaluate_n_per_group(best_n)

    # SPEC.md Section 5: Computed outputs
    return AnovaOneWayResult(
        n_per_group=best_n,
        n_total=tot_n,
        actual_power=pwr,
        critical=crit_f,
        df1=df1,
        df2=df2,
        ncp=lambda_val,
    )


def compute_post_hoc(
    effect_size_f: Any,
    alpha: Any,
    n_total: Any,
    groups: Any,
) -> AnovaOneWayResult:
    """Computes achieved statistical power (post-hoc analysis).

    SPEC.md Section 3: Formulas applied to given N and k.
    """
    f_val, alpha_val, groups_val, _, n_total_val = validate_anova_inputs(
        effect_size_f=effect_size_f,
        alpha=alpha,
        groups=groups,
        n_total=n_total,
    )

    # SPEC.md Section 3.1: df1 = k - 1
    df1 = groups_val - 1
    # SPEC.md Section 3.2: df2 = N - k
    df2 = n_total_val - groups_val
    # SPEC.md Section 3.3: lambda = f^2 * N
    lambda_val = (f_val ** 2) * n_total_val
    # SPEC.md Section 3.4: Critical F
    crit_f = f_inv_sf(alpha_val, df1, df2)
    # SPEC.md Section 3.5: Statistical power
    power = ncf_power(crit_f, df1, df2, lambda_val)
    # SPEC.md Section 5: n_per_group = N / k
    n_pg = n_total_val // groups_val

    return AnovaOneWayResult(
        n_per_group=n_pg,
        n_total=n_total_val,
        actual_power=power,
        critical=crit_f,
        df1=df1,
        df2=df2,
        ncp=lambda_val,
    )


def calculate_a_priori(
    effect_size_f: Any,
    alpha: Any,
    target_power: Any,
    groups: Any,
    max_n: int = 100_000_000,
) -> Union[AnovaOneWayResult, CalculationError]:
    """Pure functional interface: validated input in, structured result or structured error out.

    No printing, no file or network access, completely deterministic.
    """
    try:
        return compute_a_priori(
            effect_size_f=effect_size_f,
            alpha=alpha,
            target_power=target_power,
            groups=groups,
            max_n=max_n,
        )
    except CalculationError as err:
        return err
