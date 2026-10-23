THIS SESSION: SPEC AMENDMENT after differential testing. You may read everything. Do not touch src/ or tests/.

Failing post-hoc oracle rows: p038, p039, p040, p046, p049.
1. For each row print: typed inputs, values G*Power displayed (CSV and screenshot), what the CLI returned, and the difference.
2. Classify each as (a) engine numerical failure that SPEC.md already implies, or (b) spec missed a rule.
3. For p049 (alpha exactly 1e-7): determine from the oracle row and screenshot whether G*Power accepted it. Then check which boundaries the existing oracle rows actually settle (inclusive or exclusive): alpha lower and upper, power lower and upper, f lower (1e-6) and upper (50), groups minimum. Report which are settled and which are NOT. Do not guess unsettled ones. For unsettled boundaries, add single rows to oracle/boundary_vectors.csv using tools/collect_posthoc.py or tools/collect_oracle.py (values read from the window only), and tell me when the GUI automation starts and ends.
4. Amend SPEC.md with BEHAVIOUR only:
   - exact inclusivity of every boundary the oracle settled;
   - an accuracy requirement: power and critical values must be correct to 1e-6 (absolute or relative) for every N up to 2147483647 and any noncentrality, including very large values where power approaches 1; no underflow, overflow, NaN or infinity; every call must still finish in under 2 seconds;
   - Gherkin scenarios for the failing cases, using the numbers G*Power displayed.
   No function names, addresses, instruction names, tool names, file paths or internal return codes of the original program.
5. Run the SPEC.md leak scan from earlier (include 'oracle','gpower_vectors','screenshot','scratch','tools\\','\.py') and show the empty output.
6. Log in HALLUCINATIONS.md: the engine passed all a-priori rows but failed large-noncentrality post-hoc rows; caught by differential testing; include who/what/how/which test. Add a note to AGENT_COST.md. Save this prompt verbatim as prompts/session1d_spec_amendment.md. STOP.
