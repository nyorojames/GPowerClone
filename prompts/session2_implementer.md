You are implementing a command-line statistical power calculator named "gpower-clone" for a university assignment.

YOUR ONLY SOURCE OF TRUTH is the file SPEC.md in this repository. You must not read LEDGER.md, HALLUCINATIONS.md, anything in oracle/, any screenshots, or anything about how any other program is built. You must not look at, download or analyse any other software. If SPEC.md is missing or ambiguous on a point, do NOT fill the gap from outside knowledge: write the question into SPEC_QUESTIONS.md, implement the most literal reading, and mark it clearly in a code comment.

TASKS
1. Implement the engine in src/engine/ (Python 3.12) as a pure module: validated input in, structured result or structured error out. No printing, no file or network access. Use scipy for distribution functions only as SPEC.md allows.
2. Implement the CLI in src/cli/ as a thin wrapper. All flag names, flag aliases and output key names must live in ONE mapping module (src/cli/contract_map.py) and nowhere else. Success: single-line JSON. Invalid input: {"error": "..."} and a nonzero exit code.
3. Write one unit test per Gherkin scenario in SPEC.md, named after the scenario.
4. Write contract tests that check CLI output format against SPEC.md.
5. Write README.md with install and run instructions. Name the tool "gpower-clone" and never describe it as G*Power.

QUALITY
- Deterministic; no hidden state.
- Each numeric rule in the engine carries a comment pointing to the SPEC.md section.
- At the end, list every ambiguity you hit and the reading you chose.
- Keep a short running note for AGENT_COST.md: which agent you are, number of iterations, what you would do differently. Do not guess token counts.
- Save this prompt verbatim as prompts/session2_implementer.md.