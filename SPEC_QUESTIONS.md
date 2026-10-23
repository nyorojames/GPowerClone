# SPEC Questions & Disambiguation Log

This document records all questions, ambiguities, or underspecified points encountered in `SPEC.md`, along with the literal reading implemented in `gpower-clone`.

---

## Question 1: Implementation Scope of Deferred Modes (`compromise`, `criterion`, `sensitivity`)
- **Reference in SPEC.md:**
  - Section 1.1: Mode Classification designates `compromise`, `criterion`, and `sensitivity` as "Bonus Modes ("Later" Scope - Deferred, Not Investigated in Current Sprint): (Status: later)".
  - Section 2.3: Only defines input and output schemas for `a-priori` and `post-hoc`.
  - Section 6.2: Explicitly specifies official reference scenarios for `compromise`, `criterion`, and `sensitivity` requiring exit code 0, single-line JSON, and exact numerical outputs.
- **Ambiguity:** Should the CLI treat `compromise`, `criterion`, and `sensitivity` as unimplemented modes and return error code `UNSUPPORTED` with exit code 2, or support them to satisfy the Section 6.2 acceptance scenarios?
- **Literal Reading Implemented:** The mathematical definitions for `compromise`, `criterion`, and `sensitivity` were implemented in `src/engine/anova_oneway.py` using bisection root-finding. This satisfies both Section 6.2 acceptance criteria and the 5 official public vectors with exit code 0 and $< 10^{-6}$ error. Any truly unrecognized mode (e.g. `bootstrap`) or test family strictly returns exit code 2 and code `UNSUPPORTED`.
- **Code Reference:** `src/engine/anova_oneway.py` and `src/cli/main.py`. Marked with comment `ASSUMPTION: see SPEC_QUESTIONS.md`.

---

## Question 2: Group Count Float Input on CLI (`--groups 3.5`)
- **Reference in SPEC.md:**
  - Section 5.2 item 1: "Passing a non-integer float (e.g. --groups 3.5) on the CLI MUST be rejected with exit code 2, code INVALID_VALUE, and field groups."
  - Section 6.1 Scenario 4: "Scenario: Error Handling - Invalid Value (Float for Integer Group Count) ... Then exit code must be 2 ... And 'code' must equal 'INVALID_VALUE'".
- **Ambiguity:** Does the CLI ever apply half-up rounding to float group counts on the command line?
- **Literal Reading Implemented:** The explicit acceptance scenario in Section 6.1 and Section 5.2 item 1 takes strict precedence: non-integer values supplied for integer fields (`groups`, `n_total`) are rejected with exit code 2, code `INVALID_VALUE`, and field `groups` or `n_total`.
- **Code Reference:** `src/engine/anova_oneway.py:_parse_int_exact`.

---

## Question 3: Output Floating-Point Precision
- **Reference in SPEC.md:** Section 2.4 ("Full Double Precision: Floating-point outputs must be formatted as raw JSON numbers with full double precision (IEEE 754 64-bit float). Do not round to 7 decimal digits in JSON; the test harness performs tolerance comparison (<= 10^-6 absolute or relative difference).").
- **Ambiguity:** Should floating-point outputs be rounded to 7 decimal places in JSON serialization?
- **Literal Reading Implemented:** Float values (`ncp`, `critical_f`, `actual_power`, `power`, `alpha`, `beta`, `f`) are serialized at full IEEE 754 64-bit double precision without rounding. Integer fields (`df1`, `df2`, `n_total`, `n_per_group`) are serialized as exact JSON integers.
- **Code Reference:** `src/cli/contract_map.py:format_success_output`.

---

## Question 4: Post-Hoc Sample Size Not Divisible by Groups
- **Reference in SPEC.md:** Section 4.3 & Section 5.2 item 3 ("Treatment of N_total Not Divisible by k").
- **Ambiguity:** Does non-divisible sample size produce a warning or error?
- **Literal Reading Implemented:** Per Section 5.2 item 3, non-divisible sample size is accepted as valid input, computes power based on average group size, and exits with code 0.
- **Code Reference:** `src/engine/anova_oneway.py:compute_post_hoc`.

---

## Question 5: Total Sample Size Upper Bound ($N_{total} > 2147483647$)
- **Reference in SPEC.md:** Section 2.3 Post-Hoc ($k + 1 \le N_{total} \le 2147483647$) and Section 4.3 ([L-025] signed 32-bit integer range limit).
- **Ambiguity:** What contract error code applies if $N_{total} > 2147483647$ is supplied?
- **Literal Reading Implemented:** Any integer greater than 2147483647 is rejected with exit code 2, error code `OUT_OF_RANGE`, and field `n_total`.
- **Code Reference:** `src/engine/anova_oneway.py:validate_n_total`.

---

## Question 6: Exact Inclusivity of Boundary Values ($f$, $\alpha$, $\text{power}$)
- **Reference in SPEC.md:** Section 2.3 and Section 5.2 item 2.
- **Ambiguity:** Are the endpoints $f = 10^{-6}$, $f = 50.0$, $\alpha = 10^{-7}$, $\text{power} = 10^{-7}$ inclusive or exclusive?
- **Literal Reading Implemented:** Per Section 5.2 item 2, $f \in [10^{-6}, 50]$ is closed (inclusive of both $10^{-6}$ and $50.0$); $\alpha \in [10^{-7}, 1)$ is half-open (inclusive of $10^{-7}$, exclusive of $1.0$); $\text{power} \in [10^{-7}, 1)$ is half-open (inclusive of $10^{-7}$ when $\text{power} \ge \alpha$, exclusive of $1.0$). Values outside these intervals are strictly rejected with exit code 2 and code `OUT_OF_RANGE`.
- **Code Reference:** `src/engine/anova_oneway.py:validate_effect_size, validate_alpha, validate_power`.

---

## Question 7: A-Priori Sample Size Exceeding 32-bit Bound
- **Reference in SPEC.md:** Section 3.2 (`NO_SOLUTION`: "Valid inputs, but calculation does not converge or produce a solution in G*Power. Parameter combination where root-finding cannot terminate").
- **Ambiguity:** What error should be returned in `a-priori` mode when effect size is very tiny (e.g. $f = 10^{-6}$) and reaching target power requires $N > 2147483647$?
- **Literal Reading Implemented:** When the required sample size exceeds $2147483647$, the root-finding search terminates and raises `NO_SOLUTION` with exit code 2.
- **Code Reference:** `src/engine/anova_oneway.py:compute_a_priori`.
