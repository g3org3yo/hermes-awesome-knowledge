#!/usr/bin/env python3
"""Deterministic update for the Awesome Knowledge Base. LLM-free by design.

Delegates to the engine's own `update` (fetch -> per-file hash diff -> incremental reindex ->
report), then surfaces a machine-readable summary. One broken upstream repository never stops
the others: the engine isolates failures per repository and records them in update_status.json.

    python scripts/update.py              # incremental
    python scripts/update.py --full       # full rebuild (atomic swap)
    python scripts/update.py --json       # machine-readable summary only

Exit codes: 0 = everything current/updated, 1 = at least one repository reported an error,
2 = prerequisites missing (no config.json or no index).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "bin" / "awesome.py"
CONFIG = ROOT / "config.json"
STATUS = ROOT / "update_status.json"


def engine(command: str) -> int:
    return subprocess.run(
        [sys.executable, str(ENGINE), command],
        cwd=str(ROOT),
        text=True,
        encoding="utf-8",
        errors="replace",
    ).returncode


def main() -> int:
    ap = argparse.ArgumentParser(description="Update the Awesome Knowledge Base index.")
    ap.add_argument("--full", action="store_true", help="Full rebuild instead of incremental")
    ap.add_argument("--json", action="store_true", help="Print only the JSON summary")
    args = ap.parse_args()

    if not CONFIG.exists():
        print("error: missing config.json - run scripts/bootstrap.py first", file=sys.stderr)
        return 2

    code = engine("rebuild" if args.full else "update")

    summary: dict = {"command": "rebuild" if args.full else "update", "engine_exit": code}
    if STATUS.exists():
        try:
            status = json.loads(STATUS.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            status = {}
        errors = status.get("errors") or []
        summary.update(
            run_at=status.get("run_at"),
            repositories_checked=status.get("checked"),
            updated=status.get("updated"),
            unchanged=status.get("unchanged"),
            files_reindexed=status.get("files_reindexed"),
            entries=status.get("entries"),
            entries_net=status.get("entries_net"),
            duration_seconds=status.get("duration_s"),
            errors=errors,
        )
        summary["ok"] = code == 0 and not errors
    else:
        summary["ok"] = False
        summary["errors"] = ["update_status.json not written"]

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"update: {'ok' if summary.get('ok') else 'FAILED'}  ({summary.get('run_at')})")
        print(f"  repositories checked : {summary.get('repositories_checked')}")
        print(f"  updated / unchanged  : {summary.get('updated')} / {summary.get('unchanged')}")
        print(f"  files reindexed      : {summary.get('files_reindexed')}")
        print(f"  entries              : {summary.get('entries')} (net {summary.get('entries_net')})")
        print(f"  duration             : {summary.get('duration_seconds')}s")
        for err in summary.get("errors") or []:
            print(f"  ! {err}")

    return 0 if summary.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
