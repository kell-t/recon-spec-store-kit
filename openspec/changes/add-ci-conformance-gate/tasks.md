# Tasks: add-ci-conformance-gate

- [x] `.github/workflows/openspec-validate.yml` (PR+dispatch, ubuntu-latest standard, CLI pinned 1.16.1, contents:read, no secrets)
- [x] capability spec `ci-conformance-gate` + delta in this change
- [x] README tree entry for `.github/workflows/`
- [x] `openspec validate --all --strict` green at kit root (incl. this change)
- [ ] verify the check actually fires on this PR via API check-runs (not just YAML review)
- [ ] post-merge #7-then-#8 ordering (owner): #7 first, then update this branch onto main with a MERGE commit (no force-push), then merge
- [ ] post-merge (owner, GitHub UI): optional branch protection requiring check `validate (ubuntu-latest)` on main
- [ ] follow-on (separate per-store task): replicate workflow to hermes-agent / gufo / tinytuya store repos, each deciding its own no-openspec guard

## Verification tests (owner request 2026-11-22 — no requirements changed)
- [x] `tests/test_ci_conformance.py` — 4 scenario checks on the workflow
      YAML (PR trigger + merge-ref + stable name, dispatch, exact pin vs the
      generation documented in references/openspec-validator-rules.md,
      permissions + secrets audit). Offline tier; the traceability meta tests
      now cover both change-deltas on this branch.

## Post-merge: archive moves scenarios — amend test claims (owner, 2026-11-22)
- [ ] After merge + `openspec archive add-ci-conformance-gate --yes`, flip
      `tests/test_ci_conformance.py` `CHANGE = "add-ci-conformance-gate"` ->
      `CHANGE = "spec:ci-conformance-gate"` (stale-claim meta test fails
      until done). Titles unchanged by archive; only the source constant
      flips. `pytest tests` + strict validate green in the same commit.
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
