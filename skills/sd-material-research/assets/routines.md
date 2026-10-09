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

Sitting 1 writes the pointer, runs `runstate.py set mode=probe owner=pending next_leg=leg-a` and calls
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
project. The skill never changes that setting. A probe leg still held by a card after 3 min is named in the go
question; once the user has approved it, re-read its probe file before setting `continuation`.

## run-watchdog

Cron `*/30 * * * *`, `notifyOnCompletion` false. Created with the legs, on the first material. It restarts a run whose
leg died, and never becomes a second Designer caller. Stored prompt:

```
You are the run-watchdog of sd-material-research. Run: python3 ~/.claude/skills/sd-material-research/scripts/runstate.py watchdog. If its action is idle, ok or limit, end your turn now. Otherwise follow the run-watchdog rules in ~/.claude/skills/sd-material-research/assets/routines.md for that action. Never call substance-designer tools. Write only RUN.json, through runstate.py.
```

`runstate.py watchdog` reads the pointer, RUN.json and the heartbeat and writes nothing. It prints `idle` (no
unattended run, or now is outside `go_utc` to the deadline), `limit` (the watchdog has acted twice this run), `ok`
(heartbeat 45 min old or newer), `notify` or `check_runs` (heartbeat stale; `notify` when `continuation` is not
`routine`), with `heartbeat_age_min`, `over_90`, `next_leg` and `second` (one watchdog action already taken). Then:
- `notify`: no leg routine carries this run, so start nothing: record `runstate.py incident --by watchdog --text
  "heartbeat <age> min, continuation <c>"`, send "blocked", end.
- `check_runs`: list_task_runs on leg-a and leg-b.
  - No run `running`: the leg died. `runstate.py incident --by watchdog --text "leg dead: heartbeat <age> min,
    starting <next_leg>"`, `runstate.py set owner=pending`, note T (`date -u +%FT%TZ`), call `run_scheduled_task` on
    `next_leg`, then `runstate.py wait-up --since T` (3 min) and set `owner` to the session it prints and `next_leg`
    to the other leg routine, as a hand-off does (`SKILL.md`, Legs). When `second` is true, also send "blocked".
    When wait-up times out: an incident, "blocked", end.
  - A run `running` and `over_90`: the leg hangs and may still hold Designer. Start nothing: record
    `runstate.py incident --by watchdog --text "leg hung: <leg> running, heartbeat <age> min"`, send "blocked", end.
  - A run `running`, heartbeat not over 90 min: end.
Every runstate.py call takes `--tools <tools>` from the pointer. "blocked" is the notification in `SKILL.md`,
Notifications ("blocked: <leg dead | leg hung | run stalled>, heartbeat <age> min, since HH:MM"); it goes out at most
once a run: send it only when no watchdog incident ends in `notified`, and end the incident you record with
`: notified` when you send it.

The heartbeat shows that the owner's session is alive (its background loop writes it every 15 min), not that its turn
is making progress, so a hung turn in a live session is not caught here; its gap shows in the report's path clock.
