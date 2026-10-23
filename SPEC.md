# Functional & Behavioral Specification: One-Way ANOVA Omnibus F-Test

**Document Version:** 2.0.0 (Updated to match `CONTRACT.md` v1.0.0)  
**Test Family:** `anova-oneway`  
**Reference:** G*Power 3.1.9.7 (Windows)  
**Contract Version:** 1.0.0  

---

## 1. Scope & Modes

This specification defines the functional, behavioral, mathematical, and CLI contract requirements for the `anova-oneway` family (`G*Power: F tests – ANOVA: Fixed effects, omnibus, one-way`).

### 1.1 Mode Classification
- **Required Modes (Immediate Implementation Scope):**
  - `a-priori`: Compute required total sample size $N$ and actual power given effect size $f$, significance level $\alpha$, target power $1-\beta$, and group count $k$.
  - `post-hoc`: Compute achieved statistical power given effect size $f$, significance level $\alpha$, total sample size $N_{total}$, and group count $k$.
- **Bonus Modes ("Later" Scope - Deferred, Not Investigated in Current Sprint):**
  - `compromise`: Compute implied $\alpha$ and power given effect size $f$, error ratio $\beta/\alpha$, total sample size $N_{total}$, and group count $k$. *(Status: later)*
  - `criterion`: Compute required significance level $\alpha$ given effect size $f$, target power, total sample size $N_{total}$, and group count $k$. *(Status: later)*
  - `sensitivity`: Compute minimum detectable effect size $f$ given significance level $\alpha$, target power, total sample size $N_{total}$, and group count $k$. *(Status: later)*

---

## 2. CLI Invocation, Formatting, and Contract Invariants

### 2.1 Command Line Form
```bash
gpower-clone --test <TEST_ID> --mode <MODE_ID> [--<field> <value> ...]
```
- **Executable Name:** `gpower-clone`.
- **Parameter Syntax:** Every parameter is passed as `--<field> <value>`. Flag names match the contract field definitions exactly.
- **No Defaults:** The engine provides **no default parameter values**. Every required field for the selected mode must be explicitly provided. Omitting any required field produces a `MISSING_PARAM` error.
- **Unknown & Irrelevant Parameters:** Any unrecognized flag or any flag irrelevant to the active mode (e.g., providing `--power` in `post-hoc` mode, or providing `--n_total` in `a-priori` mode) is strictly rejected with an `UNKNOWN_PARAM` error.
- **Decimal Separator:** Always the dot (`0.05`). System locale must never influence number parsing or serialization.
- **Single-Line Output:** Standard output (`stdout`) must contain **exactly one line of valid JSON**, followed by a newline. No extra text, headers, logs, or debugging banners may be printed to `stdout`. All logging, warnings, or progress messages must be written to `stderr`.
- **Exit Codes:**
  - `0`: Successful execution.
  - `2`: Invalid user input (missing parameter, unknown parameter, syntax error, out of range, or inconsistent parameter combination).
  - `1`: Internal calculation error (e.g., algorithm failed to converge, unexpected runtime error).
- **Time Limit:** Execution must finish within **2.0 seconds** per invocation. No network calls are permitted.
- **Determinism:** Identical CLI inputs must unconditionally produce bitwise identical output JSON.

### 2.2 Version Query
```bash
gpower-clone --version
```
Output format (single-line JSON on `stdout`, exit code `0`):
```json
{"contract_version": "1.0.0", "name": "K3-solo", "engine": "Python 3.12"}
```

### 2.3 Input and Output Field Definitions for `anova-oneway`

#### A-Priori Mode (`--mode a-priori`)
- **Required Inputs:**
  - `--test`: String, must be `anova-oneway`.
  - `--mode`: String, must be `a-priori`.
  - `--f`: Float, Cohen's effect size $f$ ($10^{-6} \le f \le 50$, both boundaries inclusive).
  - `--alpha`: Float, significance level $\alpha$ ($10^{-7} \le \alpha < 1$, lower bound inclusive, upper bound exclusive).
  - `--power`: Float, target power $1-\beta$ ($10^{-7} \le \text{power} < 1$, lower bound inclusive, upper bound exclusive; must satisfy $\text{power} \ge \alpha$).
  - `--groups`: Integer, number of groups $k$ ($k \ge 2$, lower bound inclusive).
- **Output JSON Schema (Exit Code 0):**
  ```json
  {"ncp": <float>, "critical_f": <float>, "df1": <int>, "df2": <int>, "n_total": <int>, "actual_power": <float>}
  ```

#### Post-Hoc Mode (`--mode post-hoc`)
- **Required Inputs:**
  - `--test`: String, must be `anova-oneway`.
  - `--mode`: String, must be `post-hoc`.
  - `--f`: Float, Cohen's effect size $f$ ($10^{-6} \le f \le 50$, both boundaries inclusive).
  - `--alpha`: Float, significance level $\alpha$ ($10^{-7} \le \alpha < 1$, lower bound inclusive, upper bound exclusive).
  - `--n_total`: Integer, total sample size ($k + 1 \le N_{total} \le 2147483647$, minimum $k + 1$ inclusive, upper bound 2147483647 inclusive).
  - `--groups`: Integer, number of groups $k$ ($k \ge 2$, lower bound inclusive).
- **Output JSON Schema (Exit Code 0):**
  ```json
  {"ncp": <float>, "critical_f": <float>, "df1": <int>, "df2": <int>, "power": <float>}
  ```

### 2.4 Numeric Data Representation & Numerical Accuracy Requirements
- **Full Double Precision:** Floating-point outputs (`ncp`, `critical_f`, `actual_power`, `power`) must be formatted as raw JSON numbers with full double precision (IEEE 754 64-bit float). Do not round to 7 decimal digits in JSON; the test harness performs tolerance comparison ($\le 10^{-6}$ absolute or relative difference).
- **Exact Integers:** Integer fields (`n_total`, `df1`, `df2`) must be serialized as JSON integers (`305`, not `305.0` or `"305"`).
- **Accuracy and Numerical Stability:** Power and critical values must be correct to $10^{-6}$ (absolute or relative difference) for every total sample size $N_{total}$ up to $2147483647$ and any noncentrality parameter $\lambda$, including very large values where power approaches 1. The calculation must not underflow (e.g. producing 0.0 when true power is asymptotically 1.0), overflow, or return NaN or infinity. Every CLI invocation must finish in under 2.0 seconds.

---

## 3. Error Handling and The Seven Error Codes

When an error occurs, the engine emits a single line on `stdout` and exits with code `2` (for input/domain errors) or `1` (for internal engine errors).

### 3.1 Standard Error JSON Structure
```json
{"error": "<human readable explanation>", "code": "<ERROR_CODE>", "field": "<field_name>"}
```
- `error`: Informative error message string (in Turkish or English).
- `code`: Exactly one of the seven contract error codes.
- `field`: The name of the parameter triggering the failure (omit or null if not field-specific).

### 3.2 The Seven Contract Error Codes
| Code | Exit Code | Meaning & Condition | Example Trigger |
|---|---|---|---|
| `MISSING_PARAM` | `2` | A required field for the selected mode was omitted. | `--test anova-oneway --mode a-priori --f 0.25 --alpha 0.05 --groups 5` (missing `--power`) |
| `UNKNOWN_PARAM` | `2` | An unrecognized flag, or a flag irrelevant to the mode was supplied. | `--test anova-oneway --mode post-hoc ... --power 0.95` (`--power` is invalid in post-hoc) |
| `INVALID_VALUE` | `2` | Value cannot be parsed to expected type, or decimal passed for integer. | `--groups 3.5` (groups must be integer) or `--f abc` |
| `OUT_OF_RANGE` | `2` | Value is outside the admissible range defined in contract Section 5 or G*Power limits. | `--alpha 0.0` or `--alpha 1.0` or `--f -0.25` or `--groups 1` |
| `INCONSISTENT` | `2` | Values are individually valid, but mutually contradictory or invalid together. | `a-priori` with $\text{power} < \alpha$; `post-hoc` with $N_{total} \le groups$ ($df_2 \le 0$) |
| `UNSUPPORTED` | `2` | Unknown `--test` or `--mode` specified. | `--test t3-indep` or `--mode bootstrap` |
| `NO_SOLUTION` | `2` | Valid inputs, but calculation does not converge or produce a solution in G*Power. | Parameter combination where root-finding cannot terminate |

---

## 4. Mathematical Algorithm & Binary Behavior

### 4.1 Degrees of Freedom & Noncentrality
1. **Numerator degrees of freedom ($df_1$):**
   $$df_1 = k - 1$$
   *(Cites LEDGER.md L-005)*
2. **Denominator degrees of freedom ($df_2$):**
   $$df_2 = N_{total} - k$$
   *(Cites LEDGER.md L-006)*
3. **Noncentrality parameter ($\lambda$):**
   $$\lambda = f^2 \times N_{total}$$
   *(Cites LEDGER.md L-007)*
4. **Critical value ($F_{crit}$):**
   Inverse survival function of central $F(df_1, df_2)$ at $\alpha$:
   $$P(F(df_1, df_2) \ge F_{crit}) = \alpha \iff F_{crit} = F^{-1}_{central}(1 - \alpha; df_1, df_2)$$
   *(Cites LEDGER.md L-008)*
5. **Statistical Power:**
   Survival function of noncentral $F(df_1, df_2, \lambda)$ at $F_{crit}$:
   $$\text{Power} = 1 - F_{nc}(F_{crit}; df_1, df_2, \lambda)$$
   *(Cites LEDGER.md L-009)*

### 4.2 A-Priori Mode Search & Invariants
- **Balanced Group Divisibility Rule:**
  In a-priori mode, N_total is a multiple of the group count k: N_total = n × k with n ≥ 2 observations per group. N = k × ceil(N_continuous / k), where N_continuous is the real-valued solution. (Cites LEDGER.md L-010, L-026)
- **Search Stopping Condition:**
  Find the minimal integer $n \ge 2$ ($N_{total} = n \cdot k$) such that $\text{Power}(df_1, n k - k, f^2 n k, F_{crit}) \ge \text{target\_power}$. *(Cites LEDGER.md L-012)*.
- **Minimum $N_{total}$:** $N_{min} = 2k$ ($n = 2$ observations per group, $df_2 \ge k$). *(Cites LEDGER.md L-011)*.
- **Output:** Output field name for achieved power is `actual_power`.

### 4.3 Post-Hoc Mode Search & Invariants
- **Direct Power Evaluation:**
  Given (f, alpha, N_total, k), power is evaluated from the noncentral F distribution with df1 = k − 1, df2 = N_total − k and noncentrality = f² × N_total. (Cites LEDGER.md L-021)
- **Treatment of $N_{total}$ Not Divisible by $k$:**
  [L-022] If N_total is not a multiple of k, G*Power still performs the calculation and shows an informational message ("The total sample size (N) is not a multiple of the number of groups (k). The analysis was based on the average group size."). The CLI treats this as a success: exit code 0 and the normal JSON output (interpretation: the contract defines no warning code).
- **Treatment of $N_{total} \le k$ ($df_2 \le 0$):**
  [DOK / GUI - L-023] If N_total ≤ k, G*Power refuses the calculation and shows "Sample size must be greater than the number of groups (k)". CLI: exit code 2, code INCONSISTENT (interpretation), field n_total.
- **Minimum $N_{total}$:**
  [DOK / GUI - L-024] In post-hoc mode, the minimum valid total sample size is strictly $N_{min} = k + 1$ ($df_2 = 1$). For $k=2$, absolute minimum $N_{total} = 3$.
- **Upper Limit of $N_{total}$:**
  [L-025] G*Power imposes no upper limit on N_total other than the signed 32-bit integer range (N_total ≤ 2147483647).
- **Output:** Output field name for achieved power in post-hoc mode is `power`.

---

## 5. Error Mapping for Observed Refusals & Open Ambiguities

### 5.1 Refusal Mapping Table
The following table maps every rejection observed in G*Power testing to its contract error code and field:

| Vector / Input | G*Power Refusal Note / Dialog | Contract Code | Field | Status / Authority |
|---|---|---|---|---|
| `v035` (`power < alpha`) | *"Power must be greater than or equal to alpha."* | `INCONSISTENT` | `power` | Stated in CONTRACT.md §2.4 |
| `v036` (`power = 1.0`) | *"Power is outside the admissible range (1e-07, 1)."* | `OUT_OF_RANGE` | `power` | Stated in CONTRACT.md §5 |
| `v038` (`power = 0.0`) | *"Power is outside the admissible range (1e-07, 1)."* | `OUT_OF_RANGE` | `power` | Stated in CONTRACT.md §5 |
| `v039` (`alpha = 0.0`) | *"Alpha is outside the admissible range (1e-07, 1)."* | `OUT_OF_RANGE` | `alpha` | Stated in CONTRACT.md §5 |
| `v040` (`alpha = 1.0`) | *"Alpha is outside the admissible range (1e-07, 1)."* | `OUT_OF_RANGE` | `alpha` | Stated in CONTRACT.md §5 |
| `v041` (`f = 0.0`) | *"Effect size f is outside the admissible range (1e-06, 50)."* | `OUT_OF_RANGE` | `f` | Stated in CONTRACT.md §5 |
| `v042` (`f = -0.25`) | *"Effect size f is outside the admissible range (1e-06, 50)."* | `OUT_OF_RANGE` | `f` | Stated in CONTRACT.md §5 |
| `v043` (`groups = 1`) | *"There must be at least 2 groups."* | `OUT_OF_RANGE` | `groups` | MY INTERPRETATION ($k < 2$ outside range $\ge 2$) |
| `v044` (`groups = 0`) | *"There must be at least 2 groups."* | `OUT_OF_RANGE` | `groups` | MY INTERPRETATION ($k < 2$ outside range $\ge 2$) |
| `v045` (`f = "abc"`) | Non-numeric string in edit control | `INVALID_VALUE` | `f` | MY INTERPRETATION (CONTRACT.md §2.4: non-number is `INVALID_VALUE`) |
| Post-hoc $N_{total} \le k$ | *"Sample size must be greater than the number of groups (k)"* | `INCONSISTENT` | `n_total` | MY INTERPRETATION ($N \ge 2, k \ge 2$ valid individually, combined $df_2 \le 0$ meaningless) |
| Missing required flag | Required parameter omitted | `MISSING_PARAM` | `<missing_field>` | Stated in CONTRACT.md §2.1, §2.4 |
| Irrelevant/unknown flag | Extra parameter supplied | `UNKNOWN_PARAM` | `<extra_field>` | Stated in CONTRACT.md §2.1, §2.4 |

### 5.2 Resolution of Open Ambiguities
1. **Non-Integer Group Count (`groups = 3.5`):**
   - *Observation:* In GUI vector `v046`, typing `3.5` into G*Power rounds half-up to 4.
   - *Contract Clause:* CONTRACT.md §2.4 defines `INVALID_VALUE` as: *"Sayı değil, tam sayı olması gereken yerde ondalık vb."*. Furthermore, CONTRACT.md §5 explicitly lists `groups` as `tam sayı`.
   - *Decision (MY INTERPRETATION):* Passing a non-integer float (e.g. `--groups 3.5`) on the CLI MUST be rejected with exit code `2`, code `INVALID_VALUE`, and field `groups`. Silently rounding float inputs on CLI violates CONTRACT.md §2.4.
2. **Exact Inclusivity of Boundary Values ($f$, $\alpha$, $\text{power}$, $k$):**
   - *Observation:* Testing at boundary endpoints settles the exact domain boundaries:
     - **Effect size $f$:** Admissible interval is $[10^{-6}, 50]$ (both $f = 10^{-6}$ and $f = 50.0$ are inclusive and accepted; $f < 10^{-6}$ or $f > 50$ produces "Effect size f is outside the admissible range (1e-06, 50)").
     - **Alpha $\alpha$:** Admissible interval is $[10^{-7}, 1)$ (lower boundary $\alpha = 10^{-7}$ is inclusive and accepted; $\alpha < 10^{-7}$ or $\alpha \ge 1$ produces "Alpha is outside the admissible range (1e-07, 1)").
     - **Power:** Admissible interval is $[10^{-7}, 1)$ (lower boundary $\text{power} = 10^{-7}$ is inclusive and accepted when $\text{power} \ge \alpha$; $\text{power} < 10^{-7}$ or $\text{power} \ge 1$ produces "Power is outside the admissible range (1e-07, 1)").
     - **Groups $k$:** Admissible range is integer $k \ge 2$ ($k = 2$ is inclusive and accepted; $k < 2$ produces "There must be at least 2 groups").
   - *Decision:* Values outside these settled inclusive/exclusive intervals MUST be rejected with exit code `2` and code `OUT_OF_RANGE`.
3. **Post-Hoc Sample Size Not Divisible by Groups ($N_{total} \pmod k \ne 0$):**
   - *Observation:* G*Power shows an informational message dialog but does NOT abort the calculation; it computes power using the average group size $N_{total} / k$ and outputs the results.
   - *Decision (MY INTERPRETATION):* Because CONTRACT.md §2.3 specifies single-line JSON on `stdout` without warning wrappers, the CLI MUST accept non-divisible $N_{total}$, compute power via average group size, and exit with code `0`.

---

## 6. Acceptance Criteria in Gherkin

### 6.1 General Contract & CLI Rule Scenarios

```gherkin
Feature: CLI Contract Rules and Error Handling

  Scenario: Version Query
    When the CLI executes with "--version"
    Then exit code must be 0
    And stdout must be single-line JSON
    And "contract_version" must equal "1.0.0"
    And "name" must be present
    And "engine" must be present

  Scenario: Error Handling - Missing Required Parameter
    When the CLI executes with "--test anova-oneway --mode a-priori --f 0.25 --alpha 0.05 --groups 5"
    Then exit code must be 2
    And stdout must be single-line JSON
    And "code" must equal "MISSING_PARAM"
    And "field" must equal "power"
    And "error" must be present

  Scenario: Error Handling - Unknown / Irrelevant Parameter in Post-Hoc
    When the CLI executes with "--test anova-oneway --mode post-hoc --f 0.25 --alpha 0.05 --n_total 100 --groups 5 --power 0.95"
    Then exit code must be 2
    And stdout must be single-line JSON
    And "code" must equal "UNKNOWN_PARAM"
    And "field" must equal "power"
    And "error" must be present

  Scenario: Error Handling - Invalid Value (Float for Integer Group Count)
    When the CLI executes with "--test anova-oneway --mode a-priori --f 0.25 --alpha 0.05 --power 0.95 --groups 3.5"
    Then exit code must be 2
    And stdout must be single-line JSON
    And "code" must equal "INVALID_VALUE"
    And "field" must equal "groups"
    And "error" must be present

  Scenario: Error Handling - Out of Range Effect Size
    When the CLI executes with "--test anova-oneway --mode a-priori --f -0.25 --alpha 0.05 --power 0.95 --groups 5"
    Then exit code must be 2
    And stdout must be single-line JSON
    And "code" must equal "OUT_OF_RANGE"
    And "field" must equal "f"

  Scenario: Error Handling - Out of Range Alpha Boundary
    When the CLI executes with "--test anova-oneway --mode a-priori --f 0.25 --alpha 0.0 --power 0.95 --groups 5"
    Then exit code must be 2
    And stdout must be single-line JSON
    And "code" must equal "OUT_OF_RANGE"
    And "field" must equal "alpha"

  Scenario: Error Handling - Inconsistent Parameters (Power Less Than Alpha)
    When the CLI executes with "--test anova-oneway --mode a-priori --f 0.25 --alpha 0.05 --power 0.04 --groups 5"
    Then exit code must be 2
    And stdout must be single-line JSON
    And "code" must equal "INCONSISTENT"
    And "field" must equal "power"

  Scenario: Error Handling - Post-Hoc Sample Size Less Than or Equal to Groups
    When the CLI executes with "--test anova-oneway --mode post-hoc --f 0.25 --alpha 0.05 --n_total 5 --groups 5"
    Then exit code must be 2
    And stdout must be single-line JSON
    And "code" must equal "INCONSISTENT"
    And "field" must equal "n_total"

  Scenario: Error Handling - Unsupported Test Family
    When the CLI executes with "--test non-existent-test --mode a-priori --f 0.25 --alpha 0.05 --power 0.95 --groups 5"
    Then exit code must be 2
    And stdout must be single-line JSON
    And "code" must equal "UNSUPPORTED"
    And "field" must equal "test"

  Scenario: Post-Hoc Calculation with Sample Size Not Divisible by Groups
    When the CLI executes with "--test anova-oneway --mode post-hoc --f 0.25 --alpha 0.05 --n_total 61 --groups 5"
    Then exit code must be 0
    And stdout must be single-line JSON
    And "df1" must equal 4
    And "df2" must equal 56
    And "power" must be present
```

### 6.2 Public Reference Vectors (`anova-oneway`)
The following scenarios represent the official public vectors published in `contract/CONTRACT.md` and `contract/public_vectors.jsonl`. Tagged `[DOK]`, source: instructor.

```gherkin
Feature: Official Instructor Public Reference Vectors for anova-oneway

  # [DOK] Source: Instructor public_vectors.jsonl ("id": "anova-oneway/a-priori")
  Scenario: Official Vector - anova-oneway a-priori
    When the CLI executes with "--test anova-oneway --mode a-priori --f 0.25 --alpha 0.05 --power 0.95 --groups 5"
    Then exit code must be 0
    And stdout must be single-line JSON
    And "df1" must equal 4
    And "df2" must equal 300
    And "n_total" must equal 305
    And "ncp" must equal 19.0625000 within 1e-6
    And "critical_f" must equal 2.4017397 within 1e-6
    And "actual_power" must equal 0.9521313 within 1e-6

  # [DOK] Source: Instructor public_vectors.jsonl ("id": "anova-oneway/post-hoc")
  Scenario: Official Vector - anova-oneway post-hoc
    When the CLI executes with "--test anova-oneway --mode post-hoc --f 0.25 --alpha 0.05 --n_total 100 --groups 5"
    Then exit code must be 0
    And stdout must be single-line JSON
    And "df1" must equal 4
    And "df2" must equal 95
    And "ncp" must equal 6.2500000 within 1e-6
    And "critical_f" must equal 2.4674936 within 1e-6
    And "power" must equal 0.4663312 within 1e-6

  # [DOK] Source: Instructor public_vectors.jsonl ("id": "anova-oneway/compromise") [STATUS: later]
  Scenario: Official Vector - anova-oneway compromise (Deferred / Later)
    When the CLI executes with "--test anova-oneway --mode compromise --f 0.25 --beta_alpha_ratio 1 --n_total 100 --groups 5"
    Then exit code must be 0
    And stdout must be single-line JSON
    And "df1" must equal 4
    And "df2" must equal 95
    And "ncp" must equal 6.2500000 within 1e-6
    And "critical_f" must equal 1.4272492 within 1e-6
    And "alpha" must equal 0.2309247 within 1e-6
    And "beta" must equal 0.2309247 within 1e-6
    And "power" must equal 0.7690753 within 1e-6

  # [DOK] Source: Instructor public_vectors.jsonl ("id": "anova-oneway/criterion") [STATUS: later]
  Scenario: Official Vector - anova-oneway criterion (Deferred / Later)
    When the CLI executes with "--test anova-oneway --mode criterion --f 0.25 --power 0.95 --n_total 100 --groups 5"
    Then exit code must be 0
    And stdout must be single-line JSON
    And "df1" must equal 4
    And "df2" must equal 95
    And "ncp" must equal 6.2500000 within 1e-6
    And "critical_f" must equal 0.6552638 within 1e-6
    And "alpha" must equal 0.6245994 within 1e-6

  # [DOK] Source: Instructor public_vectors.jsonl ("id": "anova-oneway/sensitivity") [STATUS: later]
  Scenario: Official Vector - anova-oneway sensitivity (Deferred / Later)
    When the CLI executes with "--test anova-oneway --mode sensitivity --alpha 0.05 --power 0.95 --n_total 100 --groups 5"
    Then exit code must be 0
    And stdout must be single-line JSON
    And "df1" must equal 4
    And "df2" must equal 95
    And "ncp" must equal 19.5245874 within 1e-6
    And "critical_f" must equal 2.4674936 within 1e-6
    And "f" must equal 0.4418664 within 1e-6
```

### 6.3 Post-Hoc Boundary and Asymptotic Power Scenarios

```gherkin
Feature: Post-Hoc Boundary and Asymptotic Power Scenarios

  Scenario: Post-Hoc Asymptotic Power at Large Sample Size N = 100000
    When the CLI executes with "--test anova-oneway --mode post-hoc --f 0.25 --alpha 0.05 --n_total 100000 --groups 5"
    Then exit code must be 0
    And stdout must be single-line JSON
    And "df1" must equal 4
    And "df2" must equal 99995
    And "ncp" must equal 6250 within 1e-6
    And "critical_f" must equal 2.3720211 within 1e-6
    And "power" must equal 1.0000000 within 1e-6

  Scenario: Post-Hoc Asymptotic Power at Large Sample Size N = 1000000
    When the CLI executes with "--test anova-oneway --mode post-hoc --f 0.25 --alpha 0.05 --n_total 1000000 --groups 5"
    Then exit code must be 0
    And stdout must be single-line JSON
    And "df1" must equal 4
    And "df2" must equal 999995
    And "ncp" must equal 62500 within 1e-6
    And "critical_f" must equal 2.3719411 within 1e-6
    And "power" must equal 1.0000000 within 1e-6

  Scenario: Post-Hoc Asymptotic Power at Large Sample Size N = 10000000
    When the CLI executes with "--test anova-oneway --mode post-hoc --f 0.25 --alpha 0.05 --n_total 10000000 --groups 5"
    Then exit code must be 0
    And stdout must be single-line JSON
    And "df1" must equal 4
    And "df2" must equal 9999995
    And "ncp" must equal 625000 within 1e-6
    And "critical_f" must equal 2.3719331 within 1e-6
    And "power" must equal 1.0000000 within 1e-6

  Scenario: Post-Hoc Maximum Admissible Effect Size Boundary f = 50.0
    When the CLI executes with "--test anova-oneway --mode post-hoc --f 50.0 --alpha 0.05 --n_total 10 --groups 5"
    Then exit code must be 0
    And stdout must be single-line JSON
    And "df1" must equal 4
    And "df2" must equal 5
    And "ncp" must equal 25000 within 1e-6
    And "critical_f" must equal 5.1921678 within 1e-6
    And "power" must equal 1.0000000 within 1e-6

  Scenario: Post-Hoc Lower Significance Boundary Alpha = 1e-7
    When the CLI executes with "--test anova-oneway --mode post-hoc --f 0.25 --alpha 0.0000001 --n_total 100 --groups 5"
    Then exit code must be 0
    And stdout must be single-line JSON
    And "df1" must equal 4
    And "df2" must equal 95
    And "ncp" must equal 6.2500000 within 1e-6
    And "critical_f" must equal 11.6273196 within 1e-6
    And "power" must equal 0.0002068239 within 1e-6
```
