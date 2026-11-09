# Spec Reconstruction Playbook — Deconstructing Any Git Repo with Agent Fleets

A reusable, evidence-grounded process for reconstructing a specification
(OpenSpec-flavored or any requirement format) from a git repository's code,
history, and documentation. Designed for autonomous or semi-autonomous agent
fleets. Validated on two public repos of very different shapes: a ~60k-commit
monorepo with PR-ref'd squash-merge history, and a ~1k-commit library with a
ref-free history and a rich in-tree doc corpus.

Copy this file into each store's `recon/`. It is repo-agnostic law: amend it
only with lessons that would help a fleet deconstructing *any* repo.

Core principle: **history is evidence, the current tree at the pin is ground
truth.** Never replay history to build the spec; reconstruct at a checkpoint,
verified against the pin. The spec models **merged** reality at the pin.

## Document family (three layers)

| File | Mutability | Repo-specific? | Holds |
|---|---|---|---|
| `PLAYBOOK.md` (this file) | stable law, grows only repo-agnostic lessons | No | Method, phases, verification rules, reliability lessons |
| `repo_config.yaml` | amended at scope changes | **Yes** | Repo pin info, scope decision, clustering keyword map, normative-doc locations, fleet knobs |
| `RECON_LEDGER.md` | rewritten every pass | **Yes** | Current baseline, coverage table, open/closed gap register, drift register, pass history, NEXT-PASS mission |
| `DRAFT_TEMPLATE.md` | stable law | No | The drafting rules each drafting agent must read first |
| `SCENARIO_PASS_TEMPLATE.md` | stable law | No | Scenario-grounding pass rules |
| `specs_draft/` + `evidence/` | growing artifacts | Yes | Produced drafts and raw mined data |

Boot order for any agent: PLAYBOOK → repo_config → LEDGER. Boundary test for
any new fact: "would this help a fleet deconstructing a different repo?" —
yes → PLAYBOOK, no → config or ledger. A workspace with no prior LEDGER means
first pass: create it from the Phase-0 scope decision.

---

## Phase 0 — Scope and pin

1. Clone (blobless: `git clone --filter=blob:none`) at the default branch or
   chosen tag. Record and freeze the baseline:
   `BASELINE=$(git rev-parse HEAD)` — store in `evidence/baseline.txt` with
   date and branch.
2. Survey the repo shape: top-level dirs, language mix, docs locations,
   tags/release history, CONTRIBUTING/AGENTS/README files, LICENSE header.
3. Count the history: total commits, merge vs squash ratio, whether commit
   subjects carry PR refs (`(#NNNN)$` — count programmatically; this selects
   your evidence model, see the Ref-free lesson below).
4. Check API budget (e.g. `curl api.github.com/rate_limit`) before any
   GitHub-API phase; prefer the clone + `git log` over API calls.
5. **Scope decision (mandatory, explicit):** full-project reconstruction is
   almost always wrong. Pick the capability surface you actually need. Record
   the chosen scope and the deferred buckets (with commit counts). Where the
   repo has its own area-routing docs, they are the decisive basis for
   capability attribution; record each boundary call with its basis in
   repo_config.

## Phase 1 — Mine evidence (cheap, mechanical)

Sources, in priority order:
1. **PR-landed commits (PR-ref-rich repos):**
   `git log --no-merges --format=%H|%ad|%s --date=short`, filter `(#NNNN)$`.
   Parse conventional-commit type(scope). Save JSON
   `{sha, date, pr, subject, type, scope}`.
2. **Full log (ref-free repos):** same extraction without the filter;
   history is intent-provenance only — cite `[commit <12-hex>]`, evidence
   comes from docs + tests + pin code.
3. **Release notes / changelogs:** per-version curated intent statements —
   the highest-signal evidence in the repo. GitHub Releases API →
   `releases.json`, or split an in-tree release doc into per-version files.
4. **Topic docs:** design docs, dev notes, architecture docs, per-area agent
   guides. Read directory listings first; read fully the scope-matching ones.
5. **Tests at the pin:** inventory test classes/methods with line numbers.
6. **Issue tracker (optional):** carries intent language code never shows.
   Sample, don't dump.

Store everything under `evidence/`. This phase is scripted, not LLM work.

## Phase 2 — Cluster by capability

First-pass keyword/heuristic clustering into capability buckets (regex per
bucket; cap each commit at ~2 buckets) → `evidence/clusters.json`, then
`evidence/bundle_<cap>.txt` — bounded (≤60 items), newest first, with
pointers to release notes and topic docs.

Treat clusters as a **starting partition, not truth**: expect ~50%
false-positive rates in some buckets; drafters reject misfiled items.
Bare-subject regexes over-match adjacent surfaces — tighten per observed
false positives; prefer conventional-commit scope matching when available.

## Phase 3 — Draft (LLM fleet, one capability per agent)

Rules, enforced by a shared DRAFT_TEMPLATE every drafting agent reads first:

- **Evidence-first:** every requirement cites at least one real PR number,
  commit, or doc file. No citation → the requirement does not exist.
- **Verification tiers, assigned honestly:**
  - `VERIFIED` — the agent OPENED the implementing code at the pin and saw
    it. Requires an anchor (`file` or `file:line`).
  - `INFERRED` — grounded in docs/PR text, code not confirmed.
  - `UNVERIFIED` — recorded in the gaps section only, never as spec.
- **Blanks over guesses.** Never invent PR numbers, paths, or line numbers.
  Anchor not found → write "anchor not located".
- **WHAT/WHY, not HOW** — except where implementation IS the contract
  (protocols, file formats, wire limits).
- **RFC-2119 verbs:** SHALL / SHOULD / MAY.
- **Doc-vs-code disagreement:** record the doc claim as the requirement and
  log the disagreement in a drift register.
- **Density target:** 8–20 requirements per capability. Seed, not finish.

Budget rule: drafters read bundle + doc pointers first; whole-repo reads only
for anchor verification. Concurrency: waves of a few agents, not swarms;
each child owns a DISJOINT set of draft files.

## Phase 4 — Verify and tally (scripted, adversarial to self-reports)

Never trust drafting agents' self-reported counts. Programmatically:
- Count requirement headers and status grades per file; reconcile against
  reports; investigate discrepancies.
- Spot-check anchors: cited files exist at pin; cited lines contain what is
  claimed; `VERIFIED` with file-only anchor is status debt.
- Verify GitHub-number attribution independently: match by **message text
  and diff**, not number alone; verify each number's kind via
  `GET /repos/<org>/<repo>/issues/NNNN` (issue/PR share one numbering;
  `/pulls/N` 404s for issues). Keep a store-local verified-numbers allowlist
  the audit gate consults.
- Resolve every sha cite mechanically: `git cat-file -e <sha>^{commit}` at
  the pin — prose review misses two-char transpositions.

## Phase 5 — Gap register (a first-class deliverable)

Every pass ships an explicit gap register alongside requirements:
- Behaviors seen in evidence but not groundable at the pin.
- Constants claimed by docs but not found in code.
- Undocumented contracts (ordering, fallback semantics, gating conditions).
- Deferred scope decisions and capability-ownership boundaries.
- Stale/rebased evidence: bundle recency holes — re-extract, don't reuse.

Rule: "unknown" must never silently become "absent", and never "assumed".

## Phase 6 — Output package

1. Ledger (baseline pin, method summary, coverage table, cross-cutting
   findings, gap register, NEXT-PASS mission) — see RECON_LEDGER template.
2. `specs_draft/<capability>.md` — one file per capability, template-shaped.
3. `evidence/` — raw mined data so the next fleet re-derives everything.
4. Converted specs: drafts → validator-conformant specs via the converter;
   keep strict validation green at every commit; fix drafts, never the
   converted output.
5. Exclude the clone from archives; state explicitly whether the package
   contains sensitive data (it should not).
6. License tiers: process layer MIT, spec layer source-repo license (see the
   kit's LICENSE-TIERING).

## Recurring maintenance loop (after the initial pass)

```
re-pin baseline → diff vs previous baseline → extract new PR-landed commits
→ draft deltas for touched capabilities → verify anchors at NEW baseline
→ archive deltas into the living spec (only when code matches)
```

Archive precondition, always both: (a) upstream code at the fresh baseline
matches the delta, and (b) anchor verification passed at that baseline. A
stale-baseline archive poisons the source of truth. **Unmerged-PR
differences are not drift.**

## Reliability lessons encoded (worth their weight)

1. **PR numbers are hypotheses.** Squash/rebase history produces duplicate
   and misattributed refs. Match by text and diff; API-verify kind (issue vs
   pull) before judging a cite.
2. **Removal-check law:** evidence that a PR landed is NOT evidence it still
   exists at the pin. Mechanisms get deleted later. At every pin
   re-verification, `git log -S<symbol>` the anchor area for deletion commits
   before a PR-cited requirement survives. Anchor-verify waves are exactly
   where dead requirements surface. Rewrite onto the surviving successor
   mechanism or delete + log drift; never park dead mechanisms as INFERRED.
3. **A closed-unmerged PR can still have its behavior on main** (salvage
   cherry-pick is a real repo process): verify presence in code at the pin,
   note "closed unmerged; behavior via salvage", don't delete the requirement.
4. **Docs drift; code rots docs quietly.** Keep a drift register every pass;
   doc staleness is itself a reportable upstream finding.
5. **Bundle windows have tails.** Anything cut from "recent history" misses
   the newest commits. `git log --since=` filters COMMITTER date while `%ad`
   prints AUTHOR date — rebased histories mix them; filter author-date in
   script, not with `--since`. Re-extract for fresh windows; append tail
   sections idempotently.
6. **Self-reports are hypotheses.** All fleet metrics get scripted counting
   before publication; children's "all checks pass" is a claim to verify,
   including their claimed file inventory (`git status` must show only
   assigned files).
7. **Reverse-engineering captures behavior, not intent.** Where code and
   docs disagree, the *intent* belongs in the spec and the disagreement gets
   a drift entry.
8. **Full-project reconstruction is a treadmill; selective, checkpointed
   reconstruction converges.** Deep where you work, absent elsewhere.
9. **Gaps are deliverables** — a precise unknown beats a confident guess.
10. **Evidence-graded specs drift from spec-tool formats; conversion passes
    are the bridge.** Reconstruction drafts produce verified invariants
    (SHALL + anchor); spec tools demand scenario blocks (WHEN/THEN). Don't
    fabricate scenarios during reconstruction — run a separate, strictly
    grounded scenario-ification pass (trigger AND outcome in human-written
    sources); requirements without documented triggers stay property-style
    and carry a labeled derived-scenario as tracked **scenario debt**.
11. **Ref-free repos still have a number space.** Near-zero commit refs does
    not mean the tracker is dead: child drafts may legitimately cite real
    issue/PR numbers. Judge each via the issues API, allowlist it in the
    store, and have the gate reject only numbers absent from the allowlist.
12. **Grounding evidence must exist at the pin.** Newer unmerged upstream
    tests/docs are inadmissible; briefs must pin the evidence window or
    drafters will ground on post-pin material.
13. **Reproducibility survives engine swaps.** Re-run verification, not
    authorship.

## License / legality note

Specs derived from a repo's docs/code inherit that repo's encumbrances.
Check the license before publishing a reconstruction (copy the source
LICENSE into the spec tier at every pin move); note any clean-room
obligations the project itself observes. Treat a copyleft store's specs as
copyleft-derived: nothing crosses store boundaries without explicit
per-instance owner approval.
