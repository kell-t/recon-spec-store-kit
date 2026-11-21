#!/usr/bin/env python3
"""sync_repo.py — manage the store's persistent source clone at <store>/.repo.

Spec: openspec/specs/repo-cache/spec.md (kit). The clone is a CACHE: clone
once (blobless), then keep it current with fetch + forced detached checkout.
Never delete-and-reclone in normal flow; never edit or commit inside it.
Corruption recovery is manual and two-step: probe access first with a
throwaway shallow clone (`git clone --depth 1 <url> <scratch>`); only on a
successful probe AND locally confirmed corruption (git fsck) may .repo be
deleted and re-synced. Auth/server errors (401/403, rate limit, 5xx) are
NEVER grounds to delete the cache — the failure is upstream, not local.

Usage:
  sync_repo.py <source-url> [--ref <tag|sha|branch>] [--dest DIR]

--dest defaults to <store>/.repo (store root auto-detected like the other
kit scripts: from this file's location, override env RECON_STORE).

Behavior:
  - .repo absent, legacy <store>/repo present (same origin URL) -> rename,
    adopt, continue as refresh.
  - .repo absent -> `git clone --filter=blob:none`, then checkout --ref.
  - .repo present, same origin URL -> fetch --prune --tags, resolve ref
    strictly (local, refs/tags/, origin/), `checkout --force --detach` +
    `clean -fd` (cache is disposable; local dirt is discarded by design).
  - .repo present, DIFFERENT origin URL -> refuse (exit 3): likely a
    wrong store/URL, do not silently re-point a cache.
  - ref unresolvable after fetch -> exit 2, checkout untouched (pin law:
    never silently fall back to a different ref).
  - Ensures the store root .gitignore ignores `.repo/`.

Prints machine-readable tail lines for ledger capture:
  DEST=<abs path>  HEAD=<full sha>  [PREV=<full sha>]
Exit codes: 0 ok | 2 ref not found | 3 remote mismatch | 4 usage/env error.
"""
import argparse
import os
import shutil
import subprocess
import sys


def store_root() -> str:
    try:
        from common import STORE  # kit layout: same directory
        return STORE
    except Exception:
        return os.getcwd()


def git(args, cwd=None, check=True):
    r = subprocess.run(["git"] + args, cwd=cwd,
                       capture_output=True, text=True)
    if check and r.returncode != 0:
        sys.stderr.write(f"git {' '.join(args)} failed: "
                         f"{r.stderr.strip() or r.stdout.strip()}\n")
        raise SystemExit(4)
    return r.stdout.strip()


def origin_url(dest):
    return git(["-C", dest, "remote", "get-url", "origin"], check=False)


def url_eq(a, b):
    norm = lambda u: (u or "").rstrip("/").removesuffix(".git").lower()
    return norm(a) == norm(b)


def resolve_ref(dest, ref):
    """Strict resolution: tag -> origin/<ref> -> bare ref (full/abbrev sha).
    origin/ is preferred over a possibly-stale local branch ref (the cache
    is read-only; local branches are accidents). Returns full sha or None."""
    candidates = [f"refs/tags/{ref}", f"origin/{ref}", ref]
    for c in candidates:
        r = git(["-C", dest, "rev-parse", "--verify", "--quiet",
                 f"{c}^{{commit}}"], check=False)
        if r:
            return r
    return None


def ensure_gitignore(dest):
    """Keep the clone out of git: ensure '<dirname>/' line in the parent
    .gitignore (the store root when dest is a direct child)."""
    parent = os.path.dirname(os.path.abspath(dest))
    name = os.path.basename(os.path.abspath(dest))
    gi = os.path.join(parent, ".gitignore")
    line = f"{name}/"
    if os.path.exists(gi):
        text = open(gi).read()
        if any(l.strip() == line or l.strip() == f"/{line}"
               for l in text.splitlines()):
            return
        if text and not text.endswith("\n"):
            text += "\n"
        text += (f"\n# Persistent source clone (recon-spec-store-kit cache;\n"
                 f"# see recon/openspec/specs/repo-cache).\n{line}\n")
    else:
        text = f"# Persistent source clone (recon-spec-store-kit cache).\n{line}\n"
    with open(gi, "w") as f:
        f.write(text)
    print(f"gitignore: added '{line}' to {gi}")


def main():
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("url", help="source repo URL")
    ap.add_argument("--ref", default=None,
                    help="tag|sha|branch to check out (strict; detached)")
    ap.add_argument("--dest", default=None,
                    help="clone dir (default <store>/.repo)")
    args = ap.parse_args()

    dest = args.dest or os.path.join(store_root(), ".repo")
    legacy = os.path.join(os.path.dirname(os.path.abspath(dest))
                          if args.dest else store_root(), "repo")
    prev = ""

    if not os.path.isdir(os.path.join(dest, ".git")):
        if os.path.isdir(os.path.join(legacy, ".git")):
            if not url_eq(origin_url(legacy), args.url):
                sys.stderr.write(
                    f"legacy {legacy} origin '{origin_url(legacy)}' != "
                    f"requested '{args.url}'; refusing to adopt.\n")
                raise SystemExit(3)
            shutil.move(legacy, dest)
            print(f"adopted legacy clone: {legacy} -> {dest}")
        else:
            os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
            print(f"cloning (blobless) {args.url} -> {dest}")
            git(["clone", "--filter=blob:none", args.url, dest])
    else:
        if not url_eq(origin_url(dest), args.url):
            sys.stderr.write(
                f"{dest} origin '{origin_url(dest)}' != requested "
                f"'{args.url}'; refusing to re-point an existing cache.\n")
            raise SystemExit(3)
        prev = git(["-C", dest, "rev-parse", "HEAD"], check=False)

    # refresh first (requirement: cache up to date before work; and a fresh
    # ref is usually only known after fetch)
    git(["-C", dest, "fetch", "--prune", "--tags", "origin"])
    if args.ref:
        sha = resolve_ref(dest, args.ref)
        if not sha:
            sys.stderr.write(
                f"ref '{args.ref}' not resolvable in {dest} even after "
                f"fetch; checkout left untouched (pin law).\n")
            raise SystemExit(2)
    else:
        sha = None

    if sha:
        git(["-C", dest, "checkout", "--force", "--detach", sha])
        git(["-C", dest, "clean", "-fdq"], check=False)
    else:
        sha = git(["-C", dest, "rev-parse", "HEAD"])

    ensure_gitignore(dest)
    print(f"DEST={os.path.abspath(dest)} HEAD={sha}"
          + (f" PREV={prev}" if prev and prev != sha else ""))


if __name__ == "__main__":
    main()
