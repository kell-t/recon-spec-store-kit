# Tasks: add-ci-conformance-gate

- [x] `.github/workflows/openspec-validate.yml` (PR+dispatch, ubuntu-latest standard, CLI pinned 1.16.1, contents:read, no secrets)
- [x] capability spec `ci-conformance-gate` + delta in this change
- [x] README tree entry for `.github/workflows/`
- [x] `openspec validate --all --strict` green at kit root (incl. this change)
- [ ] verify the check actually fires on this PR via API check-runs (not just YAML review)
- [ ] post-merge #7-then-#8 ordering (owner): #7 first, then update this branch onto main with a MERGE commit (no force-push), then merge
- [ ] post-merge (owner, GitHub UI): optional branch protection requiring check `validate (ubuntu-latest)` on main
- [ ] follow-on (separate per-store task): replicate workflow to hermes-agent / gufo / tinytuya store repos, each deciding its own no-openspec guard
