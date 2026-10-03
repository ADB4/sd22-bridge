# Evals: spec dry runs

`evals.json` holds three spec dry runs (asphalt, concrete, wood). Each runs twice, with the skill and without it
(baseline), and a blind grader scores both against the expectations. Iteration 1 (2026-10-03) and its review page
are in the dev folder (`sd-material-research-dev/workspace/`), with the scripts `prep_blind.sh`, `unblind.py`,
`validate_checks.py` and `build_review.py`.

## Run prompt (with skill)

```
Execute this task as a test run of a skill.

- Skill path: ~/.claude/skills/sd-material-research/. Its main file is SKILL.md. Read it and follow it, and read the
  references it points to as it tells you.
- The user's request (verbatim): "<prompt from evals.json>"
- Test constraints (this is a spec dry run):
  - Do stages 0-3 only (orient, interview, research, spec) and stop at the spec gate.
  - Substance Designer is not available: do not call any substance-designer tool, and do not create a tools folder
    under ~/Documents/Allegorithmic. Write everything to the output folder below instead of <tools>.
  - You cannot ask the user questions. Write the interview questions you would ask, each with options and your
    recommended default, to interview.md, then assume the recommended defaults and proceed.
  - Do the research for real (web search and fetch through ToolSearch "select:WebSearch,WebFetch").
  - Do not read sd-material-research-dev/ (test infrastructure) or any other test run's folder.
  - Temporary files go in a scratchpad subfolder named after this run (<eval>_<condition>/): runs execute in
    parallel and share one scratchpad.
- Save outputs to: <workspace>/iteration-N/<eval>/with_skill/outputs/
- Outputs: interview.md; research/notes.md (plus a new or updated sheet in research/, never the skill's own files);
  spec.md; checks/<variant>.json per variant; summary.md (the spec-gate summary).
- Final reply: the variants, the 3-6 key invariants in one line each, and anything you could not source.
```

The baseline prompt is the same without the skill bullet, plus "do not read ~/.claude/skills/sd-material-research/".
In iteration 1 the main file was still `SKILL.draft.md`; the prompt named it explicitly.

Subagents may be blocked from writing a report-like `summary.md`; if so, save it from the run's final reply with a
comment at the top saying so. `prep_blind.sh` strips that comment before grading.
