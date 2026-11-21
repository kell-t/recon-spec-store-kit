# Capability: kit-spec-propagation

Baseline: recon-spec-store-kit main @ 2a17e73 (2026-11-21), change
`add-repo-cache`. The requirements in this kit are only binding on agents
while they work in a store if the agent can actually see them there.

## Purpose

The kit's `openspec/` folder is copied into every x-spec-store at
`recon/openspec/`, and refreshed whenever the store re-syncs its kit copy,
so any agent performing recon on the store encounters the kit requirements
next to the store's own material.

## Requirements

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
