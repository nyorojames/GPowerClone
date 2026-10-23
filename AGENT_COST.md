# Agent Cost & Reflection Log

## Process Summary
- **Sessions Run:**
  1. **Session 1:** Environment setup, Ghidra/REA initialization & reverse engineering inception.
  2. **Session 1b:** Contract update & post-hoc binary investigation.
  3. **Session 1c:** Post-hoc oracle automation & GUI vector collection.
  4. **Session 1d:** Specification amendment after initial differential testing.
  5. **Session 2:** A-priori oracle automation & discovery.
  6. **Session 2b:** Contract implementation & CLI interface alignment.
  7. **Session 2c:** Numerical distribution stability & accuracy fixes.
  8. **Session Tester:** Independent differential testing, library grid generation & mismatch analysis.
  9. **Session Final Pass:** Strict verification suite, tolerance alignment, leak sweeps & documentation.
- **Agent Used:** Gemini 3.8 Flash (Medium) in Google Antigravity.
- **Three Honest Lessons:**
  1. *False claims caught by tests:* Early assumptions claimed 100% agreement with standard statistical formulas, but rigorous testing against the G*Power oracle revealed that naive continuous sample size ceiling ($\lceil N_{library} \rceil$) matched only 19.92%. This exposed G*Power's strict requirement for balanced discrete groups ($N = k \cdot \lceil N_{lib} / k \rceil$).
  2. *Clean-room leaks caught by text scan:* Session 1b wrote reverse-engineering internals (original function names, addresses and instruction mnemonics) and a reference to the oracle file path into `SPEC.md`, violating the clean-room rule. This was noticed with a text search on `SPEC.md` before Session 2b was accepted. The manual text scan caught it; those lines were edited to describe behaviour only, the scan was re-run until empty, and Session 2b was restarted from the cleaned spec (added rule: `SPEC.md` describes behaviour only; mechanism details stay in `LEDGER.md`). As a secondary catch, automated token scanning also caught an accidental reference to `LEDGER.md` inside `tests/REPORT.md`.
  3. *Numerical underflow caught by differential testing:* Under extreme noncentrality ($\lambda \ge 6250$) in post-hoc mode with large sample sizes ($N \ge 100,000$ in `p038`–`p040`) or large effect sizes ($f = 50$ in `p046`), the standard Poisson mixture weight $e^{-\lambda/2}$ underflowed 64-bit IEEE 754 floating-point precision to $0.0$, causing the series expansion to evaluate to $0.0$ instead of $1.0$. Differential testing against ground-truth GUI oracle vectors caught this failure immediately, prompting a robust log-space summation centered at the mode.

---

## Agent Identity
- **Agent Name / Model:** Gemini 3.8 Flash (Medium) in Antigravity
- **Group:** K3 (Solo)
- **Role:** Reverse engineering, clean-room implementation, and verification assistant

---

## Session Logs & Metrics

### Session 1: Environment Setup & Reverse Engineering Inception
- **Local Date:** 2026-10-21
- **Focus:**
  1. Environment preparation (Java 21, Ghidra 12.1.4, REA doctor verification).
  2. Repository skeleton initialization (`README.md`, `SPEC.md`, `LEDGER.md`, `HALLUCINATIONS.md`, `AGENT_COST.md`, directory layout).
  3. Binary inspection of `GPowerNT.exe` (SHA-256 `C63E6A133EB6372932F810C08CC33DC35A06D1DDB658F897BD6C34A754EFC812`).
  4. Mapping ANOVA one-way structures and function addresses via REA and Ghidra.
- **Iterations count:** Complete
- **Token & Cost Metrics:**
  - Prompt tokens: Not recorded: the IDE did not expose token counts for this session.
  - Candidate / Completion tokens: Not recorded: the IDE did not expose token counts for this session.
  - Total Cost: Not recorded: the IDE did not expose token counts for this session.
- **What would I do differently / Learnings:**
  - *Network throttling:* GitHub release asset downloads can be throttled depending on the network route; browser download or segmented transfer saves substantial time over single-stream CLI downloads.
  - *Ghidra headless timeouts:* Headless auto-analysis of large PE binaries (~2.3 MB) can exceed default 3-minute MCP timeouts due to expensive analyzers such as `Decompiler Switch Analysis`. Setting `REA_GHIDRA_DISABLED_ANALYZERS` or raising `REA_GHIDRA_STARTUP_TIMEOUT_MS` allows headless analysis to complete reliably.

### Session 1b: Investigator, Contract Update
- **Local Date:** 2026-10-22
- **Focus:**
  1. Ingested instructor `contract/CONTRACT.md` v1.0.0 and `contract/public_vectors.jsonl`.
  2. Post-hoc binary investigation with REA and GNU objdump disassembly on `GPowerNT.exe` (`0x004ba6b0`, `0x004ba842`, `0x00488970`, `0x00488800`, `0x004badb0`).
  3. Proved binary mechanisms: non-divisible $N_{total}$ accepted with average group size and warning code `-2` (L-022); $N_{total} \le k$ rejected via `0x00488800` (L-023); minimum post-hoc $N_{total} = k + 1$ (L-024); no domain upper bound on $N_{total}$ (L-025); and a-priori ceiling division via `0x004badb0` (L-026).
  4. Created `oracle/posthoc_inputs.csv` (47 rows) spanning required boundary, divisibility, and scaling probe conditions.
  5. Fully updated `SPEC.md` to Contract v1.0.0, adding Gherkin acceptance scenarios for all contract rules and the five instructor public vectors (`[DOK]`).
  6. Mapped all refusals from `oracle/gpower_vectors.csv` to contract error codes with explicit `MY INTERPRETATION` tags and ambiguity resolutions.
  7. Saved prompt verbatim to `prompts/session1b_contract_update.md`. Preserved `src/` and existing oracle outputs untouched.
- **Iterations count:** Complete
- **Token & Cost Metrics:**
  - Prompt tokens: Not recorded: the IDE did not expose token counts for this session.
  - Candidate / Completion tokens: Not recorded: the IDE did not expose token counts for this session.
  - Total Cost: Not recorded: the IDE did not expose token counts for this session.
- **Learnings & What I would do differently:**
  - *Direct disassembly vs full decompilation on large PE targets:* Full Ghidra decompiler auto-analysis can exceed MCP 3-minute deadlines on 2.3 MB binaries. Targeting exact VAs via REA and GNU objdump disassembly provides immediate, verifiable byte-level proof for validation and error branches.
  - *GUI warnings vs CLI contracts:* In G*Power GUI, certain conditions (such as $N_{total}$ not a multiple of groups in post-hoc) produce warning dialogs while still populating output fields. On a single-line stdout CLI contract, this maps directly to successful output (exit code 0) without stderr noise.

### Session 1c: Post-Hoc Oracle Collector
- **Local Date:** 2026-10-22
- **Focus:**
  1. Identified G*Power 3.1.9.7 active instance and driven dropdowns to `F tests` -> `ANOVA: Fixed effects, omnibus, one-way` -> `Post hoc: Compute achieved power` via UIA automation.
  2. Created `tools/discover_posthoc.py` and dumped full post-hoc control tree (`tools/controls_dump_posthoc.txt`).
  3. Mapped 4 input edits (1020, 1021, 1022, 1023), 5 output edits (1050, 1051, 1052, 1053, 1054), and Calculate button (1009).
  4. Built `tools/collect_posthoc.py` incorporating strict safeguards: window-only output reading, per-row screenshots, typed vs displayed input recording, informational vs error dialog classification and dismissal, `SAME_AS_PREVIOUS_ROW` detection, and per-row CSV persistence.
  5. Verified first 3 rows ($f=0.25, \alpha=0.05, k=5$ with $N=100, 101, 103$), strictly validating the $N=100$ baseline: ncp `6.25`, critical F `2.4674936`, df1 `4`, df2 `95`, power `0.4663312`.
  6. Successfully processed all 49 oracle rows unattended, capturing 49 screenshots to `oracle/screenshots/` and writing results to `oracle/posthoc_vectors.csv`.
  7. Proved empirical behavior for non-multiple $N_{total}$: G*Power computes power from $N_{total}$ as typed ($ncp = 6.3125 / 6.4375, df_2 = 96 / 98$) rather than rounding $N$.
  8. Verified full mathematical invariant agreement across all rows; sanitized `SPEC.md` against forbidden binary/tool pattern strings; logged hallucination `H-007` in `HALLUCINATIONS.md`; saved verbatim prompt to `prompts/session1c_posthoc_oracle.md`. Preserved `src/` and `tests/` untouched.
- **Iterations count:** Complete
- **Token & Cost Metrics:**
  - Prompt tokens: Not recorded: the IDE did not expose token counts for this session.
  - Candidate / Completion tokens: Not recorded: the IDE did not expose token counts for this session.
  - Total Cost: Not recorded: the IDE did not expose token counts for this session.
- **Learnings & What I would do differently:**
  - *Modal dialog COM interface deadlocks:* Calling `.click()` or `.invoke()` on a control that spawns a modal Win32 dialog blocks the UIA COM calling thread. Dispatching asynchronous `PostMessageW(BM_CLICK)` cleanly decouples the invocation from subsequent modal popup discovery and dismissal.
  - *Distinguishing informational warnings from refusal errors:* G*Power uses standard Win32 dialogs for both fatal input rejections (leaving `?` outputs) and non-fatal warnings (leaving calculated output parameters intact). Collector logic must inspect the output fields after dialog dismissal to avoid incorrectly treating benign notices as failures.

### Session 1d: Spec Amendment After Differential Testing
- **Local Date:** 2026-10-22
- **Focus:**
  1. Analyzed the 5 failing post-hoc oracle rows (`p038`, `p039`, `p040`, `p046`, `p049`) identified during differential verification.
  2. Extracted typed inputs, G*Power displayed values (CSV & screenshots), CLI returned values, and differences.
  3. Classified `p038`, `p039`, `p040`, `p046` as engine numerical breakdowns at large noncentrality ($\lambda \ge 6250$) that the specification's mathematical definition already implied, and `p049` as a specification omission regarding boundary inclusivity ($\alpha = 10^{-7}$).
  4. Tested and settled all parameter boundaries on live G*Power 3.1.9.7:
     - $\alpha$ lower ($10^{-7}$): inclusive (settled by `p049`); $\alpha$ upper ($1$): exclusive (settled by `v040`).
     - $\text{power}$ lower ($10^{-7}$): inclusive (settled by `b001`); $\text{power}$ upper ($1$): exclusive (settled by `v036`).
     - $f$ lower ($10^{-6}$): inclusive (settled by `b002`); $f$ upper ($50$): inclusive (settled by `p046`).
     - $groups$ minimum ($2$): inclusive (settled by `v029`, `p025`, `p028`).
  5. Created `oracle/boundary_vectors.csv` and executed GUI automation via `tools/collect_oracle.py`, capturing screenshots `b001.png` and `b002.png`.
  6. Amended `SPEC.md` strictly with behavioral rules: domain boundary intervals, accuracy and numerical stability requirements ($10^{-6}$ precision up to $N=2147483647$, no underflow/overflow/NaN/inf, <2s execution time), and Gherkin scenarios for the 5 failing cases.
  7. Confirmed zero leaks in `SPEC.md` via regex scan against forbidden binary/tool tokens.
  8. Logged hallucination `H-008` in `HALLUCINATIONS.md` and saved the prompt verbatim to `prompts/session1d_spec_amendment.md`. Preserved `src/` and `tests/` strictly untouched.
- **Iterations count:** Complete
- **Token & Cost Metrics:**
  - Prompt tokens: Not recorded: the IDE did not expose token counts for this session.
  - Candidate / Completion tokens: Not recorded: the IDE did not expose token counts for this session.
  - Total Cost: Not recorded: the IDE did not expose token counts for this session.
- **Learnings & What I would do differently:**
  - *Large noncentrality asymptotic bounds:* Noncentral cumulative distribution functions in standard numerical packages often underflow or lose precision when evaluating tail survival $1 - F_{nc}(F_{crit}; \lambda)$ with massive noncentrality parameters ($\lambda > 1000$). Explicit accuracy requirements in the specification must instruct the engine to handle asymptotic limits safely ($\text{power} \to 1.0$) rather than silently returning 0.0.
  - *Exact boundary inclusivity:* Error dialog messages like `(1e-07, 1)` use standard G*Power text formatting that looks like an open interval, but empirical testing proves the lower endpoint is accepted ($[10^{-7}, 1)$). Testing the exact endpoints in live GUI automation is the only way to establish true boundary inclusivity.

### Session 2: Oracle Automation & Discovery (`tools/discover.py` & `tools/collect_oracle.py`)
- **Local Date:** 2026-10-21
- **Focus:**
  1. Developed `tools/discover.py` with `pywinauto` (backend `uia`).
  2. Handled Windows desktop isolation (`WinSta0/Default`) using `user32.SetThreadDesktop` before importing `pywinauto` so the automated process attaches reliably to the interactive G*Power 3.1.9.7 session.
  3. Extracted and dumped full control hierarchy to `tools/controls_dump.txt` with exact control IDs, titles, and types mapped for inputs, outputs, and the Calculate trigger.
  4. Built `tools/collect_oracle.py` to drive G*Power automation, capture window screenshots to `oracle/screenshots/`, handle error dialogs and '?' markers, and fill `oracle/gpower_vectors.csv`.
  5. Processed all 47 rows (`v001` - `v047`), saving individual screenshots in `oracle/screenshots/` and recording exact dialog error texts for all edge, boundary, and error cases into `oracle/gpower_vectors.csv`.
- **Iterations count:** Complete
- **Token & Cost Metrics:**
  - Prompt tokens: Not recorded: the IDE did not expose token counts for this session.
  - Candidate / Completion tokens: Not recorded: the IDE did not expose token counts for this session.
  - Total Cost: Not recorded: the IDE did not expose token counts for this session.
- **Learnings:**
  - `pywinauto` initializes COM and hooks on import; desktop switching via `SetThreadDesktop` must precede pywinauto import to successfully bind across virtual desktops in Windows.
  - Win32 modal dialogs (such as `#32770` error popups) are best dismissed by dispatching `BM_CLICK` (`0x00F5`) to the button handle or `WM_COMMAND`/`WM_CLOSE`, allowing composite screenshot capture prior to dismissal.

### Session 2b: Contract Implementer Update
- **Local Date:** 2026-10-22
- **Focus:**
  1. Ingested `SPEC.md` amendments and CONTRACT.md v1.0.0 definitions.
  2. Fully wired and verified all 5 calculation modes (`a-priori`, `post-hoc`, `compromise`, `criterion`, `sensitivity`) in `src/engine/anova_oneway.py`.
  3. Strictly enforced single-line JSON format, contract exit codes, and standard error JSON payloads (`{"error": "...", "code": "...", "field": "..."}`).
  4. Verified all 5 public vectors in `contract/public_vectors.jsonl` matching ground truth to $< 5 \times 10^{-8}$.
- **Iterations count:** Complete
- **Token & Cost Metrics:**
  - Prompt tokens: Not recorded: the IDE did not expose token counts for this session.
  - Candidate / Completion tokens: Not recorded: the IDE did not expose token counts for this session.
  - Total Cost: Not recorded: the IDE did not expose token counts for this session.
- **What I would do differently:**
  - Proactively verify whether the deferred modes (`compromise`, `criterion`, `sensitivity`) in Section 1.1 should be implemented or return `UNSUPPORTED`. Implementing them cleanly in the pure engine resolved the apparent conflict with Section 6.2 acceptance scenarios and allowed 100% of all public reference vectors to pass within 1e-6 tolerance.

### Session 2c: Numerics & Accuracy Fix
- **Local Date:** 2026-10-22
- **Focus:**
  1. Updated noncentral F distribution calculation in `src/engine/distributions.py` using Poisson weights evaluated in log space starting at mode with tail cutoff to eliminate large-$\lambda$ underflow.
  2. Fixed boundary intervals in `src/engine/anova_oneway.py` to match SPEC.md ($f \in [10^{-6}, 50]$, $\alpha \in [10^{-7}, 1)$, $\text{power} \in [10^{-7}, 1)$, $N_{total} \le 2147483647$).
  3. Added unit and contract tests for all Section 6.3 Gherkin scenarios and extreme edge cases ($N = 2147483647$, $k = 100$, $f = 50$, $f = 1e-6$, $\alpha = 1e-7$, power near 1, tiny $f$ in a-priori). Verified no NaN/Inf, power $\in [0, 1]$, power monotone in $N$, and all calls $< 2.0$s.
- **Iterations count:** Complete
- **Token & Cost Metrics:**
  - Prompt tokens: Not recorded: the IDE did not expose token counts for this session.
  - Candidate / Completion tokens: Not recorded: the IDE did not expose token counts for this session.
  - Total Cost: Not recorded: the IDE did not expose token counts for this session.
- **Learnings:**
  - Computing noncentral Poisson series terms in log-space starting from the Poisson mode ($\approx \lambda/2$) avoids catastrophic floating-point underflow when $\lambda > 1000$, ensuring robust convergence across the entire IEEE 754 range.

### Session Tester: Differential Verification & Oracle Testing
- **Local Date:** 2026-10-21
- **Focus:**
  1. Ran the CLI on all 46 rows of `oracle/gpower_vectors.csv` via `tests/differential/test_differential.py` comparing $N_{total}$, $n_{per\_group}$, $df_1$, $df_2$, and floating point outputs ($F_{crit}$, actual power, $\lambda$) to 7 decimal digits.
  2. Identified and corrected harness failures in `tools/collect_oracle.py` (window matching, empty screenshot path, missing field names) and populated `oracle/gpower_vectors.csv` directly from live `GPowerNT.exe`.
  3. Generated 2,194 comprehensive test vectors in `tests/data/library_vectors.csv` using `scipy.stats` and `statsmodels.stats.power`, spanning standard grids and extreme boundary regions.
  4. Demonstrated that naive ceiling $\lceil N_{library} \rceil$ matches only 19.92% due to continuous fractional formulation, whereas group-balanced ceiling $k \cdot \lceil N_{library} / k \rceil$ achieves 100.00% exact match.
  5. Documented all discrepancies, proposed amendments, and honest threshold assessments in `tests/REPORT.md`.
  6. Recorded false claims and hallucinations from previous sessions in `HALLUCINATIONS.md` (`H-004`, `H-005`, `H-006`).
- **Iterations count:** Complete
- **Token & Cost Metrics:**
  - Prompt tokens: Not recorded: the IDE did not expose token counts for this session.
  - Candidate / Completion tokens: Not recorded: the IDE did not expose token counts for this session.
  - Total Cost: Not recorded: the IDE did not expose token counts for this session.
- **Learnings:**
  - Standard statistical packages treat sample size as continuous real numbers; benchmarking against discrete calculators requires explicit group divisibility alignment.

### Session Final Pass: Verification, Demo Script & Contract Conformance
- **Local Date:** 2026-10-22 / 2026-10-23
- **Focus:**
  1. Ran full verification across 57 unit/scenario/contract tests in `tests/run_all.py` (100% pass).
  2. Aligned differential tolerance in `tests/differential/test_differential.py` to strict CONTRACT.md rule ($|a - b| \le 10^{-6}$ or relative diff $\le 10^{-6}$, integers exact).
  3. Evaluated all 46 a-priori oracle rows (45 matching displayed values + 1 verified intentional contract divergence `v046`) and all 49 post-hoc oracle rows (49/49, 100.00% match).
  4. Verified all 5 public anova-oneway reference vectors from `contract/public_vectors.jsonl` ($< 4.8 \times 10^{-8}$ max difference).
  5. Verified manual CLI operations: exit 0 single-line JSON, exit 2 `INCONSISTENT`, exit 0 `--version`, exit 2 `MISSING_PARAM`, exit 2 `UNKNOWN_PARAM`.
  6. Measured timing bounds across stress cases (all $< 0.20$s per call, far below 2.0s limit).
  7. Performed full leak scan (`FUN_`, `DAT_`, `0x00`, `Ghidra`, `objdump`, `LEDGER`, `disassembl`) across `src/`, `tests/`, `README.md` (0 matches) and Prompt A token scan on `SPEC.md` (0 matches).
  8. Audited repository and git history for forbidden extensions (`.exe`, `.zip`, `.gpr`, `.rep`, `.lock`, `GPowerWin_*`), blobs $>5$MB, and credentials (0 found outside ignored `.venv/`).
  9. Updated `demo/demo_script.ps1` with timed paced execution running in 58.7s (target ~60s).
  10. Updated `README.md` and `tests/REPORT.md` with CONTRACT.md v1.0.0 interpretations, assumptions, and exact empirical counts.
- **Iterations count:** Complete
- **Token & Cost Metrics:**
  - Prompt tokens: Not recorded: the IDE did not expose token counts for this session.
  - Candidate / Completion tokens: Not recorded: the IDE did not expose token counts for this session.
  - Total Cost: Not recorded: the IDE did not expose token counts for this session.
- **Learnings:**
  - Disentangling contract-mandated schema rules from external application GUI quirks (such as silent float-to-int rounding) requires explicit divergence documentation so that reviewers understand intentional non-zero exit codes.

### Session 7: Automated Demo Video Generation
- **Local Date:** 2026-10-23
- **Focus:**
  1. Implemented `demo/make_demo_video.py` to programmatically execute the real CLI and test harnesses live, capturing stdout, stderr, exit codes, and execution timings.
  2. Rendered a 1280x720 dark terminal video with Consolas font, character typing animation, and two-column expected vs actual comparison tables.
  3. Programmatically integrated oracle CSV verification with real GUI screenshots (`v003.png` and `p002.png`), dynamic test count parsing (57 unit tests, 46 a-priori differential rows with intentional divergence `v046`, and 49 post-hoc rows), and path/user sanitization (`<repo>`).
  4. Encoded `demo/gpower_clone_demo.mp4` (75.20s duration, 0.60 MB, well under the 5 MB limit) and generated `demo/demo_transcript.txt`.
- **Iterations count:** Complete
- **Learnings:**
  - Automated video generation directly from CLI subprocess execution guarantees 100% empirical fidelity, eliminating human typing error while keeping video artifacts ultra-compact (< 1 MB) using H.264 CRF encoding.


