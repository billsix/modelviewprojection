"""For each still-dangling path, find which sibling repo holds that task doc.

Reads ``data/dangling-after-group1.txt``; prints, per path, the sibling repos
that contain it (exact path, else by basename under ``tasks/``) and every
citing line in this repo. Sibling checkouts are looked up next to this repo's
parent directory (``../../<name>`` from the repo root, as mounted in the
sandbox) and passed on the command line, so nothing container-absolute is
baked in.

Usage (from the repo root):
    python3 -I tasks/adhoc/repoint-dangling-task-doc-paths/locate_cross_repo.py \
        <sibling-repo-dir> [<sibling-repo-dir> ...]
"""

import pathlib
import subprocess
import sys

HERE: pathlib.Path = pathlib.Path(__file__).resolve().parent
ROOT: pathlib.Path = HERE.parents[2]


def tracked_tasks(repo: pathlib.Path) -> list[str]:
    """Tracked ``tasks/**.md`` paths of a sibling repo."""
    result: subprocess.CompletedProcess[str] = subprocess.run(
        ["git", "-C", str(repo), "ls-files", "tasks/"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [p for p in result.stdout.splitlines() if p.endswith(".md")]


def main(repos: list[pathlib.Path]) -> None:
    """Print the location report; see the module docstring."""
    listings: dict[str, list[str]] = {r.name: tracked_tasks(r) for r in repos}
    dangling: list[str] = (
        (HERE / "data" / "dangling-after-group1.txt").read_text().split()
    )
    for cited in dangling:
        base: str = pathlib.PurePosixPath(cited).name
        hits: list[str] = []
        for repo_name, paths in listings.items():
            if cited in paths:
                hits.append(f"{repo_name}:{cited} (exact)")
            else:
                hits.extend(
                    f"{repo_name}:{p}"
                    for p in paths
                    if pathlib.PurePosixPath(p).name == base
                )
        print(f"## {cited}")
        print("   found: " + ("; ".join(hits) if hits else "NOWHERE"))
        sites: subprocess.CompletedProcess[str] = subprocess.run(
            ["git", "grep", "-nF", cited, "--", ".",
             ":!tasks/adhoc/repoint-dangling-task-doc-paths",
             ":!tasks/repoint-dangling-task-doc-paths.md"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        for site in sites.stdout.splitlines():
            print("   " + site[:260])


if __name__ == "__main__":
    main([pathlib.Path(arg).resolve() for arg in sys.argv[1:]])
