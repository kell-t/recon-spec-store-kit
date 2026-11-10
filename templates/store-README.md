# `<repo>`-recon-spec-store

<!-- STORE SETUP: replace every backticked `<...>` placeholder, fill the
     capability table from repo_config.yaml scope.included, delete this
     comment. Keep the Status snapshot deferring to the ledger. -->

A **reconnaissance spec store** for [`<org>/<repo>`](https://github.com/kell-t/REPLACE-ME) — a reverse-engineered behavioral model maintained by an autonomous spec agent, built *from* the source at a pinned commit, never merged upstream. Built with the [`recon-spec-store-kit`](https://github.com/kell-t/recon-spec-store-kit) (the runbook, templates and audit-script kit this store follows).

## What this is

An [OpenSpec](https://openspec.dev/) store describing what `<repo>` **does**, capability by capability:

| Capability | Models |
|---|---|
| `<capability>` | <one-line surface summary> |

Every requirement carries a provenance status:

- `VERIFIED` — an anchor (`file:line` at the pinned commit) or a PR/release-note/issue/test citation, re-checked at the pin by a scripted audit gate.
- `INFERRED` — supported by evidence not yet anchor-checked; treat as a hypothesis.

Scenario blocks are grounded, not invented: each `#### Scenario:` must carry a `Source:` line into human-written text — release notes (`[relnote vX.Y.Z]`), in-repo docs (`doc: docs/...`), or tests at the pin (`test: path::Class::method`). Requirements with no groundable trigger stay property-style and carry **SCENARIO-DEBT** derived placeholders — those are documented gaps, not evidence.

The authoritative snapshot (counts, pin, coverage, open gaps, next pass) lives in [`recon/RECON_LEDGER.md`](recon/RECON_LEDGER.md) — everything else in this README is by-design approximate.

## How it is derived

The spec agent clones upstream **blobless at the pin** (kept out of git on purpose — see `.gitignore`) and works in an isolated per-repo store.

<!-- STORE SETUP: state the evidence model in one sentence: pr-ref (commit
     subjects carry (#NNNN) refs; history is the index) or ref-free (full-log
     mining, docs + pin-code + tests carry evidence, `[commit <12-hex>]`
     cites), with the ref-ratio numbers from Phase 0. -->

Pipeline, per pass:

1. `recon/scripts/mine_evidence.py` — mine the commit log, normative docs and test inventory into `recon/evidence/` bundles.
2. Release-notes corpus — GitHub Releases API to `evidence/releases.json`, or `recon/scripts/mine_relnotes.py` splitting an in-tree release doc.
3. Drafting in `specs_draft/` (source of truth; fleet children on disjoint files under parent-audited citation law).
4. Gates before every commit: `recon/scripts/gate.py` — anchor existence at pin, cited numbers resolved, quote-overlap on scenario sources, body-length conformance.
5. Convert `specs_draft/` → `openspec/specs/` via `tools/draft_to_spec.py`, then `openspec validate --all --strict --store <slug>`.

Nothing is asserted without a citation, and citations are mechanically re-checked against the pin.

Upstream `<repo>` is `<license>`-licensed; this store is derivative documentation of it, attributed above and per-spec in `recon/`. The store's contents never cross into other repos' work (license firewall).

## Branches

`main` is the working trunk at the pin. One branch per upstream **full release** modeled here, named exactly after the tag; pre-releases never get a branch. Base choice follows the kit release-branch rule: whichever of {previous release branch, last main-dev pin} yields the smaller reconciliation delta.

## How to use

```bash
# validate (needs: npm i -g @fission-ai/openspec)
openspec store register .
openspec validate --all --strict --no-interactive

# get the pinned source alongside, the way the agent does:
git clone --filter=blob:none https://github.com/<org>/<repo> repo
git -C repo checkout <pin-sha>
```

Read order: `recon/RECON_LEDGER.md` (state + gaps) → `openspec/specs/<capability>/spec.md` (requirements) → `recon/evidence/` (bundles, release notes, docs at pin) → `specs_draft/` (per-requirement Status/Evidence/Anchor and scenario notes).

**Status snapshot (rot-prone; the ledger wins):** `<R>` requirements, `<V>` VERIFIED (`<pct>`%), `<S>` grounded scenarios + `<D>` scenario-debt placeholders, at pin `<branch/tag> @ <sha>`.
