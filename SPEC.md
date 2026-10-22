# Functional & Behavioral Specification: One-Way ANOVA Omnibus F-Test

## 1. Scope
- **Target Program:** G*Power 3.1.9.7 (Windows native 32-bit x86 PE).
- **Test Family:** F tests > ANOVA: Fixed effects, omnibus, one-way.
- **CLI Test Name:** `anova-oneway`.
- **Mode:** `a-priori` (computing required total sample size $N$ given effect size $f$, $\alpha$, target power $1-\beta$, and number of groups $k$).
- **Goal:** Comprehensive clean-room specification allowing an independent implementer with zero knowledge of the original binary to build an engine and CLI producing bitwise identical outputs to G*Power 3.1.9.7.

---

## 2. Inputs, Ranges, Defaults, and Units
| Parameter | CLI Flag | Accepted Aliases | G*Power UI Label | Type | Valid Range | Default (GUI) | Units |
|---|---|---|---|---|---|---|---|
| Effect size | `--f` | `--effect-size` | Effect size f | Float | $(10^{-6}, 50]$ | 0.25 | Cohen's $f$ (dimensionless) |
| Significance level | `--alpha` | (none) | $\alpha$ err prob | Float | $(10^{-7}, 1)$ | 0.05 | Probability |
| Target power | `--power` | (none) | Power ($1-\beta$ err prob) | Float | $[\alpha, 1) \cap (10^{-7}, 1)$ | 0.95 | Probability |
| Group count | `--groups` | `--k` | Number of groups | Float / Int | $[2, \infty)$ | 3 | Integer count (floats rounded half-up) |

---

## 3. Algorithm in Plain Language & Mathematical Formulas
The omnibus one-way ANOVA evaluates the null hypothesis that $k$ population means are identical: $H_0: \mu_1 = \mu_2 = \dots = \mu_k$.

### Mathematical Equations
1. **Numerator degrees of freedom ($df_1$):**
   $$df_1 = k - 1$$
2. **Denominator degrees of freedom ($df_2$):**
   $$df_2 = N - k$$
   where $N$ is the total sample size across all $k$ groups.
3. **Noncentrality parameter ($\lambda$):**
   $$\lambda = f^2 \times N$$
   where $f$ is Cohen's effect size.
4. **Critical value ($F_{crit}$):**
   Determined from the central $F$ distribution with parameters $(df_1, df_2)$ at significance level $\alpha$:
   $$P(F(df_1, df_2) \ge F_{crit}) = \alpha \iff F_{crit} = F^{-1}_{central}(1 - \alpha; df_1, df_2)$$
5. **Statistical Power ($1 - \beta$):**
   Determined by the survival function of the noncentral $F$ distribution with noncentrality parameter $\lambda$:
   $$\text{Power} = 1 - \beta = 1 - F_{nc}(F_{crit}; df_1, df_2, \lambda)$$

---

## 4. Search and Stopping Rules, Rounding, Minimum and Maximum N
- **Balanced Design Invariant:**
  $N$ is searched in discrete increments of $k$ ($N = n \times k$, where $n$ is sample size per group). Unequal group allocations are not used in a-priori mode.
- **Minimum Sample Size:**
  *[Open Assumption - L-011]* Denominator degrees of freedom requires $df_2 = N - k \ge 1$. For balanced groups, the minimum valid sample size per group is $n = 2$, yielding $N_{min} = 2k$ ($df_2 \ge k$).
- **Stopping Condition:**
  *[Open Assumption - L-012]* The search terminates at the smallest integer $n \ge 2$ ($N = n \cdot k$) such that:
  $$\text{Power}(F_{crit}(df_1, N-k, \alpha), df_1, N-k, f^2 N) \ge \text{target\_power}$$
- **Rounding of Group Count ($k$):**
  If a floating-point number is provided for groups (e.g. $k = 3.5$), G*Power applies half-up rounding ($3.5 \to 4$) before calculating degrees of freedom or sample size.
- **Search Strategy:**
  Implementations may use linear iteration ($n = 2, 3, 4, \dots$) or $O(\log N)$ exponential bracketing + binary search, provided the result is identical to the first discrete multiple of $k$ achieving target power.
- **Maximum N:**
  *[Open Assumption]* A practical cap of $N_{max} = 100,000,000$ should be enforced to prevent infinite loops on degenerate parameters.

---

## 5. Outputs and Exact Definitions
When calculation succeeds, the engine computes:
1. `n_per_group` (int): Number of observations per group ($n = N / k$).
2. `n_total` (int): Total required sample size ($N = n \cdot k$).
3. `actual_power` (float): Achieved power evaluated at $(df_1, df_2, \lambda, F_{crit})$.
4. `critical` (float): Critical $F$ ratio value ($F_{crit}$).
5. `df1` (int): Numerator degrees of freedom ($k - 1$).
6. `df2` (int): Denominator degrees of freedom ($N - k$).
7. `ncp` (float): Noncentrality parameter ($\lambda = f^2 N$).

---

## 6. Error Handling and Invalid Input Behavior
The program must reject invalid inputs by emitting single-line JSON `{"error": "<description>"}` and exiting with a non-zero exit code:
1. **Out of range effect size:** $f \le 10^{-6}$ or $f > 50$ (or non-numeric text) triggers error: *"Effect size f is outside the admissible range (1e-06, 50)"*.
2. **Out of range alpha:** $\alpha \le 10^{-7}$ or $\alpha \ge 1$ (or non-numeric text) triggers error: *"Alpha is outside the admissible range (1e-07, 1)"*.
3. **Out of range power:** $\text{power} \le 10^{-7}$ or $\text{power} \ge 1$ (or non-numeric text) triggers error: *"Power is outside the admissible range (1e-07, 1)"*.
4. **Power strictly below alpha:** If $\text{power} < \alpha$, triggers error: *"Power must be greater than or equal to alpha"*.
5. **Group count too low or non-numeric:** If $k < 2$ (or non-numeric text), triggers error: *"There must be at least 2 groups"*.

---

## 7. Provisional CLI Contract
> **PROVISIONAL, official CONTRACT.md not available**  
> **PROVISIONAL, official CONTRACT.md not available**  
> **PROVISIONAL, official CONTRACT.md not available**  
>
> All flag names and JSON output key names MUST reside in ONE centralized mapping module in the CLI layer (`src/cli/mapping.py`) so they can be adapted in minutes if the official specification differs.

### Invocation
```bash
# PROVISIONAL, official CONTRACT.md not available
gpower-clone --test anova-oneway --mode a-priori --f 0.25 --alpha 0.05 --power 0.95 --groups 3

# PROVISIONAL, official CONTRACT.md not available (with aliases)
gpower-clone --test anova-oneway --mode a-priori --effect-size 0.25 --alpha 0.05 --power 0.95 --k 3
```

### Success Output (Strict Single-Line JSON)
```json
{"n_per_group": 84, "n_total": 252, "actual_power": 0.9514888, "critical": 3.0320649, "df1": 2, "df2": 249, "ncp": 15.75}
```

### Failure Output (Strict Single-Line JSON with Non-Zero Exit Code)
```json
{"error": "Power must be greater than or equal to alpha"}
```

---

## 8. Acceptance Criteria in Gherkin

```gherkin
Feature: One-Way ANOVA Omnibus F-Test A-Priori Power Analysis (anova-oneway)

  # Cites LEDGER.md L-005, L-006, L-007, L-008, L-009, L-010, L-012, L-013
  Scenario: Typical Benchmark Calculation (Medium Effect, Standard Power)
    Given test is "anova-oneway"
    And mode is "a-priori"
    And effect size f is 0.25
    And alpha is 0.05
    And desired power is 0.80
    And number of groups is 3
    When the analysis engine executes
    Then the response must be valid single-line JSON
    And exit code must be 0
    And "n_total" must equal 159
    And "n_per_group" must equal 53
    And "df1" must equal 2
    And "df2" must equal 156
    And "ncp" must equal 9.9375000 within 1e-4
    And "critical" must equal 3.0540042 within 1e-4
    And "actual_power" must equal 0.8048873 within 1e-4

  # Cites LEDGER.md L-010, L-013
  Scenario: Group Divisibility Invariant
    Given test is "anova-oneway"
    And mode is "a-priori"
    And number of groups is 5
    When sample size is computed for target power 0.95, alpha 0.05, f 0.25
    Then "n_total" must equal 305
    And "n_total" modulo 5 must equal 0
    And "actual_power" must be strictly greater than 0.95

  # Cites LEDGER.md L-011 (Hidden behavior not in manual: Minimum sample size)
  Scenario: Massive Effect Size Floor Limit
    Given test is "anova-oneway"
    And mode is "a-priori"
    And effect size f is 5.0
    And alpha is 0.05
    And desired power is 0.95
    And number of groups is 3
    When the analysis engine executes
    Then "n_total" must not be less than 6
    And "n_per_group" must equal 2

  # Cites LEDGER.md L-014 (Hidden behavior not in manual: Group count float rounding)
  Scenario: Non-Integer Group Count Rounding
    Given test is "anova-oneway"
    And mode is "a-priori"
    And number of groups is 3.5
    And effect size f is 0.25
    And alpha is 0.05
    And desired power is 0.80
    When the analysis engine executes
    Then the engine must round groups to 4
    And "df1" must equal 3
    And "n_total" must equal 180

  # Cites LEDGER.md L-018 (Hidden behavior not in manual: Power below alpha rejection)
  Scenario: Error Handling - Power Less Than Alpha
    Given test is "anova-oneway"
    And mode is "a-priori"
    And alpha is 0.05
    And desired power is 0.04
    When the CLI executes
    Then exit code must be non-zero
    And stdout must be single-line JSON
    And "error" must contain "Power must be greater than or equal to alpha"

  # Cites LEDGER.md L-019 (Input validation: Minimum groups)
  Scenario: Error Handling - Insufficient Groups
    Given test is "anova-oneway"
    And number of groups is 1
    When the CLI executes
    Then exit code must be non-zero
    And stdout must be single-line JSON
    And "error" must contain "There must be at least 2 groups"

  # Cites LEDGER.md L-015 (Input validation: Out of range effect size)
  Scenario: Error Handling - Negative Effect Size
    Given test is "anova-oneway"
    And effect size f is -0.25
    When the CLI executes
    Then exit code must be non-zero
    And stdout must be single-line JSON
    And "error" must contain "outside the admissible range"
```

---

## 9. Unknowns & Open Assumptions
The following items remain open assumptions (`[AJAN]`) until confirmed by direct binary inspection or user oracle runs:
1. **Minimum sample size per group ($n_{min}$):**
   Assumed to be $n = 2$ ($N \ge 2k$), since $df_2 = N - k \ge 1$ and equal group sizes require integer $n \ge 2$. (Vector `v028` probes this).
2. **Search iteration mechanism:**
   Assumed that G*Power uses discrete evaluation stepping until power $\ge$ target. Whether the binary internally evaluates linearly or uses a secant/Brent root-finder is not proven, though the discrete multi-point output is mathematically identical.
3. **Exact floating-point epsilon in binary:**
   The exact convergence tolerance in G*Power's continued fraction and noncentral F series expansion is not disassembled, but differential testing verifies numerical agreement to 7 decimal places.
