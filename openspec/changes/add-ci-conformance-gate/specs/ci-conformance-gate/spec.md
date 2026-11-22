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
