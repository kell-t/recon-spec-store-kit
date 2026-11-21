# Change: add-ci-conformance-gate

## Why
The strict validator is a deterministic markdown rule engine (parser +
rule table; no LLM). Any PR that lands malformed spec structure — missing
scenarios, stray Requirement headers, >500-char bodies, missing SHALL —
should be refused mechanically before review, at zero cost: GitHub-hosted
standard runners are free for public repositories.

## What Changes
- `.github/workflows/openspec-validate.yml`: PR-to-main (and manual) runs
  of `openspec validate --all --strict` on pinned CLI 1.16.1, `ubuntu-latest`
  standard runner, `contents: read` only, no secrets.
- Capability `ci-conformance-gate` spec + delta.

## Impact
- Affected specs: `ci-conformance-gate` (new).
- Out of scope (design notes): merge-callback/archive automation (runner
  authorship cannot satisfy the signed-kell-t law — archive stays
  agent-side); replicating the workflow to the three store repos (follow-on,
  per store); branch-protection setup (owner, GitHub UI).
- Ordering: PR stacked on #7 (`kit-repo-cache`), merged AFTER #7 so the
  gate goes live on a tree that already carries `openspec/`.
