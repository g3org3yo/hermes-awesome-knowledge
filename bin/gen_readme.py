#!/usr/bin/env python3
"""Generate F:\\Projects\\Knowledge\\README.md — the navigation page for the Knowledge root.

The table is built from the live manifest + git state, never hand-copied, so it cannot drift
from config.json. Upstream README text is never copied into this page.
"""
from __future__ import annotations

import json
import subprocess
from collections import defaultdict
from pathlib import Path

KB = Path(r"F:/Projects/Hermes/knowledge/awesome")
ROOT = Path(r"F:/Projects/Knowledge")
cfg = json.loads((KB / "config.json").read_text(encoding="utf-8"))
def git_state(path: Path) -> dict:
    if not (path / ".git").exists():
        return {}
    def g(*a):
        return subprocess.run(["git", "-C", str(path), *a], capture_output=True, text=True,
                              encoding="utf-8", errors="replace").stdout.strip()
    return {"commit": g("rev-parse", "--short", "HEAD"), "branch": g("rev-parse", "--abbrev-ref", "HEAD")}


state = {r["id"]: {**git_state(Path(r["path"])), "path": r["id"]} for r in cfg["repositories"]}

TYPE_TITLES = {
    "awesome-meta-list": "Meta index",
    "curated-resource-list": "Curated resource lists",
    "learning-tutorials": "Learning & tutorials",
    "implementation-guides": "Implementation guides",
    "project-examples": "Project examples",
    "MCP-catalog": "MCP catalogs",
    "security-resources": "Security",
    "dataset-catalog": "Datasets",
    "software-architecture": "Architecture",
    "algorithms": "Algorithms & data structures",
}


def counts() -> dict:
    import sqlite3
    con = sqlite3.connect(str(KB / "index.db"))
    try:
        entries = con.execute("select count(*) from entries").fetchone()[0]
        sections = con.execute("select count(*) from sections").fetchone()[0]
        repos = con.execute("select count(*) from repos").fetchone()[0]
        per_repo = {r[0]: (r[1], r[2]) for r in con.execute(
            "select repo_id, count(*), count(distinct heading_path) from entries group by repo_id")}
        files = con.execute("select count(*) from files").fetchone()[0]
    finally:
        con.close()
    return {"entries": entries, "sections": sections, "repos": repos, "per_repo": per_repo, "files": files}


tot = counts()
by_type: dict[str, list[dict]] = defaultdict(list)
for r in cfg["repositories"]:
    by_type[r.get("source_type", "curated-resource-list")].append(r)

lines: list[str] = []
add = lines.append

add("# Knowledge")
add("")
add("Local, searchable collection of curated **awesome lists** — 24 upstream repositories kept as")
add("independent Git checkouts, indexed into one SQLite FTS5 database and queried from Hermes.")
add("")
add(f"`{tot['repos']} sources · {tot['entries']:,} entries · {tot['sections']:,} sections · {tot['files']} indexed documents`")
add("")
add("## How it works")
add("")
add("| Piece | Path | Role |")
add("|---|---|---|")
add("| Checkouts | `awesome/<repo>/` (this folder) | One upstream Git checkout per source (depth 1), own README and LICENSE |")
add("| Engine | `F:/Projects/Hermes/knowledge/awesome/bin/awesome.py` | Deterministic parser + indexer + search (no LLM, no network at query time) |")
add("| Manifest | `F:/Projects/Hermes/knowledge/awesome/config.json` | **Canonical source registry** — id, name, url, path, domain, description, seed keywords, source type, tags |")
add("| Generated registry | `F:/Projects/Hermes/knowledge/awesome/registry.json` | Per-repository counters and timestamps, rewritten on every rebuild |")
add("| Query aliases | `F:/Projects/Hermes/knowledge/awesome/aliases.json` | Small vocabulary correction layer (tokens/drop/repo prior) |")
add("| Database | `F:/Projects/Hermes/knowledge/awesome/index.db` | SQLite + FTS5, rebuilt atomically |")
add("| Hermes tool | `plugins/awesome_kb` | `awesome_search`, `awesome_section`, `awesome_status` |")
add("| Automation | `scripts/awesome_kb_weekly.py` | Cron, Monday 06:00 — sync, incremental reindex, report |")
add("")
add("Upstream repositories stay independent checkouts: nothing is flattened, merged or vendored,")
add("and this page never copies their content. `index.db` is derived state — delete it and rebuild.")
add("")
add("## Commands")
add("")
add("```bash")
add("cd F:/Projects/Hermes/knowledge/awesome")
add("python bin/awesome.py status            # last run, counters, per-source health")
add("python bin/awesome.py update            # sync + incremental reindex (what cron runs)")
add("python bin/awesome.py rebuild           # full rebuild with atomic swap")
add("python bin/awesome.py search \"threat intelligence stix taxii\" --limit 10")
add("python bin/awesome.py section awesome-mcp-servers --list")
add("python bin/awesome.py selftest          # 25 routing assertions")
add("python bin/awesome.py add <github-url>  # add a source, clone it, index it")
add("```")
add("")
add("## Sources")
add("")
for stype in sorted(by_type, key=lambda t: (TYPE_TITLES.get(t, t), t)):
    repos = sorted(by_type[stype], key=lambda r: r["name"].lower())
    add(f"### {TYPE_TITLES.get(stype, stype)}")
    add("")
    add("| Source | Type | Tags | Entries | Sections | Commit |")
    add("|---|---|---|---:|---:|---|")
    for r in repos:
        st = state.get(r["id"], {})
        e, s = tot["per_repo"].get(r["id"], (0, 0))
        tags = ", ".join(r.get("tags") or []) or "—"
        commit = f"[`{st.get('commit','?')}`]({r['url']}/commit/{st.get('commit','')})" if st.get("commit") else "—"
        add(f"| [{r['name']}]({r['url']}) <br><sub>`{st.get('path', r['id'])}`</sub> | `{stype}` | {tags} | {e:,} | {s:,} | {commit} |")
    add("")

add("## Adding or updating a source")
add("")
add("1. **Add** — `python bin/awesome.py add https://github.com/<owner>/<repo>` clones into")
add("   `awesome/<repo>` (depth 1, like the rest) and indexes it. Then fill in `source_type`, `tags`")
add("   and a real `description` in `config.json` and rebuild, so routing has signal to work with.")
add("2. **Update** — `python bin/awesome.py update` fast-forwards clean checkouts, leaves dirty or")
add("   diverged ones untouched (reported in `update_status.json`), and reindexes only changed files.")
add("3. **Remove** — delete the entry from `config.json`, then rebuild; the checkout stays until you")
add("   remove it by hand.")
add("")
add("Every source must keep its own upstream `README` and `LICENSE`. Translations")
add("(`README-xx.md`) and community-health files are intentionally not indexed;")
add("`config.json` `exclude_globs` can exclude more per repository.")
add("")
add("## Search tips")
add("")
add("Search is repository-first: the router picks which lists own the query, then ranks entries")
add("inside them. Natural phrases work (`mcp servers for postgres`, `public datasets for machine")
add("learning`); `awesome_section` returns the surrounding source text with line numbers.")
add("")
add("---")
add("")
add(f"Last generated: {tot['repos']} sources indexed, see `python bin/awesome.py status` for timestamps.")
add("")

(ROOT / "README.md").write_text("\n".join(lines), encoding="utf-8")
print(f"README.md written: {len(lines)} lines, {len(cfg['repositories'])} sources, {tot['entries']:,} entries")
