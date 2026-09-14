#!/usr/bin/env python3
"""
pushit - build + push a SINGLE file to GitHub in one command.

By default it works on the most recently changed file in the repo:
  pushit "my message"        build + commit + push just the latest file
  pushit -m "message"        same, message from flag
  pushit -f day3.c "msg"     push a specific file instead
  pushit --all -m "msg"      push ALL changed files at once
  pushit --no-build          skip the build step
  pushit --no-run            don't run the program / show its output
  pushit --public            create the GitHub repo as public (default: private)
"""

import argparse
import glob
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

GITIGNORE = """\
# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
env/
*.egg-info/
dist/
build/

# C / C++
*.o
*.a
*.so
*.exe
*.out

# OS / editors
.DS_Store
"""

SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "dist", "build", "node_modules"}

try:
    sys.stdout.reconfigure(line_buffering=True)
except AttributeError:
    pass


def run(cmd, cwd=None):
    return subprocess.run(cmd, shell=True, text=True, capture_output=True, cwd=cwd)


def info(msg):
    print(f"[..] {msg}")


def ok(msg):
    print(f"[ok] {msg}")


def warn(msg):
    print(f"[!]  {msg}")


def err(msg):
    print(f"[!]  {msg}", file=sys.stderr)
    sys.exit(1)


def find_root(start):
    p = Path(start).resolve()
    for d in (p, *p.parents):
        if (d / ".git").is_dir():
            return d
    return p


def ensure_git(root):
    if not (root / ".git").is_dir():
        if run("git init -b main", cwd=str(root)).returncode != 0:
            err("could not initialize a git repo here")
        ok("initialized git repo")
    branch = run("git symbolic-ref --short HEAD", cwd=str(root)).stdout.strip()
    return branch or "main"


def ensure_gitignore(root):
    if not (root / ".gitignore").exists():
        (root / ".gitignore").write_text(GITIGNORE)
        info("created .gitignore")
        return True
    return False


def changed_files(root):
    status = run("git status --porcelain", cwd=str(root)).stdout
    out = []
    for line in status.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip().strip('"')
        if path.endswith("/"):
            continue
        if path in (".git/",):
            continue
        out.append(path)
    return out


def pick_file(root, explicit=None):
    if explicit:
        p = Path(explicit)
        return root / p if not p.is_absolute() else p

    changed = [c for c in changed_files(root) if c != ".gitignore"]
    if not changed:
        return None

    def mtime(path):
        try:
            return (root / path).stat().st_mtime
        except OSError:
            return 0

    best = max(changed, key=mtime)
    info(f"most recently changed: {best}")
    return root / best


def build_one(root, fp, no_build):
    if no_build:
        info("skipping build (--no-build)")
        return False
    if fp.suffix in (".c", ".cpp"):
        out = fp.with_suffix("")
        cc = shutil.which("gcc") or shutil.which("cc") or "cc"
        info(f"build: {cc} -Wall -Wextra -o {out.name} {fp.name}")
        if run(f"{cc} -Wall -Wextra -o {shlex.quote(str(out))} {shlex.quote(str(fp))}", cwd=str(root)).returncode != 0:
            err(f"compile failed for {fp.name} - fix it before pushing")
        ok("compile succeeded")
        gi = root / ".gitignore"
        if out.name not in gi.read_text(errors="ignore").splitlines():
            with gi.open("a") as f:
                f.write(f"{out.name}\n")
            info(f"added {out.name} to .gitignore")
            return True
    elif fp.suffix == ".py":
        info(f"build: syntax-checking {fp.name}")
        if run(f"python3 -m compileall -q {shlex.quote(str(fp))}", cwd=str(root)).returncode != 0:
            err(f"python syntax check failed in {fp.name} - fix it before pushing")
        ok("python syntax check passed")
    else:
        info(f"no build step for {fp.name}")
    return False


def show_output(root, fp, no_run, timeout=10):
    if no_run:
        info("skipping program output (--no-run)")
        return
    if fp.suffix in (".c", ".cpp"):
        cmd = str(fp.with_suffix(""))
    elif fp.suffix == ".py":
        cmd = "python3 " + shlex.quote(str(fp))
    else:
        return
    try:
        r = subprocess.run(
            cmd, shell=True, text=True, capture_output=True,
            stdin=subprocess.DEVNULL, timeout=timeout, cwd=str(root),
        )
    except subprocess.TimeoutExpired:
        warn(f"program ran longer than {timeout}s - output skipped (use --no-run to suppress)")
        return
    label = fp.with_suffix("").name if fp.suffix in (".c", ".cpp") else fp.name
    print(f"--- output of {label} ---")
    if r.stdout.strip():
        print(r.stdout.rstrip())
    if r.stderr.strip():
        print(r.stderr.rstrip())
    if not r.stdout.strip() and not r.stderr.strip():
        print("(no output)")
    print(f"(exit code {r.returncode})")


def build_all(root, no_build):
    if no_build:
        info("skipping build (--no-build)")
        return False

    has = lambda p: (root / p).exists()
    c_src = sorted(glob.glob(str(root / "*.c")) + glob.glob(str(root / "*.cpp")))
    gi_touched = False

    if has("Makefile"):
        info("build: running make")
        if run("make", cwd=str(root)).returncode != 0:
            err("make failed - fix the build errors before pushing")
        ok("make build succeeded")
    elif has("CMakeLists.txt"):
        info("build: configuring and building with CMake")
        if run("cmake -S . -B build && cmake --build build", cwd=str(root)).returncode != 0:
            err("cmake build failed")
        ok("cmake build succeeded")
    elif has("pyproject.toml") or has("setup.py"):
        is_pkg = has("pyproject.toml") and "build-system" in (root / "pyproject.toml").read_text(errors="ignore")
        if is_pkg:
            info("build: python3 -m build")
            if run("python3 -m build", cwd=str(root)).returncode != 0:
                warn("python build failed; falling back to a syntax check")
                py_syntax_check_all(root)
            else:
                ok("python build succeeded")
        else:
            py_syntax_check_all(root)
    elif c_src:
        cc = shutil.which("gcc") or shutil.which("cc") or "cc"
        info(f"build: compiling each standalone source with {cc}")
        gi = root / ".gitignore"
        gi_text = gi.read_text(errors="ignore")
        for raw in c_src:
            src = Path(raw)
            out = src.with_suffix("")
            cmd = f"{cc} -Wall -Wextra -o {shlex.quote(str(out))} {shlex.quote(str(src))}"
            if run(cmd, cwd=str(root)).returncode != 0:
                err(f"compile failed for {src.name} - fix it before pushing")
            if out.name not in gi_text:
                gi_text += f"{out.name}\n"
                gi_touched = True
        if gi_touched:
            with gi.open("w") as f:
                f.write(gi_text)
            info("updated .gitignore with compiled binaries")
        ok(f"compiled {len(c_src)} source(s)")
    else:
        info("no build tool detected; skipping build")
    return gi_touched


def py_syntax_check_all(root):
    py = []
    for p in root.rglob("*.py"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        py.append(p)
    if not py:
        info("no .py files to check")
        return
    info(f"build: syntax-checking {len(py)} python file(s)")
    cmd = "python3 -m compileall -q " + " ".join(shlex.quote(str(p)) for p in py)
    if run(cmd, cwd=str(root)).returncode != 0:
        err("python syntax check failed - fix the error before pushing")
    ok("python syntax check passed")


def commit(root, paths, message):
    if not paths:
        return False

    seen = set()
    unique = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    paths = unique

    for p in paths:
        run(f"git add -- {shlex.quote(str(p))}", cwd=str(root))

    if not message:
        message = input("Commit message (or press Enter for auto): ").strip()
    if not message:
        message = f"auto-commit: {len(paths)} file(s)"

    if run(f"git commit -m {shlex.quote(message)}", cwd=str(root)).returncode != 0:
        err("commit failed")
    ok(f"committed: {message}")
    return True


def ensure_remote(root, repo_name, public):
    auth = run("gh auth status")
    if auth.returncode != 0:
        err("not logged into GitHub - run  gh auth login  first, then retry")

    remotes = run("git remote", cwd=str(root)).stdout.split()
    if "origin" in remotes:
        return False

    vis = "--public" if public else "--private"
    info(f"creating GitHub repo '{repo_name}' ({'public' if public else 'private'})")
    cmd = f"gh repo create {shlex.quote(repo_name)} {vis} --source . --remote origin --push"
    r = run(cmd, cwd=str(root))
    if r.returncode != 0:
        err(f"could not create repo on GitHub:\n{r.stderr.strip()}")

    url = run("git remote get-url origin", cwd=str(root)).stdout.strip()
    ok(f"pushed to {url}")
    return True


def push(root, branch):
    r = run(f"git push -u origin {branch}", cwd=str(root))
    if r.returncode != 0:
        warn("first push attempt failed; retrying...")
        r = run(f"git push -u origin {branch}", cwd=str(root))
    if r.returncode != 0:
        err(f"git push failed:\n{r.stderr.strip()}")
    ok(f"pushed to origin/{branch}")


def main():
    ap = argparse.ArgumentParser(
        description="Build + push a single file to GitHub.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("message", nargs="?", default=None, help="commit message (otherwise prompted)")
    ap.add_argument("-m", "--message", dest="flag_message", default=None, help="commit message from flag")
    ap.add_argument("-f", "--file", dest="file", default=None, help="file to push instead of the most recently changed one")
    ap.add_argument("--all", action="store_true", help="commit all changed files instead of one")
    ap.add_argument("--no-build", action="store_true", help="skip the build step")
    ap.add_argument("--no-run", action="store_true", help="skip running the program / showing its output (10s timeout)")
    ap.add_argument("--public", action="store_true", help="create repo as public (default: private)")
    args = ap.parse_args()

    root = find_root(Path.cwd())
    info(f"root: {root}")

    gi_touched = ensure_gitignore(root)
    branch = ensure_git(root)

    message = args.flag_message or args.message

    if args.all:
        gi_touched = build_all(root, args.no_build) or gi_touched
        paths = changed_files(root)
        committed = commit(root, paths, message)
    else:
        fp = pick_file(root, args.file)
        if fp is None:
            info("no changes to push")
            committed = False
        else:
            gi_touched = build_one(root, fp, args.no_build) or gi_touched
            show_output(root, fp, args.no_run)
            paths = [str(fp.relative_to(root))]
            if gi_touched:
                paths.append(".gitignore")
            if fp.name == ".gitignore":
                paths = [".gitignore"]
            committed = commit(root, paths, message)

    repo_name = root.name.strip().replace(" ", "-")
    ensure_remote(root, repo_name, args.public)
    push(root, branch)
    print("Done.")


if __name__ == "__main__":
    main()