"""Functional tests for the repo-cache change delta.

One test per scenario, tagged with the exact requirement/scenario titles
(specmap.spec_case) so requirement edits surface via test_spec_traceability.
Run offline part:  pytest -m "not network"  |  full:  pytest
"""
import subprocess

import pytest

from conftest import MOVED_CANONICAL, MOVED_URL, KIT_URL, git, sync
from specmap import aux, spec_case

CHANGE = "spec:repo-cache"  # living spec (add-repo-cache archived 2026-11-22)
R1 = "One persistent git-ignored clone at `.repo`"
R2 = "Source checkouts are named worktrees under the cache"
R3 = "Cache refreshed up to date before recon work"
R4 = "`.repo` treated as disposable cache"
R5 = "Re-cloning only as recovery with a `.repo-old` undo slot"
R6 = "Source identity changes are explicit and owner-directed"


# --- R1 ------------------------------------------------------------------
@spec_case(CHANGE, R1, "Cache created on first use")
@pytest.mark.network
def test_cache_created_on_first_use(store, refs):
    r = sync(store, KIT_URL, "--ref", "v0.1.0")
    assert r.returncode == 0, r.stderr
    repo = store / ".repo"
    # bare: object store at the root, no .git dir
    assert (repo / "objects").is_dir() and not (repo / ".git").exists()
    cfg = (repo / "config").read_text()
    assert "partialclonefilter = blob:none" in cfg       # blobless
    assert 'remote "origin"' in cfg                       # origin recorded
    wt = repo / "wt" / "main"
    assert git(wt, "rev-parse", "HEAD") == refs["tag"]
    gi = (store / ".gitignore").read_text()
    assert "\n.repo/\n" in gi and "\n.repo-old/\n" in gi  # both ignored


@spec_case(CHANGE, R1, "Cache reused, never re-cloned")
@pytest.mark.network
def test_cache_reused_never_recloned(store, refs):
    r1 = sync(store, KIT_URL, "--ref", "v0.1.0")
    assert r1.returncode == 0 and "cloning (bare" in r1.stdout
    r2 = sync(store, KIT_URL, "--ref", "main")
    assert r2.returncode == 0, r2.stderr
    assert "cloning" not in r2.stdout             # no second clone
    assert f"PREV={refs['tag']}" in r2.stdout     # same cache, updated
    assert f"HEAD={refs['main']}" in r2.stdout
    caches = [p.name for p in store.iterdir() if p.name in (".repo", "repo")]
    assert caches == [".repo"]                    # still exactly one clone


# --- R2 ------------------------------------------------------------------
@spec_case(CHANGE, R2, "Worktree per store branch")
@pytest.mark.network
def test_worktree_per_store_branch(store, refs):
    assert sync(store, KIT_URL, "--ref", "main").returncode == 0
    git(store, "checkout", "-qb", "feat-x")
    r = sync(store, KIT_URL)                       # wt name = current branch
    assert r.returncode == 0, r.stderr
    wt = store / ".repo" / "wt" / "feat-x"
    assert wt.is_dir()
    assert git(wt, "rev-parse", "HEAD") == refs["main"]
    assert git(wt, "symbolic-ref", "-q", "HEAD", check=False) == ""  # detached
    assert not (store / "repo").exists()           # no second clone anywhere


@spec_case(CHANGE, R2, "Worktrees share one object database")
@pytest.mark.network
def test_worktrees_share_one_object_database(store, refs):
    assert sync(store, KIT_URL, "--ref", "main").returncode == 0
    git(store, "checkout", "-qb", "feat-y")
    assert sync(store, KIT_URL).returncode == 0
    wt2 = store / ".repo" / "wt" / "feat-y"
    # worktree is a linked checkout (gitfile), never its own object store
    assert (wt2 / ".git").is_file()
    assert (wt2 / ".git").read_text().startswith("gitdir:")
    assert not (wt2 / "objects").exists()
    # removal reclaims the files; cache and sibling worktree survive
    git(store / ".repo", "worktree", "remove", "--force", "wt/feat-y")
    assert not wt2.exists()
    assert (store / ".repo" / "objects").is_dir()
    assert (store / ".repo" / "wt" / "main").is_dir()


# --- R3 ------------------------------------------------------------------
@spec_case(CHANGE, R3, "Ref present after fetch")
@pytest.mark.network
def test_ref_present_after_fetch(store, refs):
    r = sync(store, KIT_URL, "--ref", "v0.1.0")
    assert r.returncode == 0, r.stderr
    assert f"HEAD={refs['tag']}" in r.stdout       # full sha for the ledger
    assert git(store / ".repo" / "wt" / "main", "rev-parse",
               "HEAD") == refs["tag"]


@spec_case(CHANGE, R3, "Ref missing after fetch")
@pytest.mark.network
def test_ref_missing_after_fetch(store, refs):
    assert sync(store, KIT_URL, "--ref", "v0.1.0").returncode == 0
    before = git(store / ".repo" / "wt" / "main", "rev-parse", "HEAD")
    r = sync(store, KIT_URL, "--ref", "definitely-not-a-ref")
    assert r.returncode == 2                       # pin law exit code
    assert "definitely-not-a-ref" in r.stderr      # names the ref
    after = git(store / ".repo" / "wt" / "main", "rev-parse", "HEAD")
    assert after == before                         # checkout untouched


# --- R4 ------------------------------------------------------------------
@spec_case(CHANGE, R4, "Dirty worktree recovered")
@pytest.mark.network
def test_dirty_worktree_recovered(store, refs):
    assert sync(store, KIT_URL, "--ref", "v0.1.0").returncode == 0
    wt = store / ".repo" / "wt" / "main"
    (wt / "untracked_junk.txt").write_text("junk")
    tracked = wt / "README.md"
    tracked.write_text(tracked.read_text() + "\nlocal edit\n")
    r = sync(store, KIT_URL, "--ref", "v0.1.0")
    assert r.returncode == 0, r.stderr             # reset, not failed
    assert git(wt, "status", "--porcelain") == ""  # clean again


# --- R5 ------------------------------------------------------------------
@spec_case(CHANGE, R5, "Transient failure preserves the cache")
@pytest.mark.network
def test_transient_failure_preserves_cache(store, refs):
    assert sync(store, KIT_URL, "--ref", "v0.1.0").returncode == 0
    dead = "https://github.invalid/kell-t/recon-spec-store-kit.git"
    git(store / ".repo", "remote", "set-url", "origin", dead)
    before = git(store / ".repo" / "wt" / "main", "rev-parse", "HEAD")
    r = sync(store, dead, "--ref", "v0.1.0")
    assert r.returncode != 0                       # upstream trouble
    assert not (store / ".repo-old").exists()      # recovery NOT triggered
    assert (store / ".repo").is_dir()
    assert git(store / ".repo" / "wt" / "main", "rev-parse",
               "HEAD") == before                   # cache left in place


@spec_case(CHANGE, R5, "Undo slot precedes re-clone")
@pytest.mark.network
def test_undo_slot_precedes_reclone(store, refs):
    assert sync(store, KIT_URL, "--ref", "v0.1.0").returncode == 0
    old_head = git(store / ".repo" / "wt" / "main", "rev-parse", "HEAD")
    # recovery runs, the fresh clone lands, but the ref still fails:
    r = sync(store, KIT_URL, "--rebuild", "--ref", "definitely-not-a-ref")
    assert r.returncode == 2
    old = store / ".repo-old"
    assert (old / "objects").is_dir()              # previous cache preserved
    assert (store / ".repo" / "objects").is_dir()  # fresh clone in place
    # nothing lost: the next ordinary sync restores a working cache
    r2 = sync(store, KIT_URL, "--ref", "v0.1.0")
    assert r2.returncode == 0, r2.stderr
    assert git(store / ".repo" / "wt" / "main", "rev-parse",
               "HEAD") == old_head == refs["tag"]
    # NOTE the SIGKILL-mid-clone limb of this scenario was verified by hand
    # at authoring time (2026-11-21: clean failure removes the dir; killed
    # partial .git heals on next sync); it is not reproduced offline here.


@spec_case(CHANGE, R5, "Undo slot rolls")
@pytest.mark.network
def test_undo_slot_rolls(store, refs):
    repo = store / ".repo"
    repo.mkdir()                                   # husk, e.g. killed clone
    (repo / "junk").write_text("junk")
    assert sync(store, KIT_URL, "--rebuild", "--ref", "v0.1.0").returncode == 0
    assert (store / ".repo-old" / "junk").is_file()  # slot took the husk
    assert sync(store, KIT_URL, "--rebuild", "--ref", "v0.1.0").returncode == 0
    assert not (store / ".repo-old" / "junk").exists()   # slot ROLLED
    assert (store / ".repo-old" / "objects").is_dir()    # newest prev cache
    assert git(store / ".repo" / "wt" / "main", "rev-parse",
               "HEAD") == refs["tag"]


# --- R6 ------------------------------------------------------------------
@spec_case(CHANGE, R6, "Relocation refused without the deliberate flag")
@pytest.mark.network
def test_relocation_refused_without_flag(store, refs):
    assert sync(store, KIT_URL, "--ref", "v0.1.0").returncode == 0
    r = sync(store, MOVED_URL, "--rebuild")        # typo-shaped URL change
    assert r.returncode == 3
    assert git(store / ".repo", "remote", "get-url",
               "origin") == KIT_URL                # identity untouched
    assert not (store / ".repo-old").exists()      # touched nothing
    r2 = sync(store, KIT_URL, "--relocate")        # flag without --rebuild
    assert r2.returncode == 4                      # usage error, never 2


@spec_case(CHANGE, R6, "Relocation is owner-directed")
@pytest.mark.network
def test_relocation_is_owner_directed(store, refs):
    assert sync(store, KIT_URL, "--ref", "v0.1.0").returncode == 0
    bs_main = subprocess.run(
        ["git", "ls-remote", MOVED_URL, "HEAD"], capture_output=True,
        text=True, check=True).stdout.split("\t")[0].strip()
    r = sync(store, MOVED_URL, "--rebuild", "--relocate", "--ref", "main")
    assert r.returncode == 0, r.stderr
    assert git(store / ".repo", "remote", "get-url",
               "origin") == MOVED_URL              # moved through the flag
    assert git(store / ".repo" / "wt" / "main", "rev-parse",
               "HEAD") == bs_main
    assert (store / ".repo-old" / "objects").is_dir()  # undo slot kept the kit
    # the scenario's AND limb (update recorded source URL + ledger line) is
    # AGENT duty, not tool duty — see templates/store-WORKFLOW.md.


@spec_case(CHANGE, R6, "Move notice is advisory")
@pytest.mark.network
def test_move_notice_is_advisory(store, refs):
    r = sync(store, MOVED_URL, "--ref", "main")    # clone via OLD slug
    assert r.returncode == 0, r.stderr
    assert f"MOVE_NOTICE={MOVED_CANONICAL}" in r.stdout
    # advisory: origin NOT rewritten, no recovery, sync succeeded
    assert git(store / ".repo", "remote", "get-url",
               "origin") == MOVED_URL
    assert not (store / ".repo-old").exists()


@spec_case(CHANGE, R6, "Move notice is advisory")
def test_stderr_notice_channel(monkeypatch):
    # historical GitHub notice channel (probe disabled => stderr only):
    # includes the second-line 'remote: ' prefix git echoes (pitfall).
    import sync_repo as s
    text = ("remote: This repository moved. Please use the new location:\n"
            "remote:   https://github.com/twbs/bootstrap\n")
    monkeypatch.setenv("RECON_MOVE_PROBE", "0")
    assert s.move_notice(MOVED_URL, text) == MOVED_CANONICAL


@spec_case(CHANGE, R6, "Probe failure is silent")
def test_probe_failure_is_silent(monkeypatch):
    import sync_repo as s
    monkeypatch.delenv("RECON_MOVE_PROBE", raising=False)
    assert s.move_notice("file:///some/local/path", "") is None  # non-GitHub
    monkeypatch.setenv("RECON_MOVE_PROBE", "0")
    assert s.move_notice(MOVED_URL) is None        # disabled: silent
    monkeypatch.delenv("RECON_MOVE_PROBE")

    def boom(*a, **k):                             # offline / blocked net
        raise OSError("network down")
    monkeypatch.setattr(s.urlrequest, "build_opener", boom)
    assert s.move_notice(MOVED_URL) is None        # never raises, never acts


@aux("pure helper underpinning the move channel; no scenario of its own")
def test_github_slug_parsing():
    import sync_repo as s
    assert s.github_slug("https://github.com/a/b") == "a/b"
    assert s.github_slug("https://github.com/a/b.git") == "a/b"
    assert s.github_slug("https://github.com/a/b/") == "a/b"
    assert s.github_slug("git@github.com:Foo/Bar.git") == "Foo/Bar"
    assert s.github_slug("https://gitlab.com/a/b") is None
    assert s.github_slug("") is None
