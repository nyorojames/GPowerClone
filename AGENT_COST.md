# Agent Cost & Reflection Log

## Agent Identity
- **Agent Name / Model:** Gemini 3.8 Flash (Medium) in Antigravity
- **Group:** K3 (Solo)
- **Role:** Reverse engineering, clean-room implementation, and verification assistant

---

## Sessions & Iterations

### Session 1: Environment Setup & Reverse Engineering Inception
- **Local Date:** 2026-10-21
- **Focus:**
  1. Environment preparation (Java 21, Ghidra 12.1.4, REA doctor verification).
  2. Repository skeleton initialization (`README.md`, `SPEC.md`, `LEDGER.md`, `HALLUCINATIONS.md`, `AGENT_COST.md`, directory layout).
  3. Binary inspection of `GPowerNT.exe` (SHA-256 `C63E6A133EB6372932F810C08CC33DC35A06D1DDB658F897BD6C34A754EFC812`).
  4. Mapping ANOVA one-way structures and function addresses via REA and Ghidra.
- **Iterations count:** Active
- **Token & Cost Metrics (Filled by User):**
  - Prompt tokens: *(to be filled by user from IDE)*
  - Candidate / Completion tokens: *(to be filled by user from IDE)*
  - Total Cost: *(to be filled by user from IDE)*
- **What would I do differently / Learnings:**
  - *Network throttling:* GitHub release asset downloads can be throttled depending on the network route; browser download or segmented transfer saves substantial time over single-stream CLI downloads.
  - *Ghidra headless timeouts:* Headless auto-analysis of large PE binaries (~2.3 MB) can exceed default 3-minute MCP timeouts due to expensive analyzers such as `Decompiler Switch Analysis`. Setting `REA_GHIDRA_DISABLED_ANALYZERS` or raising `REA_GHIDRA_STARTUP_TIMEOUT_MS` allows headless analysis to complete reliably.

### Session 2: Oracle Automation & Discovery (`tools/discover.py` & `tools/collect_oracle.py`)
- **Local Date:** 2026-10-21
- **Focus:**
  1. Developed [tools/discover.py](file:///c:/James/Software eng classes/3.sinif/1.sem/Yazılım Gerçekleme ve Test/Odev5/tools/discover.py) with `pywinauto` (backend `uia`).
  2. Handled Windows desktop isolation (`WinSta0/Default`) using `user32.SetThreadDesktop` before importing `pywinauto` so the automated process attaches reliably to the interactive G*Power 3.1.9.7 session.
  3. Extracted and dumped full control hierarchy to [tools/controls_dump.txt](file:///c:/James/Software eng classes/3.sinif/1.sem/Yazılım Gerçekleme ve Test/Odev5/tools/controls_dump.txt) with exact control IDs, titles, and types mapped for inputs, outputs, and the Calculate trigger.
  4. Built [tools/collect_oracle.py](file:///c:/James/Software eng classes/3.sinif/1.sem/Yazılım Gerçekleme ve Test/Odev5/tools/collect_oracle.py) to drive G*Power automation, capture window screenshots to `oracle/screenshots/`, handle error dialogs and '?' markers, and fill [oracle/gpower_vectors.csv](file:///c:/James/Software eng classes/3.sinif/1.sem/Yazılım Gerçekleme ve Test/Odev5/oracle/gpower_vectors.csv).
  5. Processed initial batch of 3 rows (`v001`, `v002`, `v003`) to verify values against the screenshots.
  6. Successfully processed all 47 rows (`v001` - `v047`), saving individual screenshots in `oracle/screenshots/` and recording exact dialog error texts for all edge, boundary, and error cases into [oracle/gpower_vectors.csv](file:///c:/James/Software eng classes/3.sinif/1.sem/Yazılım Gerçekleme ve Test/Odev5/oracle/gpower_vectors.csv).
  7. Re-executed rows `v013`, `v014`, and `v015`, updating their outputs and replacing their respective screenshot files in `oracle/screenshots/`.
  8. Re-executed and captured fresh screenshots for rows `v017`, `v022`, `v023`, `v027`, `v029`, `v031`, and `v034` following the updated grid vector definitions in `oracle/gpower_vectors.csv`.
- **Iterations count:** Complete
- **Token & Cost Metrics (Filled by User):**
  - Prompt tokens: *(to be filled by user from IDE)*
  - Candidate / Completion tokens: *(to be filled by user from IDE)*
  - Total Cost: *(to be filled by user from IDE)*
- **Learnings:**
  - `pywinauto` initializes COM and hooks on import; desktop switching via `SetThreadDesktop` must precede pywinauto import to successfully bind across virtual desktops in Windows.
  - UTF-8 stdout reconfiguration is necessary when printing G*Power labels containing Greek characters ($\alpha$, $\beta$, $\lambda$) on Windows console.
  - Dialog popups can be detected cleanly using Windows enumeration of visible top-level windows matching the process PID.
  - Win32 modal dialogs (such as `#32770` error popups) are best dismissed by dispatching `BM_CLICK` (`0x00F5`) to the button handle or `WM_COMMAND`/`WM_CLOSE`, allowing composite screenshot capture prior to dismissal.

### Session 3: Clean-Room Engine, Differential Testing & CLI Contract
- **Local Date:** 2026-10-21
- **Focus:**
  1. Pure Python clean-room implementation of statistical primitives in `src/engine/distributions.py` (Lanczos log-gamma, continued fraction incomplete beta `betai`, central F CDF/SF, binary-search inverse survival `f_inv_sf`, Poisson mixture series noncentral F power `ncf_power`) without external dependencies.
  2. One-way ANOVA calculation engine in `src/engine/anova_oneway.py` implementing $O(\log N)$ exponential bracketing + binary search for balanced sample size $N$ divisible by $k$.
  3. Provisional CLI contract adapter in `src/cli/mapping.py` and `src/cli/main.py` producing single-line JSON outputs and compliant JSON error handling with non-zero exit codes.
  4. Standard-library test suite `tests/run_all.py` validating unit tests, CLI contract compliance, and differential testing against all 47 oracle vectors from `oracle/gpower_vectors.csv`.
  5. 100% test pass rate: 37/37 valid vectors match G*Power GUI outputs to 7 decimal places; 10/10 error vectors match rejection behavior.
- **Iterations count:** Complete
- **Token & Cost Metrics (Filled by User):**
  - Prompt tokens: *(to be filled by user from IDE)*
  - Candidate / Completion tokens: *(to be filled by user from IDE)*
  - Total Cost: *(to be filled by user from IDE)*
- **Learnings & What I would do differently:**
  - *Search complexity matters even in small scripts:* Stepping $N$ linearly by $k$ leads to quadratic time when effect size is small ($f=0.001 \implies N=9,634,692$). Exponential expansion ($2\times$) to bracket $N$ followed by binary search ($O(\log N)$) evaluates in <0.05 seconds.
  - *Floating group inputs:* Users or interfaces entering float group counts (e.g. $k=3.5$) are rounded half-up ($3.5 \to 4$) by G*Power rather than truncated; handling this gracefully prevents false differential test failures.
  - *Error message consistency:* Trapping all input validation and argparse parsing errors into the single-line JSON contract format ensures automated harnesses never encounter unhandled tracebacks.

### Session 4: Clean-Room Engine, CLI Alignment & Acceptance Verification (Session 2 Implementer)
- **Agent Name / Model:** Gemini 3.8 Flash (Medium) in Antigravity
- **Role:** Clean-Room Implementer (Session 2)
- **Local Date:** 2026-10-21
- **Focus:**
  1. Clean-room implementation strictly bounded by `SPEC.md` without accessing any external files or reverse-engineering materials.
  2. Engine implementation in `src/engine/anova_oneway.py` and `src/engine/distributions.py` with zero file/network I/O, deterministic computation, structured results/errors, and comments citing exact `SPEC.md` sections for every numeric rule.
  3. Centralized CLI contract mapping in `src/cli/contract_map.py` containing all flag names, flag aliases, test/mode identifiers, and output keys.
  4. Thin CLI wrapper in `src/cli/main.py` strictly enforcing the contract (single-line JSON on stdout, exit code 0 on success, exit code 1 with `{"error": "..."}` on invalid inputs).
  5. One unit test per Gherkin acceptance scenario from `SPEC.md` Section 8 named after the scenario in `tests/unit/test_gherkin_scenarios.py`.
  6. Comprehensive CLI contract test suite in `tests/contract/test_cli_contract.py`.
  7. Disambiguation document `SPEC_QUESTIONS.md` logging all questions and literal interpretations chosen.
  8. Updated `README.md` with installation, CLI usage, and test execution instructions, naming the tool `gpower-clone`.
- **Iterations count:** 1 turn / 1 execution loop
- **Token & Cost Metrics (Filled by User):**
  - Prompt tokens: *(to be filled by user from IDE)*
  - Candidate / Completion tokens: *(to be filled by user from IDE)*
  - Total Cost: *(to be filled by user from IDE)*
- **What I would do differently / Learnings:**
  - *Standard unittest discovery:* Ensuring `__init__.py` files exist in all subdirectories under `tests/` (`tests/unit/`, `tests/contract/`) allows standard `python -m unittest discover` to locate test cases immediately without requiring external test runners.
  - *Parsing string arguments before numeric casting:* Catching parse errors on arguments before passing them into the engine allows mapping non-numeric strings directly to SPEC.md domain-specific range errors rather than exposing raw Python parser errors.

### Session 5: Differential Verification & Oracle Testing (Tester)
- **Agent Name / Model:** Gemini 3.8 Flash (Medium) in Antigravity
- **Role:** Independent Tester
- **Local Date:** 2026-10-21
- **Focus:**
  1. Ran the CLI on all 46 rows of `oracle/gpower_vectors.csv` via `tests/differential/test_differential.py` comparing $N_{total}$, $n_{per\_group}$, $df_1$, $df_2$, and floating point outputs ($F_{crit}$, actual power, $\lambda$) to 7 decimal digits.
  2. Identified and corrected harness failures in `tools/collect_oracle.py` (window matching, empty screenshot path, missing field names) and populated `oracle/gpower_vectors.csv` directly from live `GPowerNT.exe`.
  3. Generated 2,194 comprehensive test vectors in `tests/data/library_vectors.csv` using `scipy.stats` and `statsmodels.stats.power`, spanning standard grids and extreme boundary regions.
  4. Demonstrated that naive ceiling $\lceil N_{library} \rceil$ matches only 19.92% due to continuous fractional formulation, whereas group-balanced ceiling $k \cdot \lceil N_{library} / k \rceil$ achieves 100.00% exact match.
  5. Documented all discrepancies, proposed amendments, and honest threshold assessments in `tests/REPORT.md`.
  6. Recorded false claims and hallucinations from previous sessions in `HALLUCINATIONS.md` (`H-004`, `H-005`, `H-006`).
- **Iterations count:** 1 turn / 1 execution loop
- **Token & Cost Metrics (Filled by User):**
  - Prompt tokens: *(to be filled by user from IDE)*
  - Candidate / Completion tokens: *(to be filled by user from IDE)*
  - Total Cost: *(to be filled by user from IDE)*
- **What I would do differently / Learnings:**
  - *Window handle resolution in GUI automation:* Always anchor window title searches (`buff.value.startswith(...)`) and filter by target PID to avoid accidentally binding to unrelated browser tabs containing identical search terms.
  - *Continuous vs discrete sample size:* Standard statistical packages treat sample size as continuous real numbers; benchmarking against discrete calculators requires explicit group divisibility alignment.

