# Fleet operations — multi-agent recon passes

For drafting/verification passes run with delegated agent fleets
(one child per capability, waves not swarms).

## Division of labour
- The parent (spec owner) does ALL scripted/mechanical work itself: evidence
  and tail mining, clustering, bundle rewrites, repo_config edits, ownership
  decisions, tallies, conversion, validation, git. Children get only work
  that needs reading code/docs and reasoning.
- Capability-ownership decisions are the parent's even when a child gathers
  the evidence. The source repo's own routing docs (per-area agent guides,
  CODEOWNERS-style maps) are the decisive attribution basis; record each
  decision + basis in `repo_config.yaml` `scope.ownership_decisions`
  (question / decision / basis), not in the draft files.
- Server concurrency caps are real: plan waves at the cap (e.g. 3), not
  swarms. In one-shot/headless sessions delegation may be disabled
  entirely (children limit 0) — run the wave inline and say so in the report.

## Child contracts (prevent collisions and fabrication)
- Children share the filesystem but not conversations. Each child owns a
  DISJOINT set of `specs_draft/<cap>.md` files. Children never write
  `openspec/`, never run git write commands, never touch `recon/` or another
  child's file. The clone is marked READ-ONLY (no checkout switching).
- If two kinds of edit target one file (anchor-verify vs scenario-grounding),
  put them in DIFFERENT waves — same-file writers never run concurrently.
- Anchor-VERIFY waves run better with children NOT editing drafts at all:
  each child writes only a verdict JSON — one entry per requirement
  `{title, verdict: VERIFIED|INFERRED (enum in the output schema), anchors
  ["file:line (hint)"], reason (required for INFERRED: where searched, what
  was found), files_opened ["path:line"]}`. The parent applies
  Status/Anchor lines itself, then runs the gate. Per-claim attribution
  beats merged child edits.
- The child brief must be fully self-contained: store root, pin SHA + tag,
  clone path, boot-read list (PLAYBOOK / DRAFT_TEMPLATE /
  SCENARIO_PASS_TEMPLATE / ledger section), exact files to edit, citation law
  (numbers only as they appear in the bundle, or from the verified-numbers
  allowlist in ref-free stores; tail commits as `[commit <12-hex>]`; docs as
  `doc: path § section`), the metadata-line format, and the required RETURN
  summary shape (per-requirement old→new grade, etc.).
- A store-wide gate scans ALL of `specs_draft/`, so during a CONCURRENT wave
  a child's run can flag a sibling's mid-write file (transient false
  failures). Tell children: fix only flags naming YOUR file, report the rest
  and stop. The parent's single gate run after the whole wave settles is the
  only authoritative result — never a child's in-wave exit code.
- Grounding briefs must state: any backticked file path in scenario/note
  PROSE (not just Anchor lines) must be repo-root-relative and exist at the
  pin — prose shorthand (`helper.py` for `src/pkg/helper.py`) is the
  systematic child false-positive shape.

## Post-wave parent ritual (every wave, no exceptions)
1. `git status` shows ONLY the assigned draft files changed.
2. Scripted tally; reconcile against children's reports; investigate gaps.
3. Source-citation audit before committing (children DO fabricate):
   - every `test:` path::Class::method segment greps EXACTLY in the test
     tree (a real file + real method with an invented CLASS segment is a
     known fabrication shape);
   - every `[relnote <tag>] "quote"` tag exists in the release corpus with
     ≥60% of the quote's non-stopword tokens in that body;
   - spot-check ~8 anchors by reading the exact line and confirming the
     CONTENT matches the claim, not just the line count.
   Fix fabrications yourself; never pass one through to a commit.
4. If any child did read→write round-trips, grep drafts for line-number
   prefix corruption (`^[0-9]+\|`).
5. Leaf children fabricate at the margin even when they report
   self-verification. Between wave completion and conversion, the scripted
   gate is MANDATORY and its output is pasted into the ledger.

## Applying children's verdict JSONs (parent-side block edits)
- Never bound a requirement block with a zero-width lookahead search
  (`re.search(r"(?=^### Requirement: ...")`): `m.end()==m.start()`, so spans
  computed from it collapse and replacements silently no-op while an
  insert-if-missing branch appends corrupting lines. Match the header line
  itself (start = m.start()); the block ends at the next `^#{2,3} ` after
  m.end() (`####` stays inside); apply multiple blocks in DESCENDING offset
  order; assert each substitution count (exactly one Status flip, exactly
  one Anchor rewrite); confirm totals with `grep -c "Status: VERIFIED"`
  before running the gate. Revert with `git checkout -- specs_draft/` and
  re-apply rather than patching a corrupted file.
- Normalize verdict payloads: children return either `{"results": [...]}` or
  a bare list.
- DEAD-at-pin requirements: a requirement backed only by a historical PR may
  describe a mechanism removed before the pin. Confirm the removal yourself
  (`git log -S <symbol>`, `git merge-base --is-ancestor <commit> HEAD`, file
  absent in worktree), then REWRITE onto the surviving successor mechanism or
  delete + log a Drift line ("the spec models merged reality at the pin").
  Never park dead mechanisms as INFERRED.

## Scenario-debt placement mechanics
The converter injects a derived scenario ONLY into requirement blocks that
contain none — adding a grounded scenario in the draft directly cuts
scenario-debt on the next conversion. Place it INSIDE the requirement block
(after metadata, before the next `###`).
- Tier-A without an API releases corpus: mine per-version
  `evidence/relnote_<ver>.txt` by splitting the in-tree release doc on its
  version headers (idempotent script) — this makes `[relnote <ver>] "quote"`
  cites mechanically overlap-verifiable, exactly like releases.json bodies.
- A store-wide pass template ported from another store silently carries the
  DONOR's evidence paths, tier examples, and cite dialect — re-anchor every
  example to THIS store's corpus, and keep the template's cite grammar
  character-identical to the audit script's regex. A template showing a
  different dialect than the gate enforces manufactures wave-wide systematic
  violations.

## Large evidence corpora
Big mined JSONs (release bodies can exceed a MB): shell one-liners that
reference them can trip command-lifecycle scan caps. Read them with
`json.load` in a script file, keep greps off their paths in terminal
commands.
