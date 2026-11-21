# Tasks: add-repo-cache

- [x] `tools/scripts/sync_repo.py` (create/fetch/rename-adopt/ref-resolve/gitignore-ensure)
- [x] `common.py` REPO → `<store>/.repo`
- [x] RUNBOOK §1 step 5 (copy kit `openspec/` → `recon/openspec/`) + Phase 0 step 1/2 (`.repo` via sync_repo.py)
- [x] PLAYBOOK Phase 0 step 1 cache wording
- [x] templates/store-README.md snippet → sync_repo.py
- [x] tools/README.md table row + dependency line
- [x] root README.md tree entries (`openspec/`, sync note)
- [x] `openspec validate --all --strict` green at kit root
- [x] recovery law (owner 2026-11-21): re-clone = corruption-only, manual, shallow-clone access probe first; auth/server errors never trigger it (spec req 4 + design decision 2 + tool docstring)
- [ ] post-merge: ARCHIVE this change — move `openspec/changes/add-repo-cache/` to `openspec/changes/archive/` (deltas already reflected in `openspec/specs/` by this PR); kit `openspec/` re-copied verbatim to each store's `recon/openspec/` at the same kit sync; `openspec validate --all --strict` green before and after the move
- [ ] post-merge per-store application (hermes-agent, gufo, tinytuya): mv repo .repo, re-copy scripts, `.gitignore`, `recon/openspec/` copy, ledger lines — spec agent, per store policy
