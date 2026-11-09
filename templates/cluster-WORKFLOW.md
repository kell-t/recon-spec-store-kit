# WORKFLOW.md — container policy for the spec store cluster

`<container-root>/` holds **independent OpenSpec stores, one per repository**:

```
<container>/
  WORKFLOW.md                  <- this file (cross-repo policy only)
  PRIORITY_LOG.md              <- one-line decisions from triage runs
  tools/draft_to_spec.py       <- shared converter (mechanical, repo-agnostic)
  github/<org>/<repo>/         <- ONE isolated OpenSpec store per repo
    .openspec-store/store.yaml (store id: <repo-slug>)
    openspec/
      config.yaml              <- repo context: pin, license, boundary
      specs/<capability>/spec.md
      changes/  +  archive/    <- repo-local, per policy 2
      LICENSE                  <- source repo's license (tier 2)
    recon/                     <- groundwork corpus (tier 1: MIT)
      LICENSE
      PLAYBOOK.md  DRAFT_TEMPLATE.md  SCENARIO_PASS_TEMPLATE.md
      RECON_LEDGER.md  repo_config.yaml  baseline.txt
      evidence/  scripts/
    WORKFLOW.md                <- repo-local pins/rules
    specs_draft/               <- drafting artifacts
    repo/                      <- read-only blobless clone at the pin
    .git/                      <- store-local history
```

## Binding policy
1. Specs are private working models. NEVER commit spec content into a public
   repository — sole exception: the target repo has its own `openspec/`
   folder; then its contributing guidelines govern.
2. A store's `openspec/changes/archive/` may contain ONLY that repo's own
   landed PRs and corrections for its incorrect/drifted specs. Implement work
   archives only on confirmed merge; spec-origin deltas archive at the spec
   owner's judgment; unmerged-PR differences are not drift. External review
   findings are advisory leads — verify against the pin before correcting;
   log the verification.
3. Every spec set is pinned to a baseline commit; validation and drift work
   start at the pin and run forward until it moves (recorded in the store's
   WORKFLOW.md + recon/RECON_LEDGER.md).
4. **Per-repo boundary (license firewall).** Stores are UNCONNECTED; do not
   break filesystem isolation in work:
   - Never import, paraphrase, or "adapt" spec content, design decisions,
     evidence, or code anchors from repo A into work for repo B without the
     owner's explicit approval per instance.
   - Generic technique knowledge is not a license problem; anything copied or
     derived from A's spec text, code, or evidence is.
   - Copyleft stores' specs are copyleft-derived — treat copies as infecting.
   - Session hygiene: when working repo B, operate inside its folder only;
     `--store <slug>` on every CLI command; do not open other stores.
   - Record cross-repo approvals below (single log for the container).
5. **License tiers per store:** `recon/` = MIT (kit license); `openspec/` =
   source repo's license (copied at pin; re-checked at every pin move).

## Repo registry
| Store id | Path | Source repo | License | Boundary |
|---|---|---|---|---|
| `<slug>` | `github/<org>/<repo>` | github.com/<org>/<repo> | <read from LICENSE> | isolated |

**Retired stores** (moved out of `github/` to the retirement hold; may be
revisited only as fresh recons — archived drafts are non-current):
- <slug> — RETIRED <date>, <reason>, hold path.

## Approvals (explicit owner cross-repo permissions)
- (none yet)

## Upstream-report dispositions
- <finding> — <filed | PARKED as Known-gaps only, owner ruling + date>.
  External posting always requires a fresh per-instance approval.

## Validation (per store — never a combined command, to preserve boundaries)
```
openspec validate --all --strict --store <slug>   # expect: <N> passed, 0 failed
```
Adding a repo: follow the kit RUNBOOK §1–2; register with
`openspec store register <path> --id <slug> --yes`; add a registry row with
the license READ from the source LICENSE.

## Triage (metadata-only; firewall-safe)
Rank stores to work on using counts/dates/SHAs only — never spec text:
open ledger debt (`grep -c '\[OPEN\]' recon/RECON_LEDGER.md`) first, then
drift rate (commits since pin relative to pin age and upstream activity,
judged against the last-worked date — a fresh clean pass absorbs drift),
then staleness. Append one decision line per run to PRIORITY_LOG.md.

## Retirement
Check `git remote -v` FIRST (local-only store gits make `rm` unrecoverable) →
MOVE the store dir to the retirement hold → drop the registry row, add a
Retired entry (reason, hold path, resume rule) → confirm `openspec store
list` has no stale id → re-validate remaining stores → commit the container.
