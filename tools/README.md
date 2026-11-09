# tools/ — the recon script kit

Generalized from production versions used across multiple passes on two
real stores. Copy into `<store>/recon/scripts/`, fill
`store_config.yaml` (from `store_config.example.yaml`), run from anywhere —
the store root is auto-detected from the scripts' location (override: env
`RECON_STORE`).

| Script | Phase | Output |
|---|---|---|
| `common.py` | — | shared config loader + audit primitives (import, don't run) |
| `store_config.example.yaml` | — | per-store knobs; copy to `store_config.yaml` |
| `mine_evidence.py` | 1 | `pr_commits.json`+`pr_index.json` (pr-ref) or `commits.json` (ref-free); doc corpus copy; test inventory |
| `mine_relnotes.py` | 1 | `evidence/relnote_<ver>.txt` from the in-tree release doc |
| `cluster.py` | 2 | `clusters.json` + bounded `bundle_<cap>.txt` |
| `mine_tail.py` | 4 | tail commits past the ref window; scope-first TAIL sections appended to bundles (idempotent) |
| `tally.py` | 4 | ledger coverage table numbers (reqs/V/I/U/grounded) |
| `audit_requirements.py` | all | the fabrication gate over drafts (anchor, hint, path, number, quote, test, sha, body-length, structural) |
| `audit_scenarios.py` | 3+ | scenario Source-line auditor (relnote/doc overlap ≥60%; test cites exact-grepped at pin) |
| `gate.py` | all | single-command gate: requirements → scenarios (if any) → tally; one exit code |
| `../draft_to_spec.py` | 6 | drafts → validator-conformant specs (see validator rules ref for the dash-dir strip) |

## Run order (first pass)

```
mine_evidence.py  ->  mine_relnotes.py  ->  cluster.py
-> (gate baseline + triage)  ->  draft waves  ->  gate.py
-> conversion + openspec validate --all --strict
```

## Dependencies

Python 3.9+ stdlib; PyYAML only for `store_config.yaml` (or write
`store_config.json`). Git present in `<store>/repo` (the blobless clone).

## Editing law

- The auditors' regexes define the store's cite GRAMMAR.
  `templates/SCENARIO_PASS_TEMPLATE.md` and `templates/DRAFT_TEMPLATE.md`
  must stay character-identical to them — update both sides together or
  children manufacture violations.
- Every new mining/audit capability you add in a store gets promoted back
  toward this kit (or at least documented in the store ledger) so the next
  store inherits it.
- The gate is adversarial to drafts, not a linter: it answers "is this
  claim evidenced at the pin?", never "is this prose good?".
- Smoke-tested: the kit passes clean drafts and flags fabricated test
  segments, unresolvable shas, ungrounded quotes, and unresolved paths
  (throwaway-fixture test, 2026-11).
