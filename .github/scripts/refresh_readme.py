"""Regenerate the dynamic sections of README.md from the GitHub API.

Updates three things in place:
  1. The repo count inside the "Public Repos" shield badge URL.
  2. The Public Repository Index table (between REPO_TABLE markers).
  3. The "Data refreshed on YYYY-MM-DD" footer (between REFRESH_DATE markers).

Requires the `gh` CLI to be authenticated (GH_TOKEN env var is enough in CI).
"""

from __future__ import annotations

import datetime
import json
import re
import subprocess
from pathlib import Path

USER = "jmlero"
TABLE_LIMIT = 10
README = Path(__file__).resolve().parents[2] / "README.md"


def fetch_repos() -> list[dict]:
    out = subprocess.check_output(
        [
            "gh", "api",
            f"/users/{USER}/repos?per_page=100&type=owner&sort=pushed&direction=desc",
        ],
        text=True,
    )
    repos = json.loads(out)
    return [r for r in repos if r.get("visibility") == "public" and not r.get("private")]


def build_table(repos: list[dict]) -> str:
    rows = [
        "| Repository | Description | Language | Last Update |",
        "| --- | --- | --- | --- |",
    ]
    for r in repos:
        name = r["name"]
        desc = (r.get("description") or "No description set").replace("|", "\\|")
        lang = r.get("language") or "-"
        date = (r.get("pushed_at") or "")[:10]
        rows.append(
            f"| [`{name}`](https://github.com/{USER}/{name}) | {desc} | {lang} | {date} |"
        )
    return "\n".join(rows)


def replace_block(src: str, tag: str, body: str, *, inline: bool = False) -> str:
    sep = "" if inline else "\n"
    pattern = re.compile(
        rf"(<!-- START:{tag} -->)(.*?)(<!-- END:{tag} -->)", re.DOTALL
    )
    return pattern.sub(
        lambda m: f"{m.group(1)}{sep}{body}{sep}{m.group(3)}", src
    )


def main() -> None:
    repos = fetch_repos()
    count = len(repos)
    today = datetime.date.today().isoformat()
    # API already sorts by pushed desc — slice the most recent for the table.
    table = build_table(repos[:TABLE_LIMIT])

    content = README.read_text()
    content = re.sub(r"(Public%20Repos-)\d+(-)", rf"\g<1>{count}\g<2>", content)
    content = replace_block(content, "REPO_TABLE", table)
    content = replace_block(
        content,
        "REFRESH_DATE",
        f"Data refreshed from public GitHub repositories on {today}.",
        inline=True,
    )
    README.write_text(content)


if __name__ == "__main__":
    main()
