"""Meta tests: bidirectional traceability between spec and test suite.

Direction 1: every scenario written in openspec/changes/*/specs/**/spec.md
must be claimed by at least one @spec_case test (requirement added without a
test -> FAIL here, naming the scenario).
Direction 2: every @spec_case must point at a scenario that still exists
(requirement renamed/removed -> FAIL here, naming the stale test).
"""
from pathlib import Path

from conftest import KIT
from specmap import SPEC_CASES

CHANGES = KIT / "openspec" / "changes"
LIVING = KIT / "openspec" / "specs"
LIVING_PREFIX = "spec:"  # claim source once a change has been archived

REQ_MARK = "### Requirement: "
SCN_MARK = "#### Scenario: "


def parsed_scenarios():
    """{(source, requirement_title): [scenario_title, ...]}

    While a change is open its scenarios live in
    `openspec/changes/<change>/specs/<cap>/spec.md` (source = change dir).
    After `openspec archive` they live in `openspec/specs/<cap>/spec.md`
    (source = "spec:<cap>"); tests flip their CHANGE constant accordingly
    as a post-merge task — the stale-claim test names every file that still
    points at the archived change dir.
    """
    roots = [(p, p.relative_to(CHANGES).parts[0])
             for p in sorted(CHANGES.glob("*/specs/*/spec.md"))]
    roots += [(p, LIVING_PREFIX + p.parent.name)
              for p in sorted(LIVING.glob("*/spec.md"))]
    out = {}
    for md, source in roots:
        req = None
        for line in md.read_text().splitlines():
            if line.startswith(REQ_MARK):
                req = line[len(REQ_MARK):].strip()
            elif line.startswith(SCN_MARK):
                assert req, f"{md}: scenario before any requirement"
                out.setdefault((source, req), []).append(
                    line[len(SCN_MARK):].strip())
    return out


def test_every_scenario_has_at_least_one_test():
    claimed = {(c, r, s) for c, r, s, _ in SPEC_CASES}
    missing = [f"{c} :: {r} :: {s}"
               for (c, r), scns in parsed_scenarios().items() for s in scns
               if (c, r, s) not in claimed]
    assert not missing, ("scenarios without tests — amend or add:\n  "
                         + "\n  ".join(missing))


def test_no_test_points_at_a_vanished_scenario():
    existing = {(c, r, s)
                for (c, r), scns in parsed_scenarios().items() for s in scns}
    stale = [f"{t} -> {c} :: {r} :: {s}"
             for c, r, s, t in SPEC_CASES if (c, r, s) not in existing]
    assert not stale, ("tests claiming scenarios that no longer exist — "
                       "rename/remove:\n  " + "\n  ".join(stale))


def test_requirements_all_have_scenario_tests():
    """A requirement whose every scenario is covered is itself covered;
    this catches requirements silently stripped down to zero scenarios."""
    empty = [f"{c} :: {r}" for (c, r), scns in parsed_scenarios().items()
             if not scns]
    assert not empty, "requirements with zero scenarios: " + "; ".join(empty)
