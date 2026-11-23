# Change: add-ci-conformance-gate

## Why
The strict validator is a deterministic markdown rule engine (parser +
rule table; no LLM). Any PR that lands malformed spec structure — missing
scenarios, stray Requirement headers, >500-char bodies, missing SHALL —
should be refused mechanically before review, at zero cost: GitHub-hosted
standard runners are free for public repositories. Beyond form, main's
health must be machine-readable: a green main commit should MEAN nothing
is owed at that commit (archiving and post-archive amendments included),
so the monitor agent reads a check status instead of inferring from
layouts.

## What Changes
- `.github/workflows/openspec-validate.yml` — on PRs to main (explicit
  types `opened/synchronize/reopened`), pushes to main (post-merge
  tripwire), and dispatch: `openspec validate --all --strict` on pinned
  CLI 1.16.1 (`ubuntu-latest`, `contents: read`, no secrets); an archive
  rehearsal (`openspec archive <id> --yes` per open change on the
  ephemeral checkout — unmergeable deltas fail before merge;
  `--no-validate` banned); a final explicit post-rehearsal strict
  validate (archive's own validation is silent; owner visibility
  ruling); and a second gate, the `tests` job, running the spec-mapped
  pytest conformity suite (full tier).
- `.github/workflows/post-merge-status.yml` — obligation gate in its own
  push-only file (workflow-level triggers are the only way a PR checks
  page stays free of skipped checks): main is red while a change dir
  sits outside `archive/` or any `tasks.md` (archived included) carries
  unchecked items; green main = nothing owed.
- Capability `ci-conformance-gate` spec delta: 7 requirements /
  13 scenarios; `tests/test_ci_conformance.py` audits all of them
  (traceability-registered; least-privilege/secret audit spans every
  workflow file).

## Impact
- Affected specs: `ci-conformance-gate` (new).
- Repo settings mirror (owner, DONE): ruleset `Default` ACTIVE on main —
  deletion + non_fast_forward + required checks `validate`/`tests`
  strictly, no bypass. Job-id renames must update the ruleset in the
  same change, or merges block on a check that never arrives.
- Out of scope: the authoritative archive stays an agent-side act —
  originally because CI authorship failed the signed-kell-t law, now by
  chain choice after the owner's 2026-11-23 relaxation (a GitHub-verified
  `github-actions[bot]` commit is lawful — the invariant is the Verified
  stamp; unsigned-PAT commits remain unlawful). Archive stays agent-side
  because store propagation, ledger lines, and verified box ticks need
  pod-local state; a CI-author bot is a permitted future option.
- Placement ruling (owner, 2026-11-23): gate workflows live ONLY in this
  kit; store repos ingest the kit verbatim and are not developed on —
  per-store workflow replication is VOID, not pending.
- Ordering: superseded history — originally stacked on #7; after #7
  merged, stacked PR #8 closed with its base branch deletion and this
  PR #9 was rebuilt directly onto post-#7 main.
