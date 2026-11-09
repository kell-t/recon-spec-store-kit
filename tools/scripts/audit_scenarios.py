#!/usr/bin/env python3
"""Scenario-level audit gate: every `#### Scenario:` block's `- Source:`
lines must be one of (cite grammar must match SCENARIO_PASS_TEMPLATE):

  [relnote <ver>] "quoted phrase"  -> version body exists (relnote_<ver>.txt
                                      and/or releases.json); >=60%
                                      non-stopword token overlap
  doc: <path> § <section> "phrase" -> path resolves under evidence/docs/
                                      (flattened) or the repo; >=60% overlap
  test: <path>::Class::method      -> EXACT grep of path + every :: segment
                                      in the repo at the pin

Exit non-zero on any violation. Scenarios with a NOTE marking them derived
(conversion-injected scenario-debt) are skipped, never counted as grounded.
"""
import os
import re
import sys

import common

DRAFTS, EV = common.DRAFTS, common.EV
DOCS = os.path.join(EV, "docs")
pin = common.PinTree()
rel_bodies = common.relnote_bodies({})


def resolve_doc(path):
    for cand in (os.path.join(DOCS, path), os.path.join(common.REPO, path),
                 os.path.join(DOCS, path.replace("/", "_"))):
        if os.path.exists(cand):
            return cand
    return None


bad, stats = [], {}
for fn in sorted(os.listdir(DRAFTS)):
    if not fn.endswith(".md"):
        continue
    cap = fn[:-3]
    text = open(os.path.join(DRAFTS, fn)).read()
    scen_blocks = []
    for m in re.finditer(r"(?m)^#### Scenario: (.+)$", text):
        nm = re.search(r"(?m)^#{2,4} ", text[m.end():])
        blk_end = m.end() + (nm.start() if nm else len(text) - m.end())
        scen_blocks.append((m.group(1), text[m.end():blk_end]))
    grounded = 0
    for name, blk in scen_blocks:
        if "SCENARIO-DEBT" in blk or "derived" in name.lower():
            continue
        grounded += 1
        sources = re.findall(r"(?m)^- Source: (.+)$", blk)
        if not sources:
            bad.append("%s | %s: scenario with no Source line" % (cap, name))
        for s in sources:
            rm = re.match(r"\[relnote ([v0-9.][\w.\-]*)\]\s*\"(.+)\"", s, re.S)
            dm = re.match(r"doc: (\S+)(?:\s*§\s*[^\"]*)?\s*\"(.+)\"", s, re.S)
            tm = re.match(r"test: (\S+)::(.+)", s)
            if rm:
                body = rel_bodies.get(rm.group(1))
                if body is None:
                    alt = [t for t in rel_bodies if rm.group(1) in t or t in rm.group(1)]
                    body = " ".join(rel_bodies[t] for t in alt) if alt else None
                if body is None:
                    bad.append("%s | %s: relnote %s not mined" % (cap, name, rm.group(1)))
                    continue
                ov = common.token_overlap(rm.group(2), body)
                if ov < 0.6:
                    bad.append("%s | %s: relnote quote overlap %.0f%%: %s..."
                               % (cap, name, ov * 100, rm.group(2)[:60]))
            elif dm:
                p = resolve_doc(dm.group(1))
                if p is None:
                    bad.append("%s | %s: doc path unresolved: %s" % (cap, name, dm.group(1)))
                    continue
                ov = common.token_overlap(dm.group(2),
                                          open(p, errors="ignore").read())
                if ov < 0.6:
                    bad.append("%s | %s: doc quote overlap %.0f%%: %s..."
                               % (cap, name, ov * 100, dm.group(2)[:60]))
            elif tm:
                path, rest = tm.group(1), tm.group(2)
                if not pin.exists(path):
                    bad.append("%s | %s: test path missing: %s" % (cap, name, path))
                    continue
                whole = "\n".join(pin.lines(path))
                for seg in [x for x in rest.split("::") if x]:
                    if seg not in whole:
                        bad.append("%s | %s: test segment missing: %s::%s"
                                   % (cap, name, path, seg))
            else:
                bad.append("%s | %s: unparseable Source: %s" % (cap, name, s[:80]))
    stats[cap] = dict(reqs=text.count("### Requirement:"), grounded=grounded)

tot_g = sum(v["grounded"] for v in stats.values())
tot_r = sum(v["reqs"] for v in stats.values())
for cap, d in sorted(stats.items()):
    print("%-28s reqs=%-3d grounded_scen=%d" % (cap, d["reqs"], d["grounded"]))
print("TOTAL grounded scenarios %d / requirements %d" % (tot_g, tot_r))
if bad:
    print("\n".join("VIOLATION: %s" % b for b in bad))
    print("FAIL: %d violations" % len(bad))
    sys.exit(1)
print("SCENARIOS GATE GREEN")
