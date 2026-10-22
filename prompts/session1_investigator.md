THIS SESSION: INVESTIGATOR (uses REA and Ghidra). You produce ONLY: SPEC.md, LEDGER.md, HALLUCINATIONS.md, the input side of oracle/gpower_vectors.csv, and AGENT_COST.md notes. You do NOT write the engine or CLI.

STEP 1: Environment
- Run `rea doctor` and confirm the ghidra check is healthy and GHIDRA_INSTALL_DIR is set. If not, stop and tell me.
- Call binary_session and report the live server identity and tool count.
- Ask yourself and answer in writing: "Are REA tools and the Ghidra provider available in this session?" I will screenshot that answer for the README.
- Seed HALLUCINATIONS.md with two real observations from my setup: (1) an agent expanded REA as "Reverse Engineering Assistant" when the course says "Reverse Engineer Anything"; (2) an agent reported 170 REA tools while `rea doctor` lists 207 MCP tools in its catalog (cause unresolved, possibly lazy loading). Label these as setup-phase entries; the entries caught by differential tests come later.

STEP 2: Oracle grid (before any investigation)
Create oracle/gpower_vectors.csv with columns:
id, mode, k_groups, effect_size_f, alpha, power, total_N, df1, df2, noncentrality, critical_F, actual_power, screenshot_file, probes
Fill ONLY the input columns, for at least 40 rows, and leave outputs blank for me. Cover:
- Typical: f = 0.1, 0.25, 0.4; k = 3, 4, 5; alpha 0.05 and 0.01; power 0.80, 0.90, 0.95
- Very small effects (f = 0.05, 0.02): convergence and large N
- Very large effects (f >= 1, 2): lower bound of N
- k = 2 and large k (10, 20)
- Boundary cases: power equal to alpha, power below alpha, power = 1, alpha = 0, f = 0
- Invalid input: k = 1, k = 0, negative f, non-numeric
Mark in "probes" which row tests which hidden-behaviour question.
Tell me exactly which fields the G*Power GUI shows for this test so I record the right output columns.

STEP 3: Hypotheses to verify (these are NOT facts; tag [AJAN] until proven)
- Noncentrality = f^2 * N; df1 = k - 1; df2 = N - k
- N is found by iterating until power >= target: check start value, step, stopping condition, upper limit
- Rounding of N; whether N must be divisible by k; minimum N
- Handling of invalid and degenerate input
- Whether reported actual power can differ from requested power
Use REA and Ghidra to find where the program computes these. Start NARROW: search strings and procedure names for terms tied to the one-way ANOVA test and its inputs, then analyse only the functions those references lead to. Do not try to decompile all 2.2 MB.
Record each finding in LEDGER.md as a table:
ID | Claim | Tag [DOK]/[REA]/[AJAN] | Evidence (tool, function address or string reference, short quote at most) | Unknown | How to test it

STEP 4: Early sanity check
Write a throwaway script using scipy.stats.ncf that computes N for 3 of my grid rows. Tell me which 3 to check in the GUI first, so we learn early whether our formula understanding is right.

STEP 5: SPEC.md (Gherkin)
Write it so an implementer with ZERO knowledge of the original can build a matching engine. Sections:
1. Scope (G*Power 3.1.9.7, anova-oneway, a-priori)
2. Inputs, ranges, defaults, units
3. Algorithm in plain language and formulas (no decompiled code)
4. Search and stopping rules, rounding, minimum and maximum N
5. Outputs and exact definitions
6. Error handling and invalid input behaviour
7. CLI contract (see Step 6)
8. Acceptance criteria in Gherkin (Feature / Scenario / Given / When / Then). Each scenario cites a LEDGER.md row ID. Include scenarios for the documented behaviour AND for every [REA] finding that is not in the manual
9. Unknowns, listed honestly
Anything you could only tag [AJAN] must be written as an open assumption, not as a rule.

STEP 6: Provisional CLI contract (mark every line "PROVISIONAL, official CONTRACT.md not available")
  gpower-clone --test anova-oneway --mode a-priori --f 0.25 --alpha 0.05 --power 0.95 --groups 3
Output, single-line JSON:
  {"n_per_group":<int>,"n_total":<int>,"actual_power":<float>,"critical":<float>,"df1":<int>,"df2":<int>,"ncp":<float>}
Invalid input: {"error":"<description>"} and a nonzero exit code.
Define accepted flag aliases (--effect-size for --f; --k for --groups) and require all flag and key names to sit in ONE mapping module in the CLI layer.

STEP 7: Save and finish
Save this prompt verbatim as prompts/session1_investigator.md. List every claim still tagged [AJAN] and which of my GUI vectors would resolve it. STOP after SPEC.md. Do not implement anything.
