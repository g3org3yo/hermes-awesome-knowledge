"""Manifest and license integrity checks. Stdlib only, no network, safe in CI.

Fails when the repository would ship something broken or non-portable:
  * duplicate ids or directories, missing url/name/domain
  * absolute paths baked into the manifest (must stay {{RAW_ROOT}}/…)
  * a source with no entry in manifest/licenses.json
  * a source missing from THIRD_PARTY_NOTICES.md
  * plugin.yaml and the manifest disagreeing on the source count

Run:  python scripts/check_manifest.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "manifest" / "repositories.json"
LICENSES = ROOT / "manifest" / "licenses.json"
NOTICES = ROOT / "THIRD_PARTY_NOTICES.md"
PLUGIN_YAML = ROOT / "plugin.yaml"

errors: list[str] = []


def require(cond: bool, msg: str) -> None:
    if not cond:
        errors.append(msg)


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    repos = manifest.get("repositories", [])
    require(bool(repos), "manifest has no repositories")

    ids, dirs = set(), set()
    for repo in repos:
        rid = repo.get("id", "")
        require(bool(rid), "repository without id")
        require(rid not in ids, f"duplicate id: {rid}")
        ids.add(rid)

        d = repo.get("dir") or ""
        require(bool(d), f"{rid}: missing dir")
        require(d not in dirs, f"duplicate dir: {d}")
        dirs.add(d)

        require(repo.get("path") == "{{RAW_ROOT}}/" + d,
                f"{rid}: path must be '{{{{RAW_ROOT}}}}/{d}', got {repo.get('path')!r}")
        require(not re.match(r"^[A-Za-z]:[\\/]", str(repo.get("path", ""))),
                f"{rid}: absolute Windows path in manifest")

        url = repo.get("url", "")
        host = urlparse(url).netloc
        require(host in ("github.com", "www.github.com"), f"{rid}: non-GitHub url {url!r}")
        require(url.rstrip("/").split("/")[-1].lower() == d.lower(),
                f"{rid}: dir {d!r} does not match repository name in {url}")

        for key in ("name", "domain", "description", "language"):
            require(bool(repo.get(key)), f"{rid}: missing {key}")
        require(isinstance(repo.get("tags"), list) and repo["tags"], f"{rid}: missing tags")
        require(bool(repo.get("source_type")), f"{rid}: missing source_type")

    licenses = json.loads(LICENSES.read_text(encoding="utf-8"))
    licensing = licenses.get("repositories", licenses)
    if isinstance(licensing, list):
        licensing = {entry.get("id"): entry for entry in licensing}
    notices = NOTICES.read_text(encoding="utf-8") if NOTICES.exists() else ""
    require(bool(notices), "THIRD_PARTY_NOTICES.md missing")
    for rid in sorted(ids):
        entry = licensing.get(rid)
        require(entry is not None, f"{rid}: no license entry")
        if entry:
            require(bool(entry.get("license")), f"{rid}: empty license value")
        require(rid in notices, f"{rid}: not listed in THIRD_PARTY_NOTICES.md")

    if PLUGIN_YAML.exists():
        yaml_text = PLUGIN_YAML.read_text(encoding="utf-8")
        match = re.search(r"(\d+)\s+curated", yaml_text)
        if match:
            require(int(match.group(1)) == len(repos),
                    f"plugin.yaml advertises {match.group(1)} sources, manifest has {len(repos)}")

    if errors:
        print(f"FAIL: {len(errors)} problem(s)")
        for err in errors:
            print(f"  - {err}")
        return 1
    print(f"OK: {len(repos)} sources, {len(ids)} unique ids/dirs, "
          f"licenses and notices complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
