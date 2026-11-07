# hermes-awesome-knowledge

A self-contained **Awesome Knowledge Base** for [Hermes Agent](https://hermes-agent.nousresearch.com):
fourteen curated GitHub `awesome-*` lists, cloned as upstream data and parsed deterministically
into SQLite/FTS5, exposed to the agent as three routing tools.

The point is *routing*, not answering: given "python pdf library", the agent gets back **which
repository and which section** to open, plus the exact file, line and GitHub URL — so it reads a
bounded slice of a 5000-line README instead of loading it whole.

```
awesome_search   ranked routes (repo › section) + hits with local path, GitHub URL, score
awesome_section  print one indexed section, bounded by a character budget
awesome_status   repositories, entry counts, last update, per-repo errors
```

## Why it is not just a search box

| Property | How it is achieved |
|---|---|
| Deterministic | Pure stdlib Python, per-file content hashing, no embeddings and no LLM in the build or update path |
| Reproducible | `manifest/repositories.json` pins every upstream URL; `manifest/sync.json` records the exact SHA of each clone |
| Fast | Full rebuild of ~12k entries / ~1.4k sections takes seconds; incremental update re-parses only changed files |
| Honest | Failures are isolated per repository and surfaced in `update_status.json`; one broken upstream never blocks the rest |
| Non-destructive | Existing clones are only fast-forwarded. A diverged clone is reported and skipped, never reset |
| Licensed | Upstream MIT/CC notices are generated into `THIRD_PARTY_NOTICES.md`; raw repos stay out of git |

## Install

```bash
git clone https://github.com/<you>/hermes-awesome-knowledge
cd hermes-awesome-knowledge
python scripts/bootstrap.py          # clone upstreams, write config.json, rebuild index, selftest
```

Then point Hermes at the directory:

```bash
hermes plugins install <you>/hermes-awesome-knowledge --enable
# or, for a local checkout:
hermes plugins link --path "$PWD"     # then enable it in Settings → Plugins
```

Set `AWESOME_KB_HOME` to use an installation outside the plugin directory.

Requirements: Python 3.9+ (stdlib only), `git`. No API keys, no network at query time.

## Update

```bash
python scripts/update.py             # incremental: fetch, hash-diff, reindex changed files only
python scripts/update.py --full      # full rebuild with atomic index swap
python scripts/update.py --json      # machine-readable summary for cron/monitoring
```

Exit code 0 means everything is current, 1 means at least one repository reported an error.
The updater needs no LLM; optional LLM enrichment (`bin/enrich.py`) is strictly additive and
never blocks the deterministic path.

Schedule it weekly (Hermes cron, Task Scheduler or systemd timer):

```
0 6 * * 1   cd /path/to/hermes-awesome-knowledge && python scripts/update.py --json
```

## Layout

```
plugin.yaml              Hermes plugin manifest (3 tools)
__init__.py              thin adapter: tools -> engine functions
bin/awesome.py           the engine: parse, index, search, section, status, update, rebuild, selftest
bin/enrich.py            optional LLM enrichment (never required)
aliases.json             deterministic query aliases (loaded from the KB root by the engine)
config.example.json      template; bootstrap.py renders config.json with real paths
manifest/repositories.json   24 upstream repositories (id, dir, url, domain, seed keywords)
manifest/licenses.json       upstream license snapshot used to build THIRD_PARTY_NOTICES.md
scripts/bootstrap.py     provision + configure + index + selftest
scripts/update.py        deterministic incremental update
tests/test_retrieval.py  retrieval regression tests (stdlib unittest, read-only)
docs/ARCHITECTURE.md     design decisions: data vs. code, what is committed and what is not
data/raw/                upstream clones (gitignored)
index.db                 SQLite + FTS5 index (gitignored, rebuilt in seconds)
```

## Tests

```bash
python -m unittest discover -s tests -v
python bin/awesome.py selftest
```

Both are read-only against the built index. `tests/test_retrieval.py` asserts routing precision,
section boundaries, alias expansion and the reference-only trust rule for security lists.

## Adding a repository

1. Append an entry to `manifest/repositories.json` (`id`, `dir`, `url`, `domain`, `language`,
   `description`, `seed_keywords`).
2. Add the same entry to `config.example.json` with `path` = `{{RAW_ROOT}}/<dir>`.
3. Re-run `python scripts/bootstrap.py --only <id>` then `python scripts/update.py --full`.

## License

MIT for the code in this repository. Upstream list content remains under its own license —
see `THIRD_PARTY_NOTICES.md`.
