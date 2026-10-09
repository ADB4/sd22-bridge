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

## Probe (sitting 1, beside the spec writing)

Sitting 1 writes the pointer, sets RUN.json `{"mode": "probe", "owner": "pending", "next_leg": "leg-a"}` and calls
`run_scheduled_task` on leg-a. Each probe leg:
1. Stamps `up` (`runstate.py stamp --stage - --event up --note "probe <leg>"`).
2. Writes `<tools>/review/probe_<leg>.json`: get_session on itself (effort, model, permissionMode),
   `$CLAUDE_CODE_SESSION_ATTENDED`, `$CLAUDE_EFFORT`, ultracode as the session reports it, the working folder, and
   per tool `present` and `call_ok`: Bash (`date -u`), Workflow (a script with no agents that returns 1), Monitor (a
   2-second one), the substance-designer MCP (designer_status and list_packages only), scheduled-tasks
   (list_scheduled_tasks), SendUserFile (the probe file itself), PushNotification ("probe: <leg> can notify"), and
   AskUserQuestion (present only: never call it). Note any approval card that appeared.
3. leg-a only: in this same turn, with no user message, check list_task_runs and call `run_scheduled_task` on leg-b,
   then record in its probe file whether leg-b showed `running` within 3 min.
4. Ends its turn.
Sitting 1 waits up to 3 min per leg, reads both probe files and list_task_runs, then sets RUN.json `continuation`:
`routine` when both legs came up at xhigh with every tool and no card, else `compaction` (route B) or `fireAt` (route
C) as the Legs rules say, and tells the user at the go question which one the night will use. An approval card that
would still appear at night is settled there: the user approves it for the routine, or chooses auto mode for the
project. The skill never changes that setting.

## run-watchdog

Cron `*/30 * * * *`, `notifyOnCompletion` false. Created with the legs, on the first material. Stored prompt:

```
Use sd-material-research's watchdog rules (assets/routines.md, run-watchdog) for the run named in ~/Documents/Allegorithmic/Substance Designer/RUN_POINTER.json. Never call substance-designer tools. Write only RUN.json, through runstate.py.
```

Rules, in order:
1. Read the pointer and RUN.json. End unless `mode` is `unattended` and now is between `go_utc` and the deadline.
2. Heartbeat age: `runstate.py heartbeat-age --tools <tools>`.
3. Age over 45 min, and list_task_runs shows no `running` run on leg-a or leg-b: the leg died.
   `runstate.py incident --by watchdog --text "leg dead: heartbeat <age> min, starting <next_leg>"`, set `owner`
   `pending`, and call `run_scheduled_task` on RUN.json's `next_leg`.
4. Age over 90 min while a leg run shows `running`: the leg hangs and may still hold Designer. Do not start another
   leg; send the "blocked" notification (`SKILL.md`, Notifications) once and record an incident.
5. Otherwise end.
Act at most twice a night (count the incidents `by` watchdog); the second action also sends the "blocked"
notification.
