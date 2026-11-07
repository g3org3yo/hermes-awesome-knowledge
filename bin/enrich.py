#!/usr/bin/env python
"""Optional LLM enrichment for the Awesome Knowledge Base.

Never required. The deterministic index in ``index.db`` stays authoritative; everything
produced here is written to ``enrichment/<repo>.json`` and is only ever *hinted* at by a
human or an agent — it never rewrites registry.json, topics.json or the search index.

Design
    * one JSON object per repository, keyed by the indexed commit -> re-running is a no-op
      until the repository changes (cache by content, not by time)
    * OpenAI-compatible ``/chat/completions`` endpoint, configured in config.json:
          "enrichment": {"enabled": true, "endpoint": "https://.../v1/chat/completions",
                         "model": "...", "api_key_env": "SOME_ENV_VAR",
                         "max_items_per_run": 200, "timeout_s": 120}
    * any failure (no key, no network, HTTP error, malformed JSON) is logged and skipped:
      the knowledge base keeps working exactly as before
    * optional use in retrieval is gated by ``"enrichment": {"use_in_search": true}``

Usage
    python bin/enrich.py                 # enrich every repository that is stale/missing
    python bin/enrich.py --repo awesome-go
    python bin/enrich.py --dry-run       # show what would be sent, call nothing
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.request
from pathlib import Path

KB_ROOT = Path(__file__).resolve().parent.parent
ENRICH_DIR = KB_ROOT / "enrichment"

PROMPT = (
    "You classify entries of a curated 'awesome' list so a retrieval router can send queries "
    "to the right section. Use ONLY the supplied headings and entry names — never invent tools.\n"
    "Reply with a single JSON object, no prose, exactly these keys:\n"
    '{"summary": "<=240 chars, what this repository is and is not", '
    '"keywords": ["<=12 short lowercase topics a user might search"], '
    '"best_for": ["<=5 concrete query intents"], '
    '"section_summaries": {"<exact heading>": "<=120 chars what this section covers"}}\n'
)


def _read_config() -> dict:
    with (KB_ROOT / "config.json").open(encoding="utf-8") as fh:
        return json.load(fh)


def _repo_context(conn: sqlite3.Connection, repo_id: str) -> dict | None:
    row = conn.execute("SELECT * FROM repos WHERE id=?", (repo_id,)).fetchone()
    if not row:
        return None
    sections = conn.execute(
        "SELECT heading, entries FROM sections WHERE repo_id=? AND entries > 0"
        " GROUP BY heading ORDER BY SUM(entries) DESC LIMIT 30", (repo_id,)).fetchall()
    names = [r["name"] for r in conn.execute(
        "SELECT name FROM entries WHERE repo_id=? ORDER BY RANDOM() LIMIT 60", (repo_id,)).fetchall()]
    return {
        "id": repo_id, "name": row["name"], "url": row["url"], "domain": row["domain"],
        "description": row["description"], "commit": row["commit_hash"],
        "entries": row["entries"], "sections": [(s["heading"], s["entries"]) for s in sections],
        "sample_entries": names,
    }


def _call(endpoint: str, model: str, api_key: str, payload: dict, timeout: int) -> str:
    body = json.dumps({
        "model": model,
        "messages": [{"role": "system", "content": PROMPT},
                     {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
        "temperature": 0.1,
        "max_tokens": 900,
    }).encode("utf-8")
    req = urllib.request.Request(endpoint, data=body, method="POST", headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8", "replace"))
    return data["choices"][0]["message"]["content"]


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        text = text[4:] if text.lstrip().lower().startswith("json") else text
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object in model reply")
    return json.loads(text[start:end + 1])


def run_enrichment(cfg: dict, limit: int = 200, repo: str | None = None, dry_run: bool = False) -> int:
    """Enrich stale repositories. Returns the number of repositories enriched."""
    conf = cfg.get("enrichment") or {}
    endpoint = (conf.get("endpoint") or "").strip()
    model = (conf.get("model") or "").strip()
    key_env = conf.get("api_key_env") or ""
    api_key = os.environ.get(key_env, "") if key_env else ""
    timeout = int(conf.get("timeout_s") or 120)
    ENRICH_DIR.mkdir(parents=True, exist_ok=True)

    db = KB_ROOT / "index.db"
    if not db.exists():
        print("enrich: no index.db — run `awesome.py index` first")
        return 0
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    done = 0
    try:
        ids = [r["id"] for r in conn.execute("SELECT id FROM repos ORDER BY id").fetchall()]
        for rid in ids:
            if repo and rid != repo:
                continue
            ctx = _repo_context(conn, rid)
            if not ctx:
                continue
            out = ENRICH_DIR / f"{rid}.json"
            if out.exists():
                try:
                    cached = json.loads(out.read_text(encoding="utf-8"))
                    if cached.get("commit") == ctx["commit"]:
                        continue
                except (OSError, json.JSONDecodeError):
                    pass
            if dry_run:
                print(f"would enrich {rid} ({ctx['entries']} entries, {len(ctx['sections'])} sections)")
                continue
            if not endpoint or not model or not api_key:
                print(f"enrich: skipped {rid} — endpoint/model/api key not configured")
                return done
            try:
                reply = _call(endpoint, model, api_key, ctx, timeout)
                data = _extract_json(reply)
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError,
                    ValueError, KeyError, json.JSONDecodeError) as exc:
                print(f"enrich: {rid} failed ({type(exc).__name__}: {exc}) — continuing")
                continue
            record = {"repo_id": rid, "commit": ctx["commit"], "model": model,
                      "generated_at": __import__("datetime").datetime.now().astimezone()
                      .replace(microsecond=0).isoformat(),
                      "authoritative": False,
                      "note": "LLM-generated hint. Never overrides the deterministic index.",
                      "data": data}
            out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            done += 1
            print(f"enrich: {rid} ok")
            if done >= limit:
                break
    finally:
        conn.close()
    return done


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="optional LLM enrichment for the Awesome KB")
    ap.add_argument("--repo")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    n = run_enrichment(_read_config(), limit=args.limit, repo=args.repo, dry_run=args.dry_run)
    print(f"enriched {n} repository(ies)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
