"""Spec-traceability registry shared by conftest and the meta tests.

Convention: every functional test is tagged with the EXACT requirement and
scenario titles from the openspec change delta it validates:

    @spec_case("add-repo-cache",
               "One persistent git-ignored clone at `.repo`",
               "Cache created on first use")

If a requirement/scenario is renamed or removed, the traceability meta tests
fail and print the exact mismatch, so the affected tests are trivially
findable (grep the title) and amendable. Tests that validate helpers rather
than a scenario carry @aux("reason") and are exempt from the
scenario->test coverage rule (they must still pass).
"""

SPEC_CASES = []  # (change_dir, requirement_title, scenario_title, test_name)


def spec_case(change, requirement, scenario):
    def deco(fn):
        SPEC_CASES.append((change, requirement, scenario, fn.__name__))
        fn.__spec_case__ = (change, requirement, scenario)
        return fn
    return deco


def aux(reason):
    def deco(fn):
        fn.__spec_aux__ = reason
        return fn
    return deco
