# Research

Research turns "make a weathered X" into facts the graph can obey: dimensions, layers, processes, invariants and PBR
values, each with a source. Its output feeds the spec. The goal is better decisions, not a long bibliography.

## A. Material with a bundled sheet

Bundled sheets: `references/materials/*.md` (brick, asphalt, concrete, wood_planks, and any added later). The
research runs as background agents while you draft the spec. The spec gate waits for every one of them.

1. Read the sheet by section: §0-3 and §5-10 in full; from §4, only the cards of the processes the interview chose
   and any card they name; from Sources, only the entries behind step 2's hard-check numbers (`grep -n '^##'` the
   sheet, then Read by line range). Note its date and its stated scope.
2. Write `<tools>/research/gaps.md`:
   - **Gaps:** what this request needs that the sheet doesn't settle (a regional standard, a sub-type, a process the
     user emphasised, a colour family, a finish). One line each: `g<n>`, the question, the spec field it decides (a
     §3 dimension, a §5 process row, a §8 albedo, a §9 target...) and the stop rule: 2 searches without a primary
     source → `(est.)` with a reason. A question that decides no spec field is not a gap.
   - **Hard-check numbers:** every number a hard check in the planned spec will rest on (the sheet's §9 hard targets
     this request uses, the §9 rows you expect to make hard, and the §2, §4 and §7 values behind them), each with
     the sheet's source.
3. Run `"$PY" -m pip install -q "pypdf[crypto]"`, then spawn the agents in one message (Agent tool, `run_in_background`;
   WebSearch and WebFetch load with ToolSearch `select:WebSearch,WebFetch`):
   - 2-3 gap agents, grouped by area, at most 3 gaps each (merge related gaps if there are more than 9). Agent `k`
     writes `<tools>/research/gap_<k>.md`.
   - One re-verify agent for the hard-check numbers that have no row in a verified-number ledger in the sheet. No
     sheet has that ledger yet, so it takes every hard-check number the request relies on. It writes
     `<tools>/research/gap_rv.md`.

   Paste into each prompt: its lines of `gaps.md`, the sheet's path and the sections that bear on them, its output
   path, the `$PY` path, the agent rules below and the Source rules.
4. While they run, draft stage 3's `spec.md` and `checks/<variant>.json`. Leave each value that a gap or a hard-check
   number decides as a placeholder, `TBD:g<n>` or `TBD:rv`. A gap you find while drafting gets one more agent. So
   does a check you make hard while drafting: if its number is not on the step-2 list, add it to `gaps.md`, leave it
   `TBD:rv`, and re-verify it (another re-verify agent, or yourself under the agent rules) before the gate.
5. When every gap file has its `end:` line, paste each row's value and source into its placeholder. Where the
   re-verify agent changed a number, change it in the spec, the checks and (step 7) the sheet. A hard-check number it
   couldn't confirm goes into the spec as `(est.)` with its reason, into §11 and onto the gate summary's estimates.
   Its check stays hard only for a direction (`references/checks.md`, "Hard checks that can fail").
   `grep -rn 'TBD:' spec.md checks/` and `grep -niE 'check:\*\* *(none|n/?a|-|—)([^a-z_]|$)' spec.md` print nothing
   before the gate.
6. Write `<tools>/research/notes.md` in the agents' table: the sheet values you are using, with their sections as
   sources; the gap files by name (don't copy them); the decisions the user should own, from the sheet and the gap
   files (ask them in a short follow-up interview round).
7. If you or an agent found something wrong or missing in the sheet itself, fix the sheet. First grep the whole sheet
   for the value or term you change, and fix every place it appears, read or not. Grep Sources for the URL before you
   add a source, and number a new one after the last entry. Add a line to its header saying what changed and when.
   The sheet is shared knowledge, and the next material benefits.

**Agent rules** (paste them into every prompt):
- First command: `date -u +%FT%TZ`. Create your file with `start: <that time>` on line 1. Last edit: `end:` and the
  time from `date -u` on line 2.
- One row per fact: `| fact | value | unit | source | spec field |`. Source: the sheet's `[n]`; or the title, URL
  and page or section of what you read; or `(est.)` with a reason. Spec field: the gap id and the field, e.g.
  `g3 → §3 joint width`. Below the table: decisions the user should own, and anything wrong or missing in the sheet.
  Don't edit the sheet, the spec or the checks, and never call Designer.
- Stop rule, per gap: 2 searches without a primary source (a kind in the Source rules list) → `(est.)` with a
  reason, then the next gap. There is no time box: in the asphalt build, fetches after 15 min gave facts it used.
- Re-verify agent: open the sheet's cited source for each number and confirm its value, unit and context. If it
  doesn't hold, find a primary source that does. Mark a number you can't confirm `(est.)`, with what you found as the
  reason.
- PDFs: save them under `<tools>/research/src/` and extract the text once, with page markers. It prints the page and
  word count, or the error:

  ```
  "$PY" -c 'import sys,logging,pypdf; logging.disable(logging.WARNING); r=pypdf.PdfReader(sys.argv[1]); t="".join("=== page %d ===\n%s\n" % (i,p.extract_text() or "") for i,p in enumerate(r.pages,1)); open(sys.argv[2],"w",encoding="utf-8").write(t); print(len(r.pages),"pages,",len(t.split()),"words")' x.pdf x.txt 2>&1 | tail -n 3
  ```

  Then `grep -n -m 20` the text and `sed -n` around a hit. Print at most 40 lines per command. Never cat or Read a
  whole PDF or its text. A page that extracts to no text (a figure, a scanned table) can be Read with `pages`.
- If extraction errors, or gives far fewer than 50 words a page (a scan), the row's source is `unreadable PDF: <URL>,
  <reason>`. That is not "not in the source" and doesn't count toward the stop rule; main decides whether to fetch
  another copy or read it by page. A `PdfStreamError` usually means the download is an HTML page (`file x.pdf`).
- If you can't write your file, return it as your reply, and main saves it.

Without the Agent tool, run step 3's install, then close the gaps yourself, one at a time under the same rules, then
re-verify the list.

## B. Material without a sheet

Create one from `references/materials/_TEMPLATE.md`. It becomes a bundled sheet for next time.

**Team** (the same shape that produced the bundled sheets):
1. **Researcher(s).** For a broad material, split the work by area: (a) construction, layout, dimensions and layers;
   (b) aging and wear processes; (c) damage and deposition processes, plus PBR values. One researcher is enough for a
   narrow material. Each one writes its sections into the sheet file, or into section files you merge.
2. **Two auditors, working independently.**
   - *Physics:* an expert in the material who also knows procedural materials. Checks mechanisms, which layer each
     process acts on, what it reveals, the invariants and the common-mistakes table.
   - *Citations:* opens every cited source and confirms each number, its units and its context. Also checks PBR values
     against measured data.
3. **Reviser.** Verifies each audit finding before applying it, since auditors can be wrong too. Fills the gaps the
   auditors flagged, and makes sections 2, 4, 7 and 9 agree with each other.

**How to run it**
- If the user has opted into workflows (ultracode is on, or they asked for a workflow or multi-agent run), run
  `assets/workflows/research_sheet.js` with the Workflow tool (`scriptPath`). Its args are documented at the top of
  the file.
- Otherwise, spawn the same roles with the Agent tool: the researchers in one message, then the auditors in one
  message, then the reviser. The prompts in the workflow file work as Agent prompts too.
- If neither is available, do the three roles yourself in sequence, and do the audit as a separate, deliberately
  adversarial pass.

## Source rules

- Prefer, in order:
  1. standards and government manuals (ASTM, BS EN, FHWA/LTPP, USDA FPL Wood Handbook, ...)
  2. industry associations (BIA, Asphalt Institute, PCA/ACI, TRADA, ...)
  3. peer-reviewed papers
  4. conservation guidance (Historic England, NPS Preservation Briefs, ...)
  5. measured PBR datasets
- Use forums and blogs for visual examples only.
- Cite only what you have read. Every number carries `[n]` or `(est.)` with a reason.
- Watch out for these:
  - Solar reflectance (whole spectrum, often 0.05-0.40 for pavements) is not visible albedo.
  - Lab values are not field values.
  - "Typical" is not a range.
- Give ranges, and say which variant or region each applies to.

## Reference photos

- **User-supplied photos are the best reference.** Read them, then:
  - Measure proportions using a known size, e.g. brick height 65 mm → joint width.
  - Note which processes are visible, and where they sit relative to their drivers.
  - Note colour relationships: face vs revealed layer, wet vs dry.
  - Treat colours in photos as relative. White balance and exposure are unknown, so take absolute albedo from the PBR
    table.
- If web photos would help, give the user the search terms from the sheet's section 11, or ask before downloading
  anything.

## Done when

- Every process in the planned spec has a card: acts on, removes/adds, reveals, never, where, scale, progression.
- Every dimension and PBR value the spec will use has a source or an explicit estimate.
- The decisions that belong to the user are listed for them.
