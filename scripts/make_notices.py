#!/usr/bin/env python3
"""Generate THIRD_PARTY_NOTICES.md from manifest/licenses.json + manifest/repositories.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
lic = json.loads((ROOT / "manifest" / "licenses.json").read_text(encoding="utf-8"))
repos = {r["id"]: r for r in json.loads(
    (ROOT / "manifest" / "repositories.json").read_text(encoding="utf-8"))["repositories"]}

lines = [
    "# Third-party notices",
    "",
    "This project does not vendor upstream content. `scripts/bootstrap.py` clones the",
    "repositories below as data into `$RAW_ROOT` (gitignored, platform cache directory by default);",
    "each clone keeps its own license file, and the retrieval tools return that content verbatim.",
    "",
    "| Repository | Project | License | License file | Installed as |",
    "|---|---|---|---|---|",
]
for entry in lic["repositories"]:
    meta = repos.get(entry["id"], {})
    name = meta.get("name") or entry["name"]
    lines.append(
        f"| `{entry['id']}` | [{name}]({entry['url']}) | {entry['license']} "
        f"| {('`' + entry['license_file'] + '`') if entry['license_file'] else '—'} "
        f"| `$RAW_ROOT/{entry['dir']}` |"
    )

lines += [
    "",
    "The engine (`bin/awesome.py`), the plugin adapter (`__init__.py`), the provisioning and",
    "update scripts and the tests are original work, licensed MIT (see `LICENSE`).",
    "",
    "List content — README text, link descriptions, section headings — remains under the license",
    "of the respective upstream project. If you redistribute a built index (`index.db`), it",
    "contains derived excerpts of that content; keep this file with it.",
    "",
    "License families were detected from the first lines of each upstream license file; consult",
    "the upstream repository for the authoritative text.",
    "",
]
(ROOT / "THIRD_PARTY_NOTICES.md").write_text("\n".join(lines), encoding="utf-8")
print("wrote THIRD_PARTY_NOTICES.md:", len(lic["repositories"]), "entries")
