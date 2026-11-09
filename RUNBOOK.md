# RUNBOOK — reconstructing a repo's spec store, pass by pass

Operator guide. The methodology law lives in `templates/PLAYBOOK.md`; this
file is the *procedure* — what to run, in what order, with what green lights.
References at the end point to the deep-dive docs.

Conventions used below:
- `<store>` = the store root (`<repo>-recon-spec-store/` or a folder inside a
  cluster container). `<slug>` = the OpenSpec store id (the repo slug).
- "Gate green" = `python3 recon/scripts/gate.py` exits 0 **and**
  `openspec validate --all --strict --store <slug>` reports 0 failures
  (post-conversion passes only).
- Boot order for every agent session: `recon/PLAYBOOK.md` → `recon/repo_config.yaml`
  → `recon/RECON_LEDGER.md`.

---

## 0. Prerequisites (once per machine)

- `openspec` CLI (validated against v1.16.1) on PATH. If installed via npm
  global prefix, **prepend/append** the bin dir to PATH — never assign PATH,
  which kills the `node` shebang lookup.
- Git identity configured (`git config --global user.name/email`) — the
  `openspec store` commands need it.
- GitHub API token for number verification (read-only is enough). Never
  print it. Check `GET /rate_limit` before any API-heavy phase; prefer
  `git log` over API calls.
- Store registration is **machine-local** (the CLI registry is not in git).
  On a fresh host or after moving folders:
  `openspec store register <path> --id <slug> --yes` before any `--store` command.

## 1. Bootstrap a store (new repo)

1. `mkdir -p <store>/{openspec/{specs,changes/archive},recon/{evidence,scripts},specs_draft,repo}`
   (`openspec store setup` refuses non-empty dirs; build by hand instead.)
2. Write `<store>/.openspec-store/store.yaml`: `version: 1`, `id: <slug>`.
   Also create `<store>/openspec/config.yaml` (a minimal `context:` block is
   enough) — `openspec store register` refuses a root missing it.
3. `git init` in `<store>`; add remote if the store gets a GitHub repo.
4. **License tiering** (see `LICENSE-TIERING.md`):
   - copy the kit's MIT text to `<store>/recon/LICENSE`;
   - after cloning the source (Phase 2), copy the source repo's `LICENSE`
     to `<store>/openspec/LICENSE`.
5. Copy templates into the store: `PLAYBOOK.md`, `DRAFT_TEMPLATE.md`,
   `SCENARIO_PASS_TEMPLATE.md` → `recon/`; `RECON_LEDGER.md` → `recon/`;
   `repo_config.yaml` → `recon/`; `store-WORKFLOW.md` → store root.
6. Copy the tool kit: `tools/draft_to_spec.py` → `<store>/tools/` (or keep a
   shared cluster copy); everything in `tools/scripts/` →
   `<store>/recon/scripts/`; copy `store_config.example.yaml` →
   `recon/scripts/store_config.yaml` and fill it.
7. `openspec store register <store> --id <slug> --yes`.
8. If you keep multiple stores, add a registry row (id, path, source repo,
   **license read from the source's LICENSE file header — never from
   memory**) to the cluster `WORKFLOW.md`.

## 2. Phase 0 — scope and pin

1. Blobless clone at the default branch (or at the chosen release tag):
   `git clone --filter=blob:none https://github.com/<org>/<repo> <store>/repo`.
2. Freeze the baseline: `BASELINE=$(git -C repo rev-parse HEAD)`; write
   `recon/evidence/baseline.txt` with SHA + date + branch/tag. Also record
   it in `repo_config.yaml` (`repo.pin_*`) and the ledger's PINS section.
3. Copy the source LICENSE → `<store>/openspec/LICENSE`.
4. Survey the shape: top-level dirs, language mix, doc locations
   (README/CONTRIBUTING/AGENTS/per-area guides), tags, `LICENSE` header.
5. Count the history: total commits, merge vs squash ratio, and **the single
   most consequential number** — count of commit subjects ending in
   `(#NNNN)`:
   `git log --no-merges --format=%s | grep -cE '\(#[0-9]+\)$'`
   This decides your evidence model (see `references/evidence-models.md`):
   - **PR-ref-rich** (refs common): history IS an index; mine with the ref
     filter, cite PR numbers.
   - **Ref-free** (refs ≈ 0): history is intent-provenance only; mine the
     FULL log into `commits.json`, cite `[commit <12-hex>]`, and let
     docs + tests + pin code carry evidence. Note: ref-free ≠ no GitHub
     number space — the tracker may still be live; verify numbers per-cite.
6. **Scope decision (mandatory, explicit, written into repo_config.yaml):**
   full-project reconstruction of a large repo is a non-converging treadmill.
   Pick the capability surface actually needed (usually 5–12 capabilities);
   list deferred buckets with their commit counts. If the repo has its own
   routing/area docs (e.g. per-area AGENTS.md), use them as the decisive
   basis for capability attribution; record each boundary call as an
   `ownership_decisions` entry (question / decision / basis).

Green light: `repo_config.yaml` filled (repo, scope, clustering regex map,
normative docs, fleet knobs); ledger Phase-0 section written.

## 3. Phase 1 — mine evidence (scripted, not LLM work)

Run from `<store>`:
- PR-ref-rich: `python3 recon/scripts/mine_evidence.py` →
  `evidence/pr_commits.json`, `evidence/pr_index.json`, scope histogram.
- Ref-free: same script with `pr_ref_mode: none` in `store_config.yaml` →
  `evidence/commits.json` (full log).
- Normative docs: the script copies the configured doc list to
  `evidence/docs/` (path-flattened names).
- Release notes: either GitHub Releases API → `evidence/releases.json`
  (tag/name/date/body), or an in-tree release doc →
  `python3 recon/scripts/mine_relnotes.py` splits it into per-version
  `evidence/relnote_<ver>.txt`. Having one of these two corpora is what makes
  quote-citation audits mechanical; if the repo has neither, plan scenario
  grounding on docs+tests only.
- Tests: the script writes `evidence/tests_inventory.txt` (test classes/methods
  with line numbers at the pin).

## 4. Phase 2 — cluster into capability bundles

`python3 recon/scripts/cluster.py` → `evidence/clusters.json` +
`evidence/bundle_<cap>.txt` (capped ≤60 items, newest first, plus the cap's
code/doc inventory for ref-free stores).

Rules: a commit lands in ≤2 buckets; clusters are a **starting partition,
not truth** — expect double-digit false-positive rates; drafters are expected
to reject misfiled items. Bare-subject regexes over-match (`\btools?\b`,
`\bcli\b` patterns pull in adjacent surfaces): tighten per lesson, and prefer
conventional-commit **scope** matching when the repo uses scopes.

## 5. Phase 3 — draft (pass 1), one capability per drafting agent

Fleet mechanics: `references/fleet-operations.md`. Non-negotiables:
- Every child gets a **disjoint** set of `specs_draft/<cap>.md` files, a
  read-only clone, and a self-contained brief (pin SHA, boot-read list,
  citation law, exact files, return-summary shape).
- Children draft from their bundle + doc pointers; whole-repo reads only for
  anchor verification. Bounded bundles in, anchor-only reads out.
- Drafting law = `recon/DRAFT_TEMPLATE.md`: every requirement cites real
  evidence; Status VERIFIED only with an opened-code anchor; blanks over
  guesses; density 8–20 reqs/capability.

After the wave (parent does ALL of this itself):
1. `git status` shows **only** the assigned draft files changed.
2. `python3 recon/scripts/tally.py` — requirement/status counts (never
   trust children's reported numbers).
3. `python3 recon/scripts/gate.py` — see Phase 6 for the check inventory;
   run it **before the first wave too**, over whatever exists, so the gate's
   false positives are triaged before children ever see it.

## 6. Phase 4 — anchor verification (pass 2)

Goal: mass-convert INFERRED → VERIFIED (or keep honest), catch dead
requirements, extend evidence to the pin's tail.

1. **Tail mining** (if the ref window stops before the pin):
   `python3 recon/scripts/mine_tail.py` — mines commits after the window
   WITHOUT the ref filter (author-date, not `--since`), scope-first
   clustering, appends an idempotent `# ==== TAIL APPEND` section to each
   bundle. Tail commits are cited `[commit <12-hex>]` — they are real at the
   pin.
2. **Verification waves**: children do NOT edit drafts. Each child returns a
   verdict JSON, one entry per requirement:

   ```
   {title, verdict: VERIFIED|INFERRED, anchors: ["file:line (hint)"],
    reason (required for INFERRED: where searched, what was found),
    files_opened: ["path:line"]}
   ```

   The parent applies Status/Anchor lines itself (block-bound edit rules in
   `references/fleet-operations.md`), then runs the gate.
3. **Removal-check law**: a requirement backed only by a historical PR may
   describe a mechanism *removed* between the PR and the pin. Evidence a PR
   landed is not evidence it still exists. For anything doubtful:
   `git log --oneline -S<symbol> -- <area>` for deletion commits; confirm
   absence in the worktree. Dead mechanism → rewrite onto the surviving
   successor or delete + log a Drift line. Never park dead mechanisms as
   INFERRED.
4. Phantom cites surface here: PR-labeled numbers that are issues, closed
   unmerged PRs whose behavior arrived by salvage, sha transpositions. Fix
   shapes are in `references/audit-gate-fp-taxonomy.md`; API-verify each
   GitHub number via `GET /repos/<org>/<repo>/issues/NNNN` (shared numbering;
   `/pulls/N` 404s for issues) and record it in
   `recon/evidence/verified_numbers.json` so the gate stays offline.

## 7. Phase 5 — scenario-ification (pass 3)

OpenSpec requires ≥1 `#### Scenario:` per requirement, but reconstruction
evidence rarely documents triggers. Do NOT fabricate scenarios from code.
Run a dedicated grounding pass (`recon/SCENARIO_PASS_TEMPLATE.md`):
- Tier A release notes > Tier B in-repo human docs > Tier C tests at the pin.
- A scenario enters only when BOTH trigger (WHEN) and outcome (THEN) appear
  in substance in cited human-written text, with a quote:
  `[relnote <ver>] "…"`, `doc: <path> § <section> "…"`,
  `test: <path>::Class::method`.
- NEVER derive a WHEN from implementation-code reading. AND clauses only for
  documented clauses.
- No groundable trigger → requirement stays a property-style invariant and
  the conversion pass injects a labeled **derived** scenario (tracked as
  scenario-debt in the ledger, never presented as evidence-backed).
- Evidence must EXIST AT THE PIN: newer unmerged tests/docs are inadmissible
  even when tempting; the child brief must pin the evidence window.
- Gate: scenario Source lines are checked by `audit_scenarios.py` (quote
  overlap ≥60%, test cite exact-grepped at pin).

## 8. Phase 6 — convert, validate, commit (green-light ritual)

1. `python3 tools/draft_to_spec.py specs_draft openspec/specs <prefix>`
   — in per-repo store layout use `''` for the prefix; then **strip the
   leading dash** the converter emits (`mv ./-<cap> ./<cap>`; on re-conversion
   convert into a fresh scratch dir and `mv -f` the spec.md over). A dash-dir
   left behind counts as an extra spec — "20 passed" when you expect 10 is
   NOT green. The converter prints `scenario-debt added=N` per cap; cross-check
   against the ledger.
2. `openspec validate --all --strict --store <slug>` → must be 0 failed.
   Conformance rules and the body-length pitfall:
   `references/openspec-validator-rules.md`. Never hand-edit
   `openspec/specs/**` — fix the draft, re-convert.
3. Gate green: `python3 recon/scripts/gate.py` (sequencer; see
   `tools/README.md`).
4. Update `recon/RECON_LEDGER.md`: CURRENT STATE numbers, coverage table,
   gap register changes, drift lines, NEXT-PASS mission.
5. Commit the store git (signed if your policy requires signing —
   **verify** with `git log --show-signature -1`; unsigned history cannot be
   fixed later without a rewrite). Push after green if a remote exists.
6. Report to whoever owns the work: paths + raw validate output, never
   summaries alone.

## 9. Maintenance loop (steady state)

```
re-pin baseline → diff vs previous pin → extract new PR-landed/ref-free
commits → draft deltas for touched capabilities → re-verify anchors at the
NEW pin (removal-check law applies to OLD requirements too) → archive deltas
into the living spec → re-run gate + validate → update ledger/PINS
```

- Archive precondition (both): upstream code at the fresh pin matches the
  delta, AND anchor verification passed at that pin.
- **Unmerged-PR differences are not drift.** Specs model merged reality at
  the pin. Review findings from other agents are advisory leads: verify each
  against the pin (open the code, check PR/commit state via API) before
  correcting; record the verification in the ledger.
- **Release branches** (if you mirror upstream releases in the store git):
  each full (non-prerelease) release R gets a branch named exactly the tag.
  Choose the base that minimizes spec reconciliation: off the previous
  release branch (walk forward) if the pin never advanced into main, else
  compute Δ(R_prev→R) and Δ(main-pin→R) and base on the smaller.
- Pin moves also trigger the license check in `LICENSE-TIERING.md`.

## 10. Multi-store triage and retirement

Triage ("which store needs work?") is **metadata-only** (license-firewall
safe: counts, SHAs, dates — never spec text):
1. open ledger debt: `grep -c '\[OPEN\]' recon/RECON_LEDGER.md`
2. last-worked date: `git log -1 --format=%ci`
3. drift: `GET /repos/<org>/<repo>/compare/<pin>...HEAD` → `total_commits`
4. rank: open debt first, then drift rate relative to last-worked date (a
   huge gap in a store validated today ranks below nothing — a fresh pass
   absorbs drift), then staleness.

Retire: check `git remote -v` FIRST (local-only store gits make `rm`
unrecoverable) → MOVE the store folder to a retirement hold, never delete
without explicit owner demand → update the cluster WORKFLOW registry (drop
row, add Retired entry with reason + resume rule "fresh recon; archived
drafts are non-current") → confirm no stale id in `openspec store list` →
re-validate the remaining stores → commit.

## References

- `references/openspec-validator-rules.md` — strict-mode format law
- `references/fleet-operations.md` — multi-agent drafting waves, child
  contracts, verdict-JSON application, fabrication audits
- `references/audit-gate-fp-taxonomy.md` — what the gate must tolerate vs
  what is real fabrication
- `references/evidence-models.md` — PR-ref vs ref-free strategies
- `references/pitfalls.md` — environment/tooling gotchas
- `tools/README.md` — the script kit inventory and run order
