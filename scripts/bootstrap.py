#!/usr/bin/env python3
"""Bootstrap the Awesome Knowledge Base from a clean checkout.

Provisions upstream data, writes config.json, builds the SQLite/FTS5 index and runs the
retrieval self-test. Deterministic and LLM-free: safe to run offline after the first clone,
safe to re-run, and never destructive (existing clones are only fast-forwarded; a diverged
clone is reported and skipped instead of being reset).

    python scripts/bootstrap.py                 # clone/refresh + full rebuild + selftest
    python scripts/bootstrap.py --only awesome-python,github-cheat-sheet
    python scripts/bootstrap.py --update        # incremental update instead of full rebuild
    python scripts/bootstrap.py --raw-root D:/kb-data/raw --no-selftest
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "manifest" / "repositories.json"
ENGINE = ROOT / "bin" / "awesome.py"


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def default_raw_root() -> Path:
    """Clones belong outside the plugin directory.

    Hermes scans a plugin directory when it validates/installs it; a few hundred MB of
    third-party markdown inside that tree trips the security scanner and bloats every
    install. Keep the data in the platform cache directory and override with --raw-root.
    """
    override = os.environ.get("AWESOME_KB_RAW_ROOT")
    if override:
        return Path(override).expanduser()
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
        return base / "hermes-awesome-knowledge" / "raw"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "hermes-awesome-knowledge" / "raw"
    base = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return base / "hermes-awesome-knowledge" / "raw"


def git(args: list[str], cwd: Path | None = None, timeout: int = 1800) -> tuple[int, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "echo"},
    )
    return proc.returncode, ((proc.stdout or "") + (proc.stderr or "")).strip()


def head_sha(repo: Path) -> str | None:
    code, out = git(["-C", str(repo), "rev-parse", "HEAD"], timeout=60)
    return out if code == 0 else None


def provision(repo: dict, raw_root: Path, depth: int, default_branch: str) -> dict:
    """Clone if missing, otherwise fast-forward. Returns a per-repo status record."""
    target = raw_root / repo["dir"]
    # Only pin a branch when the manifest says so: passing --branch main to a repo whose
    # default branch is master (or develop) turns a valid clone into a hard failure.
    branch = repo.get("branch") or None
    record = {"id": repo["id"], "dir": repo["dir"], "url": repo["url"], "path": str(target)}

    if not (target / ".git").exists():
        if target.exists() and any(target.iterdir()):
            record.update(status="skipped", detail="directory exists but is not a git clone")
            return record
        target.parent.mkdir(parents=True, exist_ok=True)
        cmd = ["clone", "--depth", str(depth), "--single-branch"]
        if branch:
            cmd += ["--branch", branch]
        cmd += [repo["url"], str(target)]
        code, out = git(cmd)
        if code != 0:
            # A stale target directory blocks the retry; remove only what we just created.
            if target.exists():
                shutil.rmtree(target, ignore_errors=True)
            record.update(status="clone-failed", detail=out[-400:])
            return record
        # Record the branch actually checked out, so sync.json stays truthful.
        code, cur = git(["-C", str(target), "rev-parse", "--abbrev-ref", "HEAD"], timeout=60)
        record.update(status="cloned", sha=head_sha(target),
                      branch=cur if code == 0 else (branch or default_branch))
        return record

    before = head_sha(target)
    code, out = git(["-C", str(target), "fetch", "--depth", str(depth), "origin"], timeout=900)
    if code != 0:
        record.update(status="fetch-failed", sha=before, detail=out[-400:])
        return record
    code, out = git(["-C", str(target), "merge", "--ff-only", "FETCH_HEAD"], timeout=300)
    after = head_sha(target)
    if code != 0:
        record.update(status="diverged-skipped", sha=after, detail=(
            "existing clone has local commits or changes; left untouched"))
        return record
    code, cur = git(["-C", str(target), "rev-parse", "--abbrev-ref", "HEAD"], timeout=60)
    record.update(status="updated" if before != after else "unchanged", sha=after,
                  branch=cur if code == 0 else (branch or default_branch),
                  previous_sha=before, detail="" if before != after else "already current")
    return record


def load_manifest() -> dict:
    """Read the canonical manifest and fail loudly if it is not portable."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    repos = manifest.get("repositories") or []
    if not repos:
        raise SystemExit(f"error: no repositories in {MANIFEST}")
    missing = [r.get("id") or "?" for r in repos if not (r.get("dir") or r.get("path"))]
    if missing:
        raise SystemExit(f"error: manifest entries without dir/path: {', '.join(missing)}")
    return manifest


def write_config(kb_root: Path, raw_root: Path, depth: int, jobs: int) -> Path:
    """Write config.json from the manifest — the manifest is the only source of truth.

    Paths in the manifest are symbolic (`{{RAW_ROOT}}/…`) so the same file works on any
    machine; this function turns them into the absolute paths the engine expects.
    """
    cfg = load_manifest()
    cfg["raw_root"] = raw_root.as_posix()
    cfg["kb_root"] = kb_root.as_posix()
    cfg["clone"] = {"depth": depth, "parallel": jobs}
    for repo in cfg["repositories"]:
        repo["dir"] = repo.get("dir") or Path(repo["path"]).name
        repo["path"] = (raw_root / repo["dir"]).as_posix()
    blob = json.dumps(cfg, ensure_ascii=False, indent=2)
    if "{{" in blob:
        raise SystemExit("error: unresolved placeholder in generated config (check the manifest)")
    target = kb_root / "config.json"
    target.write_text(blob + "\n", encoding="utf-8")
    return target


def run_engine(command: str) -> int:
    proc = subprocess.run(
        [sys.executable, str(ENGINE), command],
        cwd=str(ROOT),
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode


def main() -> int:
    ap = argparse.ArgumentParser(description="Provision and index the Awesome Knowledge Base.")
    ap.add_argument("--raw-root", default=None,
                    help="Where upstream clones live (default: platform cache dir, e.g. "
                         "LOCALAPPDATA/hermes-awesome-knowledge/raw on Windows; "
                         "pass <repo>/data/raw for a fully self-contained tree)")
    ap.add_argument("--kb-home", default=str(ROOT),
                    help="Where config.json and index.db live (default: repo root)")
    ap.add_argument("--only", default=None, help="Comma-separated repository ids to provision")
    ap.add_argument("--depth", type=int, default=1, help="Clone depth (default 1)")
    ap.add_argument("--jobs", type=int, default=4, help="Parallel clone/fetch jobs (metadata only)")
    ap.add_argument("--update", action="store_true",
                    help="Run incremental update instead of a full rebuild")
    ap.add_argument("--skip-provision", action="store_true",
                    help="Only write config.json and index (data already present)")
    ap.add_argument("--no-selftest", action="store_true", help="Skip the retrieval self-test")
    args = ap.parse_args()

    manifest = load_manifest()
    kb_root = Path(args.kb_home).resolve()
    raw_root = Path(args.raw_root).resolve() if args.raw_root else default_raw_root().resolve()
    try:
        raw_root.relative_to(kb_root)
        print("warn: raw_root is inside the knowledge directory; `hermes plugins validate` scans that "
              "tree, so third-party markdown will be flagged. Prefer the default location.")
    except ValueError:
        pass
    repo_ids = {x.strip() for x in args.only.split(",")} if args.only else None

    if not shutil.which("git"):
        print("error: git is required on PATH", file=sys.stderr)
        return 2

    records = []
    if args.skip_provision:
        print("provision: skipped (--skip-provision)")
    else:
        for repo in manifest["repositories"]:
            if repo_ids and repo["id"] not in repo_ids:
                continue
            rec = provision(repo, raw_root, args.depth, manifest.get("default_branch", "main"))
            records.append(rec)
            print(f"  {rec['status']:<16} {rec['id']}")

    cfg_path = write_config(kb_root, raw_root, args.depth, args.jobs)
    print(f"config: {cfg_path}")

    sync = {
        "generated_at": now(),
        "raw_root": raw_root.as_posix(),
        "kb_root": kb_root.as_posix(),
        "repositories": records,
    }
    try:
        (ROOT / "manifest" / "sync.json").write_text(
            json.dumps(sync, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:  # read-only plugin install: the record is a convenience, not a gate
        print(f"warn: could not write manifest/sync.json ({exc})")

    command = "update" if args.update else "rebuild"
    print(f"index: {command} ...")
    code = run_engine(command)
    if code != 0:
        print(f"error: index command exited {code}", file=sys.stderr)
        return code

    if not args.no_selftest:
        print("selftest: running")
        sel = run_engine("selftest")
        if sel != 0:
            print(f"error: selftest exited {sel}", file=sys.stderr)
            return sel

    failures = [r for r in records if r["status"] in ("clone-failed", "fetch-failed", "diverged-skipped")]
    print(f"done: {len(records) - len(failures)}/{len(records)} repositories provisioned")
    for f in failures:
        print(f"  ! {f['id']}: {f['status']}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
