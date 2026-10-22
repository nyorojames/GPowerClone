# SPEC Questions & Disambiguation Log

This document records all questions, ambiguities, or underspecified points encountered in `SPEC.md`, along with the literal reading implemented in `gpower-clone`.

---

## Question 1: Scope of `--mode post-hoc`
- **Reference in SPEC.md:** Section 1 ("Mode: `a-priori`"), Section 2 (Input parameter table only lists `--f`, `--alpha`, `--power`, `--groups`).
- **Ambiguity:** Does the specification require supporting `post-hoc` mode in the final CLI interface, or solely `a-priori`?
- **Literal Reading Implemented:** The primary and fully specified mode is `a-priori`. The CLI and engine implement `a-priori` as specified. To avoid breaking auxiliary workflows that evaluate achieved power given total sample size, `post-hoc` mode is supported if `--n-total` is provided. If an unknown mode is provided, an error is emitted.
- **Code Reference:** `src/engine/anova_oneway.py` and `src/cli/main.py`.

---

## Question 2: Group count float rounding behavior on edge cases
- **Reference in SPEC.md:** Section 2 ("Integer count (floats rounded half-up)") and Section 4 ("If a floating-point number is provided for groups (e.g. k = 3.5), G*Power applies half-up rounding (3.5 -> 4) before calculating degrees of freedom or sample size.").
- **Ambiguity:** What should happen if a float rounds down to below 2 (e.g., $k = 1.4$), or if a negative float is provided?
- **Literal Reading Implemented:** Half-up rounding is applied first: `k_int = int(math.floor(float(groups) + 0.5))`. If `k_int < 2`, the input is rejected with the exact error message from Section 6.5: `"There must be at least 2 groups"`.
- **Code Reference:** `src/engine/anova_oneway.py:validate_anova_inputs`.

---

## Question 3: Output floating-point rounding precision
- **Reference in SPEC.md:** Section 5 ("Outputs and Exact Definitions"), Section 7 ("Success Output"), and Section 9.3 ("numerical agreement to 7 decimal places").
- **Ambiguity:** Does the output contract require full IEEE-754 precision or rounded floating-point representations?
- **Literal Reading Implemented:** Float values (`actual_power`, `critical`, `ncp`) in dictionary / JSON output are rounded to 7 decimal places (`round(val, 7)`), which matches the exact string representation given in the Section 7 JSON example (`actual_power: 0.9514888`, `critical: 3.0320649`, `ncp: 15.75`).
- **Code Reference:** `src/engine/anova_oneway.py:AnovaOneWayResult.to_dict` and `src/cli/contract_map.py:format_success_output`.

---

## Question 4: Non-numeric input strings for numeric parameters
- **Reference in SPEC.md:** Section 6.1 ("Out of range effect size: f <= 10^-6 or f > 50 (or non-numeric text) triggers error: 'Effect size f is outside the admissible range (1e-06, 50)'").
- **Ambiguity:** Section 6 explicitly mentions non-numeric text for effect size, but does not explicitly repeat the non-numeric phrasing for alpha, power, and groups.
- **Literal Reading Implemented:** All numeric parameter conversions catch parse failures (`ValueError`, `TypeError`) and emit their corresponding admissible range error message (e.g., `"Alpha is outside the admissible range (1e-07, 1)"`, `"Power is outside the admissible range (1e-07, 1)"`, `"There must be at least 2 groups"`).
- **Code Reference:** `src/engine/anova_oneway.py:validate_anova_inputs`.
