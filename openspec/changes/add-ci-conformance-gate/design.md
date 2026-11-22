# Design: add-ci-conformance-gate

## Decisions

1. **Deterministic CI validates structure, never content.** `openspec
   validate` is a parser + fixed rule table (same bytes in, same verdict
   out). A green check means the specs are WRITTEN SOUNDLY (headers,
   scenario presence, body length, RFC-2119 verb, delta format) — it is
   silent on whether a requirement is true of the code. Content truth
   remains the store gates' (anchor/cite auditors, also deterministic) and
   the spec agent's job. This note exists so no future reader mistakes a
   green check for a validated model.
2. **Archive stays agent-side.** `openspec archive` is a deterministic CLI
   step (move `changes/<id>/` → `changes/archive/`, apply deltas), but the
   actor may NOT be CI: a workflow committing to main is authored by
   `github-actions[bot]` or by an unsigned PAT identity — the latter renders
   **Unverified** on GitHub, and bot authorship violates the owner's
   signed-kell-t authorship law even when GitHub stamps its own bot
   signature. Copying the SSH signing key into Actions secrets would
   restore "Verified" but hands the key to every workflow run in the repo —
   rejected. Therefore: CI gates; the spec agent archives (daily pass,
   on-merge request, or a future webhook-wake), with signed kell-t
   authorship plus the store propagation and ledger lines only an agent
   may perform.
3. **Pinned validator version.** `@fission-ai/openspec@1.16.1` — the
   conformance rules in `references/openspec-validator-rules.md` are
   written and battle-tested against 1.16.x. An unpinned install lets
   runner-side upgrades silently change the rule table. Bumps go through a
   PR that updates the rules reference in the same change.
4. **Stacked PR, merged after #7.** The gate validates `openspec/`, which
   #7 introduces. Landing #8 after #7 means the first real PR sees a live,
   meaningful gate — no inert window, no guard step needed here (store-repo
   replication may add its own guard decision later).
5. **Economics.** Standard GitHub-hosted runner on a public repo: free, no
   minute accounting (private-repo quota/rates documented in GitHub
   billing; 2,000 min/mo Free plan, Linux 1x multiplier, $0.008/min
   overage — all N/A here). Larger runners are billed even on public
   repos and must not be used.

## Notes (not requirements)
- Merge latency for archive remains ≤1 daily pass unless the owner later
  wires the Hermes webhook route (planned separately; HMAC route bound to
  the spec profile).
- Branch protection (required check `validate (ubuntu-latest)`) is a
  GitHub-side owner action post-merge; the workflow works without it
  (advisory checks).

## Decision 12 — tests job: full tier in CI, public read only (owner request 2026-11-22)
The suite's @network tier exists because blobless lazy fetches need real
GitHub origins; CI runners have that by default. All clones are anonymous
HTTPS of public repos, so the job needs no secrets — the least-privilege
ceiling extends unchanged. Cost: one standard runner minute (~1-2 min wall
for the suite). Risk accepted: anonymous git rate limits per runner IP —
the suite clones the small kit repo a handful of times plus one bootstrap
(blobless) per run; failures here surface as honest red, retriable via
re-run, never auto-recover. setup-python pinned to @v6 (first node24
major; @v5 still declares node20 — verified in action.yml, same
annotation-avoidance law as checkout/setup-node v5).

## Decision 13 — pull_request stays, push-to-main added as tripwire (owner decision 2026-11-22)
Debated replacing pull_request with push-on-commit. Rejected: push checks
the branch head only, losing the "green PR => green merge" merge-ref
guarantee; open-PR branches would double-fire (PR number and ref are
separate concurrency groups); fork PRs would get no run at all; and
required-check configuration gets fragile. Adopted instead: keep
pull_request + workflow_dispatch authoritative, add push: branches [main]
so whatever lands (merge, admin override, direct commit) is recorded by
the same two jobs. No duplication: pre-merge branch pushes never touch
main. First natural firing is the merge of this very change.

## Decision 14 — archive rehearsal inside the CI gate (owner request 2026-11-22)
Measured on 1.16.1: `validate` previews archive collisions only as INFO
(green either way); `archive` merges deltas into living specs and VALIDATES
its produced specs by default (its `--no-validate` flag exists to opt out —
banned in this workflow), refuses unmergeable deltas atomically with exit 1
("Aborted. No files were changed."), and warns pre-apply on strict issues
like a too-brief Purpose. Therefore a third manual `validate` post-archive
is redundant; the missing CI coverage was the MERGE itself. The `validate`
job now rehearses `openspec archive <id> --yes` per open change on the
ephemeral runner checkout: unmergeable or unsound-result deltas fail the PR
before merge; the authoritative archive remains the agent-side post-merge
act (canonical flow untouched). Loop is alphabetical; stacked dependent
deltas (one MODIFIED against another unmerged delta's creation) could
sequence-red — accepted, honest, resolvable by merging order.
