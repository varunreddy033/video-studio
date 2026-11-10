"""
publish_public.py  -  copy the public part of this (private) repo to the public repo, as one new commit.

    bin/python tools/publish_public.py            publish (after the private commit is pushed)
    bin/python tools/publish_public.py --dry-run  show what would change, publish nothing

Two repos:
  private  varunreddy033/youtube-pipeline   everything (this folder): code + private notes, scripts, plans
  public   varunreddy033/video-studio       only what's safe to show; its own history, made by this script

How it works:
  1 refuses unless every tracked change is committed and pushed to the private repo (only pushed code goes public)
  2 takes the files of the private HEAD commit, minus the paths in .publicignore
  3 checks them: no secrets/keys, no Tailscale or Gmail addresses, none of the `backticked` values in PRIVATE.md,
    no blocked files (.env, data/, output/, models/, assets/audio/). Any hit = nothing is published
  4 mirrors them into output/public_repo (a clone of the public repo, never inside the private repo's git),
    commits "Sync: <private commit subjects since the last sync>" and pushes
"""

import argparse
import fnmatch
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC_URL = "https://github.com/varunreddy033/video-studio.git"
PUBLIC_DIR = ROOT / "output" / "public_repo"
TRAILER = "Synced-From"

SECRET_RE = re.compile(
    r"RENDER_TOKEN=[0-9a-f]{16,}|FAL_KEY=[A-Za-z0-9:_-]{16,}|PEXELS_API_KEY=[A-Za-z0-9]{16,}|HF_TOKEN=hf_[A-Za-z0-9]{16,}"
    r"|hf_[A-Za-z0-9]{30,}|AIza[0-9A-Za-z_-]{30,}|sk-[A-Za-z0-9_-]{30,}|gh[pousr]_[A-Za-z0-9]{30,}"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----|AKIA[0-9A-Z]{16}|xox[abpr]-[A-Za-z0-9-]{10,}")
PERSONAL_RE = re.compile(r"[A-Za-z0-9-]+\.tail[0-9a-f]{6}\.ts\.net|[A-Za-z0-9._%+-]+@gmail\.com")
BLOCKED_RE = re.compile(r"(^|/)\.env($|\.)(?!example$)|n8n_data_backup|^output/|^models/|^assets/audio/|^data/|users\.json$")


def git(*args, cwd=ROOT, check=True, text=True):
    p = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=text)
    if check and p.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed:\n{p.stderr.strip() if text else p.stderr.decode(errors='replace')}")
    return p.stdout if text else p.stdout


def private_patterns():
    pats = []
    f = ROOT / ".publicignore"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                pats.append(line)
    return pats


def is_private(path: str, pats) -> bool:
    for p in pats:
        if p.endswith("/"):
            if path.startswith(p):
                return True
        elif fnmatch.fnmatchcase(path, p):
            return True
    return False


def forbidden_strings():
    """Every `backticked` value in the '## My setup' section of PRIVATE.md (committed version)."""
    p = subprocess.run(["git", "show", "HEAD:PRIVATE.md"], cwd=ROOT, capture_output=True, text=True)
    if p.returncode != 0:
        return []
    m = re.search(r"^## My setup\s*$(.*?)(?=^## |\Z)", p.stdout, re.M | re.S)
    vals = re.findall(r"`([^`\n]{4,})`", m.group(1)) if m else []
    return sorted({v.strip() for v in vals})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="show what would be published, change nothing")
    a = ap.parse_args()

    # 1 only committed + pushed code goes public
    dirty = [l for l in git("status", "--porcelain").splitlines() if not l.startswith("??")]
    if dirty:
        sys.exit("REFUSED: commit (and push) your changes first; uncommitted:\n  " + "\n  ".join(dirty[:10]))
    head = git("rev-parse", "HEAD").strip()
    git("fetch", "-q", "origin")
    if git("rev-parse", "origin/main").strip() != head and not a.dry_run:
        sys.exit("REFUSED: push the private repo first (git push); HEAD isn't on origin/main yet")

    # 2 the public file list
    pats = private_patterns()
    tree = [l.split("\t", 1) for l in git("ls-tree", "-r", "HEAD").splitlines()]
    files = [(meta.split()[0], meta.split()[2], path) for meta, path in tree]   # (mode, blob, path)
    public = [(m, b, p) for m, b, p in files if not is_private(p, pats)]
    kept_private = [p for _, _, p in files if is_private(p, pats)]

    # 3 leak checks on exactly what would be published
    forbid = forbidden_strings()
    problems = []
    for mode, blob, path in public:
        if BLOCKED_RE.search(path):
            problems.append(f"{path}: this file must never be published")
            continue
        data = git("cat-file", "blob", blob, text=False)
        if b"\0" in data[:8000]:
            continue                                     # binary (images, fonts)
        txt = data.decode("utf-8", errors="replace")
        for rx, what in ((SECRET_RE, "looks like a secret"), (PERSONAL_RE, "personal address")):
            for m in rx.finditer(txt):
                line = txt.count("\n", 0, m.start()) + 1
                problems.append(f"{path}:{line}: {what}: {m.group(0)[:60]}")
        for s in forbid:
            if s in txt:
                line = txt.count("\n", 0, txt.index(s)) + 1
                problems.append(f"{path}:{line}: contains a private value from PRIVATE.md: {s}")
    if problems:
        sys.exit("REFUSED, nothing published. Fix these in the private repo first:\n  " + "\n  ".join(problems))
    print(f"checked {len(public)} public files: no secrets, no personal data, no private values "
          f"({len(forbid)} checked from PRIVATE.md); {len(kept_private)} files stay private")

    # 4 mirror into the public clone
    if not (PUBLIC_DIR / ".git").exists():
        PUBLIC_DIR.parent.mkdir(parents=True, exist_ok=True)
        p = subprocess.run(["git", "clone", "-q", PUBLIC_URL, str(PUBLIC_DIR)], capture_output=True, text=True)
        if p.returncode != 0:
            sys.exit(f"can't clone the public repo {PUBLIC_URL}:\n{p.stderr.strip()}")
    pub = lambda *args, **kw: git(*args, cwd=PUBLIC_DIR, **kw)  # noqa: E731
    has_commits = subprocess.run(["git", "rev-parse", "HEAD"], cwd=PUBLIC_DIR, capture_output=True).returncode == 0
    if has_commits:
        pub("fetch", "-q", "origin")
        pub("reset", "-q", "--hard", "origin/main")
    want = {path for _, _, path in public}
    for old in pub("ls-files").splitlines():
        if old not in want:
            (PUBLIC_DIR / old).unlink(missing_ok=True)
    for mode, blob, path in public:
        out = PUBLIC_DIR / path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(git("cat-file", "blob", blob, text=False))
        out.chmod(0o755 if mode == "100755" else 0o644)
    for d in sorted((p for p in PUBLIC_DIR.rglob("*") if p.is_dir() and ".git" not in p.parts), reverse=True):
        if not any(d.iterdir()):
            d.rmdir()
    pub("add", "-A")
    stat = pub("diff", "--cached", "--stat")
    if not stat.strip():
        print("public repo is already up to date; nothing to publish")
        if not a.dry_run:
            return
    print(stat.strip()[-2000:] or "(no changes)")

    # commit message: the private subjects since the last sync
    last = None
    if has_commits:
        m = re.search(rf"^{TRAILER}: ([0-9a-f]{{40}})", pub("log", "-1", "--format=%B"), re.M)
        last = m.group(1) if m else None
    rng = f"{last}..{head}" if last and git("cat-file", "-t", last, check=False).strip() == "commit" else head
    subjects = [s for s in git("log", "--format=%s", rng).splitlines() if s][:20]
    if not has_commits:
        msg = f"Video Studio: first public release\n\n{TRAILER}: {head}\n"
    else:
        msg = ("Sync: " + subjects[0] if len(subjects) == 1 else f"Sync: {len(subjects)} changes") + "\n\n" + \
            "\n".join(f"- {s}" for s in subjects) + f"\n\n{TRAILER}: {head}\n"
    if a.dry_run:
        pub("reset", "-q")
        print("\nDRY RUN, nothing committed. Commit message would be:\n" + msg)
        return
    author = git("log", "-1", "--format=%an <%ae>").strip()
    pub("commit", "-q", "--author", author, "-m", msg)
    pub("push", "-q", "origin", "HEAD:main")
    print(f"published to {PUBLIC_URL.removesuffix('.git')}: {pub('rev-parse', '--short', 'HEAD').strip()} "
          f"(from private {head[:7]})")


if __name__ == "__main__":
    main()
