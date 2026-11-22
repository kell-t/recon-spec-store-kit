## Purpose
Refuse structurally malformed spec changes mechanically, before review:
the validator is a parser with a fixed rule table (see
`references/openspec-validator-rules.md`), so the check is reproducible,
LLM-free, and costs nothing on a public repository.

## ADDED Requirements


### Requirement: Strict conformance check on every pull request
Every pull request targeting `main` SHALL run
`openspec validate --all --strict` via GitHub Actions on a standard
`ubuntu-latest` GitHub-hosted runner, and the workflow SHALL also be
manually dispatchable.

#### Scenario: PR opened or synchronized
- **WHEN** a pull request targeting `main` is opened, receives new commits,
  or is reopened
- **THEN** the check runs against the PR merge ref
- **AND** reports pass/fail with a stable check name suitable for branch
  protection

#### Scenario: Manual dispatch
- **WHEN** the workflow is triggered via `workflow_dispatch`
- **THEN** the same strict validation runs on the selected ref

### Requirement: Pinned validator version
The workflow SHALL install an exact pinned version of the OpenSpec CLI,
and any version bump SHALL arrive in a PR that updates
`references/openspec-validator-rules.md` in the same change.

#### Scenario: Install line is pinned
- **WHEN** the workflow file is inspected
- **THEN** the CLI install line names an exact version (no floating tag)
- **AND** it matches the CLI generation documented in the validator-rules
  reference

### Requirement: Read-only, secret-free workflow
The workflow SHALL declare `contents: read` permissions and SHALL NOT
reference repository secrets, so runs (including future fork PRs) cannot
expose credentials or write to the repo.

#### Scenario: Least-privilege audit
- **WHEN** the workflow file is inspected
- **THEN** `permissions` grants at most `contents: read`
- **AND** no step reads `${{ secrets.* }}`

### Requirement: Requirements conformity tests run on every pull request
The workflow SHALL run the kit's `tests/` pytest suite in a dedicated
`tests` job on every `pull_request` targeting `main` and on
`workflow_dispatch`. The job SHALL provision a throwaway virtualenv from
`tests/requirements.txt`, SHALL run the full suite with the network tier
enabled (public GitHub read access is the only external dependency), and
SHALL use no secrets or credentials, reporting under a stable job name so
branch protection can require it beside the validation check.

#### Scenario: Tests job runs both gates green
- **WHEN** a pull request is opened or synchronized (or the workflow is
  dispatched)
- **THEN** the `validate` and `tests` jobs run independently under stable
  names
- **AND** `tests` provisions a virtualenv from `tests/requirements.txt`
  and runs `pytest tests` with all tiers enabled
- **AND** either job failing turns the PR red — structural soundness and
  behavioral conformity are separate merge gates

#### Scenario: Tests job stays secret-free
- **WHEN** the `tests` job is inspected
- **THEN** its steps reference no secrets and no credentials, cloning
  public origins only
- **AND** the workflow-level `contents: read` ceiling covers it with no
  job-level permission escalation

### Requirement: Post-merge tripwire on pushes to main
The workflow SHALL ALSO trigger on `push` to `main`, running both the
`validate` and `tests` jobs on the pushed commit, so whatever actually
lands on main — merged PR, admin override, or direct commit — is recorded
in checks. The pull-request gate remains the authoritative merge control;
the tripwire never gates a merge.

#### Scenario: Push to main runs both gates
- **WHEN** a commit lands on `main` (merged PR or direct push)
- **THEN** the same `validate` and `tests` jobs run against the pushed
  commit
- **AND** the run records main's health after the fact rather than
  blocking anything
- **AND** the pull-request trigger keeps its merge-ref guarantee
  independently

### Requirement: CI pre-simulates archive on the throwaway checkout
After strict validation, the `validate` job SHALL run
`openspec archive <id> --yes` for every open change against the ephemeral
CI checkout; a refusal or failure SHALL fail the gate. The job SHALL then
re-run `openspec validate --all --strict` on the post-rehearsal tree so
the produced specs are validated visibly, by name. The rehearsal SHALL
NOT push; the authoritative archive remains the agent-side act after
merge.

#### Scenario: Unmergeable delta turns the gate red
- **WHEN** an open change's delta would be refused at archive time
- **THEN** the simulated archive exits non-zero and the PR check fails
- **AND** nothing real changes: the checkout is ephemeral and the
  authoritative archive still happens agent-side after merge

#### Scenario: Post-rehearsal specs validated by name
- **WHEN** the archive rehearsals complete
- **THEN** a final strict validation run lists every living spec,
  including the ones the rehearsals just produced, in the check output

### Requirement: Post-merge obligations are surfaced on main pushes
On pushes to `main` the workflow SHALL run a `post-merge status` job that
fails while the repository still owes post-merge work at that commit: a
change directory outside `openspec/changes/archive/`, or an unchecked
task item in any `tasks.md` under `openspec/changes/`, archived
included. A green main commit SHALL therefore mean every obligation of
that commit — archiving and post-archive amendments included — is
closed, making the check status alone a machine-readable work signal.

#### Scenario: Unarchived change turns main red
- **WHEN** a push lands on `main` while a change directory sits outside
  `openspec/changes/archive/`
- **THEN** the post-merge status job fails
- **AND** names the pending change id in the check output

#### Scenario: Unchecked tasks turn main red
- **WHEN** a push lands on `main` while any `tasks.md` under
  `openspec/changes/` carries an unchecked task item
- **THEN** the post-merge status job fails
- **AND** prints the file and line of each unchecked item, archived
  changes included

#### Scenario: A completed main passes and says so
- **WHEN** a push lands on `main` with no unarchived change and no
  unchecked task item anywhere under `openspec/changes/`
- **THEN** the post-merge status job passes
- **AND** states that main owes nothing

#### Scenario: Pull requests are exempt from main obligations
- **WHEN** the workflow event is a pull request
- **THEN** the post-merge status job does not run
- **AND** the branch is judged only by validation, tests, and the
  archive rehearsal, since a change branch legitimately carries an
  open delta and unchecked post-merge tasks
