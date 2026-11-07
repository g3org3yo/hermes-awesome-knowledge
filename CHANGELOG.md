# Changelog

SemVer for the plugin/engine, CalVer for data snapshots (`kb-YYYY.MM.DD` tags).

## 1.1.3 — 2026-11-07

- **Docs:** record the install-time scan behaviour for a repository outside the Hermes catalog
  (`Blocked — community source + caution verdict`, `--force` after review).
- **CI:** green on `main` (integrity + adapter tests on 3.10/3.12, single-source bootstrap smoke).

## 1.1.2 — 2026-11-07

- **Fix:** the adapter test used `__import__("os")` to swap `AWESOME_KB_HOME`, which Hermes's install
  scanner classified as obfuscation and used to block installation (`Decision: BLOCKED`). Plain
  `import os` keeps the test identical and the package clean.

## 1.1.1 — 2026-11-07

Distribution readiness. No change to retrieval behaviour or to the index schema.

- **Fix:** `manifest/repositories.json` had no `dir` field, so `bootstrap.py` raised `KeyError` on a
  clean install. Every entry now carries `dir`, and the manifest uses `{{RAW_ROOT}}/…` paths
  instead of absolute paths from the authoring machine.
- **Fix:** bootstrap renders `config.json` from the manifest. `config.example.json` (stale at 14
  sources) is removed; the manifest is the single source of truth.
- **Fix:** the adapter no longer raises out of a tool handler. Missing config, missing engine,
  missing index and engine `SystemExit` all return `error: …` strings that name the exact command
  to run.
- **Fix:** `tests/test_retrieval.py` skips instead of failing on a fresh clone, and its selftest
  assertion uses the same window (limit 8, routes + top-3) as `bin/awesome.py selftest`.
- **Change:** upstream clones default to the platform cache directory instead of `<repo>/data/raw`,
  so `hermes plugins validate` no longer scans hundreds of megabytes of third-party markdown.
  `--raw-root data/raw` restores the fully self-contained layout.
- **New:** `scripts/check_manifest.py` — manifest, license, notices and `plugin.yaml` consistency
  gate, also run in CI.
- **New:** `tests/test_plugin_adapter.py` — registration, schemas, and the three
  "not provisioned" failure paths, plus the happy path when an index exists.
- **New:** GitHub Actions workflow: compile + integrity + adapter tests on Python 3.10/3.12, and a
  single-source bootstrap smoke test.
- **Docs:** README, `docs/INSTALL.md`, `docs/ARCHITECTURE.md` rewritten for 24 sources, the new
  data layout and a troubleshooting table with the real error strings.

## 1.1.0 — 2026-11-07

- 24 sources (10 new: `sindresorhus/awesome`, `build-your-own-x`, `awesome-llm-apps`,
  `awesome-mcp-servers`, `awesome-malware-analysis`, `awesome-web-security`,
  `awesome-threat-intelligence`, `awesome-public-datasets`, `awesome-software-architecture`,
  `awesome-algorithms`).
- RST parsing (`README.rst` sources), HTML-table row parsing, corrected per-repo file skipping,
  router fixes (max 2 sections per repo, guaranteed slot for the top-3 routed repositories).
- 25 routing assertions in `selftest`, dynamic tool description from live index counts.
- License audit: CC0/CC-BY sources declared in README are recorded; `build-your-own-x` ships no
  license and is indexed locally only, never redistributed.

## 1.0.0 — 2026-11-01

- First standalone release: engine, bootstrap, incremental updater, three plugin tools,
  retrieval tests, license notices.
