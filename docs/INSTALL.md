# Install

## Requirements

| Requirement | Notes |
|---|---|
| Python 3.9+ | stdlib only — no `pip install` step exists |
| git | must be on `PATH`; the bootstrap uses it for cloning |
| Hermes Agent | optional, only for the three agent tools |

## 1. Get the code

```bash
git clone https://github.com/<owner>/hermes-awesome-knowledge
cd hermes-awesome-knowledge
```

## 2. Provision and index

```bash
python scripts/bootstrap.py
```

What it does, in order:

1. clones each repository in `manifest/repositories.json` to `data/raw/<dir>` (depth 1);
2. writes `config.json` with absolute `raw_root` / `kb_root` paths;
3. runs `bin/awesome.py rebuild` — full parse into `index.db` (SQLite + FTS5);
4. runs `bin/awesome.py selftest`;
5. writes `manifest/sync.json` with the SHA of every clone.

Options: `--raw-root <dir>` to keep clones elsewhere, `--only id1,id2` for a subset,
`--update` for an incremental pass instead of a rebuild, `--no-selftest`.

## 3. Wire it into Hermes

```bash
# from a published repo
hermes plugins install <owner>/hermes-awesome-knowledge --enable

# or from this local checkout
hermes plugins link --path "$PWD"
hermes plugins enable awesome_knowledge
```

Enable takes effect on the next session. Verify:

```bash
hermes plugins list | grep -A2 awesome_knowledge
```

The plugin resolves its knowledge base to its own directory, so a plugin install is
self-contained. To reuse a base kept elsewhere, set `AWESOME_KB_HOME=/path/to/kb`.

## 4. Keep it current

```bash
python scripts/update.py          # incremental, deterministic, LLM-free
```

Weekly schedule (pick one):

```cron
# Hermes cron
hermes cron add --name awesome-kb --schedule "0 6 * * 1" \
  --command "cd /path/to/hermes-awesome-knowledge && python scripts/update.py --json"
```

```
# systemd timer (Linux)
[Unit]
Description=Awesome KB update
[Service]
Type=oneshot
WorkingDirectory=/opt/hermes-awesome-knowledge
ExecStart=/usr/bin/python3 scripts/update.py --json
```

Windows: Task Scheduler → weekly → `python.exe scripts\update.py --json` with the checkout as
"Start in".

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `missing config: .../config.json` | bootstrap never ran | `python scripts/bootstrap.py` |
| `git is required on PATH` | no git in the environment | install git, or use `--skip-provision` on a machine that already has the clones |
| `diverged-skipped` for a repo | that clone has local commits | inspect it manually; nothing was modified |
| search returns nothing | index not built | `python bin/awesome.py rebuild` |
| plugin loads but no tools | plugin not enabled | `hermes plugins enable awesome_knowledge`, then start a new session |

## Uninstall

Remove the plugin (`hermes plugins remove awesome_knowledge`) and delete the directory. There is
no state outside it: no global config, no services, no database elsewhere.
