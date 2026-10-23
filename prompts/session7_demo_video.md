# Session 7: Automated Demo Video Generation

## Initial Prompt

```
Create an automatically generated demo video for my repo. Rules: do not change src/, tests/, oracle/, SPEC.md, LEDGER.md or HALLUCINATIONS.md. Never show or copy GPowerNT.exe or any file from the G*Power download. Never write credentials anywhere. No network use except `pip install`. Show me a short plan (scenes, libraries) and WAIT for my "OK" before building.

GOAL
demo/make_demo_video.py: one command (`python demo/make_demo_video.py`) that (1) really runs the CLI, (2) captures stdout, exit code and elapsed time of every command, (3) renders a video that a viewer can follow without any explanation, (4) writes demo/gpower_clone_demo.mp4 and demo/demo_transcript.txt (the raw captured outputs). NOTHING shown in the video may be typed by hand or invented: every output, exit code, timing, count and PASS/FAIL comes from a real run executed by the script. If a real result does not match what is expected, the video shows FAIL in red and the script exits with a nonzero code.

TECHNICAL APPROACH
- Render frames with Pillow as a dark terminal window (1280x720, large monospace font; use Consolas from C:\Windows\Fonts if present, otherwise any available monospace font), encode with imageio and imageio-ffmpeg (bundled ffmpeg, so no manual install). Add pillow, numpy, imageio and imageio-ffmpeg to requirements.txt.
- Run commands with subprocess (timeout 60 s each) from the repo root using the same interpreter, exactly as a user would: `python -m src.cli.main ...` (check README for the real invocation and show it as `gpower-clone ...` only if a launcher with that name really exists; otherwise show the real command).
- Followability: a step counter (e.g. "Step 3 / 8") and a one-line caption in plain English at the top of every scene; the command is "typed" character by character (about 40 characters per second), then the output appears; hold each output long enough to read (minimum 3 seconds, more for longer output); wrap long JSON lines at the frame width, pretty-printing a copy of each JSON result with one field per line and a short plain-English label for each field (ncp = noncentrality, critical_f = critical F value, df1/df2 = degrees of freedom, n_total = total sample size, actual_power); show the exit code and elapsed milliseconds under every command.
- Programmatic checks before encoding: no text is cut off at any frame edge (measure each rendered line with the font and wrap or shrink); total duration is between 60 and 90 seconds; file size under 10 MB. Afterwards extract 6 frames (one per scene), look at each, and tell me what you saw.

SCENES (all values read from real runs or real files)
1. Title: "gpower-clone: one-way ANOVA power analysis (K3)", "Independent clean-room reimplementation, not G*Power", date, and the real short git commit hash (`git rev-parse --short HEAD`, or "uncommitted" if none).
2. `--version`: show the real output.
3. A-priori public vector from contract/public_vectors.jsonl (anova-oneway, a-priori): show the command, the real output, then a two-column comparison "expected (instructor)" versus "gpower-clone" for every expected field, with a green PASS or red FAIL per field using the rule |a-b| <= 1e-6 absolute or relative, integers exact.
4. Post-hoc public vector, same layout.
5. An oracle comparison: take one a-priori row from oracle/gpower_vectors.csv and one post-hoc row whose n_total is NOT a multiple of groups from oracle/posthoc_vectors.csv. Show "G*Power displayed (from my recorded oracle CSV)" versus "gpower-clone", per-field PASS/FAIL. If the row's screenshot exists in oracle/screenshots/, show it on the left half of the frame (scaled to fit) and the comparison on the right.
6. Invalid input: power below alpha. Show the real error JSON, the exit code (must be 2), and a one-line explanation of the fields code and field.
7. A missing parameter and an unknown parameter (two short commands). Show real outputs and exit codes.
8. Verification summary: run the real differential tests (46 a-priori rows, 49 post-hoc rows) and the real unit tests, parse the real counts from their output (never type them), and display "matches / total" for each, plus the slowest elapsed time seen in this video.
9. Closing frame: a checklist of what was shown, each with a PASS/FAIL taken from the real runs, the line "Video generated automatically by demo/make_demo_video.py", the date, and the commit hash.

AFTER BUILDING
- Run the script once end to end and report: duration, file size, exit code, per-scene PASS/FAIL, and anything that did not match.
- Update README.md: replace the "Video: <ADD LINK HERE>" line with "Demo video: demo/gpower_clone_demo.mp4 (generated automatically by `python demo/make_demo_video.py`, which executes the real CLI and renders its actual output; transcript in demo/demo_transcript.txt)". Do not claim it is a screen recording.
- Keep demo/demo_script.ps1 untouched. Run `Select-String -Path README.md,demo\make_demo_video.py -Pattern 'FUN_','DAT_','0x00','Ghidra','objdump','LEDGER','disassembl'` and show the output; the demo must not mention how the original was analysed.
- Add a short note to AGENT_COST.md and save this prompt verbatim as prompts/session7_demo_video.md. Then STOP. Do not commit or push.
```

## Follow-up Approval & Requirements

```
OK, build it, with these changes:
1. Scene 8: parse the real output of the differential test and show the a-priori result as "matching G*Power values: 45/46 + 1 intentional divergence (v046: contract requires INVALID_VALUE for non-integer groups)", the post-hoc result as 49/49, and the unit tests as the real count. Parse both stdout and stderr (unittest writes to stderr). Never type a count by hand.
2. Scene 5: choose the rows programmatically: a-priori v003, and the FIRST row in oracle/posthoc_vectors.csv where n_total % groups != 0. Show the real row ID, inputs and G*Power-displayed values from the CSV, and its screenshot if the file exists.
3. Scene 1 and 9: show the base commit as `git rev-parse --short HEAD`, followed by "(uncommitted changes)" if `git status --porcelain` is non-empty. Do not claim the video corresponds to the final commit.
4. Label the timing "slowest of the commands shown in this video".
5. Replace the repository's absolute path and my Windows user name with <repo> everywhere in the frames, in demo_transcript.txt and in the console output; display commands with relative paths only.
6. Keep the mp4 under 5 MB, duration 60 to 90 s.
7. After building: extract the 6 frames, tell me what you see in each, and list per-scene PASS/FAIL, duration, size, exit code. Do NOT commit or push. Run AGENT_COST.md edits last and keep them to one short note about this session.
```
