# Routines for an unattended run

An unattended run (`SKILL.md`, Unattended run) continues in legs: sessions of two cron routines, `leg-a` and `leg-b`,
that take the run in turn. A routine run may not start another routine: the app refuses `run_scheduled_task` from a
scheduled-task run session ("Run it from a regular session instead"), so a leg is never started by the other one.
Every firing of a leg runs `runstate.py claim`, which takes the run only when RUN.json `owner` is `pending` and
`next_leg` names that leg, inside the run's window; otherwise the firing ends at once. A hand-off is `owner=pending` and
the end of the outgoing leg's turn (`SKILL.md`, Legs), and the next leg's firing takes the run within about 10 min. A
run in progress blocks its own routine's later firings, so a leg never runs twice at once.

The first material creates the three routines once (scheduled-tasks `create_scheduled_task`, from the session that
runs sitting 1, in the bridge repo folder: the routines' sessions start there); later materials only rewrite the
pointer file. Sitting 1 enables leg-a, leg-b and run-watchdog at the go answer (`update_scheduled_task` enabled true);
the session that takes the user's first reply after the stop point disables them (a routine run nobody has open is
refused that call). While they are on, an idle firing ends after its claim; while they are off, nothing fires.

**Permissions.** A routine run starts in permission mode "default", whatever the project's `defaultMode` says, and the
app shows its approval cards only in a run someone has open: at night a card is a refusal. The legs work through the
repo's `.claude/settings.local.json` allowlist (gitignored), which routine runs read. First material only, the user adds
it at readiness (it is theirs to change; the skill never writes it):
```bash
python3 -c "import json;p='.claude/settings.local.json';d=json.load(open(p));a=d.setdefault('permissions',{}).setdefault('allow',[]);R=['Bash','Read(~/Documents/Allegorithmic/Substance Designer/**)','Read(~/.claude/skills/**)','Edit(~/Documents/Allegorithmic/Substance Designer/**)','mcp__substance-designer','mcp__scheduled-tasks','mcp__ccd_session_mgmt__get_session','Workflow','Agent','TaskStop','SendUserFile','PushNotification'];[a.append(r) for r in R if r not in a];json.dump(d,open(p,'w'),indent=2)"
```
(run in the bridge repo folder). Routine sessions are not on Remote Control, so a leg's PushNotification reaches this
Mac only ("Mobile push not sent (Remote Control inactive)").

**Pointer file** `~/Documents/Allegorithmic/Substance Designer/RUN_POINTER.json`, written by sitting 1 for each
material: `{"tools": "<absolute tools folder>", "material": "<name>", "set_utc": "<UTC>"}`. Every routine reads it
first.

## leg-a and leg-b

Cron `*/10 * * * *`, `notifyOnCompletion` false, disabled between runs. A routine run is told that the user is away
and to take a "write" action only when its task file asks for it, so the stored prompt names them. Stored prompt, the
same for both apart from the name:

```
You are leg-a of sd-material-research's unattended runs. Run: python3 ~/.claude/skills/sd-material-research/scripts/runstate.py claim --leg leg-a. If its action is idle, end your turn now. If it is probe, do the probe steps in ~/.claude/skills/sd-material-research/assets/routines.md (Probe) and end your turn. If it is take, you own the run in the printed tools folder: use sd-material-research, read that run's RUN.json and the run block at the top of its CONTEXT_PROMPT.md, follow the skill's Legs rules for a new leg, and carry on from the run block's next step. Ask nothing until the stop point; at the stop point give the report's answer batch. This task file asks for every action those rules prescribe: substance-designer calls while RUN.json names you owner, list_task_runs, update_scheduled_task on leg-a, leg-b and run-watchdog after the stop point, Workflow and Agent runs, SendUserFile, PushNotification, and file writes in the run's tools folder.
```

## Probe (sitting 1, beside the spec writing)

Sitting 1 is a regular session, so it may call `run_scheduled_task`. Once the allowlist is in, it writes the pointer,
runs `runstate.py set mode=probe owner=pending`, and calls `run_scheduled_task` on leg-a, leg-b and run-watchdog. Each
leg's claim prints `probe` (until its probe file exists), and the leg:
1. Stamps `up` (`runstate.py stamp --stage - --event up --note "probe <leg>"`).
2. Writes `<tools>/review/probe_<leg>.json` with the Write tool, then records in it: get_session on itself (effort,
   model, permissionMode, remoteControlState), `$CLAUDE_CODE_SESSION_ATTENDED`, `$CLAUDE_EFFORT`, ultracode as the
   session reports it, the working folder, and per tool `present` and `call_ok`: Bash (`date -u`), Read
   (`<tools>/RUN.json`), Edit (one key of the probe file), Workflow (a script with no agents that returns 1), Agent
   (model haiku, "reply 1"), a background Bash (`python3 -c "import time; time.sleep(60)"`) stopped with TaskStop, the
   substance-designer MCP (designer_status, list_packages, and run_python with `result = 1`), list_task_runs on both
   legs, SendUserFile (the probe file itself), PushNotification ("probe: <leg> can notify", with its reply), and
   AskUserQuestion (present only: never call it). A refused or held call is recorded with its message.
3. Ends its turn.
Sitting 1 waits up to 3 min per routine, reads both probe files, RUN.json `probe_watchdog` and list_task_runs (each run
`succeeded` once its turn has ended), then sets RUN.json `continuation`: `routine` when both legs came up at xhigh with
every tool, else `compaction` (route B, `SKILL.md`, Legs), and tells the user at the go question which one the night
will use. A refused or held call means the allowlist misses a rule: the go question names it, with the rule to add.

## run-watchdog

Cron `*/30 * * * *`, `notifyOnCompletion` false, enabled and disabled with the legs. It releases a run whose leg died,
and never becomes a second Designer caller. Stored prompt:

```
You are the run-watchdog of sd-material-research. Run: python3 ~/.claude/skills/sd-material-research/scripts/runstate.py watchdog. If its action is idle, ok or limit, end your turn now. Otherwise follow the run-watchdog rules in ~/.claude/skills/sd-material-research/assets/routines.md for that action. Never call substance-designer tools. Write only RUN.json, through runstate.py. This task file asks for the actions those rules prescribe: list_task_runs and PushNotification.
```

`runstate.py watchdog` reads the pointer, RUN.json and the heartbeat and writes nothing. It prints `idle` (no
unattended run, or now is outside `go_utc` to the deadline), `limit` (the watchdog has acted twice this run), `ok`
(heartbeat 45 min old or newer), `notify` or `check_runs` (heartbeat stale; `notify` when `continuation` is not
`routine`), with `heartbeat_age_min`, `over_90`, `next_leg` and `second` (one watchdog action already taken). Then:
- `notify`: no leg routine carries this run, so release nothing: record `runstate.py incident --by watchdog --text
  "heartbeat <age> min, continuation <c>"`, send "blocked", end.
- `check_runs`: list_task_runs on leg-a and leg-b.
  - No run `running`: the leg died (a stopped or failed turn shows `succeeded` or `failed`). `runstate.py incident --by
    watchdog --text "leg dead: heartbeat <age> min, released to <next_leg>"`, then `runstate.py set owner=pending`:
    `next_leg`'s next firing takes the run. When `second` is true, also send "blocked".
  - A run `running` and `over_90`: the leg hangs and may still hold Designer. Release nothing: record
    `runstate.py incident --by watchdog --text "leg hung: <leg> running, heartbeat <age> min"`, send "blocked", end.
  - A run `running`, heartbeat not over 90 min: end.
- `probe` (mode probe, no `probe_watchdog` yet): call list_task_runs on leg-a and PushNotification ("probe: watchdog can
  notify"), then `runstate.py set 'probe_watchdog={"utc": "<date -u>", "calls_ok": [...], "refused": {...}}'`, end.
Every runstate.py call takes `--tools <tools>` from the pointer. "blocked" is the notification in `SKILL.md`,
Notifications ("blocked: <leg dead | leg hung | run stalled>, heartbeat <age> min, since HH:MM"); it goes out at most
once a run: send it only when no watchdog incident ends in `notified`, and end the incident you record with
`: notified` when you send it.

The heartbeat shows that the owner's session wrote something recently: its background loop (`runstate.py heartbeat
--loop 300`) writes it only while the session's transcript, or a subagent or Workflow agent of it, was written in the
last 20 min, or a lease the owner set is still ahead (`runstate.py lease`, before it ends a turn to wait on a
background shell). A leg whose turn died (an API error, a stop) leaves the loop running but no longer writing, so the
heartbeat goes stale within about 65 min. A turn that hangs inside a live tool call is caught the same way; whether
its run still shows `running` decides between releasing the run and only notifying.
