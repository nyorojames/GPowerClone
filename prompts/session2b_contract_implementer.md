You are updating the command-line tool "gpower-clone" so it follows SPEC.md exactly. SPEC.md is your ONLY source of truth about required behaviour, including the interface contract it contains.

ALLOWED TO READ: SPEC.md, and my own earlier code in src/ and tests/ (your previous work).
NOT ALLOWED TO READ: LEDGER.md, HALLUCINATIONS.md, AGENT_COST.md, anything in oracle/, contract/, ContractFile/, ClassTranscript/, tools/, scratch/, prompts/ and all screenshots. Do not look at, download, run or analyse any other software, and do not use outside knowledge of how G*Power is built. If SPEC.md is ambiguous or silent, do NOT fill the gap from outside knowledge: write the question to SPEC_QUESTIONS.md, implement the most literal reading, and mark it with a comment "ASSUMPTION: see SPEC_QUESTIONS.md".

Never put function names, addresses, instruction names, or any reference to reverse engineering tools into code, comments, tests or the README. Comments may cite SPEC.md section numbers only.

TASKS
1. CLI behaviour (all names and keys live ONLY in src/cli/contract_map.py):
   - Command form: gpower-clone --test <TEST_ID> --mode <MODE_ID> [--<field> <value> ...]
   - No defaults. Missing required field -> MISSING_PARAM. Unknown or mode-irrelevant field (for example --power in post-hoc) -> UNKNOWN_PARAM.
   - --version prints the single-line JSON required by SPEC.md.
   - Success: exactly one line of JSON on stdout, nothing else (logs only on stderr), exit code 0. Numbers at full double precision (no rounding). Integer fields (n_total, df1, df2) are JSON integers, never 88.0.
   - Errors: one line on stdout {"error": "...", "code": "...", "field": "..."}; exit code 2 for invalid input, 1 for internal error. Use all seven error codes exactly as SPEC.md defines them.
   - Output keys come from SPEC.md. The critical value for this family is "critical_f". Extra fields such as n_per_group are allowed.
   - Decimal separator is always a dot, independent of the operating system locale.
   - Valid but unimplemented modes (compromise, criterion, sensitivity) and other test ids: follow SPEC.md; if it is silent, return UNSUPPORTED with exit code 2 and record that assumption.
2. Engine: one pure module in src/engine/ (validated input in, structured result or structured error out; no I/O). Implement a-priori and post-hoc exactly as SPEC.md states, including every observed boundary and error rule. The CLI contains no calculation logic.
3. Speed: every call must finish in under 2 seconds, including process start. Use bracketing plus bisection, never linear scans over N, and avoid heavy imports. Measure and report: process start time, and the slowest case among very small effects (f = 1e-5), very large N (1e7), large group counts (100), and extreme alpha. If any valid input exceeds 1.5 seconds, report it; do not change the spec.
4. Tests (use the standard library unittest unless pytest is installed):
   - one test per Gherkin scenario in SPEC.md, named after the scenario
   - the five public anova-oneway examples that SPEC.md lists
   - contract tests: stdout is exactly one line of JSON, key names, JSON integer types, exit codes 0/1/2, error code and field, missing and unknown parameters, --version
   - a timing test for the worst cases above
   - numeric comparison rule everywhere: |a - b| <= 1e-6 OR relative difference <= 1e-6; integers must match exactly
5. Update README.md only for: install and run instructions, flag names and output keys. Do not write about the original program's internals. Name the tool "gpower-clone", never G*Power.
6. At the end, list every ambiguity you hit and the reading you chose, and the measured timings. Do NOT edit SPEC.md. Add a short note to AGENT_COST.md (agent, iterations, what you would do differently); do not guess token counts. Save this prompt verbatim as prompts/session2b_contract_implementer.md.
