## Purpose
Keep the kit's openspec requirements visible to agents working inside each spec store by propagating a copy of the kit `openspec/` folder into every store, so recon flows can consult the rules where the work happens.

## ADDED Requirements


### Requirement: Kit openspec copy present in every store
Every store bootstrapped from this kit SHALL carry a verbatim copy of the
kit's `openspec/` folder at `<store>/recon/openspec/`; the copy is
read-only in the store — requirement changes happen in the kit repo (via
PR), never by editing the store's copy.

#### Scenario: Bootstrap placement
- **WHEN** a new store is bootstrapped (RUNBOOK §1 step 5)
- **THEN** the kit's `openspec/` folder is copied to `<store>/recon/openspec/`
  before the store's first push

#### Scenario: Refresh on kit sync
- **WHEN** a store re-syncs its kit scripts/templates to a new kit version
- **THEN** `recon/openspec/` is re-copied verbatim and the store ledger
  records the kit version + copy date

#### Scenario: Store copy never diverges
- **WHEN** an audit diffs `<store>/recon/openspec/` against the kit tree at
  the recorded kit version
- **THEN** the diff is empty (any divergence is corrected by re-copying from
  the kit, not by editing either side ad hoc)

### Requirement: Copy refreshed whole; PIN line kept current
Refreshes of `<store>/recon/openspec/` SHALL replace the entire folder with
the kit's `openspec/` tree; agents SHALL NOT edit, add, or delete individual
files inside the copy. The copy's `openspec/project.md` carries a `PIN:`
line naming the kit main commit the copy came from; store re-syncs update
it, and the kit SHALL update it at every `openspec archive` via a follow-up
one-line commit naming the archive commit.

#### Scenario: Refresh replaces, never patches
- **WHEN** a store refreshes its kit copy
- **THEN** the whole `recon/openspec/` folder is replaced with the kit tree
  at the recorded PIN and that line is updated in the same store commit —
  no in-place edits inside the copy

#### Scenario: Archive advances the kit-side PIN
- **WHEN** `openspec archive` lands on kit main
- **THEN** the same flow commits a follow-up one-line update of the
  `PIN:` line in `openspec/project.md` to that archive commit, so every
  later copy carries a fresh reference
