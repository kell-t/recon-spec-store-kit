# RECON_LEDGER — `<slug>`

Store: `<path>` (id `<slug>`). Boot order: PLAYBOOK.md → repo_config.yaml →
this file. This ledger is the store's state machine: every pass rewrites
CURRENT STATE and NEXT-PASS; history sections are append-only.

## CURRENT STATE (`<pass N>` complete, `<date>`)

- Baseline pin: `<branch> @ <full-sha>` (tag **`<tag>`**, `<date>`).
  `recon/baseline.txt`. `<moved? from what? why>`
- Validation: `openspec validate --all --strict --store <slug>` →
  **Totals: `<N>` passed, 0 failed** (openspec `<ver>`), GREEN at every pass-N commit.
- Fleet: **`<R>` requirements**, **`<V>` VERIFIED (`<pct>`%)**, `<I>` INFERRED,
  `<U>` UNVERIFIED-as-spec (must be 0).
- Scenario debt: **`<D>`** requirements carry derived (non-evidence) scenarios;
  **`<S>` evidence-backed scenarios**. Residual debt reasons live in per-file
  Scenario-ification notes.
- Audit gate: `recon/scripts/gate.py` — <one-line inventory of active
  checks>. MANDATORY between every wave completion and every commit.
- License tiers: `recon/LICENSE` MIT; `openspec/LICENSE` = `<source license>`
  (copied at pin `<sha>`).

### Coverage table (scripted tally of specs_draft/, pass N — never hand-counted)

| Capability | Reqs | VERIFIED | INFERRED | Grounded scenarios | Scenario debt |
|---|---|---|---|---|---|
| `<cap>` | | | | | |
| **TOTAL** | | | | | |

Pass-N audit summary: <what the gate + spot-checks caught and fixed, in
plain lines: fabricated cites, dead requirements, re-anchored statuses,
gate false positives fixed in the checker>.

## Gap register (state after pass N)

Entries: `G-NN <title> [OPEN|CLOSED]` — evidence, what would close it, who
decided. Closed entries keep their closing evidence (they are the audit
trail of the pass that closed them).

- G-01 `<title>` [OPEN] — `<state, blocking condition>`
- G-02 `<title>` [CLOSED pass N] — `<how, evidence>`

## Drift register

Doc-vs-code or spec-vs-pin disagreements found this pass:
`Drift (pass N): <requirement> — <what changed upstream> — <action taken>`
Include: requirements rewritten/deleted by the removal-check law ("the spec
models merged reality at the pin"), doc-staleness findings worth reporting
upstream, license/pin-move findings.

## PINS

| Date | Pin sha | Tag | Branch | Reason |
|---|---|---|---|---|
| `<date>` | `<full-sha>` | `<tag>` | `<branch>` | initial pass / re-pin / drift correction |

## Pass history

- **Pass 1 (`<date>`):** scope decision executed; `<R>` reqs drafted in `<W>`
  waves; `<%>` VERIFIED; conversion green; gaps G-01..G-0n opened.
- **Pass 2 (`<date>`):** anchor verification; tail mining; VERIFIED `<a%>`→`<b%>`;
  `<n>` dead requirements removed (removal-check law); `<n>` cites fabricated
  and fixed.
- **Pass 3 (`<date>`):** scenario grounding; +`<S>` grounded; debt `<D>`;
  `<findings>`.

## NEXT-PASS (the mission the next session executes)

Numbered, executable, each with its completion check. Include:
1. Remaining OPEN gaps worth closing and how.
2. Status-debt cleanup (file-only anchors → `file:line`; INFERRED masses to
   re-verify if pin moved).
3. Scenario-debt targets (which caps, which tiers).
4. Pin health: current drift (commits since pin, releases since pin) and
   the re-pin trigger.
5. Standing laws for the next pass (e.g. "run the gate green over existing
   drafts FIRST and triage before the first wave").
