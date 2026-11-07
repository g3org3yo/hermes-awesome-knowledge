# Architecture

## The shape of the thing

```
                 manifest/repositories.json          (pinned: id, dir, url, domain, keywords)
                              |
                              v
   upstream GitHub lists  ---->  data/raw/<dir>/      (cloned data, gitignored)
        (14 repos)                |
                                  v   bin/awesome.py: parse -> hash -> index
                             index.db (SQLite + FTS5: entries, sections, files, hashes)
                                  |
                                  v   __init__.py: thin adapter
                     awesome_search / awesome_section / awesome_status
```

Three layers, one owner each: **data provisioning** (`scripts/bootstrap.py`), **indexing and
retrieval** (`bin/awesome.py`), **agent surface** (`__init__.py`). The engine owns all knowledge
of the schema; the plugin never re-implements a query.

## Decisions

**A. Upstream repos: fetched data, not submodules.**
Only one or two files per list matter (`README.md` plus a couple of docs), and the useful unit is
"the current upstream content", not a pinned commit. Submodules would pin SHAs into the parent
history (constant version churn), complicate licensing, and force a recursive clone of ~14
histories to get 14 markdown files. `manifest/repositories.json` holds the pins instead, and
`manifest/sync.json` records the SHA each clone actually sits on — reproducible without coupling.

**B. Raw repositories are not committed.**
They are third-party, large, and mostly irrelevant (`assets/`, `.github/`). `.gitignore` excludes
`data/`. A clone downloads only the default branch at depth 1 (~1–10 MB per list).

**C. The generated SQLite/FTS5 database is not committed.**
It is a pure function of (data, engine version) and rebuilds in seconds (~12k entries). Committing
binary artifacts would make every upstream typo a 6 MB diff and guarantee merge conflicts. For
air-gapped installs, publish the DB as a **release asset** (`kb-YYYY.MM.DD.db.zst`) instead of a
git object.

**D. Derived indexes are not stored separately.**
FTS5 tables, file hashes and section line ranges live inside `index.db`. One file = one atomic
swap on rebuild, one backup unit, no partial-index states.

**E. Provisioning is a script, and it is the only way in.**
`scripts/bootstrap.py` clones missing repos, fast-forwards existing ones, renders `config.json`
from `config.example.json`, then calls the engine. It is idempotent: safe on a clean machine, safe
on a warm one.

**F. Incremental update.**
`scripts/update.py` → engine `update`: `git fetch` → compare the recorded content hash of every
tracked file → re-parse only files whose bytes changed → update FTS rows. A full rebuild is ~2 s
for this corpus, so incremental is an optimisation for large corpora and a courtesy to the
network, not a correctness requirement.

**G. Keeping generated files out of git.**
`.gitignore` excludes `data/`, `index.db*`, `registry.json`, `topics.json`, `INDEX.md`,
`update_status.json`, `logs/`, `config.json`. Everything committed is either code, a template, or
small JSON metadata. Repository size stays under a few hundred KB.

**H. Third-party install, end to end.**
`git clone` → `python scripts/bootstrap.py` → `hermes plugins install <owner>/<repo> --enable`.
The bootstrap step is the only thing a user must understand; the plugin directory *is* the
knowledge base (`AWESOME_KB_HOME` defaults to it), so there is no second path to configure.

**I. Licensing and attribution.**
`manifest/licenses.json` snapshots each upstream license file name and family at packaging time;
`THIRD_PARTY_NOTICES.md` is generated from it and shipped in the repo. Clones keep their own
`LICENSE` files on disk. The engine never rewrites upstream content, so what the user reads in
`awesome_section` is byte-identical to upstream.

**J. Versioning.**
Two independent axes, deliberately:
* code — SemVer (`v1.0.0`): engine, plugin, scripts, schema.
* data — CalVer (`kb-2026.11.07`): a snapshot tag whose annotation records every upstream SHA.

A schema change bumps the engine major and makes `rebuild` mandatory; a data refresh only moves
the snapshot tag. `manifest/sync.json` is the machine-readable half of that snapshot.

**K. How an end user updates.**
Code: `hermes plugins update awesome_knowledge` (or `git pull`). Data: `python scripts/update.py`
— deterministic, no LLM, safe to schedule. Both are safe to run in any order; a stale index is
detected by the engine and rebuilt.

## Trust boundary

Security-adjacent lists (`awesome-hacking`, `book-of-secret-knowledge`) are marked
`untrusted_repos` in `config.example.json`. `awesome_search` labels their routes
`REFERENCE-ONLY`, and `awesome_section` returns text as data — the index is a pointer system, never
an instruction source. Commands found there are never executed.

## Failure isolation

The updater records a per-repository outcome (`updated`, `unchanged`, `diverged-skipped`,
`fetch-failed`) and exits non-zero only if something actually failed. A repository with local
commits is reported, not reset; the remaining repositories still update and reindex.
