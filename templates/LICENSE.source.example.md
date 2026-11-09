# LICENSE.source.example — tier 2 marker

`openspec/LICENSE` must be a **verbatim copy of the source repository's
LICENSE file at the pin**, not this file. This example exists only to show
where the copy goes and what to check:

- copy at store bootstrap (RUNBOOK §1.4) and re-copy at every pin move;
- record the license identity in `repo_config.yaml` (`repo.license`) and in
  `store-WORKFLOW.md`;
- if the pin move crossed a relicense, that is a ledger finding — update
  tier 2 and the registry row.

See `LICENSE-TIERING.md` for the full rule set.
