"""Functional tests for the add-ci-conformance-gate change delta.

The gate is a static artifact (workflow YAML), so these checks are fully
offline: they audit the file the way the scenario's "WHEN the workflow file
is inspected" prescribes.
"""
import re

import pytest
import yaml

from conftest import KIT
from specmap import spec_case

CHANGE = "add-ci-conformance-gate"
R1 = "Strict conformance check on every pull request"
R2 = "Pinned validator version"
R3 = "Read-only, secret-free workflow"
R4 = "Requirements conformity tests run on every pull request"
R5 = "Post-merge tripwire on pushes to main"
R6 = "CI pre-simulates archive on the throwaway checkout"

WF_PATH = KIT / ".github" / "workflows" / "openspec-validate.yml"


@pytest.fixture(scope="module")
def wf():
    return yaml.safe_load(WF_PATH.read_text())


def triggers(wf):
    # YAML 1.1 parses the bare `on:` key as boolean True
    return wf.get("on", wf.get(True))


def steps(wf):
    return wf["jobs"]["validate"]["steps"]


# --- R1 ------------------------------------------------------------------
@spec_case(CHANGE, R1, "PR opened or synchronized")
def test_pr_opened_or_synchronized(wf):
    t = triggers(wf)
    pr = t["pull_request"]
    assert pr["branches"] == ["main"]
    # spec WHEN: opened or receives new commits ONLY. The bare `pull_request`
    # default enables EVERY activity type — an API body/title edit (`edited`)
    # would re-run the gate and cancel the in-flight run (observed on
    # f345e79/9f39b2a); an explicit list is the conformance-correct shape.
    assert pr.get("types") is not None, "types must be explicit, not default"
    assert set(pr["types"]) == {"opened", "synchronize", "reopened"}
    runs = [s.get("run", "") for s in steps(wf)]
    assert any("openspec validate --all --strict" in r for r in runs)
    # merge ref: default actions/checkout on pull_request checks out the
    # PR merge commit — proven by the absence of any ref override
    checkout = [s for s in steps(wf)
                if str(s.get("uses", "")).startswith("actions/checkout@")]
    assert checkout and "ref" not in (checkout[0].get("with") or {})
    # stable check name usable in branch protection
    assert wf.get("name") == "openspec-validate"
    # standard GitHub-hosted runner (requirement body)
    assert wf["jobs"]["validate"]["runs-on"] == "ubuntu-latest"


@spec_case(CHANGE, R1, "Manual dispatch")
def test_manual_dispatch(wf):
    assert "workflow_dispatch" in triggers(wf)
    # same strict validation for the dispatched ref: one shared job, and
    # the concurrency group covers both trigger shapes
    group = wf["concurrency"]["group"]
    assert "github.event.pull_request.number" in group and "github.ref" in group


# --- R2 ------------------------------------------------------------------
@spec_case(CHANGE, R2, "Install line is pinned")
def test_install_line_is_pinned(wf):
    installs = [r for r in (s.get("run", "") for s in steps(wf))
                if "openspec@" in r]
    assert len(installs) == 1
    m = re.search(r"@fission-ai/openspec@(\S+)", installs[0])
    assert m and re.fullmatch(r"\d+\.\d+\.\d+", m.group(1)), \
        "install must name an exact version, no floating tag"
    assert not any(tok in installs[0] for tok in ("^", "~", "latest"))
    # matches the CLI generation documented in the validator-rules reference
    rules = (KIT / "references" / "openspec-validator-rules.md").read_text()
    fam = re.search(r"CLI v(\d+\.\d+)\.x", rules)
    assert fam and m.group(1).startswith(fam.group(1) + "."), \
        "workflow pin must sit in the generation documented by the rules ref"


# --- R3 ------------------------------------------------------------------
@spec_case(CHANGE, R3, "Least-privilege audit")
def test_least_privilege_audit(wf):
    assert wf["permissions"] == {"contents": "read"}   # at most read
    text = WF_PATH.read_text()
    assert "${{ secrets." not in text
    # no job-level permission escalation overriding the read-only default
    for job in wf["jobs"].values():
        assert "permissions" not in job or \
            job["permissions"] == {"contents": "read"}


# --- R4 ------------------------------------------------------------------
@spec_case(CHANGE, R4, "Tests job runs both gates green")
def test_tests_job_runs_both_gates(wf):
    # two PR gates; post-merge (R7) exists in the file but is main-only
    assert set(wf["jobs"]) == {"validate", "tests", "post-merge"}
    tj = wf["jobs"]["tests"]
    assert tj["runs-on"] == "ubuntu-latest"
    runs = "\n".join(s.get("run", "") for s in tj["steps"])
    assert "python -m venv" in runs
    assert "pip install -r tests/requirements.txt" in runs
    assert re.search(r"pytest tests\b", runs)
    # full tier: the network tier must NOT be deselected in CI
    assert "not network" not in runs
    # both gates share the one trigger surface (PR to main + dispatch)
    t = triggers(wf)
    assert "pull_request" in t and "workflow_dispatch" in t


@spec_case(CHANGE, R4, "Tests job stays secret-free")
def test_tests_job_secret_free(wf):
    steps_text = "\n".join(str(s) for s in wf["jobs"]["tests"]["steps"])
    assert "secrets." not in steps_text
    assert "token" not in steps_text.lower()          # public origins only
    # covered by the workflow ceiling, no job-level override
    assert "permissions" not in wf["jobs"]["tests"]


# --- R5 ------------------------------------------------------------------
@spec_case(CHANGE, R5, "Push to main runs both gates")
def test_push_to_main_runs_both_gates(wf):
    t = triggers(wf)
    assert t["push"]["branches"] == ["main"]
    # validate+tests fire on push too; post-merge (R7) is the third job,
    # main-only, and carries the obligation signal rather than a gate pair
    assert set(wf["jobs"]) == {"validate", "tests", "post-merge"}
    # the tripwire adds a trigger, not a third job or a permissive scope:
    # no all-branch push, and the PR gate keeps its merge-ref guarantee
    # (pull_request trigger still present, scoped to main)
    assert t["pull_request"]["branches"] == ["main"]


# --- R6 ------------------------------------------------------------------
@spec_case(CHANGE, R6, "Unmergeable delta turns the gate red")
def test_archive_simulation_gates(wf):
    vsteps = steps(wf)
    names = [s.get("name", "") for s in vsteps]
    assert "simulate archive" in names
    # ORDER matters: rehearsal runs AFTER plain strict validation
    assert names.index("simulate archive") > names.index("strict validate")
    sim = vsteps[names.index("simulate archive")]["run"]
    assert "openspec archive" in sim and "--yes" in sim
    # archived folders must be skipped, else the loop re-archives history
    assert "archive" in sim                      # the skip guard
    # rehearsal only: the job never pushes, never mutates the remote
    all_runs = "\n".join(s.get("run", "") for s in vsteps)
    assert "git push" not in all_runs
    # archive validates its produced specs by default; opting out is banned
    assert "--no-validate" not in all_runs


@spec_case(CHANGE, R6, "Post-rehearsal specs validated by name")
def test_post_rehearsal_validation_by_name(wf):
    # archive's internal validation is silent (and --json shows only merge
    # totals), so a final explicit strict validate must exist AFTER the
    # rehearsal step - its output lists every spec by name in the log
    names = [s.get("name", "") for s in steps(wf)]
    assert "strict validate (post-rehearsal)" in names
    assert names.index("strict validate (post-rehearsal)") > \
        names.index("simulate archive")
    step = steps(wf)[names.index("strict validate (post-rehearsal)")]
    assert step["run"].strip() == \
        "openspec validate --all --strict --no-interactive"


# --- R7 ------------------------------------------------------------------
R7 = "Post-merge obligations are surfaced on main pushes"


def pm_run(wf):
    return wf["jobs"]["post-merge"]["steps"][-1]["run"]


@spec_case(CHANGE, R7, "Unarchived change turns main red")
def test_post_merge_names_unarchived(wf):
    run = pm_run(wf)
    # every dir under openspec/changes except archive/ is an open obligation
    assert 'openspec/changes/*/' in run
    assert '"$id" = "archive"' in run
    assert "unarchived change on main" in run


@spec_case(CHANGE, R7, "Unchecked tasks turn main red")
def test_post_merge_scans_tasks(wf):
    run = pm_run(wf)
    # recursive tasks.md scan, archived changes included; file:line printed
    assert "grep -rn --include=tasks.md" in run
    assert "^[[:space:]]*- \\[ \\]" in run
    assert "unchecked task:" in run


@spec_case(CHANGE, R7, "A completed main passes and says so")
def test_post_merge_green_says_owed_nothing(wf):
    run = pm_run(wf)
    assert "main owes nothing" in run
    assert "exit $rc" in run


@spec_case(CHANGE, R7, "Pull requests are exempt from main obligations")
def test_post_merge_pr_exempt(wf):
    # a change branch legitimately carries an open delta + unchecked tasks;
    # the obligation gate is main-push-only
    assert wf["jobs"]["post-merge"]["if"] == "github.event_name == 'push'"
