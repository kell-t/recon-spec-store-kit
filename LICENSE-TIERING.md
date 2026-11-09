# License tiering (owner directive)

Every store built from this kit carries **two license tiers**, in separate
folders. Do not mix them.

```
<repo>-recon-spec-store/
  recon/                  <- process IP: **MIT** (this repo's license)
    LICENSE               <- MIT text (templates/LICENSE.recon), verbatim
  openspec/               <- derived spec content: **source repo's license**
    LICENSE               <- copy of the source repo's LICENSE at the pin
```

## Rules

1. **`recon/` is MIT.** Playbooks, ledgers, scripts, configs, evidence
   *inventory* structures — the process layer — carry the MIT license of this
   kit (`templates/LICENSE.recon` copied in at store creation). Note: raw
   *evidence corpora* mined from the source repo (release-note bodies, copied
   docs, commit JSON) remain encumbered by the source license no matter which
   folder they sit in; the MIT `recon/LICENSE` covers the tooling and prose
   you wrote, not copied upstream text. Treat `recon/evidence/` contents as
   source-licensed material held for working use.
2. **`openspec/` follows the source repo.** Copy the source repo's `LICENSE`
   file to `<store>/openspec/LICENSE` at pin time; re-copy when the pin moves
   (a relicensing upstream commit is a pin-move finding worth its own ledger
   line). Reconstructed specs are derivative works of that repo's code and
   docs and inherit its encumbrance.
3. **Copyleft sources infect copies.** If the source repo is GPL-family (or
   AGPL), the `openspec/` tier is GPL-derived: its content may never be pasted
   into work for an MIT/permissive repo, and cross-store reuse is a license
   event requiring explicit owner approval.
4. **Per-instance approval log.** Cross-repo reuse approvals live in the
   cluster `WORKFLOW.md` (single log). One approval per instance; never
   blanket.
5. **Publication default.** Reconstructed specs stay private to the store
   repo unless the owner rules otherwise. The store repo being on GitHub does
   not change tier 1 vs tier 2; it just publishes both under their licenses.

## Check at every pin move

- `head -1 openspec/LICENSE` matches the source repo's license at the new pin.
- `recon/LICENSE` still present and MIT.
- If the source is newly relicensed: update tier 2, log in RECON_LEDGER.
