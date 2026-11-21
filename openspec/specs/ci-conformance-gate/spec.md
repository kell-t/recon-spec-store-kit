# Capability: ci-conformance-gate

Baseline: recon-spec-store-kit main @ 2a17e73 (2026-11-21), change
`add-ci-conformance-gate`. Deterministic GitHub Actions gate over this
repo's `openspec/` folder, free for public repos on standard runners.

## Purpose
Refuse structurally malformed spec changes mechanically, before review:
the validator is a parser with a fixed rule table (see
`references/openspec-validator-rules.md`), so the check is reproducible,
LLM-free, and costs nothing on a public repository.

## Requirements

### Requirement: Strict conformance check on every pull request
Every pull request targeting `main` SHALL run
`openspec validate --all --strict` via GitHub Actions on a standard
`ubuntu-latest` GitHub-hosted runner, and the workflow SHALL also be
manually dispatchable.

#### Scenario: PR opened or synchronized
- **WHEN** a pull request targeting `main` is opened or receives new commits
- **THEN** the check runs against the PR merge ref and reports pass/fail
  with a stable check name suitable for branch protection

#### Scenario: Manual dispatch
- **WHEN** the workflow is triggered via `workflow_dispatch`
- **THEN** the same strict validation runs on the selected ref

### Requirement: Pinned validator version
The workflow SHALL install an exact pinned version of the OpenSpec CLI,
and any version bump SHALL arrive in a PR that updates
`references/openspec-validator-rules.md` in the same change.

#### Scenario: Install line is pinned
- **WHEN** the workflow file is inspected
- **THEN** the CLI install line names an exact version (no floating tag),
  matching the CLI generation documented in the validator-rules reference

### Requirement: Read-only, secret-free workflow
The workflow SHALL declare `contents: read` permissions and SHALL NOT
reference repository secrets, so runs (including future fork PRs) cannot
expose credentials or write to the repo.

#### Scenario: Least-privilege audit
- **WHEN** the workflow file is inspected
- **THEN** `permissions` grants at most `contents: read` and no step reads
  `${{ secrets.* }}`
