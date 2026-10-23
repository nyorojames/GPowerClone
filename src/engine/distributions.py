"""Statistical distribution functions implemented from first principles.

Provides central F and noncentral F distribution CDF, survival, and inverse survival
functions using Lanczos gamma approximation, continued-fraction incomplete beta,
and Poisson mixture series expansion.

SPEC.md References:
- Section 4.1: Central F distribution critical value F_crit.
- Section 4.1: Noncentral F distribution survival function for statistical power.
"""

import math


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
    """Evaluates continued fraction for incomplete beta function by modified Lentz's method."""
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

    SPEC.md Section 4.1:
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
        diff = val - alpha
        if abs(diff) <= 1e-15 * max(alpha, 1.0) or (high - low) <= 1e-14 * max(mid, 1.0):
            return mid
        if val > alpha:
            low = mid
        else:
            high = mid

    return (low + high) / 2.0


def ln_poisson_mode(mu: float) -> float:
    """Computes ln(P(X = floor(mu))) where X ~ Poisson(mu)."""
    if mu <= 0.0:
        return 0.0
    M = int(mu)
    if M == 0:
        return -mu
    if M < 20:
        return -mu + M * math.log(mu) - log_gamma(M + 1.0)
    delta = mu - M
    corr = M * math.log1p(delta / M) - delta if delta > 0.0 else 0.0
    return -0.5 * math.log(2.0 * math.pi * M) + corr - 1.0 / (12.0 * M) + 1.0 / (360.0 * M**3)


def ncf_power(f_crit: float, df1: float, df2: float, lambda_nc: float) -> float:
    """Noncentral F survival function (Power) = P(F(df1, df2, lambda_nc) >= f_crit).

    SPEC.md Section 2.4 & 4.1:
    Numerically stable calculation across all lambda >= 0 and N <= 2147483647.
    Evaluates Poisson weights in log space starting at the mode M = floor(lambda/2),
    with tail cutoff and asymptotic bounds for extreme noncentrality.
    """
    if math.isnan(f_crit) or math.isnan(lambda_nc):
        return float("nan")
    if f_crit <= 0.0:
        return 1.0
    if lambda_nc < 0.0:
        raise ValueError(f"noncentrality parameter lambda must be >= 0, got {lambda_nc}")
    if lambda_nc == 0.0:
        return f_sf(f_crit, df1, df2)

    x = (df1 * f_crit) / (df1 * f_crit + df2)
    if x <= 0.0:
        return 1.0
    if x >= 1.0:
        return 0.0

    mu = lambda_nc / 2.0

    # Tail cutoff & extreme check for large mu
    if mu > 1000.0:
        sigma = math.sqrt(mu)
        j_min = max(0, int(mu - 8.0 * sigma))
        ix_min = betai(df1 / 2.0 + j_min, df2 / 2.0, x)
        if ix_min < 1e-15:
            return 1.0
        j_max = int(mu + 8.0 * sigma) + 1
        ix_max = betai(df1 / 2.0 + j_max, df2 / 2.0, x)
        if 1.0 - ix_max < 1e-15:
            return 0.0

    M = int(mu)
    ln_w_M = ln_poisson_mode(mu)
    w_M = math.exp(ln_w_M)

    T_M = 1.0 - betai(df1 / 2.0 + M, df2 / 2.0, x)
    power = w_M * T_M
    w_sum = w_M

    # Expand upward: j = M + 1, M + 2, ...
    w = w_M
    j = M
    while True:
        j += 1
        w *= mu / j
        if w < 1e-18:
            break
        T_j = 1.0 - betai(df1 / 2.0 + j, df2 / 2.0, x)
        power += w * T_j
        w_sum += w
        if 1.0 - T_j < 1e-16:
            while True:
                j += 1
                w *= mu / j
                if w < 1e-18:
                    break
                power += w
                w_sum += w
            break

    # Expand downward: j = M - 1, M - 2, ... 0
    w = w_M
    j = M
    while j > 0:
        w *= j / mu
        j -= 1
        if w < 1e-18:
            break
        T_j = 1.0 - betai(df1 / 2.0 + j, df2 / 2.0, x)
        power += w * T_j
        w_sum += w
        if T_j < 1e-16:
            while j > 0:
                w *= j / mu
                j -= 1
                if w < 1e-18:
                    break
                w_sum += w
            break

    if w_sum > 0.0:
        power /= w_sum

    return min(1.0, max(0.0, power))
