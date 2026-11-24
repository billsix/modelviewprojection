#!/usr/bin/env bash
#
# Copy a repository's history into another repository with some paths left out.
#
#     copy_history_without_paths.sh SOURCE_REPO DEST_REPO PATH...
#
# SOURCE_REPO and DEST_REPO are git repositories (DEST_REPO may be a fresh `git init` with no commits). Each PATH is a
# repo-relative file or directory, or `glob:PATTERN` for a glob (`glob:tools/ctc_*`); every one is left out of EVERY
# commit. SOURCE_REPO is never touched: the work happens in a scratch `git clone --no-local`, and the result is fetched
# into DEST_REPO. Only the branch BRANCH (default: the branch SOURCE_REPO has checked out) and the tags on its history are
# copied. Commits that touched only left-out paths stay as empty commits (KEEP_EMPTY=0 drops them instead), so the copy has
# the same number of commits as the source.
#
# Writes the map "old hash, new hash" (one pair per line) to COMMIT_MAP_OUT (default: DEST_REPO.commit-map, beside
# DEST_REPO), for tools/verify_history_copy.py and for repointing hashes cited in documents.
#
# Needs git-filter-repo. Idempotent: the same inputs give the same hashes.
set -uo pipefail

usage() { echo "usage: $0 SOURCE_REPO DEST_REPO PATH..." >&2; exit 2; }
[ "$#" -ge 3 ] || usage
source_repo="$(cd "$1" && pwd)"
dest_repo="$(cd "$2" && pwd)"
shift 2
branch="${BRANCH:-$(git -C "$source_repo" symbolic-ref --short HEAD)}"
map_out="${COMMIT_MAP_OUT:-$dest_repo.commit-map}"

filters=()
for path in "$@"; do
    case "$path" in
        glob:*) filters+=(--path-glob "${path#glob:}") ;;
        *) filters+=(--path "$path") ;;
    esac
done
prune=never
[ "${KEEP_EMPTY:-1}" = 0 ] && prune=always

scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT
git clone --quiet --no-local --single-branch --branch "$branch" "$source_repo" "$scratch/work" || exit 1
git -C "$scratch/work" filter-repo --force --invert-paths "${filters[@]}" \
    --prune-empty "$prune" --prune-degenerate never >/dev/null 2>&1 || { echo "filter-repo failed" >&2; exit 1; }
cp "$scratch/work/.git/filter-repo/commit-map" "$map_out.raw"
# Drop the header line; keep every pair, including commits that map to the null hash when KEEP_EMPTY=0.
tail -n +2 "$map_out.raw" > "$map_out" && rm -f "$map_out.raw"

git -C "$dest_repo" fetch --quiet "$scratch/work" "+refs/heads/$branch:refs/remotes/source/$branch" \
    "+refs/tags/*:refs/tags/*" || exit 1
git -C "$dest_repo" checkout --quiet -B "$branch" "refs/remotes/source/$branch" || exit 1
git -C "$dest_repo" update-ref -d "refs/remotes/source/$branch"
echo "copied $(git -C "$dest_repo" rev-list --count "$branch") commits of $branch to $dest_repo; map: $map_out"
