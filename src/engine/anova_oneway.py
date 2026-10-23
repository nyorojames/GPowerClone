"""Calculation engine for one-way ANOVA omnibus F-test.

SPEC.md References:
- Section 1.1: Scope and mode classification.
- Section 2.3: Inputs and output schemas.
- Section 4.1: Mathematical algorithm (df1, df2, noncentrality, critical_f, power).
- Section 4.2: A-priori search algorithm, divisibility rule, stopping condition.
- Section 4.3: Post-hoc search, average group size, refusal rules.
- Section 5.1: Refusal mapping table and error codes.
- Section 5.2: Resolution of non-integer inputs and boundary handling.
"""

from dataclasses import dataclass
import math
from typing import Any, Dict, Optional, Union

from src.engine.distributions import f_sf, f_inv_sf, ncf_power


@dataclass(frozen=True)
class EngineResult:
    """Statistical power analysis output parameters.

    SPEC.md Section 2.3 & 4.1.
    """
    df1: int
    df2: int
    ncp: float
    critical_f: float
    actual_power: Optional[float] = None
    power: Optional[float] = None
    n_total: Optional[int] = None
    n_per_group: Optional[int] = None
    alpha: Optional[float] = None
    beta: Optional[float] = None
    f: Optional[float] = None
    is_success: bool = True
    error: Optional[str] = None

    # Backward-compatible property aliases
    @property
    def critical(self) -> float:
        """Alias for critical_f."""
        return self.critical_f

    @property
    def df_num(self) -> int:
        """Alias for df1."""
        return self.df1

    @property
    def df_denom(self) -> int:
        """Alias for df2."""
        return self.df2


# Backward compatibility alias
AnovaOneWayResult = EngineResult


class EngineError(ValueError):
    """Structured error for contract violations, invalid inputs, or calculation limits.

    SPEC.md Section 3.1 & 3.2.
    """
    def __init__(self, code: str, message: str, field: Optional[str] = None, exit_code: int = 2):
        super().__init__(message)
        self.code = code
        self.message = message
        self.field = field
        self.exit_code = exit_code
        self.is_success = False
        self.error = message

    def to_dict(self) -> Dict[str, Any]:
        """SPEC.md Section 3.1."""
        out: Dict[str, Any] = {"error": self.message, "code": self.code}
        if self.field is not None:
            out["field"] = self.field
        return out


# Backward compatibility alias
CalculationError = EngineError


# ============================================================================
# Input Validation Helpers (SPEC.md Section 3.2, 5.1, 5.2)
# ============================================================================
def _parse_int_exact(val: Any, field_name: str) -> int:
    """Parses value ensuring strict integer format (no decimals or non-digits).

    SPEC.md Section 5.2 item 1: Non-integer float on integer field produces INVALID_VALUE.
    """
    val_str = str(val).strip()
    if "." in val_str:
        raise EngineError(
            code="INVALID_VALUE",
            message=f"Field '{field_name}' must be an integer, got '{val_str}'",
            field=field_name,
        )
    try:
        return int(val_str)
    except (ValueError, TypeError):
        raise EngineError(
            code="INVALID_VALUE",
            message=f"Field '{field_name}' must be an integer, got '{val_str}'",
            field=field_name,
        )


def _parse_float(val: Any, field_name: str) -> float:
    """Parses floating-point value.

    SPEC.md Section 5.1 v045: Non-numeric string produces INVALID_VALUE.
    """
    try:
        f_val = float(val)
        if math.isnan(f_val) or math.isinf(f_val):
            raise ValueError()
        return f_val
    except (ValueError, TypeError):
        raise EngineError(
            code="INVALID_VALUE",
            message=f"Field '{field_name}' must be a valid number, got '{val}'",
            field=field_name,
        )


def validate_effect_size(f_raw: Any) -> float:
    """SPEC.md Section 2.3, 5.1 (v041, v042), 5.2 item 2: Range [1e-6, 50]."""
    f_val = _parse_float(f_raw, "f")
    if not (1e-6 <= f_val <= 50.0):
        raise EngineError(
            code="OUT_OF_RANGE",
            message="Effect size f is outside the admissible range (1e-06, 50)",
            field="f",
        )
    return f_val


def validate_alpha(alpha_raw: Any) -> float:
    """SPEC.md Section 2.3, 5.1 (v039, v040), 5.2 item 2: Range [1e-7, 1)."""
    alpha_val = _parse_float(alpha_raw, "alpha")
    if not (1e-7 <= alpha_val < 1.0):
        raise EngineError(
            code="OUT_OF_RANGE",
            message="Alpha is outside the admissible range (1e-07, 1)",
            field="alpha",
        )
    return alpha_val


def validate_power(power_raw: Any) -> float:
    """SPEC.md Section 2.3, 5.1 (v036, v038), 5.2 item 2: Range [1e-7, 1)."""
    power_val = _parse_float(power_raw, "power")
    if not (1e-7 <= power_val < 1.0):
        raise EngineError(
            code="OUT_OF_RANGE",
            message="Power is outside the admissible range (1e-07, 1)",
            field="power",
        )
    return power_val


def validate_groups(groups_raw: Any) -> int:
    """SPEC.md Section 2.3, 5.1 (v043, v044), 5.2 item 1: Integer >= 2."""
    groups_val = _parse_int_exact(groups_raw, "groups")
    if groups_val < 2:
        raise EngineError(
            code="OUT_OF_RANGE",
            message="There must be at least 2 groups",
            field="groups",
        )
    return groups_val


def validate_n_total(n_total_raw: Any, groups_val: int) -> int:
    """SPEC.md Section 2.3, 4.3, 5.1: Integer in [k+1, 2147483647]."""
    n_val = _parse_int_exact(n_total_raw, "n_total")
    if n_val <= 0:
        raise EngineError(
            code="OUT_OF_RANGE",
            message="Total sample size must be positive",
            field="n_total",
        )
    if n_val > 2_147_483_647:
        raise EngineError(
            code="OUT_OF_RANGE",
            message="Total sample size exceeds maximum limit (2147483647)",
            field="n_total",
        )
    if n_val <= groups_val:
        raise EngineError(
            code="INCONSISTENT",
            message="Sample size must be greater than the number of groups (k)",
            field="n_total",
        )
    return n_val


def validate_beta_alpha_ratio(ratio_raw: Any) -> float:
    """SPEC.md Section 6.2: ratio > 0."""
    ratio_val = _parse_float(ratio_raw, "beta_alpha_ratio")
    if ratio_val <= 0.0:
        raise EngineError(
            code="OUT_OF_RANGE",
            message="Ratio beta/alpha must be positive",
            field="beta_alpha_ratio",
        )
    return ratio_val


# ============================================================================
# Engine Calculation Routines (SPEC.md Section 4)
# ============================================================================
def compute_a_priori(
    effect_size_f: Any,
    alpha: Any,
    target_power: Any,
    groups: Any,
    max_n: int = 2_147_483_647,
) -> EngineResult:
    """Computes required total sample size N and actual power (a-priori analysis).

    SPEC.md Section 4.1 & 4.2:
    - Balanced group divisibility rule: N = n * k with n >= 2 (Section 4.2).
    - Minimum sample size: N_min = 2k (Section 4.2).
    - Stopping condition: smallest integer n >= 2 where Power >= target_power (Section 4.2).
    - Bracketing plus bisection over integer n.
    """
    f_val = validate_effect_size(effect_size_f)
    alpha_val = validate_alpha(alpha)
    power_val = validate_power(target_power)
    groups_val = validate_groups(groups)

    # SPEC.md Section 5.1 v035: Inconsistent if target power < alpha
    if power_val < alpha_val:
        raise EngineError(
            code="INCONSISTENT",
            message="Power must be greater than or equal to alpha",
            field="power",
        )

    # SPEC.md Section 4.1: df1 = k - 1
    df1 = groups_val - 1

    def eval_n(n_pg: int):
        tot = n_pg * groups_val
        df2 = tot - groups_val
        lam = (f_val ** 2) * tot
        crit = f_inv_sf(alpha_val, df1, df2)
        pwr = ncf_power(crit, df1, df2, lam)
        return pwr, crit, df2, tot, lam

    # Minimum sample size: n = 2 observations per group (Section 4.2)
    pwr_min, crit_min, df2_min, tot_min, lam_min = eval_n(2)
    if pwr_min >= power_val:
        return EngineResult(
            n_per_group=2,
            n_total=tot_min,
            actual_power=pwr_min,
            critical_f=crit_min,
            df1=df1,
            df2=df2_min,
            ncp=lam_min,
        )

    # Exponential bracketing to find upper bound (Section 4.2)
    low_n = 2
    high_n = 4
    max_pg = max_n // groups_val

    while high_n <= max_pg:
        pwr, _, _, _, _ = eval_n(high_n)
        if pwr >= power_val:
            break
        low_n = high_n
        high_n *= 2

    if high_n > max_pg:
        high_n = max_pg
        pwr, _, _, _, _ = eval_n(high_n)
        if pwr < power_val:
            raise EngineError(
                code="NO_SOLUTION",
                message=f"Sample size exceeds maximum 32-bit limit without reaching target power",
            )

    # Binary search (bisection) over integer n in [low_n, high_n]
    best_n = high_n
    while low_n <= high_n:
        mid = (low_n + high_n) // 2
        pwr, _, _, _, _ = eval_n(mid)
        if pwr >= power_val:
            best_n = mid
            high_n = mid - 1
        else:
            low_n = mid + 1

    pwr, crit, df2, tot, lam = eval_n(best_n)
    return EngineResult(
        n_per_group=best_n,
        n_total=tot,
        actual_power=pwr,
        critical_f=crit,
        df1=df1,
        df2=df2,
        ncp=lam,
    )


def compute_post_hoc(
    effect_size_f: Any,
    alpha: Any,
    n_total: Any,
    groups: Any,
) -> EngineResult:
    """Computes achieved statistical power (post-hoc analysis).

    SPEC.md Section 4.1 & 4.3:
    - Direct power evaluation using noncentral F distribution.
    - If N is not divisible by k, calculation succeeds using average group size (Section 4.3).
    - If N <= k, rejected with INCONSISTENT (Section 4.3).
    """
    f_val = validate_effect_size(effect_size_f)
    alpha_val = validate_alpha(alpha)
    groups_val = validate_groups(groups)
    n_total_val = validate_n_total(n_total, groups_val)

    # SPEC.md Section 4.1: df1 = k - 1, df2 = N - k, lambda = f^2 * N
    df1 = groups_val - 1
    df2 = n_total_val - groups_val
    lam = (f_val ** 2) * n_total_val
    crit = f_inv_sf(alpha_val, df1, df2)
    pwr = ncf_power(crit, df1, df2, lam)
    n_pg = n_total_val // groups_val

    return EngineResult(
        n_per_group=n_pg,
        n_total=n_total_val,
        power=pwr,
        critical_f=crit,
        df1=df1,
        df2=df2,
        ncp=lam,
    )


def compute_compromise(
    effect_size_f: Any,
    beta_alpha_ratio: Any,
    n_total: Any,
    groups: Any,
) -> EngineResult:
    """Computes implied alpha, beta, and power (compromise analysis).

    ASSUMPTION: see SPEC_QUESTIONS.md (Section 1.1, 6.2).
    """
    f_val = validate_effect_size(effect_size_f)
    ratio_val = validate_beta_alpha_ratio(beta_alpha_ratio)
    groups_val = validate_groups(groups)
    n_total_val = validate_n_total(n_total, groups_val)

    df1 = groups_val - 1
    df2 = n_total_val - groups_val
    lam = (f_val ** 2) * n_total_val

    # Bisection on critical_f
    low = 0.00001
    high = 50.0
    for _ in range(90):
        mid = (low + high) / 2.0
        a = f_sf(mid, df1, df2)
        b = 1.0 - ncf_power(mid, df1, df2, lam)
        if a <= 1e-15:
            high = mid
            continue
        cur_ratio = b / a
        if cur_ratio < ratio_val:
            low = mid
        else:
            high = mid

    crit = (low + high) / 2.0
    a = f_sf(crit, df1, df2)
    pwr = ncf_power(crit, df1, df2, lam)
    b = 1.0 - pwr

    return EngineResult(
        df1=df1,
        df2=df2,
        ncp=lam,
        critical_f=crit,
        alpha=a,
        beta=b,
        power=pwr,
    )


def compute_criterion(
    effect_size_f: Any,
    target_power: Any,
    n_total: Any,
    groups: Any,
) -> EngineResult:
    """Computes required alpha (criterion analysis).

    ASSUMPTION: see SPEC_QUESTIONS.md (Section 1.1, 6.2).
    """
    f_val = validate_effect_size(effect_size_f)
    power_val = validate_power(target_power)
    groups_val = validate_groups(groups)
    n_total_val = validate_n_total(n_total, groups_val)

    df1 = groups_val - 1
    df2 = n_total_val - groups_val
    lam = (f_val ** 2) * n_total_val

    # Bisection on critical_f where ncf_power(critical_f) == target_power
    low = 0.00001
    high = 100.0
    for _ in range(90):
        mid = (low + high) / 2.0
        p = ncf_power(mid, df1, df2, lam)
        if p > power_val:
            low = mid
        else:
            high = mid

    crit = (low + high) / 2.0
    a = f_sf(crit, df1, df2)

    return EngineResult(
        df1=df1,
        df2=df2,
        ncp=lam,
        critical_f=crit,
        alpha=a,
    )


def compute_sensitivity(
    alpha: Any,
    target_power: Any,
    n_total: Any,
    groups: Any,
) -> EngineResult:
    """Computes minimum detectable effect size f (sensitivity analysis).

    ASSUMPTION: see SPEC_QUESTIONS.md (Section 1.1, 6.2).
    """
    alpha_val = validate_alpha(alpha)
    power_val = validate_power(target_power)
    groups_val = validate_groups(groups)
    n_total_val = validate_n_total(n_total, groups_val)

    df1 = groups_val - 1
    df2 = n_total_val - groups_val
    crit = f_inv_sf(alpha_val, df1, df2)

    # Bracket upper bound on lambda
    low = 0.0
    high = 10.0
    while high <= 500.0 and ncf_power(crit, df1, df2, high) < power_val:
        low = high
        high *= 2.0

    # Bisection on noncentrality parameter lambda
    for _ in range(90):
        mid = (low + high) / 2.0
        p = ncf_power(crit, df1, df2, mid)
        if p < power_val:
            low = mid
        else:
            high = mid

    lam = (low + high) / 2.0
    f_val = math.sqrt(lam / n_total_val)

    return EngineResult(
        df1=df1,
        df2=df2,
        ncp=lam,
        critical_f=crit,
        f=f_val,
    )


def calculate_a_priori(
    effect_size_f: Any,
    alpha: Any,
    target_power: Any,
    groups: Any,
    max_n: int = 2_147_483_647,
) -> Union[EngineResult, EngineError]:
    """Pure functional interface returning structured result or structured error.

    SPEC.md Section 2.1 & 4.2.
    """
    try:
        return compute_a_priori(
            effect_size_f=effect_size_f,
            alpha=alpha,
            target_power=target_power,
            groups=groups,
            max_n=max_n,
        )
    except EngineError as err:
        return err


def validate_anova_inputs(
    effect_size_f: Any,
    alpha: Any,
    groups: Any,
    power: Optional[Any] = None,
    n_total: Optional[Any] = None,
):
    """Backward compatibility validation function."""
    f_val = validate_effect_size(effect_size_f)
    alpha_val = validate_alpha(alpha)
    groups_val = validate_groups(groups)
    power_val = validate_power(power) if power is not None else None
    if power_val is not None and power_val < alpha_val:
        raise EngineError(
            code="INCONSISTENT",
            message="Power must be greater than or equal to alpha",
            field="power",
        )
    n_val = validate_n_total(n_total, groups_val) if n_total is not None else None
    return f_val, alpha_val, groups_val, power_val, n_val
