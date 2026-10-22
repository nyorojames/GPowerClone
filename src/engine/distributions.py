"""Statistical distribution functions implemented from first principles.

Provides central F and noncentral F distribution CDF, survival, and inverse survival
functions using Lanczos gamma approximation, continued-fraction incomplete beta,
and Poisson mixture series expansion.

SPEC.md References:
- Section 3.4: Central F distribution critical value F_crit.
- Section 3.5: Noncentral F distribution survival function for statistical power.
- Section 9.3: Numerical agreement to 7 decimal places.
"""

import math

# Optional scipy integration: Use scipy for distribution functions only as SPEC.md allows
try:
    from scipy.stats import f as _scipy_f, ncf as _scipy_ncf  # type: ignore
    _USE_SCIPY = True
except ImportError:
    _USE_SCIPY = False


def log_gamma(x: float) -> float:
    """Natural logarithm of the Gamma function ln(Gamma(x)) using Lanczos approximation."""
    if x <= 0.0:
        raise ValueError(f"log_gamma requires x > 0, got {x}")
    # Lanczos coefficients for g=7, n=9 (accuracy ~ 1e-15)
    p = [
        0.99999999999980993,
        676.5203681218851,
        -1259.1392167224028,
        771.32342877765313,
        -176.61502916214059,
        12.507343278686905,
        -0.13857109526572012,
        9.9843695780195716e-6,
        1.5056327351493116e-7,
    ]
    if x < 0.5:
        # Reflection formula
        return math.log(math.pi / math.sin(math.pi * x)) - log_gamma(1.0 - x)
    x -= 1.0
    a = p[0]
    t = x + 7.5
    for i in range(1, len(p)):
        a += p[i] / (x + i)
    return 0.5 * math.log(2.0 * math.pi) + (x + 0.5) * math.log(t) - t + math.log(a)


def _betacf(a: float, b: float, x: float, max_it: int = 500, eps: float = 3e-14) -> float:
    """Evaluates continued fraction for incomplete beta function by modified Lentz's method.

    SPEC.md Section 9.3: Continued fraction series expansion.
    """
    fpmin = 1e-30
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < fpmin:
        d = fpmin
    d = 1.0 / d
    h = d

    for m in range(1, max_it + 1):
        m2 = 2 * m
        # One step of the recurrence (even)
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        h *= d * c

        # Next step of the recurrence (odd)
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        del_val = d * c
        h *= del_val
        if abs(del_val - 1.0) <= eps:
            break

    return h


def betai(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta function I_x(a, b)."""
    if x < 0.0 or x > 1.0:
        raise ValueError(f"x must be in [0, 1], got {x}")
    if x == 0.0:
        return 0.0
    if x == 1.0:
        return 1.0

    # Factor bt = x^a * (1-x)^b / (a * Beta(a,b))
    bt = math.exp(
        log_gamma(a + b)
        - log_gamma(a)
        - log_gamma(b)
        + a * math.log(x)
        + b * math.log(1.0 - x)
    )

    # Use symmetry transformation if x is beyond transition point
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    else:
        return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def f_cdf(f_val: float, df1: float, df2: float) -> float:
    """Cumulative distribution function P(F <= f_val) for central F-distribution."""
    if f_val <= 0.0:
        return 0.0
    x = (df1 * f_val) / (df1 * f_val + df2)
    return betai(df1 / 2.0, df2 / 2.0, x)


def f_sf(f_val: float, df1: float, df2: float) -> float:
    """Survival function (upper tail) P(F >= f_val) for central F-distribution."""
    if f_val <= 0.0:
        return 1.0
    return 1.0 - f_cdf(f_val, df1, df2)


def f_inv_sf(alpha: float, df1: float, df2: float, tol: float = 1e-12) -> float:
    """Inverse survival function: finds critical F such that P(F >= F_crit) == alpha.

    SPEC.md Section 3.4:
    P(F(df1, df2) >= F_crit) = alpha <=> F_crit = F_central^-1(1 - alpha; df1, df2)
    """
    if not (0.0 < alpha < 1.0):
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")

    # Bracketing bounds
    low = 0.0
    high = 10.0
    while f_sf(high, df1, df2) > alpha:
        high *= 2.0

    # Binary search refinement followed by bisection
    for _ in range(120):
        mid = (low + high) / 2.0
        val = f_sf(mid, df1, df2)
        if abs(val - alpha) < tol or (high - low) < 1e-14:
            return mid
        if val > alpha:
            low = mid
        else:
            high = mid

    return (low + high) / 2.0


def ncf_power(f_crit: float, df1: float, df2: float, lambda_nc: float) -> float:
    """Noncentral F survival function (Power) = P(F(df1, df2, lambda_nc) >= f_crit).

    SPEC.md Section 3.5:
    Power = 1 - beta = 1 - F_nc(F_crit; df1, df2, lambda_nc)
    SPEC.md Section 9.3:
    Computed via the Poisson-weighted sum of central regularized incomplete beta functions.
    """
    if f_crit <= 0.0:
        return 1.0
    if lambda_nc < 0.0:
        raise ValueError(f"noncentrality parameter lambda must be >= 0, got {lambda_nc}")
    if lambda_nc == 0.0:
        return f_sf(f_crit, df1, df2)

    x = (df1 * f_crit) / (df1 * f_crit + df2)
    lam_half = lambda_nc / 2.0
    power = 0.0

    weight = math.exp(-lam_half)
    for j in range(1500):
        if weight > 1e-35:
            # P(F >= f_crit) term for degree of freedom (df1 + 2j, df2)
            term = 1.0 - betai(df1 / 2.0 + j, df2 / 2.0, x)
            power += weight * term

        weight *= lam_half / (j + 1)
        # Convergence threshold
        if weight < 1e-16 and j > lam_half:
            break

    return min(1.0, max(0.0, power))
