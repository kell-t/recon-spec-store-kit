"""Functional tests for the kit-spec-propagation change delta.

The propagation flow is RUNBOOK §1 step 5 (verbatim copy of the kit
`openspec/` folder to `<store>/recon/openspec/`), so these tests perform
exactly that documented operation against the kit tree under test and audit
the result. Ledger bookkeeping (record kit version + copy date) is agent
duty; what IS testable is that the duty text travels inside the propagated
copy, so a store agent can always consult it.
"""
import filecmp
import re
import shutil

import pytest

from conftest import KIT
from specmap import spec_case

CHANGE = "spec:kit-spec-propagation"  # living spec (add-repo-cache archived 2026-11-22)
RA = "Kit openspec copy present in every store"
RB = "Copy refreshed whole; PIN currency owned by the kit"

KIT_OPENSPEC = KIT / "openspec"
RUNBOOK = KIT / "RUNBOOK.md"


def bootstrap_copy(store):
    """RUNBOOK §1 step 5 verbatim: cp -r kit/openspec -> recon/openspec."""
    shutil.copytree(KIT_OPENSPEC, store / "recon" / "openspec")


def refresh(store):
    """Requirement law: wholesale replacement, never a patch."""
    dst = store / "recon" / "openspec"
    shutil.rmtree(dst)
    shutil.copytree(KIT_OPENSPEC, dst)


def tree_diff(a, b):
    """Empty list <=> b is verbatim-identical to a (files + content)."""
    fa = {p.relative_to(a) for p in a.rglob("*") if p.is_file()}
    fb = {p.relative_to(b) for p in b.rglob("*") if p.is_file()}
    out = [(str(r), "missing") for r in fa - fb]
    out += [(str(r), "extra") for r in fb - fa]
    out += [(str(r), "differs") for r in fa & fb
            if not filecmp.cmp(a / r, b / r, shallow=False)]
    return sorted(out)


# --- RA ------------------------------------------------------------------
@spec_case(CHANGE, RA, "Bootstrap placement")
def test_bootstrap_placement(store):
    # the placement step is documented (RUNBOOK §1 step 5, before first push)
    doc = RUNBOOK.read_text()
    assert "Copy this kit's `openspec/` folder → `<store>/recon/openspec/`" \
        in doc
    # and performing it yields a verbatim copy in the store
    bootstrap_copy(store)
    dst = store / "recon" / "openspec"
    assert (dst / "project.md").is_file()
    assert tree_diff(KIT_OPENSPEC, dst) == []


@spec_case(CHANGE, RA, "Refresh on kit sync")
def test_refresh_on_kit_sync(store):
    bootstrap_copy(store)
    dst = store / "recon" / "openspec"
    edited = dst / "project.md"
    edited.write_text(edited.read_text().replace("PIN:", "EDITED:", 1))
    refresh(store)                                 # store re-syncs the kit
    assert tree_diff(KIT_OPENSPEC, dst) == []      # verbatim again
    # the ledger duty is consultable INSIDE the copy the store just received
    propagated = dst / "specs" / "kit-spec-propagation" / "spec.md"
    assert propagated.is_file()
    assert "kit version + copy date" in propagated.read_text()


@spec_case(CHANGE, RA, "Store copy never diverges")
def test_store_copy_never_diverges(store):
    bootstrap_copy(store)
    dst = store / "recon" / "openspec"
    (dst / "project.md").write_text("ad hoc store-side edit")
    (dst / "rogue_requirement.md").write_text("invented locally")
    audit = tree_diff(KIT_OPENSPEC, dst)
    assert ("project.md", "differs") in audit      # audit DOES catch drift
    assert ("rogue_requirement.md", "extra") in audit
    # correction law: re-copy from the kit, not ad-hoc edits
    refresh(store)
    assert tree_diff(KIT_OPENSPEC, dst) == []


# --- RB ------------------------------------------------------------------
@spec_case(CHANGE, RB, "Refresh replaces, never patches")
def test_refresh_replaces_never_patches(store):
    bootstrap_copy(store)
    dst = store / "recon" / "openspec"
    # a patch-style merge would keep these; a wholesale replacement must not
    (dst / "stale_from_old_kit.md").write_text("obsolete")
    deep = dst / "specs" / "kit-spec-propagation"
    (deep / "stale_task.md").write_text("obsolete")
    refresh(store)
    assert tree_diff(KIT_OPENSPEC, dst) == []      # zero residue, zero edits
    assert not (dst / "stale_from_old_kit.md").exists()
    assert not (deep / "stale_task.md").exists()


@spec_case(CHANGE, RB, "Archive advances the kit-side PIN")
def test_archive_advances_kit_side_pin(store):
    pin = KIT_OPENSPEC / "project.md"
    text = pin.read_text()
    # kit side: a well-formed PIN line exists and carries the KIT-side duty
    assert re.search(r"^PIN: kit main @ [0-9a-f]{7,} \(\d{4}-\d{2}-\d{2}\)",
                     text, re.M), "kit project.md must carry the PIN line"
    assert "Maintained KIT-side" in text
    # store side: the copy inherits the PIN byte-identically — the tool of
    # record (refresh) provides no patch path, and no store edit survives
    bootstrap_copy(store)
    copy_pin = store / "recon" / "openspec" / "project.md"
    assert copy_pin.read_bytes() == pin.read_bytes()
    copy_pin.write_text(copy_pin.read_text().replace("PIN:", "STORE-PIN:", 1))
    refresh(store)
    assert copy_pin.read_bytes() == pin.read_bytes()
    # stores record versions in their OWN ledger, never in the copy:
    assert "stores record kit versions in their own ledgers" in \
        (KIT_OPENSPEC / "specs" / "kit-spec-propagation" / "spec.md").read_text()
