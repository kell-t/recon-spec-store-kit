# SCENARIO_PASS_TEMPLATE.md — scenario-ification of verified requirements

<!-- STORE SETUP: rewrite the Tier A/B/C examples to THIS store's actual
     evidence corpus (release-note file names, doc list, test file paths)
     before briefing children. The cite grammar must stay character-identical
     to what recon/scripts/audit_scenarios.py enforces — a template showing a
     different dialect than the gate enforces manufactures wave-wide
     systematic violations. -->

Goal: add OpenSpec-conformant `#### Scenario:` blocks (WHEN / THEN / AND)
beneath existing requirements in `specs_draft/`, WITHOUT ever inventing
behavior.

## THE GROUNDING RULE (stricter than drafting passes — binding)

Every scenario clause must be traceable to a HUMAN-WRITTEN SOURCE:
- **Tier A (preferred): release notes** — `evidence/relnote_<ver>.txt` (or
  release bodies in `evidence/releases.json`) text describing the trigger
  and outcome.
- **Tier B (accepted): repo documentation** — the store's evidence docs copy
  (`evidence/docs/**`) at the pin: `<list this repo's normative docs>` — text
  describing the trigger and outcome.
- **Tier C (accepted): tests at the pin** — test names / test asserts in the
  pin's test tree (inventory in `evidence/tests_inventory.txt`). A test name
  may supply the WHEN trigger and the asserted outcome together.

A scenario is admitted ONLY when BOTH the trigger (WHEN) and the outcome
(THEN) appear, in substance, in the cited Tier A/B/C text. Exact quote not
required — substance match is — but you must cite the file and quote the
supporting phrase(s). Evidence must EXIST AT THE PIN: post-pin or unmerged
material is inadmissible.

## Rules

1. If release notes / docs / tests give trigger + outcome → write:
   ```
   #### Scenario: <short name>
   - **WHEN** <trigger as documented>
   - **THEN** <outcome as documented>
   - **AND** <further documented clause>   (only if documented)
   - Source: [relnote <ver>] "…quoted phrase…"   (or doc:/test: cite, below)
   ```
   Place the scenario block INSIDE its requirement block — after the
   `- Anchor:` line, before the next `###` header (`####` stays inside). Add
   one `- Source:` line per cited clause group at the end of the scenario.
   Keep the requirement's Status/Evidence/Anchor lines untouched.
   Cite formats (enforced by `recon/scripts/audit_scenarios.py`):
   - `[relnote <ver>] "quoted phrase"` — ≥60% non-stopword token overlap
     with the cited version's body;
   - `doc: <path> § <section> "quoted phrase"` — path resolves under
     evidence/docs/ (flattened names) or the repo; ≥60% overlap with that doc;
   - `test: <path>::TestClass::test_method` — EXACT class+method grep in the
     repo at the pin (invented segments are the known fabrication shape).
   Quotes that themselves contain a package-relative path: drop the inner
   backticks from the quote (tokens unchanged, overlap unaffected) — never
   re-qualify a path inside a quote; that falsifies it.
2. If trigger or outcome is NOT in Tier A/B/C text (code-only or inferred) →
   DO NOT write a scenario. Leave the requirement as-is (property-style) and
   add, under the file's `## Scenario-ification notes` section:
   `- REQ "<title>": no doc-grounded trigger; kept as invariant. (reason)`
   The conversion pass injects a labeled derived scenario; that is tracked as
   scenario debt, never presented as evidence-backed.
3. NEVER derive a WHEN clause from code reading. Code says a behavior
   exists; only human-written sources document its contract.
4. AND clauses only for clauses that are themselves documented. Do not
   compound inferences.
5. One scenario minimum per requirement where documentable; two preferred
   when docs describe both a happy path and a fallback/edge ("stays",
   "unless", "even when", "instead").
6. Keep RFC-2119 verbs consistent with the parent requirement's force.
7. Do not modify any requirement text, grade, anchor, or gap entry.
   Append-only: scenarios under requirements, notes under the notes section.
8. Update each file's header line: append `| Scenario pass applied <date>`.
9. Return summary per assigned file: scenarios added (count); requirements
   left property-style (count + one-line reasons); doc-grounding surprises
   (docs contradicting the drafted requirement → flag, don't fix).
