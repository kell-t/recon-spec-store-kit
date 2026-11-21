# Project: recon-spec-store-kit

The kit repo's OWN requirements. These are process requirements for stores
built from this kit — NOT a reconstruction spec of any source repo (those
live in each store's own `openspec/`).

A copy of this entire `openspec/` folder is placed at
`<store>/recon/openspec/` in every x-spec-store (capability
`kit-spec-propagation`) so agents are aware of these requirements when
performing recon on a store. The store's root-level `openspec/` remains the
store's spec store; `recon/openspec/` is a read-only kit copy — never edit
it in the store, refresh it from kit instead.

PIN: kit main @ 2a17e73 (2026-11-21). Refresh this line whenever the copy
is re-synced, and note the kit version in the store ledger.
