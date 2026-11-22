# tests/ — executable contract for the kit's specs

These tests live at KIT level (outside any spec store) so every store
implementation is validated against the same functional reading of the
requirements. Traceability is by exact title: each test is decorated with
the verbatim requirement/scenario titles from
`openspec/changes/<change>/specs/<cap>/spec.md`, and
`test_spec_traceability.py` fails in BOTH directions when a requirement
changes and the tests were not amended.

## Setup
```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r tests/requirements.txt
```

## Running
```bash
pytest -m "not network"     # offline tier: unit + traceability meta tests
pytest                      # full tier: clones real GitHub origins (small)
```

## Conventions
- New scenario in a spec delta -> the meta test fails with its exact title;
  add a test tagged `@spec_case(change, requirement, scenario)` using the
  verbatim titles (copy-paste from the spec file).
- Renamed/removed scenario -> the stale-claim meta test names the orphaned
  test; update the decorator or delete the test.
- Helper-only tests carry `@aux("reason")` and do not count as scenario
  coverage.
- Real GitHub origins only: local-path transports cannot serve blobless
  (partial-clone) lazy fetches. `twitter/bootstrap` is used as a genuinely
  MOVED slug (canonical `twbs/bootstrap`) to exercise the live
  redirect-table move channel; do not replace it with a repo that has not
  actually moved.
- The suite supersedes the ad-hoc dev battery (n2_battery) used during
  authoring; keep new behavioral checks here, in spec-mapped form.

## Coverage notes
- `Relocation is owner-directed`: the tool-side THEN limb is tested; the
  AND limb (update the store's recorded source URL + ledger line) is agent
  duty defined in `templates/store-WORKFLOW.md`, not a process exit.
- The SIGKILL-mid-clone limb of `Undo slot precedes re-clone` was verified
  by hand at authoring time (2026-11-21); the deterministic parts
  (slot-before-clone, nothing-lost, restore-on-next-sync) are tested here.
