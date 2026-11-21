# Project: recon-spec-store-kit

The kit repo's OWN requirements. These are process requirements for stores
built from this kit — NOT a reconstruction spec of any source repo (those
live in each store's own `openspec/`).

A copy of this entire `openspec/` folder is placed at
`<store>/recon/openspec/` in every x-spec-store (capability
`kit-spec-propagation`) so agents are aware of these requirements when
performing recon on a store. The store's root-level `openspec/` remains the
store's spec store; `recon/openspec/` is a read-only copy of the kit — do
not edit, add, or delete any file inside it. Refresh means replacing the
WHOLE folder with the kit's `openspec/` tree, then updating the PIN line
below and noting the kit version in the store ledger.

PIN: kit main @ 2a17e73 (2026-11-21). Refresh this line whenever the copy
is re-synced; the kit refreshes it on its side at every `openspec archive`
(a follow-up one-line commit naming the archive commit), so a stale PIN
here means the kit has shipped specs this copy does not yet carry.
