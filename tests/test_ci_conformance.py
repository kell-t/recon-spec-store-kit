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
    assert t["pull_request"]["branches"] == ["main"]
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
