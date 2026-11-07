# Install, configure, update, troubleshoot

## Requirements

| Requirement | Notes |
|---|---|
| Python 3.10+ | stdlib only — no `pip install` step exists, no virtualenv needed |
| git | must be on `PATH`; used only during bootstrap and update |
| network | only at bootstrap/update time; queries are fully offline |
| Hermes Agent | optional — needed only for the three agent tools |

Disk: about 800 MB for the clones and 15 MB for the index with all 24 sources. Use
`python scripts/bootstrap.py --only <id>` to start with a subset.

## 1. Get the code

```bash
git clone https://github.com/g3org3yo/hermes-awesome-knowledge
cd hermes-awesome-knowledge
```

## 2. Provision and index

```bash
python scripts/bootstrap.py
```

What it does, in order:

1. clones each repository in `manifest/repositories.json` into the platform cache directory
   (`LOCALAPPDATA/hermes-awesome-knowledge/raw` on Windows, `~/.cache/hermes-awesome-knowledge/raw`
   on Linux and macOS) at depth 1 — never inside the plugin directory;
2. writes `config.json` with absolute `raw_root` / `kb_root` paths for this machine;
3. runs `bin/awesome.py rebuild` — full parse into `index.db` (SQLite + FTS5);
4. runs `bin/awesome.py selftest` (25 routing assertions);
5. writes `manifest/sync.json` with the SHA of every clone.

Options:

| Flag | Meaning |
|---|---|
| `--raw-root <dir>` | keep clones somewhere else; `data/raw` makes the tree self-contained |
| `--kb-home <dir>` | write `config.json` / `index.db` somewhere else (use with `AWESOME_KB_HOME`) |
| `--only id1,id2` | provision a subset |
| `--update` | incremental pass instead of a full rebuild |
| `--skip-provision` | only (re)write the config and the index — clones already present |
| `--no-selftest` | skip the routing assertions |

Bootstrap is idempotent. Re-running it fast-forwards existing clones and reindexes changed files;
a clone with local commits is reported as `diverged-skipped` and never reset.

## 3. Wire it into Hermes

```bash
# published repository
hermes plugins install g3org3yo/hermes-awesome-knowledge --enable

# or a local checkout already inside the plugins directory
hermes plugins enable awesome_knowledge
```

Verify before enabling, without touching the live install:

```bash
hermes plugins validate .     # manifest, registration, security scan
hermes plugins doctor .       # real runtime contracts
```

Enable takes effect on the next session. Then confirm:

```
awesome_status {}                                     # repos, counts, last update
awesome_search {"query": "python pdf library"}        # routes + hits
```

The plugin resolves its knowledge base to its own directory, so a plugin install is
self-contained; `AWESOME_KB_HOME=/path/to/kb` points it at a base kept elsewhere.

## 4. Keep it current

```bash
python scripts/update.py          # incremental, deterministic, LLM-free
python scripts/update.py --full   # full rebuild with atomic swap
```

Weekly schedule (pick one):

```cron
# Hermes cron
hermes cron add --name awesome-kb --schedule "0 6 * * 1" \
  --command "cd /path/to/hermes-awesome-knowledge && python scripts/update.py --json"
```

```ini
# systemd timer (Linux)
[Unit]
Description=Awesome KB update
[Service]
Type=oneshot
WorkingDirectory=/opt/hermes-awesome-knowledge
ExecStart=/usr/bin/python3 scripts/update.py --json
```

Windows: Task Scheduler → weekly → `python.exe scripts\update.py --json`, with the checkout as
"Start in".

Exit code 0 means everything is current; 1 means at least one repository reported an error (the
rest still updated). Details land in `update_status.json`.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| tool returns `error: knowledge base not provisioned — no config.json …` | bootstrap never ran (or `AWESOME_KB_HOME` points elsewhere) | `python scripts/bootstrap.py`, or unset/fix `AWESOME_KB_HOME` |
| tool returns `error: index not built yet — run python bin/awesome.py rebuild` | sources exist, index does not | `python bin/awesome.py rebuild` |
| tool returns `error: index contains no repositories` | empty or half-written index | `python bin/awesome.py rebuild` |
| `git is required on PATH` | no git in the environment | install git, or use `--skip-provision` on a machine that already has the clones |
| `diverged-skipped` for a repo | that clone has local commits | inspect it manually; nothing was modified |
| `hermes plugins validate` reports `security scan — curl_pipe_shell (README.md…)` and similar | the clones were placed **inside** the plugin directory, so the scanner reads third-party markdown | move them out: `python scripts/bootstrap.py --raw-root "$HOME/.cache/hermes-awesome-knowledge/raw"`, then `hermes plugins validate .` again |
| `hermes plugins install` succeeded but no tools appear | plugin installed disabled | `hermes plugins enable awesome_knowledge`, then start a new session |
| search returns nothing for a repo | that repo is not in `config.json` | `python scripts/bootstrap.py --only <id>`, then `python bin/awesome.py rebuild` |
| `badly formed help string` | an old bootstrap copy | use the version from this repository |

Diagnostics that are always safe to run (read-only):

```bash
python scripts/check_manifest.py
python bin/awesome.py status
python bin/awesome.py selftest
python tests/test_plugin_adapter.py
```

## Uninstall

```bash
hermes plugins remove awesome_knowledge
rm -rf <checkout>
rm -rf "$LOCALAPPDATA/hermes-awesome-knowledge"   # clones (Windows)
rm -rf ~/.cache/hermes-awesome-knowledge          # clones (Linux/macOS)
```

There is no state outside those two locations: no global config, no services, no database
elsewhere.
