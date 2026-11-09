# OpenSpec strict-mode conformance rules (CLI v1.16.x)

The converter (`tools/draft_to_spec.py`) handles all of this mechanically;
this file is the law behind it — read it when a hand-converted spec fails
`openspec validate --all --strict` or when adapting the converter.

## Parsing rules (from the CLI's requirement-text parser)

1. **Requirements are parsed ONLY inside the main `## Requirements`
   section.** A fresh `## ` header after `## Known gaps` ends the
   requirements region; any `### Requirement:` found after that errors as
   "Requirement header outside Requirements section". `## Sub-area:` h2
   headers inside Requirements also orphan nested requirements — the
   converter flattens them to bold text lines.
2. **Required headers:** `## Purpose` (drafts say `## Summary`; converter
   renames) and `## Requirements`.
3. **Every requirement needs ≥1 `#### Scenario:`** — ERROR even without
   `--strict`. Evidence-less requirements get a converter-injected DERIVED
   scenario labeled `SCENARIO-DEBT (derived, … conformance)`; count it in
   the ledger, replace it on the next grounding pass.
4. **Requirement body < 500 chars.** The body is the prose from the title to
   the first header (or first metadata line), backticks and all. `**Key**:`
   metadata lines are excluded from the length check — `- Key:` style
   bullets are NOT. Hence evidence must render as
   `**Status**:` / `**Evidence**:` / `**Anchor**:` metadata lines (the
   converter turns draft bullets into these).
   - **Never eyeball length.** Measure programmatically: split the converted
     spec on `^### Requirement: `, body = text before the first
     `#### Scenario:` minus `**Key**:` lines, count. The validator reports a
     0-based requirement index; map index→title that way.
   - A multi-behavior requirement should be SPLIT, not compressed past
     clarity.
5. **RFC-2119:** the body must contain SHALL or MUST; MAY alone fails.
6. Scenario blocks live INSIDE the requirement block: after the metadata
   lines, before the next `###` header (`####` stays inside).

## Converter mechanics & the dash-dir pitfall

`draft_to_spec.py <drafts_dir> <specs_out> <prefix>` always joins prefix
with a hyphen — with an empty prefix (the per-store layout, where the folder
is the namespace) dirs come out as `-<cap>`. Strip before validating:

```
cd <specs_out>
for d in ./-*; do mv -f "$d/spec.md" "./${d#./-}/spec.md" && rmdir "$d"; done
```

Notes: bare `mv -- -x` still parses `-x` as options — keep the `./` prefix.
On RE-conversion (plain dir already exists) the rename nests inside it; the
mv-the-spec.md-over form above is idempotent. Confirm zero `./-*` dirs
before claiming green: the validator counts each dash dir as an extra spec,
so "20 passed" when you expect 10 is NOT green. Cleanest re-conversion:
convert into a fresh scratch dir, strip the dash there, overwrite per file.

The converter prints `scenario-debt added=N` per capability — reconcile that
tally with your own count of requirements lacking grounded scenarios before
committing (children's self-reported property-style counts are hypotheses).

## Golden rules

- Fix the DRAFT, re-convert. Never hand-edit `openspec/specs/**` — the next
  conversion silently erases the edit and you lose the audit trail.
- Validation runs per store: `openspec validate --all --strict --store
  <slug>`, and stays green at every milestone commit.
- Registration is machine-local and needs `openspec/config.yaml` in the
  root: `openspec store register <path> --id <slug> --yes` after moving or
  cloning a store on a new machine.
- PATH: if the CLI came from an npm global prefix, APPEND/PREPEND its bin to
  PATH; assigning PATH breaks the `node` shebang lookup
  (`env: 'node': No such file or directory`).
