"""Repoint dangling ``tasks/<slug>.md`` citations at the archived file.

A dangling path is repointed when its basename matches exactly one file under
``tasks/archive/`` and the citation is not preceded by another path component
(so ``runClaudeInContainer/tasks/x.md`` is left alone). Occurrences listed in
``data/keep.txt`` (``file:line:path``, reviewed by hand as citations of another
repo's doc) are left alone too. Idempotent: a second run changes nothing,
because a repointed path no longer dangles.

Usage (from the repo root):
    python3 -I tasks/adhoc/repoint-dangling-task-doc-paths/repoint.py report
    python3 -I tasks/adhoc/repoint-dangling-task-doc-paths/repoint.py apply
"""

import pathlib
import re
import subprocess
import sys

HERE: pathlib.Path = pathlib.Path(__file__).resolve().parent
ROOT: pathlib.Path = HERE.parents[2]
# The task doc and this directory quote dangling paths on purpose.
EXCLUDED: tuple[str, ...] = (
    "tasks/repoint-dangling-task-doc-paths.md",
    "tasks/adhoc/repoint-dangling-task-doc-paths/",
)
PATH_RE: re.Pattern[str] = re.compile(
    r"(?<![A-Za-z0-9_./-])tasks/[A-Za-z0-9_./-]+\.md"
)
OTHER_REPO_RE: re.Pattern[str] = re.compile(
    r"gacalc|geometricalgebra|runClaude|runCrush|sandbox|multivariate|"
    r"spimulator|hanoi|methodfinder|texExp|\.claude",
    re.IGNORECASE,
)


def git_lines(*args: str) -> list[str]:
    """Run git in the repo root and return its stdout lines."""
    out: str = subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout
    return out.splitlines()


def archive_index() -> dict[str, list[str]]:
    """Map each archived task's basename to its archive paths."""
    index: dict[str, list[str]] = {}
    for path in git_lines("ls-files", "tasks/archive/"):
        if path.endswith(".md"):
            index.setdefault(pathlib.PurePosixPath(path).name, []).append(path)
    return index


def load_keep() -> set[str]:
    """The reviewed ``file:line:path`` occurrences to leave unchanged."""
    keep_file: pathlib.Path = HERE / "data" / "keep.txt"
    if not keep_file.exists():
        return set()
    return {
        line.strip()
        for line in keep_file.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    }


def main(mode: str) -> None:
    """Report or apply the repointing; see the module docstring."""
    index: dict[str, list[str]] = archive_index()
    keep: set[str] = load_keep()
    files: list[str] = [
        f
        for f in git_lines("grep", "-lE", r"tasks/[A-Za-z0-9_./-]+\.md")
        if not f.startswith(EXCLUDED)
    ]
    changed_files: int = 0
    changed_sites: int = 0
    for name in files:
        path: pathlib.Path = ROOT / name
        lines: list[str] = path.read_text().splitlines(keepends=True)
        new_lines: list[str] = []
        for number, line in enumerate(lines, start=1):

            def swap(match: re.Match[str]) -> str:
                nonlocal changed_sites
                cited: str = match.group(0)
                if (ROOT / cited).exists():
                    return cited
                targets: list[str] = index.get(
                    pathlib.PurePosixPath(cited).name, []
                )
                site: str = f"{name}:{number}:{cited}"
                match len(targets):
                    case 1 if site not in keep:
                        flag: str = (
                            "  OTHER-REPO?" if OTHER_REPO_RE.search(line) else ""
                        )
                        print(f"{site} -> {targets[0]}{flag}")
                        changed_sites += 1
                        return targets[0]
                    case _:
                        return cited

            new_lines.append(PATH_RE.sub(swap, line))
        if new_lines != lines:
            changed_files += 1
            if mode == "apply":
                path.write_text("".join(new_lines))
    print(f"{mode}: {changed_sites} sites in {changed_files} files")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "report")
