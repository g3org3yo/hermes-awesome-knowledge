# Awesome Knowledge for Hermes Agent

[![ci](https://github.com/g3org3yo/hermes-awesome-knowledge/actions/workflows/ci.yml/badge.svg)](https://github.com/g3org3yo/hermes-awesome-knowledge/actions/workflows/ci.yml)

A self-contained **Awesome Knowledge Base** for [Hermes Agent](https://hermes-agent.nousresearch.com):
24 curated GitHub `awesome-*` lists, cloned as upstream data and parsed deterministically into
SQLite/FTS5, exposed to the agent as three routing tools.

The point is *routing*, not answering: given "python pdf library", the agent gets back **which
repository and which section** to open, plus the exact file, line and GitHub URL — so it reads a
bounded slice of a 5000-line README instead of loading it whole.

```
awesome_search   ranked routes (repo › section) + hits with local path, GitHub URL, score
awesome_section  print one indexed section, bounded by a character budget
awesome_status   repositories, entry counts, last update, per-repo errors
```

Current corpus: **24 lists · 101 indexed documents · 20,937 resources · 3,186 sections**,
rebuilt from scratch in about 4 seconds.

## What it indexes

`awesome`, `awesome-mcp-servers`, `awesome-go`, `awesome-rust`, `awesome-cpp`, `awesome-python`,
`awesome-nodejs`, `awesome-java`, `awesome-selfhosted`, `awesome-scalability`,
`awesome-design-patterns`, `awesome-android-ui`, `awesome-for-beginners`, `awesome-hacking`,
`the-book-of-secret-knowledge`, `github-cheat-sheet`, `build-your-own-x`, `awesome-llm-apps`,
`awesome-malware-analysis`, `awesome-web-security`, `awesome-threat-intelligence`,
`awesome-public-datasets`, `awesome-software-architecture`, `awesome-algorithms`.

The full list with ids, URLs, domains and licenses is in `manifest/repositories.json` and
`THIRD_PARTY_NOTICES.md`.

## Why it is not just a search box

| Property | How it is achieved |
|---|---|
| Deterministic | Pure stdlib Python, per-file content hashing, no embeddings and no LLM in the build or update path |
| Reproducible | `manifest/repositories.json` pins every upstream URL; `manifest/sync.json` records the exact SHA of each clone |
| Fast | Full rebuild of ~21k entries / ~3.2k sections takes seconds; incremental update re-parses only changed files |
| Honest | Failures are isolated per repository and surfaced in `update_status.json`; one broken upstream never blocks the rest |
| Non-destructive | Existing clones are only fast-forwarded. A diverged clone is reported and skipped, never reset |
| Portable | No absolute path is committed; `config.json` is generated per machine from the manifest |
| Licensed | Upstream license notices are generated into `THIRD_PARTY_NOTICES.md`; raw repos stay out of git |

## Install

```bash
git clone https://github.com/g3org3yo/hermes-awesome-knowledge
cd hermes-awesome-knowledge
python scripts/bootstrap.py          # clone upstreams, write config.json, rebuild index, selftest
```

`bootstrap.py` keeps the upstream clones in the platform cache directory
(`LOCALAPPDATA/hermes-awesome-knowledge/raw` on Windows, `~/.cache/hermes-awesome-knowledge/raw`
on Linux, `~/Library/Caches/hermes-awesome-knowledge/raw` on macOS) so the repository stays small
and `hermes plugins validate` does not scan hundreds of megabytes of third-party markdown. Pass
`--raw-root <dir>` to put them elsewhere, or `--raw-root data/raw` for a fully self-contained tree.

Then enable the plugin:

```bash
hermes plugins install g3org3yo/hermes-awesome-knowledge --enable
```

The repository is not in the Hermes catalog, so the install-time scan reaches a caution verdict
(the plugin shells out to `git`) and asks for `--force` after you review it.

For a local checkout, copy or symlink the directory into your Hermes plugins folder and run
`hermes plugins enable awesome_knowledge`. Nothing else needs configuring: the plugin resolves
its knowledge base to its own directory and honours `AWESOME_KB_HOME` when you keep the base
somewhere else.

Requirements: Python 3.10+ (stdlib only), `git` on `PATH`. No API keys, no network at query time.

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
plugin.yaml                  Hermes plugin manifest (3 tools)
__init__.py                  thin adapter: tools -> engine, with safe "not provisioned" errors
bin/awesome.py               the engine: parse, index, search, section, status, update, rebuild, selftest
bin/enrich.py                optional LLM enrichment (never required)
aliases.json                 deterministic query aliases (loaded from the KB root by the engine)
manifest/repositories.json   the canonical source list (24 entries, portable {{RAW_ROOT}} paths)
manifest/licenses.json       upstream license snapshot used to build THIRD_PARTY_NOTICES.md
scripts/bootstrap.py         provision + configure + index + selftest
scripts/update.py            deterministic incremental update
scripts/check_manifest.py    manifest/license integrity gate (also used by CI)
scripts/make_notices.py      regenerate THIRD_PARTY_NOTICES.md from manifest/licenses.json
tests/test_plugin_adapter.py adapter contract: registration, schemas, failure messages
tests/test_retrieval.py      retrieval regression tests (stdlib unittest, read-only)
docs/INSTALL.md              install, wiring, scheduling, troubleshooting
docs/ARCHITECTURE.md         design decisions: data vs. code, what is committed and what is not
```

Generated at bootstrap time and gitignored: `config.json`, `index.db`, `INDEX.md`, `registry.json`,
`topics.json`, `update_status.json`, `logs/`, `manifest/sync.json`.

## Tests

```bash
python scripts/check_manifest.py     # manifest, licenses, notices, plugin.yaml consistency
python tests/test_plugin_adapter.py  # registration + failure paths (no KB needed)
python tests/test_retrieval.py       # routing/section regressions (needs a built index)
python bin/awesome.py selftest       # 25 routing assertions against the live index
```

The retrieval tests skip themselves when the knowledge base has not been provisioned, so a fresh
clone always reports a green (or skipped) suite instead of a fake failure.

## Adding a repository

1. Append an entry to `manifest/repositories.json` (`id`, `dir`, `url`, `domain`, `language`,
   `description`, `seed_keywords`, `source_type`, `tags`, and `path` = `{{RAW_ROOT}}/<dir>`).
2. Add its license to `manifest/licenses.json` and regenerate notices with
   `python scripts/make_notices.py`.
3. `python scripts/check_manifest.py` must pass.
4. `python scripts/bootstrap.py --only <id>` then `python scripts/update.py --full`.

## License

MIT for the code in this repository. Upstream list content remains under its own license and is
**not** redistributed here — it is cloned on the user's machine at bootstrap time. See
`THIRD_PARTY_NOTICES.md` for the per-source licenses, including the source that ships no license
file and is therefore indexed locally but never redistributable.
