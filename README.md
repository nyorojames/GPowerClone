# gpower-clone

A command-line statistical power calculator implementing a-priori sample size estimation for one-way ANOVA omnibus F-tests.

---

## Clean-Room Reimplementation Disclaimer
`gpower-clone` is an independent clean-room reimplementation and is **not** G*Power. It was developed without copying or redistributing any proprietary binaries, source code, or intellectual property of Heinrich Heine University Düsseldorf. All reverse-engineering findings were captured as behavioral contracts and mathematical specifications in `SPEC.md`, from which the engine and CLI were authored independently.

### Target Reference Program
- **Program:** G*Power 3.1.9.7 (Windows native 32-bit x86 PE executable)
- **Executable SHA-256:** `C63E6A133EB6372932F810C08CC33DC35A06D1DDB658F897BD6C34A754EFC812`

---

## Demo
Video: <ADD LINK HERE>

An automated PowerShell demonstration script is available at `demo/demo_script.ps1`. It executes typical cases, boundary cases from `LEDGER.md` [REA], invalid input rejection, and the differential test suite:
```powershell
.\demo\demo_script.ps1
```

---

## Environment & Ghidra / REA Availability
During the reverse-engineering phase (Session 1), binary inspection and architectural mapping were conducted using REA ("Reverse Engineer Anything") with Ghidra.

<!-- Ghidra/REA Availability Screenshot Placeholder -->
![Ghidra REA Availability Screenshot](<ADD SCREENSHOT PATH HERE>)

---

## Installation & Requirements

### Requirements
- Python 3.12 or newer.
- Core engine and CLI require **zero third-party dependencies** (runs using the Python standard library).
- Auxiliary verification tools and test generators (`tools/`) use libraries listed in `requirements.txt` (`scipy`, `statsmodels`, `pandas`, `pywinauto`). To install optional test dependencies:
  ```bash
  pip install -r requirements.txt
  ```

### Setup
Clone the repository and verify your Python version:
```bash
python --version
```

---

## Usage

### Command-Line Invocation

The CLI accepts inputs using standardized flags or accepted aliases:

```bash
# Standard invocation
python -m src.cli.main --test anova-oneway --mode a-priori --f 0.25 --alpha 0.05 --power 0.95 --groups 3

# Invocation with accepted aliases (--effect-size and --k)
python -m src.cli.main --test anova-oneway --mode a-priori --effect-size 0.25 --alpha 0.05 --power 0.95 --k 3
```

> **Note on CLI Contract:** The official course `CONTRACT.md` was never shared, so the ANOVA CLI contract implemented here is an assumption and marked provisional in `SPEC.md`. All flag names and JSON output keys reside in `src/cli/contract_map.py` to allow instant adaptation if the official specification differs.

### CLI Parameters & Flags

All flags and output keys are centralized in `src/cli/contract_map.py`:

| Parameter | CLI Flag | Accepted Aliases | Type | Admissible Range | Description |
|---|---|---|---|---|---|
| Test Name | `--test` | (none) | String | `anova-oneway` | Test identifier |
| Mode | `--mode` | (none) | String | `a-priori` | Analysis mode |
| Effect Size | `--f` | `--effect-size` | Float | $(10^{-6}, 50]$ | Cohen's effect size $f$ |
| Alpha | `--alpha` | (none) | Float | $(10^{-7}, 1)$ | Significance level $\alpha$ |
| Power | `--power` | (none) | Float | $[\alpha, 1) \cap (10^{-7}, 1)$ | Desired target power ($1-\beta$) |
| Group Count | `--groups` | `--k` | Float / Int | $[2, \infty)$ | Number of groups (floats rounded half-up) |

---

## Output Contract

### Success Output (Strict Single-Line JSON, Exit Code 0)
When inputs are valid, `gpower-clone` emits a single-line JSON dictionary on `stdout` and exits with code 0:
```json
{"n_per_group":84,"n_total":252,"actual_power":0.9514888,"critical":3.0320649,"df1":2,"df2":249,"ncp":15.75}
```

#### Output Fields:
- `n_per_group` (int): Number of observations per group ($n = N / k$).
- `n_total` (int): Total required sample size ($N = n \cdot k$).
- `actual_power` (float): Achieved power evaluated at $(df_1, df_2, \lambda, F_{crit})$, rounded to 7 decimal places.
- `critical` (float): Critical $F$ ratio value ($F_{crit}$), rounded to 7 decimal places.
- `df1` (int): Numerator degrees of freedom ($k - 1$).
- `df2` (int): Denominator degrees of freedom ($N - k$).
- `ncp` (float): Noncentrality parameter ($\lambda = f^2 N$), rounded to 7 decimal places.

### Error Output (Strict Single-Line JSON, Non-Zero Exit Code)
On invalid input or contract violation, `gpower-clone` emits a single-line JSON error message on `stdout` and exits with code 1:
```json
{"error":"Power must be greater than or equal to alpha"}
```

---

## Verification & Differential Testing

### Oracle Verification
Oracle collection was scripted with `pywinauto` (UIA backend) in `tools/collect_oracle.py` driving live `GPowerNT.exe` instances, capturing window screenshots to `oracle/screenshots/` and recording exact GUI values and modal dialog error messages. Every row in `oracle/gpower_vectors.csv` was verified against its corresponding screenshot.

- **Oracle dataset:** The oracle is 46 rows read from the G*Power GUI (36 calculation rows, 10 boundary/error rows).
- **Match rate against Oracle:** 46 / 46 (100.00% exact match).
- **Numeric tolerance in `tests/differential/test_differential.py`:** Integer outputs (`n_total`, `n_per_group`, `df1`, `df2`) are checked for **exact equality**. Floating-point outputs (`critical`, `actual_power`, `ncp`) are evaluated with a tolerance of `1e-4` against G*Power's displayed numbers.
- **Displayed precision:** G*Power displays **7 decimal places** for floating-point outputs.

### Library Vectors Note
The 2,194 library vectors in `tests/data/library_vectors.csv` come from scipy/statsmodels and only check the group-balanced rounding rule; they are **NOT** a measure of agreement with G*Power. Standard Python libraries solve for continuous real $N$, which matches G*Power discrete balanced sample size ($N = n \cdot k$) only when aligned via the group-balanced ceiling $k \cdot \lceil N / k \rceil$.

> **Note on Specification Updates:** SPEC.md was amended after differential testing and Session 2 was not rerun.

---

## Running the Test Suite

Run all test suites (unit tests, Gherkin scenario acceptance tests, CLI contract tests, and differential oracle tests) with the built-in runner:
```bash
python tests/run_all.py
```

Or run individual suites:
```bash
# Run differential verification against G*Power oracle
python -m unittest tests/differential/test_differential.py

# Run Gherkin acceptance criteria scenarios
python -m unittest tests/unit/test_gherkin_scenarios.py

# Run CLI contract tests
python -m unittest tests/contract/test_cli_contract.py

# Run distribution & engine unit tests
python -m unittest tests/unit/test_engine.py
```

---

## Architecture

- `src/engine/`: Pure calculation module. Contains no I/O, no printing, no environment mutations. Deterministic distribution algorithms (`distributions.py`) and search routine (`anova_oneway.py`).
- `src/cli/contract_map.py`: Single source of truth for all CLI flag names, aliases, valid values, and output key mappings.
- `src/cli/main.py`: Thin CLI wrapper handling argument parsing, input routing, and JSON formatting.
- `tests/`: Comprehensive test suite containing contract tests, unit tests, Gherkin acceptance scenarios, and differential verification.

---

## Academic References & Credit
- Faul, F., Erdfelder, E., Lang, A.-G., & Buchner, A. (2007). G*Power 3: A flexible statistical power analysis program for the social, behavioral, and biomedical sciences. *Behavior Research Methods*, 39(2), 175–191.
- Faul, F., Erdfelder, E., Buchner, A., & Lang, A.-G. (2009). Statistical power analyses using G*Power 3.1: Tests for correlation and regression analyses. *Behavior Research Methods*, 41(4), 1149–1160.
