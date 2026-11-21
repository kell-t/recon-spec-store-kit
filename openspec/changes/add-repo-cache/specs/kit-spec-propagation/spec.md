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
