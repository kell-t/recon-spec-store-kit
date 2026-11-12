# Capability Spec Draft Template (OpenSpec-flavored)

<!-- STORE SETUP: replace `<REPO>`, `<org/repo>`, `<LICENSE>`, `<sha>`, `<dates>` and
     the example citation URL before briefing drafting agents. Re-anchor any
     example paths to THIS repo's layout. -->

You are reconstructing a capability spec for `<REPO>`
(https://github.com/`<org>`/`<repo>`, `<LICENSE>`) from evidence. Output ONE file
in this exact shape. Rules at the end are binding.

```markdown
# Capability: <name>

Baseline: <REPO> <branch> @ <sha you checked> (<pin date>). Evidence window: <start> .. <pin date>.

## Summary
<2-4 sentences: what this capability is and where it lives in the code.>

## Primary code locations
- `path/...` — <one-line role>

## Requirements

### Requirement: <short title>
The <system/library> SHALL <behavior, testable, present tense>.
- Status: VERIFIED | INFERRED | UNVERIFIED
- Evidence: [PR #NNNN](https://github.com/<org>/<repo>/pull/NNNN) — <what it did>; doc: docs/...
  (ref-free repos: [commit <12-hex>] — <subject>; doc: ...)
- Anchor: `file:line or file` in the pinned tree that implements it (VERIFIED only)
- History: <optional, append-only pass annotations: never delete existing
  Evidence/Anchor/History content; corrections are appended with the pass number>

(...repeat; group under `## Sub-areas` if needed)

## Known gaps / open questions
- <behavior seen in issue titles or partial evidence that could NOT be
   grounded — list explicitly>
```

## Binding rules

1. EVIDENCE FIRST: every requirement must cite at least one real PR number,
   commit, or doc file found in your evidence bundle. No citation → do not
   write the requirement.
2. VERIFIED means you OPENED the current code at the pin and saw the
   implementation at the anchor. Paste the anchor path in the canonical
   form `` `file:line` (hint) `` — the hint is a symbol visible near the
   line; the gate greps for it. If you did not open it, it is INFERRED (cited from
   docs/PRs but code unconfirmed) or UNVERIFIED.
3. Blanks over guesses. Never invent PR numbers, file paths, or line
   numbers. If unknown, write "anchor not located". Cite commits by 12-hex
   (expand any short sha with `git rev-parse`, take the first 12 — never
   zero-pad). Cite GitHub numbers only as they appear in your bundle, or
   only from the store's verified-numbers allowlist if the repo's commits
   carry no refs.
4. All file paths (anchors AND prose) are repo-root-relative and must exist
   at the pin. Package-relative shorthand (`pkg/foo.py` when the file lives
   at `src/pkg/foo.py`) is a gate violation.
5. Requirements describe WHAT/WHY (behavior + intent), not implementation
   detail, except where implementation IS the contract (protocol names,
   file formats, wire limits).
6. Prefer RFC-2119 verbs: SHALL (hard), SHOULD (strong default), MAY
   (optional). The requirement statement before the first metadata line must
   contain SHALL or MUST and stay under ~400 characters (the validator fails
   bodies at 500): push detail into Anchor/Evidence lines and sub-areas.
7. Where docs and code disagree, record the DOC claim as the requirement and
   note the disagreement in Known gaps.
8. Density target: 8–20 requirements for your capability. Depth over
   breadth; this is a reconstruction seed, not the final spec.
9. Read the release notes' summary sections first — curated intent
   statements are your highest-signal evidence.
10. Only edit the draft file(s) assigned to you. Never touch `openspec/`,
    `recon/`, the clone (read-only), or another agent's files. Never run
    git write commands.
