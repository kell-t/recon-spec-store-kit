# WORKFLOW.md — `<slug>` store policy (repo-local)

Store for github.com/`<org>`/`<repo>` (`<license>`). Cross-repo policy lives in the
cluster WORKFLOW.md; this file is repo-local and more specific.

## Pin
- Current: `<branch> @ <full-sha>` (tag `<tag>`, `<date>`) — also in
  `recon/RECON_LEDGER.md` PINS and `recon/baseline.txt`.
- Validation and drift analysis start at the pin and run forward until the
  pin moves.
- Anchors in specs are `file:line` AT THE PIN — re-locate on a fresh clone
  of the target branch; never trust pin line numbers blindly.

## License tiers (see kit LICENSE-TIERING.md)
- `recon/LICENSE` = MIT (process IP).
- `openspec/LICENSE` = `<source license>`, copied from the source repo at the
  pin; re-copy on every pin move; relicensing upstream = ledger finding.

## Boundary
- Operate inside this store directory only; read only this store's specs,
  ledger, repo_config. No content in or out of other stores without explicit
  per-instance owner approval (logged in cluster WORKFLOW.md).

## Spec-change policy
1. `openspec/changes/archive/` may contain ONLY this repo's own landed PRs
   and corrections for this repo's incorrect/drifted specs.
2. Implement-originated changes archive ONLY on confirmed PR merge (verify
   merge state via API). Pre-merge: merge simulation + spec-violation
   validation instead.
3. Spec-originated deltas (recon/bootstrap, verified-drift corrections)
   archive at the spec owner's judgment.
4. Unmerged-PR differences are not drift; the spec models merged reality at
   the pin. External review findings are advisory leads: independently verify
   against the pin before correcting; record the verification in the ledger.
5. Never commit spec content into the public repo — sole exception: the repo
   carries its own `openspec/` folder; then its contributing guidelines
   govern.

## Validation
- `openspec validate --all --strict --store <slug>` must be green at every
  milestone commit (expect `<N>` specs).
- Fix drafts and re-convert; never hand-edit `openspec/specs/**`.
- Gate: `python3 recon/scripts/gate.py` green between waves and before
  commits.

## Release branches (optional mirror policy)
- One branch per full (non-prerelease) upstream release, named exactly the
  tag, pushed to the store's remote.
- Base choice minimizes spec reconciliation: off the previous release branch
  (walk forward) if the pin never advanced into main; else compute both
  deltas (prev-release→R, main-pin→R) and base on the smaller.
- Pre-releases never get a branch.

## Push & signing
- Push touched branches after strict validate is green at the milestone
  commit.
- If commits must be signed: verify at commit time —
  `git log --show-signature -1` must print a good signature line. Unsigned
  history cannot be fixed later without a rewrite.
- On push 403: confirm you run under the right HOME (config/token resolve
  relative to it) before blaming the token; never print the token.

## After landing a PR upstream
1. Change folder under `openspec/changes/`, then
   `openspec archive <name> --store <slug>`.
2. Commit the store git; update RECON_LEDGER + PINS if anchors moved.
