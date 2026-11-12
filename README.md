# recon-spec-store-kit

**Runbook + templates + tooling for reconstructing behavior specs of public
git repositories into isolated OpenSpec stores.**

This is the distilled process from two completed reconstruction programs
(both MIT-licensed repos, one ~60k-commit polyglot monorepo with PR-ref'd
squash history, one ~1k-commit library with a ref-free history and a rich
in-tree doc corpus). The methodology also has one earlier exploratory
ancestor that was retired; its lessons are folded in here.

The goal: a private, pinned, validated spec model of a repo's capability
surface, kept in a separate store repo, so that an agent (or human) can make
PRs to the upstream repo **without breaking existing behavior** — and so the
next pass can resume exactly where this pass stopped.

## What lives where

```
recon-spec-store-kit/              <- THIS repo: process IP only
  README.md                        <- you are here
  RUNBOOK.md                       <- the operator runbook, pass by pass
  LICENSE                          <- MIT (this repo's content)
  LICENSE-TIERING.md               <- license rules for every store built from this
  templates/                       <- drop-in skeletons for a new store
    PLAYBOOK.md                    <- method law (repo-agnostic, grows with lessons)
    DRAFT_TEMPLATE.md              <- drafting law every drafting agent reads first
    SCENARIO_PASS_TEMPLATE.md      <- scenario-ification pass rules
    RECON_LEDGER.md                <- per-pass ledger skeleton
    repo_config.yaml               <- per-repo intel skeleton
    store-WORKFLOW.md              <- per-store policy skeleton
    store-README.md                <- store repo README skeleton (kit-referencing;
                                      fill at bootstrap — every store repo has one)
    cluster-WORKFLOW.md            <- container policy (multi-store)
    store.yaml                     <- OpenSpec store identity
    LICENSE.recon                  <- MIT text to drop into each store's recon/
  tools/                           <- generalized script kit (see tools/README.md)
    draft_to_spec.py               <- drafts -> validator-conformant specs
    gate.py                        <- single-command gate over the auditors
    scripts/...                    <- mine / cluster / tally / audit auditors
  references/
    openspec-validator-rules.md    <- strict-mode conformance rules (CLI 1.16.x)
    fleet-operations.md            <- drafting-fleet (multi-agent) operational law
    audit-gate-fp-taxonomy.md      <- the false-positive shapes a gate must encode
    evidence-models.md             <- PR-ref vs ref-free evidence strategies
    pitfalls.md                    <- environment/tooling war stories, abstracted
```

## The core loop (one paragraph)

Pin the repo at a baseline commit → script-mine evidence (commit log,
release notes, docs, tests) → cluster commits into capability buckets → draft
requirements with an LLM fleet, each citing real evidence and an anchor into
the code at the pin → run a scripted audit gate (the fleet's self-reports are
hypotheses, not data) → convert drafts to OpenSpec format → keep
`openspec validate --all --strict` green → record everything (grades, gaps,
drift, scenario debt) in a ledger so the next pass inherits a mission, not a
mystery.

## Three laws this repo exists to enforce

1. **History is evidence, the tree at the pin is ground truth.** Never
   replay history to build the spec; reconstruct at the checkpoint and verify
   against the pinned tree. The spec models merged reality at the pin.
2. **Blanks over guesses.** No citation → the requirement does not exist.
   Never invent PR numbers, paths, line numbers, or quotes. An honestly
   recorded gap is worth more than a confident guess.
3. **License firewall.** Stores of different repos are unconnected. Nothing —
   spec text, designs, evidence, anchors — crosses repo boundaries without the
   owner's explicit per-instance approval. See `LICENSE-TIERING.md`.

## Getting started with a new repo

1. Read `RUNBOOK.md` end to end once.
2. Create a store repo named `<thing>-recon-spec-store`; copy every file in
   `templates/` into it per the header comments inside each file.
3. Fill `repo_config.yaml` (Phase 0 of the runbook does this).
4. Run the passes. The ledger is your state machine; `gate.py` +
   `openspec validate --all --strict` are your green light.

## Status of the kit

Everything here was exercised in production passes: Phase 0-6 initial
reconstruction, anchor-verification waves, scenario-grounding waves, tail
mining, the audit gate, conversion, and per-release re-pinning. Scripts are
generalized from the working versions; the per-repo parts moved into
`scripts/store_config.yaml`.
