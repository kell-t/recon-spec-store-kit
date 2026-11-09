#!/usr/bin/env python3
"""common.py — shared store-config loading and audit primitives.

Copy into <store>/recon/scripts/ alongside store_config.yaml. All toolkit
scripts import this module; keep cite grammar in sync with
templates/SCENARIO_PASS_TEMPLATE.md (the templates show what children write;
this module defines what the gate accepts — divergence manufactures
wave-wide false positives).
"""
import json
import os
import re
import subprocess

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
STORE = os.environ.get(
    "RECON_STORE",
    os.path.abspath(os.path.join(SCRIPTS_DIR, os.pardir, os.pardir)))
DRAFTS = os.path.join(STORE, "specs_draft")
EV = os.path.join(STORE, "recon", "evidence")
REPO = os.path.join(STORE, "repo")

_DEFAULTS = {
    "pin_sha": "",
    "pr_ref_mode": "pr-ref",          # pr-ref | ref-free
    "capabilities": {},               # cap -> {subject_regex, scopes, code}
    "docs": [],                       # normative docs to copy into evidence/docs
    "test_files": [],                 # for Tier-C inventory
    "release_notes": {"mode": "relnote_files",
                      "source": "recon/evidence/docs/RELEASE.md",
                      "header_regex": r"(?m)^## (v[0-9][^\n]*)$"},
    "anchor_extensions": ["py", "md", "ts", "tsx", "yaml", "yml", "json",
                          "sh", "toml"],
    "tail_after": None,               # author-date the ref window stops at
}


def _deep_merge(base, override):
    out = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config():
    """Load recon/scripts/store_config.yaml (YAML-lite: json is a subset, so
    we accept either real YAML via PyYAML if installed, or a JSON file named
    .json alongside)."""
    cfg = dict(_DEFAULTS)
    path = os.path.join(SCRIPTS_DIR, "store_config.yaml")
    if os.path.exists(path):
        try:
            import yaml  # type: ignore
            user = yaml.safe_load(open(path)) or {}
            return _deep_merge(cfg, user)
        except ImportError:
            jpath = os.path.join(SCRIPTS_DIR, "store_config.json")
            if os.path.exists(jpath):
                return _deep_merge(cfg, json.load(open(jpath)))
            raise SystemExit(
                "store_config.yaml present but PyYAML is not installed; "
                "pip install pyyaml, or keep a store_config.json twin.")
    else:
        jpath = os.path.join(SCRIPTS_DIR, "store_config.json")
        if os.path.exists(jpath):
            cfg = _deep_merge(cfg, json.load(open(jpath)))
    if not cfg["pin_sha"]:
        raise SystemExit("store_config: pin_sha is required")
    return cfg


def corpus(name, default=None):
    """Load an evidence JSON corpus if present (stores differ in which exist)."""
    p = os.path.join(EV, name)
    return json.load(open(p)) if os.path.exists(p) else default


# ---------- shared audit primitives (validated shapes) ----------

STOP = set((
    "a an the and or but if then that this these those of to in on for with "
    "as at by from is are was were be been being it its into over under not "
    "no nor so than too very can could will would shall may might must do "
    "does did done have has had having you your we our they their he she i "
    "when while before after also more most other some any each per via"
).split())


def tokens(s):
    return [t for t in re.findall(r"[A-Za-z0-9_]{3,}", s.lower())
            if t not in STOP]


def token_overlap(quote, body):
    """Substance-match: fraction of the quote's non-stopword tokens found in
    the body. The gate threshold in practice is 0.6."""
    qt = tokens(quote)
    if not qt:
        return 1.0
    bt = set(tokens(body))
    return sum(1 for t in qt if t in bt) / len(qt)


class PinTree:
    """Read-only view of the source clone at the pin, with caches."""

    def __init__(self, repo=REPO):
        self.repo = repo
        self._files = {}
        self._shas = {}

    def lines(self, rel):
        if rel not in self._files:
            try:
                with open(os.path.join(self.repo, rel), errors="ignore") as fh:
                    self._files[rel] = fh.read().splitlines()
            except OSError:
                self._files[rel] = None
        return self._files[rel]

    def exists(self, rel):
        return self.lines(rel) is not None

    def sha_resolves(self, tok):
        if tok not in self._shas:
            r = subprocess.run(
                ["git", "-C", self.repo, "cat-file", "-e",
                 tok + "^{commit}"], capture_output=True)
            self._shas[tok] = (r.returncode == 0)
        return self._shas[tok]

    def resolve_bare_path(self, name):
        """BARE-PATH rule: EXISTENCE-based, not slash-based. A no-slash name
        is fine when <repo>/<name> exists (repo-root file); flag only names
        that resolve nowhere. Returns repo-root-relative path or None."""
        if self.exists(name):
            return name
        return None


def relnote_bodies(cfg):
    """Release-note corpus, dual-mode: per-version relnote_<ver>.txt files,
    or releases.json (GitHub API). Returns {version-tag: body}, including
    name-carried aliases (tag may be date-based while the release NAME
    carries the semver, e.g. tag v2026.3.30 ships "v0.6.0")."""
    bodies = {}
    for p in os.listdir(EV) if os.path.isdir(EV) else []:
        if p.startswith("relnote_") and p.endswith(".txt"):
            bodies[p[len("relnote_"):-len(".txt")]] = \
                open(os.path.join(EV, p)).read()
    rels = corpus("releases.json")
    if rels:
        by_tag = {r["tag"]: r.get("body", "") for r in rels}
        bodies.update(by_tag)
        for r in rels:
            for v in re.findall(r"v?\d+\.\d+\.\d+", r.get("name", "")):
                key = v if v.startswith("v") else "v" + v
                bodies.setdefault(key, by_tag[r["tag"]])
                bodies.setdefault(r["tag"] + " (" + key + ")", by_tag[r["tag"]])
    return bodies


def verified_numbers():
    """{number: {...}} allowlist of API-verified GitHub numbers
    (issue-or-PR kind verified via GET /repos/<org>/<repo>/issues/NNNN).
    Accepts the canonical verified_numbers.json or a legacy
    verified_prs.json ({number: title} shape)."""
    vn = corpus("verified_numbers.json")
    if vn:
        return vn
    legacy = corpus("verified_prs.json", {})
    return {k: (v if isinstance(v, dict) else
                {"kind": "migrated", "title": str(v)})
            for k, v in legacy.items()}
