# Design: add-repo-cache

## Decisions

1. **Name `.repo`, one clone per store, git-ignored.** A dot-dir keeps the
   cache visually out of the way at store root and signals machine-owned.
   One clone per store (not a cluster-wide shared cache) keeps store repos
   self-contained and license tiering simple: each store's clone is of its
   own source repo, and per the kit's license firewall nothing shared across
   stores crosses repo boundaries implicitly.
2. **Fetch, don't re-clone.** The clone is a cache: `sync_repo.py` clones
   only when absent, otherwise `git fetch --prune --tags` + forced detached
   checkout + `git clean -fd`. Re-cloning is a recovery action for a
   **corrupted cache only** (`git fsck` failure, unreadable refs, index
   damage), never for authentication or server errors — a 403/401, rate
   limit, or 5xx says nothing about the local clone.
   Recovery is **quarantine-first** (owner design, 2026-11-21): rename
   `.repo` → `.repo-corrupt-YYYYMMDD`, THEN clone fresh into `.repo`.
   This ordering removes the destructive step entirely — every operation is
   either reversible (rename) or additive (clone into an empty path) — so
   no failure mode can lose data: pre-clone failure leaves a defined
   absent-`.repo` state (ordinary sync re-creates), and the sick copy
   survives as quarantine until the owner authorizes deletion. An earlier
   draft required a shallow-clone access probe; it was superseded — the
   ordering itself makes the probe redundant (nothing is consumed or
   destroyed before access is proven by the clone's own success). A
   staging-dir + swap design was also considered and rejected as more
   moving parts for the same guarantee.
3. **Strict ref resolution (pin law).** After fetch the requested
   tag/sha/branch must resolve (local, then `origin/<ref>`, then
   `refs/tags/<ref>`); otherwise exit non-zero leaving the checkout
   untouched. Silent fallback to another ref would poison pin-anchored
   evidence.
4. **Remote-mismatch guard.** If an existing `.repo`'s `origin` URL differs
   from the requested source URL, the tool refuses (exit 3) rather than
   re-pointing someone's cache — likely a typo or a store mix-up.
5. **Legacy adoption over dual paths.** `common.py` resolves strictly
   `.repo`; the one-time migration is `sync_repo.py` renaming `<store>/repo`
   when `.repo` is absent (same filesystem, instant). No fallback read path:
   two accepted locations would fork conventions across stores.
6. **Kit openspec copy is read-only in stores.** Requirements change only
   via kit PR; the store copy is re-copied verbatim on kit sync. This keeps
   a single source of truth and an audit-diffable invariant (empty diff
   against the kit tree at the recorded version).
7. **Blobless clone stays the default** (`--filter=blob:none`): history
   mining needs commit/tree metadata, old blobs rarely; it also minimizes
   the SSD footprint this change is protecting.

## Notes (not requirements)
- Scope note (owner, 2026-11-21): the kit's openspec folder intentionally
  tracks ONLY this change's requirements for now. Formally specifying the
  rest of the kit's behavior (evidence models, gate dialect, license
  tiering) is deferred; those remain governed by RUNBOOK/PLAYBOOK/references
  prose. No requirement is written to enforce that deferral.
- A cluster-wide shared source cache (multiple stores or agents sharing one
  clone via `git worktree`) was considered and deferred: concurrency
  coordination is the hard part, and per-store clones already remove the
  repeated-clone wear this change targets.

## Migration (per existing store)
`python3 recon/scripts/sync_repo.py <source-url> --ref <pin>` once → renames
legacy `repo/`, refreshes, prints the pin SHA; then re-copy kit scripts,
ensure `.gitignore` has `.repo/`, copy kit `openspec/` → `recon/openspec/`,
ledger line with kit version.
