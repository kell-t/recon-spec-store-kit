#!/usr/bin/env python3
"""sync_repo.py — manage the store's persistent bare source cache at
<store>/.repo.

Spec: openspec/specs/repo-cache/spec.md (kit). The clone is a CACHE: clone
once (bare + blobless), keep it current with fetch. Every checkout of the
source is a NAMED WORKTREE under `<store>/.repo/wt/<branch>`, named after
the branch of this spec-store it serves (git keeps its own admin in
`.repo/worktrees/`; checkouts live in `.repo/wt/`). Never delete-and-
reclone in normal flow; never edit or commit inside the cache or worktrees.

Corruption recovery is QUARANTINE-FIRST (spec): `sync_repo.py --rebuild
<url>` renames the cache — worktrees included — to
`.repo-corrupt-YYYYMMDD` (never deletes; kept until the owner authorizes
removal), THEN clones fresh. The tool keeps this policy stricter than the
spec's SHOULD: use it only for locally confirmed corruption (git fsck);
authentication or server errors (401/403, rate limit, 5xx) are NEVER
grounds — the failure is upstream, and normal sync touches nothing then.

Usage:
  sync_repo.py <source-url> [--ref <tag|sha|branch>] [--wt NAME]
               [--dest DIR] [--rebuild]

--dest defaults to <store>/.repo (store root auto-detected like the other
kit scripts: from this file's location, override env RECON_STORE).
--dest exists for tool development/testing only — store work always uses
the default path (spec: one active clone per store).
--wt defaults to the store repo's current branch (fallback "main").

Behavior:
  - .repo absent, legacy <store>/repo present (same origin URL) -> rename,
    adopt (adopted caches may stay non-bare; worktrees attach the same
    way), continue as refresh.
  - .repo absent -> `git clone --bare --filter=blob:none`; refspec
    rewritten to mirror refs/remotes/origin/* (bare's default mirror maps
    to refs/heads/* and would leave no origin/* refs to resolve).
  - .repo present (bare or non-bare), same origin URL -> fetch --prune
    --tags; resolve ref strictly (refs/tags/, refs/remotes/origin/, bare
    ref/sha); worktree wt/<name>: `worktree add --detach` if absent, else
    `checkout --force --detach` + `clean -fdq` (cache is disposable).
  - .repo present, DIFFERENT origin URL -> refuse (exit 3), BEFORE any
    quarantine: a wrong-URL --rebuild must never consume a healthy cache.
  - ref unresolvable after fetch -> exit 2, checkout untouched (pin law:
    never silently fall back to a different ref).
  - Ensures the store root .gitignore ignores `.repo/` and `.repo-corrupt-*`.
  - Mid-clone interruption needs no special handling: a clean git clone
    failure removes its directory; a hard-killed partial .git is completed
    by the next run's fetch + forced checkout (verified 2026-11-21).
  - --rebuild quarantines any existing directory at --dest, including a
    husk without git metadata (clone killed before init completed).

Prints machine-readable tail lines for ledger capture:
  DEST=<abs worktree path>  CACHE=<abs cache path>  HEAD=<full sha>
  [PREV=<full sha>]
Exit codes: 0 ok | 2 ref not found | 3 remote mismatch | 4 usage/env error
(usage errors exit 4, never argparse's default 2 — 2 belongs to the pin law).
"""
import argparse
import os
import shutil
import subprocess
import sys
import time


class ArgParser(argparse.ArgumentParser):
    """Usage errors must not exit 2: 2 is reserved for the pin law."""

    def error(self, message):
        self.print_usage(sys.stderr)
        sys.stderr.write(f"{self.prog}: error: {message}\n")
        raise SystemExit(4)


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


def is_cache(d):
    """Bare or non-bare git repository directory."""
    return (os.path.isdir(os.path.join(d, ".git"))
            or (os.path.isfile(os.path.join(d, "HEAD"))
                and os.path.isdir(os.path.join(d, "objects"))))


def origin_url(dest):
    return git(["-C", dest, "remote", "get-url", "origin"], check=False)


def url_eq(a, b):
    norm = lambda u: (u or "").rstrip("/").removesuffix(".git").lower()
    return norm(a) == norm(b)


def store_branch():
    """Current branch of the spec-store repo (names the default worktree)."""
    b = git(["-C", store_root(), "branch", "--show-current"], check=False)
    return b or "main"


def resolve_ref(dest, ref):
    """Strict resolution: tag -> origin/<ref> -> bare ref (full/abbrev sha).
    origin/ is preferred over a possibly-stale local ref (worktrees detach;
    cache refs are read-only). Returns full sha or None."""
    candidates = [f"refs/tags/{ref}", f"refs/remotes/origin/{ref}", ref]
    for c in candidates:
        r = git(["-C", dest, "rev-parse", "--verify", "--quiet",
                 f"{c}^{{commit}}"], check=False)
        if r:
            return r
    return None


def ensure_gitignore(dest):
    """Keep the cache AND recovery artifacts out of git: the cache dir plus
    any .repo-corrupt-* quarantine must never be committed."""
    parent = os.path.dirname(os.path.abspath(dest))
    name = os.path.basename(os.path.abspath(dest))
    gi = os.path.join(parent, ".gitignore")
    need = [f"{name}/", f"{name}-corrupt-*"]
    text = open(gi).read() if os.path.exists(gi) else ""
    have = {l.strip() for l in text.splitlines()}
    missing = [l for l in need if l not in have and f"/{l}" not in have]
    if not missing:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    text += ("\n# Persistent source cache + recovery quarantine"
             " (recon-spec-store-kit cache;\n"
             "# see recon/openspec/specs/repo-cache).\n"
             + "".join(l + "\n" for l in missing))
    with open(gi, "w") as f:
        f.write(text)
    print(f"gitignore: added {missing} to {gi}")


def quarantine(dest, reason):
    """Rename (reversible) BEFORE anything else; never delete — the copy
    outlives recovery by design until the owner authorizes removal."""
    stamp = time.strftime("%Y%m%d")
    q = f"{dest}-corrupt-{stamp}"
    n = 1
    while os.path.exists(q):
        q = f"{dest}-corrupt-{stamp}-{n}"
        n += 1
    shutil.move(dest, q)
    print(f"quarantined ({reason}): {dest} -> {q}"
          f" (kept until owner authorizes deletion)")


def main():
    ap = ArgParser(description="manage the store's persistent bare source"
                               " cache (see module docstring)")
    ap.add_argument("url", help="source repo URL")
    ap.add_argument("--ref", default=None,
                    help="tag|sha|branch to check out (strict; detached)")
    ap.add_argument("--wt", default=None,
                    help="worktree name (default: store's current branch)")
    ap.add_argument("--dest", default=None,
                    help="cache dir (default <store>/.repo;"
                         " dev/testing override only)")
    ap.add_argument("--rebuild", action="store_true",
                    help="recovery: quarantine the existing cache (husks"
                         " included), then clone fresh; auth/server errors"
                         " are never grounds")
    args = ap.parse_args()

    dest = args.dest or os.path.join(store_root(), ".repo")
    legacy = os.path.join(os.path.dirname(os.path.abspath(dest))
                          if args.dest else store_root(), "repo")
    wt = os.path.join(dest, "wt", args.wt or store_branch())

    # Wrong-URL --rebuild is refused BEFORE any quarantine: recovery may
    # never consume a healthy cache on an upstream/parameter problem.
    if args.rebuild and is_cache(dest) \
            and not url_eq(origin_url(dest), args.url):
        sys.stderr.write(
            f"{dest} origin '{origin_url(dest)}' != requested "
            f"'{args.url}'; refusing rebuild of a cache that tracks a "
            f"different source.\n")
        raise SystemExit(3)
    if args.rebuild and os.path.isdir(dest):
        quarantine(dest, "recovery rebuild; contents quarantined as-is")
    elif args.rebuild:
        print("--rebuild: nothing at --dest to quarantine; cloning fresh")

    prev = ""
    if not is_cache(dest):
        if os.path.isdir(os.path.join(legacy, ".git")) and not args.rebuild:
            if not url_eq(origin_url(legacy), args.url):
                sys.stderr.write(
                    f"legacy {legacy} origin '{origin_url(legacy)}' != "
                    f"requested '{args.url}'; refusing to adopt.\n")
                raise SystemExit(3)
            shutil.move(legacy, dest)
            print(f"adopted legacy clone: {legacy} -> {dest}")
        else:
            os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
            print(f"cloning (bare, blobless) {args.url} -> {dest}")
            git(["clone", "--bare", "--filter=blob:none", args.url, dest])
            git(["-C", dest, "config", "remote.origin.fetch",
                 "+refs/heads/*:refs/remotes/origin/*"])
    else:
        if not url_eq(origin_url(dest), args.url):
            sys.stderr.write(
                f"{dest} origin '{origin_url(dest)}' != requested "
                f"'{args.url}'; refusing to re-point an existing cache.\n")
            raise SystemExit(3)

    # refresh first (requirement: cache up to date before work; and a fresh
    # ref is usually only known after fetch)
    git(["-C", dest, "fetch", "--prune", "--tags", "origin"])

    wt_exists = os.path.exists(os.path.join(wt, ".git"))
    if args.ref:
        sha = resolve_ref(dest, args.ref)
        if not sha:
            sys.stderr.write(
                f"ref '{args.ref}' not resolvable in {dest} even after "
                f"fetch; checkout left untouched (pin law).\n")
            raise SystemExit(2)
    elif wt_exists:
        sha = None  # no ref given + worktree exists: leave it where it is
    else:
        sha = resolve_ref(dest, "main") or resolve_ref(dest, "HEAD")
        if not sha:
            sys.stderr.write("no --ref and neither origin HEAD nor "
                             "'main' resolves in the cache.\n")
            raise SystemExit(2)

    if wt_exists:
        prev = git(["-C", wt, "rev-parse", "--verify", "--quiet", "HEAD"],
                   check=False)  # empty on unborn HEAD (aborted state)
        if sha:
            git(["-C", wt, "checkout", "--force", "--detach", sha])
            git(["-C", wt, "clean", "-fdq"], check=False)
        head = sha or prev
    else:
        os.makedirs(os.path.join(dest, "wt"), exist_ok=True)
        git(["-C", dest, "worktree", "add", "--detach", wt, sha])
        head = sha

    ensure_gitignore(dest)
    print(f"DEST={os.path.abspath(wt)} CACHE={os.path.abspath(dest)}"
          f" HEAD={head}" + (f" PREV={prev}" if prev and prev != head else ""))


if __name__ == "__main__":
    main()
