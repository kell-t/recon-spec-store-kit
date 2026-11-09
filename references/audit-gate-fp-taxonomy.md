# Audit-gate false-positive taxonomy

The scripted gate WILL false-positive before it catches its first real
fabrication. Run it over the EXISTING drafts as a baseline and triage every
finding BEFORE the first child wave — that separates checker FPs, prior-pass
debt, and per-wave regressions, and keeps "gate green" meaningful per wave.

## Legit claim shapes a naive checker flags (encode all of these)

- **Anchor line ranges** `file.py:29-33` — allow `(?:-\d+)?` after the
  number and validate the first endpoint; a closing-backtick-anchored regex
  silently treats range anchors as missing.
- **Anchor hint inside vs outside the backticks** —
  `` `f.py:10` (symbol) `` and `` `f.py:10 (symbol)` `` both appear in the
  wild; accept both, canonical form is the outside one.
- **BARE-PATH flagging must be EXISTENCE-based, not slash-based.** A
  no-slash name is fine when `<repo>/<name>` exists (repo-root `tests.py`);
  flag only names that resolve nowhere. Child drafts systematically carry
  package-relative anchors and bare module names in prose — qualify hits to
  repo-root-relative, and children must write root-relative.
- **Hint keywords need STEM tolerance.** Match window words sharing a ≥5-char
  prefix with the hint token — prose hints ("creation") never verbatim-match
  code identifiers (`create_live_things`). Also: drop generic words (field,
  method, class, module, docstring, comment, header, note…) from hint tokens,
  and resolve dotted `Cls.member` to the final segment.
- **Release bodies live under dual identity.** The git tag may be date-based
  while the release NAME carries the semver — resolve version aliases
  through the releases corpus `name` field before flagging an unknown
  relnote tag.
- **Prose `## ` sections after `## Known gaps` are validator-legal;** only
  `### Requirement:` sections there break strict. The gate rule must scan
  the section BODY for requirement headers, not flag the section header.
- **VERIFIED with file-only anchors is status debt, not a fabrication** —
  resolve by opening the file and pinning exact implementing lines; do NOT
  downgrade a genuinely-opened requirement; downgrade only what you re-check
  and cannot see.
- **Quotes containing backticked paths** trip the existence rule when the
  quoted package-relative path resolves nowhere. Fix by DROPPING the inner
  backticks from the quote (tokens unchanged, overlap unaffected) — never
  re-qualify inside a quote; that falsifies it.

## Real fabrications the gate must catch (all observed in production)

- Invented test `::Class::method` segments against real files.
- Wrong release tags on quotes; quotes with <60% substance overlap.
- Sha cites with last-two-char TRANSPOSITIONS (b85→b86, c0→0c) — prose
  review misses these; `git cat-file -e` does not. When one fails, grep the
  mined tail JSON for the nearest prefix first — usually a one-char typo,
  not a fabrication.
- GitHub numbers labeled 'PR' that are actually ISSUES (issue-vs-pull
  mislabel is systematic). GET `pulls/N` AND `issues/N` before judging — the
  numbering is shared; `/pulls/N` 404s for issues. Record kind+state+title
  in `evidence/verified_numbers.json` ({number: {kind, state, title,
  checked_via}}) so the gate stays offline/deterministic.
- A closed-UNMERGED PR cite whose behavior is nonetheless on main via
  salvage: verify presence in code at the pin, annotate "closed unmerged;
  behavior via salvage", keep the requirement.
- Numbers cited in ref-free stores that don't exist in the (live!) tracker:
  ref-free ≠ numberless. Only the verified-numbers allowlist passes there.
- Requirements citing PRs for mechanisms deleted between the PR and the pin
  (the removal-check law; the gate's anchor+keyword checks usually surface
  these indirectly when the anchor file moved).

## Failure-shape bookkeeping

Every gate fix (checker FP or draft fix) gets a ledger line. If two passes
hit the same FP shape, the checker — not the draft — was wrong; encode the
shape in the checker for the next store.
