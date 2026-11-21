# Design: add-repo-cache

## Decisions

1. **Name `.repo`, one clone per store, git-ignored.** A dot-dir keeps the
   cache visually out of the way at store root and signals machine-owned.
   The cache is **bare** (decision 9): it holds no root checkout — all
   working views are named worktrees under it. One clone per store (not a
   cluster-wide shared cache) keeps store repos self-contained and license
   tiering simple: each store's clone is of its own source repo, and per the
   kit's license firewall nothing shared across stores crosses repo
   boundaries implicitly.
2. **Fetch, don't re-clone.** The clone is a cache: `sync_repo.py` clones
   only when absent, otherwise `git fetch --prune --tags` + forced detached
   update of the named worktree + `git clean -fd`. Re-cloning is a recovery
   action for a **corrupted cache only** (`git fsck` failure, unreadable
   refs, index damage), never for authentication or server errors — a
   403/401, rate limit, or 5xx says nothing about the local clone.
   Requirement strength follows that split (owner ruling, 2026-11-21): the
   *policy* is soft (re-cloning **SHOULD** be reserved for recovery), the
   *mechanics* are hard (quarantine-first, never-auto-delete, auth-never-
   triggers: **SHALL**).
   Recovery is **quarantine-first** (owner design, 2026-11-21): rename
   `.repo` → `.repo-corrupt-YYYYMMDD`, THEN clone fresh into `.repo`.
   This ordering removes the destructive step entirely — every operation is
   either reversible (rename) or additive (clone into an empty path) — so
   no failure mode can lose data: if the fresh clone fails mid-recovery,
   the quarantine still holds the old copy, and the next run of
   `sync_repo.py` restores the cache — verified empirically on 2026-11-21
   with SIGKILL mid-clone: a *cleanly* failed clone leaves no directory
   (git cleans up; next run clones as on first install), and a
   **hard-killed partial `.git`** (objects present, HEAD unborn) is healed
   by the next run's fetch + forced checkout (recovered to a healthy HEAD,
   rc=0). The sick copy
   survives as quarantine until the owner authorizes deletion. An earlier
   draft required a shallow-clone access probe; it was superseded — the
   ordering itself makes the probe redundant (nothing is consumed or
   destroyed before access is proven by the clone's own success). A
   staging-dir + swap design was also considered and rejected as more
   moving parts for the same guarantee. The quarantine renames the whole
   cache including its worktrees; each worktree's git link is stored
   cache-relative (decision 10), so quarantined worktrees stay usable for
   inspection, while the cache's back-links to them read stale until
   `git worktree repair` fixes them in place (verified). A wrong-URL
   `--rebuild` is refused (exit 3)
   BEFORE any quarantine rename — recovery may never consume a healthy
   cache on a parameter mistake — and `--rebuild` quarantines husk
   directories (no git metadata) that would otherwise deadlock the fresh
   clone.
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
   two accepted locations would fork conventions across stores. Adopted
   legacy clones stay non-bare; named worktrees attach to them the same way
   (the tool detects bare vs non-bare), and their old root checkout becomes
   vestigial — the owner may reclaim that disk after a passing gate.
6. **Kit openspec copy is read-only in stores.** Requirements change only
   via kit PR; the store copy is re-copied verbatim on kit sync. This keeps
   a single source of truth and an audit-diffable invariant (empty diff
   against the kit tree at the recorded version).
7. **Blobless clone stays the default** (`--filter=blob:none`): history
   mining needs commit/tree metadata, old blobs rarely; it also minimizes
   the SSD footprint this change is protecting.
8. **Canonical change→archive flow (owner-confirmed 2026-11-21).** Living
   specs are NOT pre-applied on the change branch: `changes/` holds the
   delta, and `openspec archive` (post-merge, per team-workflow doctrine —
   "specs/ moves forward only with work that actually shipped") creates or
   updates `openspec/specs/`. A `## Purpose` section in the delta is read
   when the capability is created; without it archive writes a `TBD`
   placeholder that fails strict. Verified chain: change-only strict 1/1 →
   archive → specs created with real Purpose → strict 2/2.
9. **Bare cache + named worktrees (owner ruling, 2026-11-22; measured on
   hermes-agent, which supersedes this decision's first-draft kit-only
   estimate).** Baseline bare blobless clone = 198 MB (objects 184 MB);
   then `main` + the last five releases as worktrees, in order:

   | # | ref | working files | obj-DB step | total step | total vs bare |
   |---|-----|---------------|-------------|------------|---------------|
   | 1 | main | 319 MiB | +106 MiB | +428 MiB | 316% |
   | 2 | v2026.9.7 | 183 MiB | +39 MiB | +223 MiB | 429% |
   | 3 | v2026.9.11 | 189 MiB | +12 MiB | +202 MiB | 531% |
   | 4 | v2026.9.14 | 192 MiB | +14 MiB | +207 MiB | 636% |
   | 5 | v2026.9.21 | 208 MiB | +23 MiB | +233 MiB | 754% |
   | 6 | v2026.9.24 | 210 MiB | +20 MiB | +231 MiB | 870% |

   Mechanism: a blobless clone lazily fetches each tree's blobs at first
   checkout (every pack here carries a `.promisor` marker), so the object
   store DOES grow per new worktree — but only by that tree's **unique**
   blobs: after the first checkout the step falls to a ~12–39 MiB flat
   band between adjacent releases (deduplicated across worktrees;
   saturating, not monotonically shrinking). The first-draft claim "zero
   new pack objects" was wrong for blobless clones and is retracted —
   it held only where blobs were already local. Working files are linear
   and intrinsic (~190–210 MiB per release tree): N concurrent worktrees
   cost N checkout file trees, so TOTAL footprint is ~linear with a slope
   far below N clones — 6 refs shared 398 MB of objects where six clones
   would carry ~1.1 GB. That is why the requirement mandates removing a
   worktree when its store branch retires: total footprint stays bounded
   by the number of CONCURRENT active branches — normally one.
   Checkouts live only at `<store>/.repo/wt/<branch>`, named after the
   spec-store branch each serves (`--wt` overrides; default is the store
   repo's current branch). `.repo/worktrees/` is git's own admin
   namespace — putting checkouts there collides with it, so they live in
   `.repo/wt/` instead. Consumers read source files through
   `common.SRC` (the current branch's worktree), never through the bare
   cache root.
10. **Hybrid worktree git links (owner-prompted hardening, 2026-11-22).**
    `sync_repo.py` rewrites each worktree's `.git` file to a
    cache-RELATIVE `gitdir:` link after creation (and upgrades older
    caches on the next sync); the admin-side
    `worktrees/<name>/gitdir` file stays ABSOLUTE. Verified on git
    2.47.3: making BOTH sides relative is unsafe — git resolves the
    admin-side file literally, judges a LIVE worktree "prunable", and
    `git worktree prune` then deletes its admin entry, orphaning the
    checkout. With the hybrid form the full lifecycle is green (worktree
    list and prune no-op, fetch, force-checkout, second add, remove,
    fsck) AND a quarantine-renamed cache keeps usable, inspectable
    worktrees — surviving even relocation of the quarantined copy —
    without running `git worktree repair`, which remains the fallback
    for pre-existing renamed caches. git 2.47.3 offers no supported
    creation-time relative mode: there is no `--relative-paths` flag and
    `worktree.useRelativePaths` is NOT a real key (git accepts any
    dotted config silently but the binary contains no such code path —
    pointers stayed absolute with it set). Never set it globally; the
    tool rewrites the one file it owns per worktree instead.

## Notes (not requirements)
- Scope note (owner, 2026-11-21): the kit's openspec folder intentionally
  tracks ONLY this change's requirements for now. Formally specifying the
  rest of the kit's behavior (evidence models, gate dialect, license
  tiering) is deferred; those remain governed by RUNBOOK/PLAYBOOK/references
  prose. No requirement is written to enforce that deferral.
- A cluster-wide shared source cache (multiple stores or agents sharing one
  clone via `git worktree`) was considered and deferred: concurrency
  coordination is the hard part, and per-store clones already remove the
  repeated-clone wear this change targets. (Within ONE store, worktrees are
  now the standard working view — decision 9; the deferred idea is sharing
  ACROSS stores/agents.)
- `--dest` and `--wt` are tool-development/testing conveniences; store work
  always uses the defaults (`<store>/.repo`, current branch).

## Migration (per existing store)
`python3 recon/scripts/sync_repo.py <source-url> --ref <pin>` once → renames
legacy `repo/`, refreshes, creates this branch's worktree, prints the pin
SHA; then re-copy kit scripts, ensure `.gitignore` has `.repo/`, copy kit
`openspec/` → `recon/openspec/`, ledger line with kit version.
