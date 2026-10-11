#!/usr/bin/env bash
#
# spellcheck.sh -- NON-INTERACTIVE book spellcheck (the Option-A fix, 2026-10-12).
#
# Runs `aspell list` over the book's .rst prose, reusing the curated
# book/docs/mvp_dict.pws, and exits nonzero if any unknown word remains. Unlike the
# old `aspell check` (which opened a curses UI and was a prerequisite of every Sphinx
# target), this needs no TTY -- so `make html`/`docs` builds headless, and spellcheck
# runs as its own step. See tasks/non-interactive-spellcheck.md.
#
# aspell has no reStructuredText mode, so a small sed pre-filter drops the markup that
# is not prose (inline literals ``...``, interpreted-text roles :role:`...`, and the
# directive / option lines beginning with `..` or `:word:`); `--mode=url` skips URLs
# and emails. Every file is checked (so one run reports all the misspellings), and the
# exit status is nonzero if ANY file had an unknown word.
#
# Portable: it cd's to book/docs relative to THIS script, so it runs the same in the
# container or on a host, from any directory.
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$here/../book/docs"

dict=./mvp_dict.pws

strip_markup() {
    sed -E \
        -e 's/``[^`]*``//g' \
        -e 's/:[a-zA-Z0-9_+.-]+:`[^`]*`//g' \
        -e '/^[[:space:]]*\.\./d' \
        -e '/^[[:space:]]*:[a-zA-Z0-9_+.-]+:/d'
}

status=0
report=""
for f in *.rst; do
    words="$(strip_markup < "$f" \
        | aspell --personal="$dict" --lang=en --mode=url list 2>/dev/null \
        | sort -u)"
    if [ -n "$words" ]; then
        status=1
        report="${report}"$'\n'"-- ${f} --"$'\n'"${words}"
    fi
done

if [ "$status" -ne 0 ]; then
    echo "Spellcheck: unknown words (add real project terms to book/docs/mvp_dict.pws):"
    echo "$report"
else
    echo "Spellcheck: clean (no unknown words)."
fi
exit "$status"
