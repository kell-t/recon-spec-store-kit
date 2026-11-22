"""pytest fixtures for the kit test suite.

Stores are throwaway git repos laid out exactly like a real spec store
(<store>/recon/scripts/*.py copied from tools/scripts), so the scripts'
own path-based store detection is what the tests exercise — no shims.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parent
KIT = TESTS.parent
SCRIPTS = KIT / "tools" / "scripts"
sys.path.insert(0, str(SCRIPTS))  # unit imports: sync_repo, common

# Real GitHub origins only: local-path transports cannot serve blobless
# (partial-clone) lazy fetches — verified 2026-11-22; the suite therefore
# splits unit (offline) from @network e2e tests.
KIT_URL = "https://github.com/kell-t/recon-spec-store-kit"
MOVED_URL = "https://github.com/twitter/bootstrap"
MOVED_CANONICAL = "https://github.com/twbs/bootstrap"


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "network: exercises a real GitHub origin (deselect "
                   "with -m 'not network' when offline)")


def git(cwd, *args, check=True):
    r = subprocess.run(["git", *args], cwd=str(cwd),
                       capture_output=True, text=True)
    if check and r.returncode != 0:
        raise AssertionError(
            f"git {' '.join(args)} rc={r.returncode}: {r.stderr.strip()}")
    return r.stdout.strip()


@pytest.fixture(scope="session")
def refs():
    """Full SHAs for the kit's v0.1.0 tag and default branch, once."""
    def ls(spec):
        out = subprocess.run(["git", "ls-remote", KIT_URL, spec],
                             capture_output=True, text=True,
                             check=True).stdout
        return out.split("\t")[0].strip()
    return {"tag": ls("refs/tags/v0.1.0"), "main": ls("HEAD")}


@pytest.fixture()
def store(tmp_path):
    """A pristine spec store: git repo with recon/scripts holding the kit
    scripts (path-based store detection resolves to this dir)."""
    s = tmp_path / "store"
    (s / "recon" / "scripts").mkdir(parents=True)
    for name in ("common.py", "sync_repo.py"):
        shutil.copy(SCRIPTS / name, s / "recon" / "scripts" / name)
    git(s, "init", "-qb", "main", ".")
    (s / "f").write_text("x")
    git(s, "add", "-A")
    git(s, "-c", "user.email=tests@kit.local", "-c", "user.name=kit-tests",
        "commit", "-qm", "store init")
    return s


def sync(store, *args, probe="1", env_extra=None):
    """Run the store-copied sync_repo.py exactly as an agent would."""
    env = dict(os.environ, RECON_MOVE_PROBE=probe)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, "recon/scripts/sync_repo.py", *args],
        cwd=str(store), capture_output=True, text=True, env=env)
