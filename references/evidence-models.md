# Evidence models — PR-ref vs ref-free repositories

The Phase-0 count of commit subjects ending in `(#NNNN)` selects one of two
evidence strategies. Getting this wrong poisons every later pass: a ref-free
repo mined with the ref filter yields an empty corpus, and a PR-ref-rich repo
mined without it floods bundles with unattributable noise.

## PR-ref-rich (refs common on squash-merge subjects)

- History IS an index. Mine `--no-merges` filtered by `(#NNNN)$` →
  `pr_commits.json` + `pr_index.json`.
- Drafters cite `[PR #NNNN](https://github.com/<org>/<repo>/pull/NNNN)`.
- Cite validation: number must appear in pr_index ∪ bundles ∪ release
  bodies ∪ verified-numbers allowlist.
- Expect a TAIL: squash-ref conventions often start (or the window ends)
  before the pin — run `mine_tail.py` for the author-date gap
  (see RUNBOOK Phase 4).
- Pitfalls: refs can be duplicated by rebase, misattributed, or point at
  closed-unmerged PRs whose behavior arrived by salvage. Match by TEXT and
  DIFF, not number; API-verify kind and state for anything load-bearing.

## Ref-free (near-zero refs in subjects)

- Check the ratio first: `refs/total`. A few refs in a thousand is ref-free.
- **Ref-free ≠ no number space.** The GitHub tracker is often live; child
  drafts will legitimately cite issues/PRs. Never blanket-reject number
  cites. Judge each via `GET /repos/<org>/<repo>/issues/NNNN` (shared
  numbering; `/pulls/N` 404s for issues), record it in the store's
  `evidence/verified_numbers.json` allowlist, and have the gate reject only
  numbers absent from the allowlist.
- Evidence shifts to: **docs at the pin + pin code + tests**; history is
  intent-provenance only. Mine the FULL log (no filter) into
  `commits.json`; cluster bundles by subject keywords with the capability's
  code inventory in the header; cite history as `[commit <12-hex>]`
  (expand any short sha via `git rev-parse`, take 12 — never zero-pad).
- Release notes: ref-free repos more often keep in-tree release docs —
  `mine_relnotes.py` makes per-version corpora so quotes stay
  overlap-verifiable.
- The scenario-grounding tiers still apply; Tier A may be thinner than Tier
  B (rich docs) — reorder per store but keep the grounding rule intact.

## Mixed / migrating conventions

Some repos migrate to refs partway through history. Treat the ref-bearing
window as the pr-ref corpus and the earlier stretch as ref-free provenance;
the tail-mining script shape works for head gaps too. Record the convention
cutover date in repo_config.

## Which model when re-running an existing store?

The model is a property of the PIN window, not the repo forever. A pin move
across a convention cutover changes it — re-run the Phase-0 count on every
pin move.
