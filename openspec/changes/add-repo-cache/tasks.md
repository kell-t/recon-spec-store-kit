# Tasks: add-repo-cache

- [x] `tools/scripts/sync_repo.py` (create/fetch/rename-adopt/ref-resolve/gitignore-ensure)
- [x] `common.py` REPO → `<store>/.repo`
- [x] RUNBOOK §1 step 5 (copy kit `openspec/` → `recon/openspec/`) + Phase 0 step 1/2 (`.repo` via sync_repo.py)
- [x] PLAYBOOK Phase 0 step 1 cache wording
- [x] templates/store-README.md snippet → sync_repo.py
- [x] tools/README.md table row + dependency line
- [x] root README.md tree entries (`openspec/`, sync note)
- [x] `openspec validate --all --strict` green at kit root
- [x] recovery law (owner 2026-11-21, simplified 2026-11-22): re-clone = corruption-only, manual, undo-first (rename `.repo` → `.repo-old`, a rolling one-slot undo that REPLACES any previous `.repo-old`, before the fresh clone; store work ignores `.repo-old`; mid-clone failure self-heals on next sync); auth/server errors never trigger it (spec req 4 + design decision 2 + tool docstring)
- [ ] post-merge: ARCHIVE with `openspec archive add-repo-cache --yes` on
  main — this CREATES the living specs under `openspec/specs/` from the
  deltas (their `## Purpose` sections are consumed at creation); commit the
  created specs + archived folder (signed) and push; then a follow-up
  one-line commit sets `PIN: kit main @ <archive-commit-sha>` in
  openspec/project.md (kit-side PIN duty). Deltas are deliberately
  NOT pre-applied on the branch (canonical flow, design decision 8). Kit
  `openspec/` re-copied verbatim to each store's `recon/openspec/` at the
  same kit sync; `openspec validate --all --strict` green before and after
- [ ] post-merge fleet adoption (inventory CONFIRMED 2026-11-21 — not a contingency: all three stores carry a legacy `repo/` clone, ~817 MB total: hermes-agent 721 MB @ pin `3b42157858`, gufo 92 MB, tinytuya 4.1 MB). Per store, IN ORDER: (1) run `sync_repo.py <source-url> --ref <pin>` FIRST — it rename-adopts `repo/` → `.repo` on the spot (NEVER re-clone; adopted caches stay non-bare — the tool attaches the named worktree `.repo/wt/<branch>` the same way; verify HEAD survived the rename and no fresh clone appeared); (2) re-copy kit scripts (new `common.py` resolves `.repo` strictly and reads source files via `common.SRC` = the branch worktree — adoption must precede this step or gates lose the clone; after a passing gate the owner MAY reclaim the vestigial root checkout's disk); (3) confirm `.gitignore` carries `.repo/` (script ensures); (4) copy kit `openspec/` → `recon/openspec/`; (5) ledger line with kit version. Start with tinytuya (smallest; proves the path). — spec agent, per store policy
