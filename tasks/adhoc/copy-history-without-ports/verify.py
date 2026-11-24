"""Prove that a history copy is the source history minus the left-out paths.

    verify_history_copy.py SOURCE_REPO DEST_REPO COMMIT_MAP PATH...

``COMMIT_MAP`` is the file ``copy_history_without_paths.sh`` writes (one
``old new`` hash pair per line); each ``PATH`` is a repo-relative path or
``glob:PATTERN``, exactly as given to the copy. For every pair the check is:

* the new commit's tree equals the old commit's tree minus the left-out paths
  (same path, mode and blob), so nothing ported remains and nothing else moved;
* author and committer name, email and date are equal;
* the new commit's parents are the mapped old parents;
and for the whole copy: equal commit counts, and every tag points at the
mapped commit. Commit messages are compared too, but filter-repo rewrites old
hashes quoted in a message, so a difference there is only counted and reported.

SOURCE_REPO and DEST_REPO are only read. Exits 0 when every check holds.
"""

import fnmatch
import pathlib
import subprocess
import sys

TreeEntries = dict[str, tuple[str, str]]


def git(repo: pathlib.Path, *args: str) -> str:
    """Run ``git -C repo args`` and return its standard output.

    Args:
        repo: The repository directory.
        *args: The git arguments.

    Returns:
        The decoded standard output.
    """
    result: subprocess.CompletedProcess[str] = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        errors="surrogateescape",
    )
    return result.stdout


def is_left_out(path: str, patterns: list[str]) -> bool:
    """Say whether ``path`` is covered by one of the left-out patterns.

    Args:
        path: A repo-relative file path.
        patterns: ``PATH`` or ``glob:PATTERN`` arguments.

    Returns:
        True when the copy must not contain the path.
    """
    for pattern in patterns:
        if pattern.startswith("glob:"):
            if fnmatch.fnmatchcase(path, pattern[len("glob:") :]):
                return True
        elif path == pattern.rstrip("/") or path.startswith(
            pattern.rstrip("/") + "/"
        ):
            return True
    return False


def tree_entries(repo: pathlib.Path, commit: str) -> TreeEntries:
    """Read every file of a commit's tree as ``path -> (mode, blob)``.

    Args:
        repo: The repository directory.
        commit: The commit hash.

    Returns:
        The tree entries.
    """
    entries: TreeEntries = {}
    listing: str = git(repo, "ls-tree", "-r", "-z", commit)
    for record in listing.split("\0"):
        if not record:
            continue
        meta: str
        path: str
        meta, path = record.split("\t", 1)
        mode: str
        blob: str
        mode, _kind, blob = meta.split(" ")
        entries[path] = (mode, blob)
    return entries


def commit_facts(repo: pathlib.Path, commit: str) -> tuple[str, ...]:
    """Read author, committer and parents of one commit.

    Args:
        repo: The repository directory.
        commit: The commit hash.

    Returns:
        Author name, email and date, committer name, email and date, then
        the parent hashes joined by spaces.
    """
    fields: str = git(
        repo, "show", "-s", "--format=%an%x00%ae%x00%ad%x00%cn%x00%ce%x00%cd%x00%P", "--date=raw", commit
    ).rstrip("\n")
    return tuple(fields.split("\0"))


def commit_message(repo: pathlib.Path, commit: str) -> str:
    """Read one commit's message.

    Args:
        repo: The repository directory.
        commit: The commit hash.

    Returns:
        The raw message.
    """
    return git(repo, "show", "-s", "--format=%B", commit)


def main(argv: list[str]) -> int:
    """Run every check and print the failures and a summary.

    Args:
        argv: ``SOURCE_REPO DEST_REPO COMMIT_MAP PATH...``.

    Returns:
        0 when every check holds, 1 otherwise.
    """
    if len(argv) < 4:
        print(__doc__)
        return 2
    source: pathlib.Path = pathlib.Path(argv[0])
    dest: pathlib.Path = pathlib.Path(argv[1])
    patterns: list[str] = argv[3:]
    mapping: dict[str, str] = {}
    for line in pathlib.Path(argv[2]).read_text().splitlines():
        old: str
        new: str
        old, new = line.split()
        mapping[old] = new
    failures: list[str] = []
    message_differences: int = 0
    for index, (old, new) in enumerate(mapping.items()):
        expected: TreeEntries = {
            path: entry
            for path, entry in tree_entries(source, old).items()
            if not is_left_out(path, patterns)
        }
        if expected != tree_entries(dest, new):
            failures.append(f"tree differs: {old} -> {new}")
        old_facts: tuple[str, ...] = commit_facts(source, old)
        new_facts: tuple[str, ...] = commit_facts(dest, new)
        if old_facts[:6] != new_facts[:6]:
            failures.append(f"author or committer differs: {old} -> {new}")
        mapped_parents: str = " ".join(
            mapping[parent] for parent in old_facts[6].split() if parent
        )
        if mapped_parents != new_facts[6]:
            failures.append(f"parents differ: {old} -> {new}")
        if commit_message(source, old) != commit_message(dest, new):
            message_differences += 1
        if index % 200 == 0:
            print(f"  checked {index} of {len(mapping)}", flush=True)
    old_count: int = len(mapping)
    new_count: int = int(git(dest, "rev-list", "--all", "--count"))
    if old_count != new_count:
        failures.append(f"commit counts: source {old_count}, copy {new_count}")
    for tag in git(dest, "tag", "--list").split():
        old_target: str = git(source, "rev-parse", f"{tag}^{{commit}}").strip()
        new_target: str = git(dest, "rev-parse", f"{tag}^{{commit}}").strip()
        if mapping.get(old_target) != new_target:
            failures.append(f"tag {tag} points at the wrong commit")
    for failure in failures[:20]:
        print("FAIL", failure)
    print(
        f"{old_count} commits checked, {len(failures)} failures, "
        f"{message_differences} messages rewritten by filter-repo"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
