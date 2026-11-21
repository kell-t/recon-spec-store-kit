# Capability: repo-cache

Baseline: recon-spec-store-kit main @ 2a17e73 (2026-11-21), change
`add-repo-cache`. Motivation: per-session re-clones of 700 MB+ source trees
waste bandwidth and wear SSDs; a store's source clone is a cache, not a
disposable.

## Purpose

Every store keeps ONE persistent, git-ignored clone of its source repo at
`<store>/.repo`. Sessions reuse it and bring it up to date with `git fetch`
instead of cloning; the clone is only created when absent.

## Requirements

### Requirement: One persistent git-ignored clone at `.repo`
Each store SHALL keep exactly one source clone at `<store>/.repo`, ignored
by the store repo's git; workflows needing the source at the pin SHALL use
that clone and SHALL NOT create duplicate clones, delete-and-reclone, or
checkout the source into any other path of the store.

#### Scenario: Cache created on first use
- **WHEN** `<store>/.repo` does not exist
- **THEN** `tools/scripts/sync_repo.py` creates it as a blobless clone
  (`git clone --filter=blob:none`) of the store's source URL and ensures the
  store root `.gitignore` ignores `.repo/`

#### Scenario: Cache reused, never re-cloned
- **WHEN** `<store>/.repo` already exists for the same source URL
- **THEN** `sync_repo.py` refreshes it with `git fetch` and a forced
  detached checkout of the requested ref — no clone, no delete

#### Scenario: Legacy `repo/` adopted once
- **WHEN** `<store>/.repo` is absent but a legacy `<store>/repo` clone of the
  same source URL exists
- **THEN** `sync_repo.py` renames it to `.repo` (one-time adoption, same
  filesystem) and proceeds as the reuse case

### Requirement: Cache refreshed up to date before recon work
Agents SHALL run the sync step at the start of any work that reads the
source repo, so the cache is current before pin checks, anchor re-opens, or
evidence mining; after fetch, the requested ref (tag/sha/branch) SHALL be
resolved strictly — if it still does not resolve, the tool SHALL fail loudly
and leave the checkout untouched (pin law: never silently fall back to a
different ref).

#### Scenario: Ref present after fetch
- **WHEN** `sync_repo.py --ref <tag|sha|branch>` resolves the ref after fetch
- **THEN** the tool checks it out detached and prints the resolved full SHA
  for the ledger line

#### Scenario: Ref missing after fetch
- **WHEN** the requested ref cannot be resolved locally or on `origin` after
  fetch
- **THEN** the tool exits non-zero with a message naming the ref and changes
  nothing in the checkout

### Requirement: `.repo` treated as disposable cache
The `.repo` working tree SHALL be treated as a read-only view for recon
purposes: the sync step may force-discard local modifications, and nothing
outside the store's tooling SHALL depend on local commits or edits inside
it.

#### Scenario: Dirty cache recovered
- **WHEN** a previous run left `<store>/.repo` with local modifications
- **THEN** the sync step resets it to the requested ref (force checkout +
  clean of untracked files) rather than failing
