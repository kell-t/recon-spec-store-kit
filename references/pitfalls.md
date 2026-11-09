# Pitfalls — environment, tooling, process

Abstracted war stories. Each entry is phrased as the rule it taught.

## Environment / tooling

- **PATH: prepend/append, never assign.** An npm-global-installed CLI's
  shebang needs `node` on PATH; assigning PATH kills it
  (`env: 'node': No such file or directory`).
- **Store registration is machine-local**, not in the store's git. Fresh
  host or moved folder ⇒ `openspec store register <path> --id <slug> --yes`
  before any `--store` command ("Unknown store" is this). Registration also
  refuses a root without `openspec/config.yaml`, and `store setup` refuses
  non-empty dirs — build the root by hand.
- **Git identity must exist** before store tooling runs (commits during
  setup fail cryptically otherwise).
- **Unattended sessions may block flagged commands** (`python3 -c`,
  heredocs, destructive flags, machine-registry writes). A flagged command
  timing out is NOT a rejection — never treat silence as consent, but do
  work around with tool-native equivalents (write_file over heredoc,
  `mv -f` + `rmdir` over `rm -rf`). Genuinely dangerous steps get deferred to
  the owner in the final report; never disguise dangerous intent.
- **After batch writes, verify on-disk state** (line counts, file lists) —
  approval-rejected or timed-out calls can silently skip a step.
- **Signed commits: verify at commit time** — `git log --show-signature -1`
  must show a good signature. A commit can land silently UNSIGNED despite
  `commit.gpgsign=true`, and unsigned history cannot be fixed later without
  a rewrite.
- **Push 403 on a token remote: check HOME first** (config and token paths
  resolve relative to it) before blaming the token. Never print the token.
- **Container mounts lie**: a path inside the container may map to a
  different host path (`findmnt` before quoting host paths to the owner).

## Fleet / audit

- **Children's self-reports are hypotheses** — including "all checks pass"
  and their file inventories. Scripted tally + `git status` only-assigned +
  gate before any claim.
- **The gate false-positives first.** Baseline-run + triage before the first
  wave (see audit-gate-fp-taxonomy).
- **Lookahead-regex block editing silently no-ops** (see fleet-operations
  § Applying verdict JSONs).
- **In-wave sibling files cause transient gate failures** — only the
  post-wave parent run is authoritative.
- **`git log --since` filters committer date; `%ad` prints author date.**
  Rebased histories mix them; filter author-date in script.
- **Short shas**: expand with `git rev-parse`, take the first 12; never
  zero-pad a short sha to satisfy a 12-hex cite format.
- **Unmerged PRs are not drift.** Review findings (even from other agents)
  are advisory leads: independently verify against the pin before correcting
  anything; record the verification.
- **A huge compare number ≠ stale store.** Rank staleness against
  last-worked date, not pin gap alone; a fresh clean pass absorbs drift.

## Spec process

- **Never hand-edit converted specs**; fix drafts and re-convert.
- **Dash-dirs from the converter count as extra specs** — "20 passed" when
  you expect 10 is NOT green. Strip and confirm zero `./-*` remain.
- **Body-length limits: measure, don't eyeball**, and map the validator's
  0-based requirement index to titles programmatically.
- **Grounding evidence must exist at the pin** — brief children with an
  explicit evidence window; newer unmerged tests/docs get grounded otherwise.
- **A pass template ported between stores carries the donor's dialect** —
  re-anchor every example and keep cite grammar identical to the gate regex.
- **"anchor not located" is a legal draft state; a guessed line number is
  not.**
- **The gap register and NEXT-PASS section are deliverables**, not debris:
  the next session boots from them.
- **Report with paths + raw validation output**, never summaries alone.
- **Milestone messages to the owner: paste proof, not claims** — e.g. for
  API sends, the raw response containing the success flag.

## Markdown rendering (GitHub)

- **Raw `<placeholder>` tokens are HTML, not text.** `<S>` renders as a
  LIVE strikethrough that runs unclosed through everything below it; `<U>`
  underlines; unknown tags (`<D>`, `<slug>`, `<cap>`) are silently stripped
  — the rendered page loses them. Wrap every placeholder in backticks
  in .md files.
- **Inline code spans cannot cross a newline** — a backtick pair split
  across lines renders literal backticks and re-exposes any placeholder
  inside. Keep code spans line-local; use fenced blocks for multi-line
  shapes.

## Retirement

- `git remote -v` before anything else: a local-only store git makes `rm`
  unrecoverable. MOVE to a retirement hold; hard-delete only on explicit
  owner demand. Resume rule: fresh recon; archived drafts are non-current.
