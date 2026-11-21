## Purpose
Give every spec store a single persistent, git-ignored source clone (`.repo`) that all recon tooling shares, refreshed by fetch instead of re-cloned per session, so repeated spec work does no redundant download or SSD wear.

## ADDED Requirements


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

### Requirement: Re-cloning only as quarantine-first corruption recovery
Deleting and re-creating `<store>/.repo` SHALL be a manual recovery for a
locally confirmed corrupted clone (`git fsck` failure, unreadable refs,
index damage) only, and it SHALL quarantine first: rename `.repo` to
`.repo-corrupt-YYYYMMDD` BEFORE the fresh clone begins. Authentication or
server errors (401/403, rate limits, 5xx, timeouts) SHALL NOT trigger
recovery; the quarantined copy SHALL never be auto-deleted.

#### Scenario: Transient failure preserves the cache
- **WHEN** a sync fails with an authentication, rate-limit, or server error
- **THEN** the existing `.repo` is left in place untouched — recovery is
  not a response to upstream trouble

#### Scenario: Quarantine precedes re-clone
- **WHEN** recovery runs (`sync_repo.py --rebuild` or the manual
  equivalent) on a confirmed-corrupt cache
- **THEN** `.repo` is renamed to `.repo-corrupt-YYYYMMDD` first and only
  then is the fresh blobless clone created at `.repo` — if that clone
  fails, nothing is lost: the quarantined copy remains and the next
  ordinary sync run restores the cache, either by cloning again from
  scratch (a cleanly failed clone leaves no directory behind, exactly as
  on first install) or by completing a hard-interrupted partial `.git`
  with its fetch and forced checkout

#### Scenario: Quarantine lifetime
- **WHEN** a recovery completes successfully
- **THEN** the corrupt copy stays on disk until the owner authorizes its
  deletion
