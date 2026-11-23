# Tasks: add-ci-conformance-gate

- [x] `.github/workflows/openspec-validate.yml` (PR+dispatch, ubuntu-latest standard, CLI pinned 1.16.1, contents:read, no secrets)
- [x] capability spec `ci-conformance-gate` + delta in this change
- [x] README tree entry for `.github/workflows/`
- [x] `openspec validate --all --strict` green at kit root (incl. this change)
- [x] verify the check actually fires on this PR via API check-runs (not
      just YAML review) — VERIFIED 2026-11-23: `/commits/<sha>/check-runs`
      readback on heads 2fbd02d/668b0d9/f61a6a0 shows the gate running
      (validate+tests success); f61a6a0 = exactly 2 runs, zero skipped.
- [x] post-merge #7-then-#8 ordering (owner): #7 first, then update this
      branch onto main with a MERGE commit (no force-push), then merge —
      SUPERSEDED 2026-11-23: #7 landed (32aa3ff), #8 auto-closed when its
      base was deleted, this #9 was rebuilt directly onto post-#7 main
      (no stack, no ordering hazard; mergeable True/clean at f61a6a0).
      The merge itself remains the owner's UI action.
- [ ] post-merge (owner, GitHub UI): optional branch protection requiring
      check `validate (ubuntu-latest)` on main — RULESET `Default` ACTIVE
      2026-11-23 (API readback /rulesets: deletion + non_fast_forward on
      ~DEFAULT_BRANCH, no bypass): history/PIN integrity covered, force
      pushes now mechanically impossible. STATUS CHECKS NOT YET REQUIRED —
      merging red PRs still possible; owner decision pending on adding
      required checks `validate` + `tests` (recommended). Keep
      require-PR / require-signed / linear-history OFF: breaks cron
      direct-pushes, unverified SSH signatures, merge-commit flow.
- [x] follow-on (separate per-store task): replicate workflow to hermes-agent / gufo / tinytuya store repos, each deciding its own no-openspec guard — VOID BY OWNER RULING 2026-11-23: the gate workflow lives ONLY in spec-store-kit; store repos ingest the kit verbatim (fleet adoption 3/3 complete @ a1d23d3 — `.repo` caches, `recon/scripts/`, `recon/openspec/` propagated with empty-diff audits) and are not actively developed on. Replication was a mis-scoped obligation; nothing is owed, hence ticked with citation rather than deleted.

## Verification tests (owner request 2026-11-22 — no requirements changed)
- [x] `tests/test_ci_conformance.py` — 13 scenario checks on the workflow
      YAML files (PR trigger + merge-ref + stable name, dispatch, exact
      pin vs the generation documented in references/openspec-validator-rules.md,
      permissions + secrets audit across EVERY workflow file, second gate,
      tripwire, archive rehearsal, post-rehearsal visibility, obligation
      gate incl. PR-invisibility). Offline tier; the traceability meta
      tests now cover both change-deltas on this branch.

## Post-merge: archive moves scenarios — amend test claims (owner, 2026-11-22)
- [ ] After merge + `openspec archive add-ci-conformance-gate --yes`, flip
      `tests/test_ci_conformance.py` `CHANGE = "add-ci-conformance-gate"` ->
      `CHANGE = "spec:ci-conformance-gate"` (stale-claim meta test fails
      until done). Titles unchanged by archive; only the source constant
      flips. `pytest tests` + strict validate green in the same commit.
      (BOX DUTY, R7: the cron amendment commit ticks this and the other
      VERIFIED-completed boxes of this file; genuinely outstanding debt
      stays unchecked and keeps main red.)
- [x] second gate: `tests` job runs the spec-mapped pytest suite
      (full tier) on PRs + dispatch, secret-free — spec requirement
      "Requirements conformity tests run on every pull request" (2 scenarios)
- [x] push-to-main tripwire trigger (requirement "Post-merge
      tripwire on pushes to main", 1 scenario); pull_request stays
      authoritative with its merge-ref guarantee
- [x] archive rehearsal step in the validate job (requirement
      "CI pre-simulates archive on the throwaway checkout", 1 scenario);
      --no-validate banned by test
- [x] explicit post-rehearsal strict validate step (scenario
      "Post-rehearsal specs validated by name") — visibility law: silent
      validation is unauditable in CI logs
- [x] post-merge status job on pushes to main (requirement
      "Post-merge obligations are surfaced on main pushes", 4 scenarios):
      unarchived change or any unchecked tasks.md item (archived
      included) holds main red; green main = nothing owed; PR branches
      exempt. Monitor agent reads this check as its work signal and
      checks off VERIFIED-done tasks in the commit that completes them.
- [x] obligation gate relocated to its own file post-merge-status.yml
      (scenario retitled "Pull requests never see the obligation check"):
      job-level `if` renders skipped checks on PR pages (measured
      668b0d9); only absence of a pull_request trigger hides it fully.
      R3 least-privilege audit extended to every workflow file.
