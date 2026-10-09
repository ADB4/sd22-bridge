# Context: code review of the Substance Designer 2022 bridge

## Task

Review the code in this repo for bugs, write up what holds up under scrutiny, then fix what's safe to fix on a branch. I chose these options on 2026-10-03:

- **Scope:** the bridge and the skill's scripts (exact list below).
- **Method:** a **lean** workflow of at most 20 agents (about 15 is typical), with models chosen per task. Cost matters: follow the budget rules under "Review process", and don't add agents beyond them without asking me.
- **Environment:** this Mac, **static only**. Never connect to Substance Designer, even if it happens to be running.
- **Output:** a findings report, then fixes committed on a new branch in a separate worktree. Stop before pushing.

The repo is public (`git@github.com:ADB4/sd22-bridge.git`). This file was written against commit `6864cf6` on `main`.

- **This file:** it's untracked. Never commit, stash, clean or delete it.
- **If `main` has moved:**
  - If local `main` isn't at `6864cf6`, review it as it is and say so in the report.
  - If `origin/main` is ahead, say so too.
  - Never pull, merge, reset or check out anything in this checkout (see "Live installs" for why).

## Paths

Most of these contain spaces, so quote them, and use `$HOME` rather than `~` inside quotes. Subagents and fresh Bash calls don't inherit shell variables. In the workflow script, write these out as absolute `/Users/andybui/...` strings, and have each Bash command set what it needs inline.

```
REPO="$HOME/Documents/Allegorithmic/Substance Designer/python/sduserplugins/sd-claude-bridge"
WT="$HOME/Documents/Allegorithmic/Substance Designer/sd-claude-bridge-review"   # fix worktree, created later
APP="$HOME/Library/Application Support/Steam/steamapps/common/Substance 3D Designer 2022/Adobe Substance 3D Designer.app/Contents"
SDPY="$APP/plugins/pythonsdk/bin/python3.9"                      # Designer's Python 3.9.9, PySide2 5.15.8, no numpy/PIL
PY37="$HOME/.pyenv/versions/3.7.9/bin/python3.7"                 # real 3.7 for syntax checks; can't import sd (no _ctypes)
VPY="$HOME/Library/Application Support/sd-claude-bridge/venv/bin/python"   # 3.12.15, mcp 1.30.0, pydantic 2.13.5, pillow 12.3.0
SKPY="$HOME/.cache/sd-material-research/venv/bin/python"         # 3.14.3, numpy, Pillow, scipy, cv2
DEV="$HOME/Documents/Allegorithmic/Substance Designer/sd-material-research-dev"   # skill dev tests, not under git
SCRIPTS="$REPO/skills/sd-material-research/scripts"              # use $WT/... in the fix phase
SCRATCH=<your scratchpad directory>; each agent works in $SCRATCH/<agent-label>/
```

Inside `APP`:
- `Resources/python/sd/api` and `sd/ui`: the `sd` API source. Use it as the authority on API semantics, but note that most methods are thin wrappers around `sd._sdk`. `APIException` derives from `BaseException`. `UndoGroup.__exit__` (in `sdhistoryutils.py`) always commits; there's no rollback API.
- `Resources/python/tests`: Adobe's API tests. `tests/assets/test_read_content.txt` lists real property type ids.
- `Resources/packages`: 485 `.sbs` files counted recursively, 814 graphs.

Tools on this Mac:
- `pylint` 3.2.7 is on PATH.
- Not installed: ruff, pyflakes, mypy, vermin, shellcheck, pwsh. You may install them into a throwaway venv under `$SCRATCH`.
- `/bin/dash` exists; `/bin/sh` is bash 3.2.57.

## Live installs

**The live installs are symlinks into `$REPO`:**
- `sduserplugins/sd_claude_bridge` → `designer_plugin/sd_claude_bridge`
- the three files in `~/Library/Application Support/sd-claude-bridge/` → `mcp_server/`
- `~/.claude/skills/sd-material-research` → `skills/sd-material-research`

Any change in `$REPO`, even a stray `__pycache__`, lands in my live setup. Hence the read-only review and the separate worktree for fixes.

## In scope

- **Code:**
  - `designer_plugin/sd_claude_bridge/{__init__,bridge,commands}.py`
  - `mcp_server/{sd_designer_mcp,configure_claude}.py` and `mcp_server/requirements.txt`
  - `install.{bat,ps1,command}` and `uninstall.{bat,ps1,command}`
  - `tools/{link_install,tool_call}.py`, `.gitattributes`, `.gitignore`
  - `skills/sd-material-research/scripts/{sdkit,sdcall,matcheck,previews,calibrate}.py` and `setup_env.sh`
- **Docs, for drift only:** `README.md`, `skills/sd-material-research/SKILL.md`, `references/checks.md`, `references/sd_craft.md` §1-2, `assets/*.md`. Any other file that misstates an in-scope script's API or CLI is a drift finding. Fix it only with a one-line correction.
- **Out of scope:** `references/materials/*`, `method.md`, `research.md`, `interview.md`, `review.md`, `evals/`, and the workflow JS beyond the drift rule above.

## What the code is

```
Claude --stdio--> mcp_server/sd_designer_mcp.py --127.0.0.1:9881, JSON lines + token--> designer_plugin/sd_claude_bridge (inside Designer) --> sd API
```

| Part | Files (lines) | Runs under | Notes |
| --- | --- | --- | --- |
| Plugin | `__init__.py` (40), `bridge.py` (241), `commands.py` (1433) | `SDPY`, on Designer's Qt main thread | Stdlib plus Designer's `sd` and PySide2. A QTimer polls a non-blocking socket every 25 ms, so every command runs synchronously on the GUI thread. 20 commands. Nine edit commands run inside `_undo()` (an `UndoGroup`, or a nullcontext without `SDHistoryUtils`): create_node, create_library_node, create_output, connect, disconnect, set_parameter, move_nodes, delete_nodes, run_python. `commands.py` handlers can be hot-reloaded; changes to `dispatch()`, `bridge.py` or `__init__.py` need a Designer restart. |
| MCP server | `sd_designer_mcp.py` (421), `configure_claude.py` (104), `requirements.txt` | `VPY` | FastMCP stdio server, 19 tools: every command except `ping`, with renames `designer_status`=`info`, `connect_nodes`=`connect`, `disconnect_input`=`disconnect`, `render_preview`=`render`. One TCP connection per call. `SESSION_FILE` is fixed at import; the file itself is re-read on every call. stdout carries the MCP protocol. |
| Installers | `install.*`, `uninstall.*`, `tools/link_install.py` (242) | cmd plus Windows PowerShell 5.1; `/bin/sh`; Python 3.7+ | `link_install.py` links the installs into the checkout its own `__file__` sits in. Targets come from `$HOME`. |
| Dev harness | `tools/tool_call.py` (238) | `VPY` | Imports the server and runs tool calls in-process. `--raw` sends plugin commands directly. `--source` loads the `mcp_server/` beside it. |
| Skill, Designer side | `sdkit.py` (950) | `SDPY`, through `run_python` | Imports 27 symbols from `commands.py`, mostly private `_helpers`, so they are a de facto API. Also makes its own `sd` calls. |
| Skill, bridge client | `sdcall.py` (69) | Any `python3` | A second, independent socket client for long jobs (900 s timeout). |
| Skill, analysis | `matcheck.py` (1575), `previews.py` (720), `calibrate.py` (64), `setup_env.sh` | `SKPY` | They measure maps exported from Designer and never touch Designer or the bridge. |

**Session file:** `~/.sd_claude_bridge/session.json`, with keys `port, token, pid, bridge_version, python, started`. The plugin writes it when it starts and removes it on a clean exit, only if the pid and port match. A crash leaves it stale.

**`phase4_context.md` / `phase5_context.md`:** historical hand-offs. Only three of their rules carry over:
- plugin code is Python 3.7-compatible and stdlib only;
- the server never prints to stdout;
- `INSTRUCTIONS` and each tool description stay at most 2048 characters.

Ignore their install, hot-reload, live-test and memory-update steps.

## Ground rules

**Every agent is read-only.** Don't create, edit or delete anything outside `$SCRATCH/<agent-label>/`. To try a change, patch a copy in scratch. Never edit any of these:
- `$REPO`
- `$DEV`
- the venvs
- anything under `~/Library`, `~/.claude` or `~/.sd_claude_bridge`

Only the main session edits, and only in `$WT` during the fix phase.

Never do any of these, from any copy of the code:
- Use the `substance-designer` MCP tools, or open a socket to 127.0.0.1:9881-9890.
- Invoke the `sd-material-research` skill. Read its files as code.
- Run `tool_call.py` without `--list`/`--help`, or `sdcall.py` without `--help`.
- Call an `sdkit` function. Importing it is fine.
- Run an installer or uninstaller.
- Execute `configure_claude.py` as a script, with any arguments, including `--help`: every run rewrites the real Claude Desktop config. Only import it.
- Run any copy of `link_install.py` without `--status`/`--help`, unless the same command sets `HOME="$SCRATCH/<label>/home"`. Without that, it rewires Designer, Claude and the skill to that copy.
- Call `BridgeServer.start()`. It binds 9881-9890 and overwrites the real `session.json`.
- `brew install` anything, or `pip install` into an existing venv.
- Run `setup_env.sh` without `SDMR_VENV="$SCRATCH/<label>/venv"`.

Bytecode and caches:
- Run Python with `PYTHONDONTWRITEBYTECODE=1`.
- **That isn't enough for `py_compile`:** it writes `__pycache__` next to the source even with `-B`. Set `PYTHONPYCACHEPREFIX="$SCRATCH/<label>/pyc"`, or check syntax with `compile(open(f, encoding="utf-8").read(), f, "exec")`.
- Run linters from scratch: `ruff check --no-cache`, `mypy --cache-dir "$SCRATCH/<label>/mypy"`, `pylint --persistent=n`.

**Baseline to keep.** In `$REPO`, `git status --short --ignored` shows exactly two lines: `?? code_review_context.md` and `!! .claude/`. This must print nothing:

```
find "$REPO" \( -name __pycache__ -o -name .link-backups -o -name .ruff_cache -o -name .mypy_cache \) -not -path '*/.git/*'
```

## Offline techniques (all checked on 2026-10-03)

- **Plugin import:**
  ```
  cd "$SCRATCH/<label>" && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$APP/Resources/python:$REPO/designer_plugin" "$SDPY" -c 'import sd_claude_bridge.commands as C; print(sorted(C.COMMANDS))'
  ```
  `import sd` has no side effects. Pure-Python helpers work:
  - XML library parsing (`C._library_graphs(path)`, `C._main_graph(graphs, base)`);
  - HTML and description handling;
  - argument checks.

  Anything that reaches `sd.getContext()` or creates `SDValue*` objects needs Designer, so reason about it from the API source instead.
- **sdkit import:** the same command with `$SCRIPTS` added to `PYTHONPATH`. `import sdkit` only sets constants and `sd._sdk`.
- **Bridge protocol without a socket:** this needs `SDPY`.
  ```
  s = BridgeServer(stub_dispatch, "test")
  s._handle(json.dumps({"id": 1, "token": s.token, "cmd": "x", "args": {}}).encode())
  ```
  The second argument is the version; the token is `s.token`.
- **Server offline:**
  - Set `SD_CLAUDE_BRIDGE_SESSION="$SCRATCH/<label>/session.json"` in the command's environment, *before* Python starts. Setting `os.environ` after the import does nothing.
  - Give the fake file `"port": 1`.
  - Patch `socket.create_connection` before the first call.
  - Then `anyio.run(...)` over `mcp.list_tools()` / `mcp.call_tool(name, args)`.
  - Coercion without a call: `mcp._tool_manager.get_tool(name).fn_metadata.pre_parse_json(args)` and `.arg_model.model_validate(...)` (private APIs in mcp 1.30; see the venv's `mcp/server/fastmcp/utilities/func_metadata.py`).
  - `--check` enforces the 2048-character limits and opens no socket. It prints the tool count but doesn't assert it.
- **configure_claude:** import it and call `merge(path, entry, remove=False)` on files in scratch.
- **tool_call:** `--list` and `--source --list` work. Or import it and call `parse_arguments(items, schema)` / `check_arguments(args, schema, tool)`.
- **link_install logic:** copy the repo to `$SCRATCH/<label>/repo` and run that copy with `HOME="$SCRATCH/<label>/home"`.
- **Shell scripts:**
  - The `.command` files are `#!/bin/sh`: check them with `sh -n` and `/bin/dash -n`.
  - `setup_env.sh` is bash (`set -euo pipefail`): check it with `bash -n` only.
  - `.ps1` and `.bat` can only be reviewed by reading them against documented PowerShell 5.1 and cmd semantics. Tag those findings `platform: windows`.
- **Analysis scripts:** run with `SKPY` and synthetic 16-bit PNGs written with cv2/numpy in scratch. The baseline suites (each with `TMPDIR="$SCRATCH/<label>/tmp"`):
  - `MATCHECK_DIR="$SCRIPTS" "$SKPY" "$DEV/tests/matcheck/synthetic.py"`: 300/300 in about 3 s.
  - `MATCHECK_DIR="$SCRIPTS" "$SKPY" "$DEV/tests/matcheck/regress.py"`: 233/233 in about 26 s.
  - Copy `$DEV/tests/previews/t_previews.py` into scratch first (it writes and `rmtree`s folders next to itself), then run it with `PREVIEWS_DIR="$SCRIPTS"`: 91/91 in about 58 s.

  Without those env vars the suites import the `$REPO` copy. Real configs are at `$DEV/tests/matcheck/{classic,weathered,rustic}.json`; always pass `--out "$SCRATCH/..."`.

## Constraints any fix must respect

- **Plugin and `sdkit.py`:**
  - Stdlib only, plus `sd` and PySide2.
  - Python 3.7 syntax (`PY37` with `compile()`).
  - No stdlib APIs newer than 3.7 (`vermin -t=3.7- --no-tips`).
  - Must compile under `SDPY`.
- **Server:**
  - Python 3.10+.
  - Never write to stdout; use `_log`/stderr.
  - `INSTRUCTIONS` and each tool description stay at most 2048 characters. `INSTRUCTIONS` is 1996 now, so there are 52 characters of headroom.
  - Keep 19 tools (README:160).
- **`link_install.py` and `sdcall.py`:** keep them running on Apple's `python3` (3.9) and the Windows `py` launcher.
- **sdkit coupling:** never change the signature or return shape of a `commands.py` helper that `sdkit.py` uses unless `sdkit.py` is updated in the same commit.
- **Installer files.** Expected `git ls-files --eol` output:
  - `.bat`/`.ps1`: `i/lf w/crlf attr/text eol=crlf`. Pure ASCII, no BOM.
  - `.command`/`.sh`: `i/lf w/lf`, mode 100755.
  - The `.command` files stay bash 3.2- and dash-compatible; `setup_env.sh` stays bash 3.2-compatible.
- **Leave alone:**
  - Don't bump `VERSION` (`1.0.0`, `__init__.py:13`).
  - Don't edit `phase4_context.md`/`phase5_context.md` or anything in `$DEV`.
- **Style:** match the surrounding code (naming, comment density, plain-English error messages). User-facing text is plain and direct.

## Already known

Don't report these as new findings unless you find a concrete consequence the docs don't already cover.

- Windows isn't cloned or linked yet. The `.ps1` link-skip edits from `6864cf6` are untested. Nobody has verified that Designer loads a symlinked or junctioned plugin after a restart on Windows.
- `setup_env.sh` assumes `venv/bin/python`.
- The MCP client cuts a call at about 60 s while Designer keeps computing, and later calls queue. Never retry a timed-out mutation. Long jobs go through `sdcall.py`.
- On 12.4.1:
  - The direction of `SDConnection` is unreliable (`_far_end` handles it).
  - `compute()` only cooks nodes that feed an Output.
  - There's no API to open a graph in the editor.
  - `getDefaultParentSize()` is unset.
  - Library-declared enums can't be built with `sFromValueId`.
- `run_python` is arbitrary code by design. Any process running as my user that can read `session.json` can use it.
- `--raw` bypasses the schema, so a misspelled `save_as` overwrites the package (README.md:205).
- Ctrl+Z is unreliable after big `run_python` scripts (`sd_craft.md`).

## Review process

### Budget rules

- **Agents.** At most 20 in total; a typical run is about 15:
  - 6 area finders;
  - at most 6 skeptics (one per area, and one for the gap findings);
  - 1 completeness critic;
  - at most 3 gap finders;
  - 1 final diff review.

  No agents for fixing or for running checks: the main session does both. Give every agent a unique label (`find-PLG`, `skep-PLG`, `gap-2`, ...), and put the label in the prompt text too, because agents name their scratch folder after it.
- **Models**, set with `agent(..., {model, effort})`:
  - **Area finders and gap finders:** inherit the session model (omit `model`).
  - **Skeptics, the completeness critic and the final diff review:** `model: 'sonnet', effort: 'medium'`.
  - **The docs-drift checker:** `model: 'haiku', effort: 'low'`.
- **Prompts:**
  - Start every agent prompt with one short shared preamble (the identical prefix also helps prompt caching):
    - the Paths block, written out absolute;
    - the Live installs sentence;
    - the Ground rules;
    - Already known.
  - Then add only that agent's area: its files, the offline techniques it needs, and its group of leads from the appendix.
  - Pass the finding schema through the `schema` option only; don't also paste it into the prompt.
  - Never paste this whole file into an agent, or tell one to read it.
- **Reading:**
  - Each area finder reads its own files in full, once.
  - For anything outside its area, it greps and reads only the functions involved.
  - Skeptics read only the line ranges a finding cites, plus what those call. Never whole files, and at most two repros.
  - The main session never reads a whole code file. It uses `sed -n` on cited ranges, to settle a dispute or to make a fix.
- **Outputs:**
  - Agents return structured output only, with `evidence` of 6 lines or fewer and no file dumps.
  - Lows and nits carry only `title`, `area`, `locations`, `severity` and a one-line `failure_scenario`; the other fields can be empty.

### Steps

**0. Scout inline, without agents.**
- Check the baseline and note `HEAD`.
- Write `$SCRATCH/check.sh <tree>`. It runs, against `<tree>`:
  - `PY37` `compile()` on the plugin and `sdkit.py`;
  - `py_compile` under `SDPY` with `PYTHONPYCACHEPREFIX` in scratch;
  - `"$VPY" <tree>/mcp_server/sd_designer_mcp.py --check`;
  - `"$VPY" <tree>/tools/tool_call.py --source --list`;
  - `sh -n` and `dash -n` on the `.command` files, `bash -n` on `setup_env.sh`;
  - the three suites with `MATCHECK_DIR`/`PREVIEWS_DIR` set to `<tree>/skills/sd-material-research/scripts`;
  - `git -C <tree> ls-files --eol` and the file modes, compared with the expected values;
  - the baseline `find` on `<tree>`.
- The script prints one PASS/FAIL line per check, plus the last 5 lines of each failure, and nothing else. A `--quick` flag skips the three suites.
- Run it once in full on `$REPO` and confirm 300/233/91 and everything else green. If you install vermin in a scratch venv, add it to the script.

**1. Find and verify, in one workflow.**
- Run a `pipeline()` over the six areas, with two stages: finder, then skeptic. That makes six lanes at most, and each area goes straight to verification when its finder returns.
- The finders get the leads up front, so no separate leads stage is needed.
- Skeptics refer to findings by their index within their batch.
- Ids and duplicate merging happen after the pipeline (step 2).

| Id | Files | Leads | Also covers |
| --- | --- | --- | --- |
| PLG | `__init__.py`, `bridge.py`, `commands.py`. Check every `sd` call against `$APP/Resources/python/sd/api`. | Plugin | Undo groups on partial failure; error masking; value conversion; GUI-thread blocking; the session file; security of `run_python`, `save_package` and `render` paths. |
| SRV | `sd_designer_mcp.py`, `configure_claude.py`, `requirements.txt`, `tool_call.py`, `sdcall.py`. Compare the clients against `bridge.py`'s protocol. | Server | FastMCP 1.30 coercion; docstrings and `INSTRUCTIONS` vs plugin behaviour; error translation; timeouts; `render_preview` payload; Claude config edits. |
| INS | `install.*`, `uninstall.*`, `link_install.py`, `.gitattributes`, `.gitignore` | Installers | Data loss: deletions that could follow a link into the checkout (`sd-claude-bridge` vs `sd_claude_bridge` differ only by `-`/`_`); PowerShell 5.1 semantics; folder discovery; exit codes. |
| KIT | `sdkit.py`, `setup_env.sh`, plus the 27 `commands.py` helpers sdkit uses (read only those) | sdkit | sdkit's own `sd` calls; state and registry; touching nodes it didn't create; the `export_outputs` manifest as matcheck's input. |
| ANA | `matcheck.py`, `previews.py`, `calibrate.py`, with `checks.md` as the contract | Analysis | Bit depth, sRGB vs linear, mm scaling, wraparound, NaN, exit codes, config validation. Targeted repros only: the suites already ran. |
| DOC | The in-scope docs (Haiku) | Docs drift | Check each doc claim against the code with targeted greps. Don't read whole code files. |

**Finding schema:**
- `title`, `area`
- `locations`: a list of `file:line`, primary first.
- `severity`, judged by impact if the problem happens:
  - **critical:** loses user data (a `.sbs` file, the checkout, the Claude config), widens code execution beyond the documented model, or hangs or crashes Designer.
  - **high:** a silently wrong result, or a broken install on a supported platform.
  - **medium:** a misleading error, or a contract between components that breaks but has a workaround.
  - **low:** minor robustness, or a doc mismatch with little impact.
  - **nit:** style.
- `likelihood`: common, uncommon or rare.
- `failure_scenario`
- `evidence`
- `repro`: true when the evidence includes an offline command and its output.
- `platform`: mac, windows or both.
- `needs_live_designer`: true or false.
- `fix_sketch`.

**Verification stage** (in the same pipeline):
- **What gets a skeptic:** medium and above, without a repro.
  - One Sonnet skeptic per area takes all of that area's eligible findings.
  - If an area has more than 12, the skeptic takes the 12 most severe; the rest stay UNVERIFIED.
  - Repro'd findings, lows, nits and DOC findings get no skeptic.
- **The skeptic's job:** refute each finding by tracing the code and the `sd` API source, and looking for a guard elsewhere. It may also try a quick repro in its own scratch folder. "Unsure" means unsure that the path is reachable or that the trace is right. It does not mean the failure can't be run offline: for findings that need live Designer or Windows, judge the trace against the code and documented PowerShell/cmd behaviour.
- **What it returns, per finding:** refuted or not, a one-line reason, an adjusted severity and likelihood, and whether the finding repeats "Already known".
- **Decision:**
  - A finding survives unless the skeptic refutes it.
  - When the skeptic refutes a critical or high finding, the main session reads both arguments and decides, without another agent.
- **Labels:**
  - **CONFIRMED:** repro'd; or not refuted, with an airtight trace.
  - **PLAUSIBLE:** not refuted, but it needs live Designer or Windows to show, or the trace isn't airtight.
  - **UNVERIFIED:** got no skeptic (lows, nits, DOC findings, and the overflow above 12).
  - **Rejected:** refuted; or repeats "Already known" with no new consequence. List these under Rejected.

**2. Merge, after the pipeline.**
- In script code, assign ids by area plus a counter (`PLG-01`, ...). Never use `Math.random`/`Date.now`.
- The main session spots duplicates across areas from the compact list (ids, titles, locations) and merges them.

**3. Completeness: one pass.**
- One Sonnet critic gets the compact finding list (titles and locations only) and the in-scope list. It names up to 5 unexamined functions, files or failure modes, ranked.
- Run at most 3 gap finders, on the top items. One Sonnet skeptic verifies their medium+ findings that have no repro.
- List the remaining gaps under "Not covered".

## Report and fixes

**4. Set up the worktree:**
```
git -C "$REPO" worktree add "$WT" -b code-review-fixes main
```
- **Location:** outside `sduserplugins`, so Designer never scans it, and `$REPO` stays on `main`.
- **Permissions:** make sure this session can write to `$WT`. Request access to the directory (or `/add-dir` in the CLI), then test one write. If writes are refused, stop and ask me; never fall back to editing `$REPO`.
- **Resuming:** if `$WT` or the branch already exists, don't recreate, reset or force anything, and never run `git branch -D` or `git worktree remove`. Read `git -C "$WT" log --oneline main..` and the existing report, then continue from there.

**5. Write `$WT/code_review_report.md` and commit it.** Contents:
- At the top: a note that it contains security details, and should be removed or redacted before the branch is pushed anywhere public.
- A summary table.
- Findings ordered by severity, then likelihood. For each: id, locations, scenario, evidence, label, skeptic verdict, and fix status. Fix status starts as `pending`.
- **PLAUSIBLE:** for each, what a live Designer or Windows test would need to show.
- **Needs a decision:** options for each item; these aren't implemented.
- **Rejected:** one line each with the reason.
- **Not covered.**

Plain prose; no marketing tone.

**6. Fix, inline in the main session.**
- **What to fix:**
  - CONFIRMED findings.
  - PLAUSIBLE findings whose fix is local and can be checked statically; mark these "needs live test".
  - Lows and drift only when cheap: one file, about 20 changed lines or fewer, no contract change.
  - Before fixing an UNVERIFIED finding, read its cited lines and confirm it yourself.
- **What goes under "Needs a decision" instead:** changes to tool or command signatures, defaults, CLI flags, exit codes, file locations or formats, `run_python`/security gating, or install behaviour. Error-message wording doesn't count.
- **Commit groups.** Commit one group at a time, citing the finding ids. After each group:
  - Run `$SCRATCH/check.sh "$WT"` in full if the group touched `commands.py`, `sdkit.py` or the analysis scripts, and with `--quick` otherwise.
  - Check the `$REPO` baseline.

  Group by coupling:
  - `commands.py` + `sdkit.py` + `sd_craft.md`;
  - `bridge.py` + `__init__.py`;
  - `sd_designer_mcp.py` + `tool_call.py` + `configure_claude.py`;
  - installers + `link_install.py`;
  - `sdcall.py` + `setup_env.sh`;
  - analysis scripts + `checks.md`;
  - last: README.md, SKILL.md and `INSTRUCTIONS`.
- **Repro tests** live in `$SCRATCH/repro/<id>.py`. Quote the command and its output in the report; don't commit them.
- **If a fix changes a baseline suite result,** revert it and move it to "Needs a decision" with the before and after values. Never edit the suites or their goldens.
- **If a fix fails the checks twice,** revert it and record `not fixed: <reason>`.
- **Final pass:**
  - Write `git -C "$WT" diff main...code-review-fixes` and the Constraints section to files in `$SCRATCH/final/`.
  - One Sonnet agent reads those files and reviews the diff for regressions and cross-component breaks. Like every agent, it's read-only.
  - Don't paste the diff into its prompt or into your own context.
- **Finish:**
  - Set every fix status to one of: `fixed`, `fixed, needs live test`, `not fixed: <reason>`, `needs decision`, `not attempted`. Commit the report.
  - Don't push, merge or open a PR.
  - Tell me:
    - the branch and worktree path;
    - how many agents ran, and on which models;
    - which fixes need a live Designer or Windows test, with a short test plan for each;
    - which items need my decision.

## Appendix: leads from the mapping pass

Give each area finder only its own group. "Repro" means the failure was reproduced offline on 2026-10-03; treat the rest as questions. Line numbers are as of `6864cf6`. Files under `skills/` are in `skills/sd-material-research/`.

**Plugin (PLG)**
- `commands.py:135-142` builds the undo group (its `__exit__` always commits). A handler that raises midway leaves its partial edits as one undo step but reports failure. Examples:
  - `move_nodes` with a bad id mid-list (1205-1209);
  - `delete_nodes` with the same id twice (1218-1221);
  - `set_parameter` switches to Absolute (1181) before the set (1183) can raise.
- `bridge.py:172-197`:
  - the 16 MiB cap (186) only applies while the buffer has no newline;
  - buffering is quadratic: `c.buf += chunk` (185), and the split per line (191-192);
  - there's no per-poll budget across clients.
- `bridge.py:223-232`: a blocking `sendall` with a 30 s timeout on the GUI thread. SIGPIPE on macOS is unverified.
- `bridge.py:114-140`, `__init__.py:18-29`:
  - a second `initializeSDPlugin` doesn't stop the old server;
  - a second Designer instance overwrites `session.json`;
  - no client checks pid liveness.
- `commands.py:37`: only the exact string `'0'` disables `run_python`, and the value is read at import.
- `commands.py:1373-1400`: `run_python` swaps process-global stdout/stderr. Its `try` (1393) lets `KeyboardInterrupt`/`GeneratorExit` through. `bridge._handle` (213) still replies, so the cost is lost output and a committed undo group.
- `commands.py:1263-1279`: a relative `save_as` gets the error "folder does not exist: " (empty name) or resolves against Designer's working directory. Overwrites of other packages' files, or of Designer's `resources/packages` (user-writable on macOS), are silent.
- `commands.py:88-92`: `_try` hides `SDApiError` codes. In `set_parameter` (1158-1167), if `isReadOnly`/`isFunctionOnly`/`isConnectable` raise, the guards default to permissive.
- `commands.py:531-680`, value conversion:
  - banker's rounding (587, 599); bools accepted as numbers;
  - no colour range check; a bad hex string raises a raw `ValueError`;
  - an int enum value matches only an option id equal to `str(value)` (611-623);
  - unsupported: `double*`, `ColorRGB`, `bool2-4`.
- `commands.py:924-974`, `391-439`, `search_library`:
  - globs about 485 files on every call;
  - an XML `ParseError` caches a partial list (436-438);
  - `limit=0` becomes 25 and a negative limit slices from the end.
- `commands.py:1335-1370`, `render`:
  - `gid_ident_output.png` names in a shared temp folder collide across packages and clients, and nothing cleans them up;
  - a non-SBS graph gives a raw `AttributeError`;
  - `tex.save` keeps its default `outputColorSpace`.
- `commands.py:776-777`: `limit=0` becomes 400, a negative limit slices from the end, and `include_values` is unbounded.
- `commands.py:1225-1260`, `create_graph`:
  - no identifier validation;
  - `newUserPackage` runs before `sNew`, so a failure leaves an empty package;
  - no `_undo`;
  - the clash check covers only user packages.

**Server (SRV)**
- `sd_designer_mcp.py:81-122`:
  - sync tools run inline on mcp 1.30's event loop, blocking it for up to 600 s;
  - the timeout applies per `recv` (100-108), not as a total.
- `:109-113`: the timeout text says "try again", but `sd_craft.md:16` and `SKILL.md:128` say never retry a mutation.
- `:83-115`:
  - untranslated errors when `port` is missing or not an int, on a non-object JSON root, on `ConnectionResetError`, and on a malformed reply;
  - the response id isn't checked.
- Coercion (mcp's `func_metadata.py:153-191`):
  - `graph='null'` becomes None, which targets the current graph;
  - a `value` string holding a JSON array becomes a list;
  - pydantic drops misspelled keys silently.
- `:304-390`, `render_preview`:
  - payload up to about 56 MB;
  - HDR values are lost when Designer writes the PNG, not in Pillow;
  - the fallback without Pillow (325-327) is uncapped.
- `configure_claude.py:37-100`:
  - it replaces the whole entry (73), dropping the user's env vars;
  - the write isn't atomic (74-75);
  - only `ValueError` is caught;
  - `.bak` files are never pruned.
- No `destructiveHint`/`readOnlyHint` annotations on `delete_nodes`, `save_package` or `run_python`.
- `tool_call.py:225-234`: result-shape branches for mcp versions other than 1.30, while `requirements.txt` allows 1.6 and up.
- `sdcall.py:26-57`:
  - `json.loads(b'')` raises on an empty reply (54);
  - ignores `SD_CLAUDE_BRIDGE_SESSION`;
  - `open()` without an encoding (28, 30).

**Installers (INS)**
- `install.ps1:57-58,126-127`, `uninstall.ps1:26-41`, `link_install.py:85-93`: the reparse-point attribute is treated as "is a link", and OneDrive placeholders carry it too.
  - `os.rmdir` (`link_install.py:134`) on a populated folder raises an uncaught `OSError` at `link()` (177).
  - `uninstall.ps1`'s `Remove-LinksIn` calls `.Delete()` on placeholder children.
- README:216-221 runs the installer, which deletes real copies without a backup (`install.ps1:62-65`, `install.command:95-100`), before `link_install`. The Windows PC may hold edits that aren't in git.
- `link_install.py:131-149`: a dangling junction goes to `os.unlink`. Check the `mklink /J` quoting with paths that contain spaces.
- `install.ps1`:
  - mixes `-Path` and positional paths with `-LiteralPath`;
  - doesn't check `Copy-Item` (65, 131);
  - `install.bat`'s `pause` hides the exit code;
  - `Read-Host` (173) blocks callers that aren't interactive.
- `install.ps1:44-47,54` creates the Adobe folder when none exists. `link_install.py:66-71` then links every folder that exists, so a Steam user who installs before first launch gets the wrong folder.
- `link_install.py:35`: `SERVER_FILES` is hard-coded, while the installers copy `mcp_server/*`.
- The uninstallers:
  - never touch `~/.claude/skills` or call `--unlink`;
  - `uninstall.command:31` `[ -e ]` skips dangling links;
  - `rm -rf` runs right next to the repo folder.
- `link_install.py:57`, `tool_call.py:53`: an empty `LOCALAPPDATA` gives a relative path.
- `link_install.py` compares the folder on disk, not git's tracked set; `--status` always exits 0.

**sdkit (KIT)**
- `sdkit.py:120-133` (`_register`) runs after its callers `lib`/`atom`/`output` (257-296) have created the node, so a collision leaves an orphan. `replace=True` doesn't rewire the old node's consumers.
- `sdkit.py:34-99`: the global `S['reg']` is never reset, so `save_registry` can write a previous material's graphs.
- `sdkit.py:747-783`, `make_variant`:
  - sets `$randomseed` through `cmd_set_parameter`, which makes it Absolute, contradicting `set_seed`/`sd_craft.md:244`;
  - uses `sNew` directly, which skips the clash guard;
  - sets no 16-bit `$format`.
- `sdkit.py:673-715`, `export_outputs`:
  - the 8-bit warning is added after the manifest is written;
  - `'16' not in format` misflags 32F formats;
  - an output without an identifier raises `TypeError` mid-export;
  - `only=` overwrites the full manifest.
- `sdkit.py:825-912`: `prune_dead`/`layout` touch nodes that sdkit didn't create.
- `sdkit.py:472-539`:
  - `_value()` (534-539) treats a list spec as a constant;
  - `_expand` (474) only expands tuples;
  - `_fn_node` takes a bare string's first character as the op (497).
- `setup_env.sh`:
  - never installs OpenCV, although `SKILL.md:45`, `checks.md:71`, `matcheck.py:9-10` and `review_round.js:99` say it does;
  - exits 1 silently when `python3` is missing.

**Analysis (ANA)**
- `matcheck.py:578-589`: an RGB height PNG makes `height_mm` 0-1 instead of mm, with no warning (repro). This affects every check through `height_mm()`/`map_values(..., "mm")`, but not region `min_mm`/`max_mm` (520-521).
- `matcheck.py:1382-1400`, `1486-1508`, `1531`, `1571`:
  - a hard check that errors, is vacuous or returns NaN still exits 0 (repro);
  - a check without `type` and without a target key raises `KeyError` outside the `try` (1391, 1489): exit 1, no scorecard (repro).
- `matcheck.py:1540` + `previews.py:686-691`: scorecards land beside the configs, so the documented `previews.py checks/*.json` aborts with exit 2 (repro).
- `matcheck.py:432`, `1326-1340`: `normal_format: "dx"` is accepted, then fails as a green-convention mismatch (repro). `previews.py:470-471` rejects it.
- `matcheck.py:968-983`: `lowfreq` lets a later NaN overwrite a valid worst value.
- `matcheck.py:62-64`: the Pillow `'I'` mode heuristic.
- `matcheck.py:1059-1080`: `spacing` takes the argmax, not a local maximum.
- `matcheck.py:1545`: bare `NaN`/`Infinity` in the JSON, and `default=int(o)`.
- `previews.py:188-194`: `optional_gray` swallows every `ConfigError`, including a size mismatch.
- `calibrate.py:23-60`: no input validation.

**Docs drift (DOC)**
- README:70 and `INSTRUCTIONS` (`sd_designer_mcp.py:64`) say "each edit is one Ctrl+Z step", but `create_graph` has no undo group.
- README:21 says macOS is untested, which is stale.
- README:28-30 and 50-52 say "whichever of these exists", but the installers install into every folder that exists.
- README:227 says "puts a plain copy back", but only when nothing remains at the path (`link_install.py:198-200`).
- README never mentions `SD_CLAUDE_BRIDGE_SESSION` or `-SkipClaudeConfig`.
- `bridge.py:209`: the bad-token text says to restart the MCP server, which re-reads the file anyway.
- `sd_craft.md:25` says the first search takes about 60 s; the measured time is about 2-3 s.
- `assets/context_prompt_template.md:33-35` uses `sdkit.Session`, which doesn't exist.
- `assets/workflows/review_round.js:99` imports a `regions` symbol that matcheck doesn't have.
- `tool_call.py:19-20` claims a Mac shell keeps double quotes (README:203 is right); line 34 names only `install.ps1`.
