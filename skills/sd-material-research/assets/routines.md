# Routines for an unattended run

An unattended run (`SKILL.md`, Unattended run) continues in legs: sessions started by two routines, `leg-a` and
`leg-b`, that start each other at a hand-off. The first material creates them once (scheduled-tasks
`create_scheduled_task`), with their approvals granted while the user is present; later materials only rewrite the
pointer file. Create them from the session that runs sitting 1, in the bridge repo folder (the routines' sessions start
there).

**Pointer file** `~/Documents/Allegorithmic/Substance Designer/RUN_POINTER.json`, written by sitting 1 for each
material: `{"tools": "<absolute tools folder>", "material": "<name>", "set_utc": "<UTC>"}`. Every routine reads it
first.

## leg-a and leg-b

No schedule (run on demand), `notifyOnCompletion` false. Stored prompt, the same for both apart from the name:

```
Use sd-material-research to continue the unattended run named in ~/Documents/Allegorithmic/Substance Designer/RUN_POINTER.json. You are leg-a. Read that run's RUN.json and the run block at the top of its CONTEXT_PROMPT.md first. If RUN.json mode is "probe", do the probe steps in the skill's assets/routines.md and stop. Otherwise follow the skill's Legs rules: stamp up, wait until RUN.json names you owner, then carry on from the run block's next step. Ask nothing until the stop point; at the stop point give the report's answer batch.
```
