# Make the book spellcheck non-interactive (headless-compatible)

**Status:** Option A implemented 2026-10-12 — needs review
**Priority:** 4
**Difficulty:** 3
**Created:** 2026-10-12 (William Emerison Six <billsix@gmail.com>)

## Implemented: Option A (Bill chose A, 2026-10-12)

`tools/spellcheck.sh` — non-interactive `aspell list` over the `.rst` prose, reusing
`book/docs/mvp_dict.pws` verbatim, with the sed markup pre-filter (inline literals,
roles, `..`/`:option:` lines) + `--mode=url`; checks every file, exits nonzero if any
unknown word. `book/docs/Makefile`: the `spellcheck` target now calls the script, and
**`spellcheck` was removed from the `%: Makefile` catch-all**, so the Sphinx build runs
headless. Verified: `make spellcheck` → "clean (no unknown words)", rc 0, no TTY; `make
html` no longer has a spellcheck prereq. The curated dict already covered the prose
(`epix` only appears inside `.. figure::` paths, which the filter strips), so the gate is
clean today without dictionary edits.

**Review/finish items for this piece:**
- Add the real new project terms to `mvp_dict.pws` when prose starts using them (`ePiX`,
  `eepic`, `elaps`, `nanobind`, …) — not needed for the gate today, but good hygiene.
  (Deferred to avoid racing a concurrent interactive `aspell` session on 2026-10-11/12.)
- Decide whether to also add a **top-level** `make spellcheck` (containerized, like the
  standard template's other targets) — belongs with
  `tasks/conform-makefile-dockerfile-to-standard-template.md`.
- If the sed filter proves too blunt on future prose (strips a real word in a directive
  argument), tighten it; it is deliberately conservative now.

---

## Original analysis (options considered)

## BLUF

The book's spellcheck is **interactive** and wired into the build path, so the docs
cannot build headless (CI, a nested sandbox, or any non-TTY run dies with
`aspell: Stdin not a terminal`). Replace it with a **non-interactive** spellcheck that
**reuses the existing `book/docs/mvp_dict.pws` dictionary** (278 custom words), and move
it out of the build catch-all into its own target. There IS a drop-in compatible option
(`aspell list`, same dictionary); two better doc-aware alternatives are below if the
maintainer wants `.rst`-markup awareness. "Done" = `make docs`/`sphinx-build` runs with
no TTY and no prompts, and a separate `make spellcheck` (or `-b spelling`) reports
misspellings and fails on any. Split out of
`tasks/conform-makefile-dockerfile-to-standard-template.md` (step 5) at the maintainer's
request; surfaced during the ePiX figure migration (2026-10-11).

## The problem (what's there now)

`book/docs/Makefile`:
```make
PERSONAL_DICT := ./mvp_dict.pws
spellcheck:
	for file in $(shell ls *.rst); do aspell --personal=$(PERSONAL_DICT) check $$file; done

%: Makefile spellcheck            # <-- every Sphinx target depends on spellcheck
	cd _static/ && make
	@$(SPHINXBUILD) -M $@ ...
```
- **`aspell ... check`** opens the **interactive** curses UI (prompt per unknown word).
  Headless → `Error: Stdin not a terminal` → `make: *** [spellcheck] Error 255`.
- It is a **prerequisite of the catch-all**, so it blocks **every** `make html/latexpdf/epub`.
  In the real `make html` (`podman run -it`) it "works" only by prompting the maintainer
  on every build.
- **The dictionary** `book/docs/mvp_dict.pws` is a standard aspell personal word list
  (`personal_ws-1.1 en 278` header + 278 words). Any replacement must keep using it.

## Options (all non-interactive; each keeps the dictionary)

### Option A — `aspell list` (minimal, fully compatible, no new deps) — RECOMMENDED default
`aspell list` is aspell's non-interactive mode: it reads text on stdin and prints the
unknown words (one per line), using the **same `--personal=mvp_dict.pws`**. Verified
2026-10-12: `aspell --personal=./mvp_dict.pws --lang=en list < ch01.rst` prints the
misspellings and exits 0. Wrap it to fail when the output is non-empty:
```make
.PHONY: spellcheck
spellcheck:                       # NOT a prerequisite of any Sphinx target
	@bad=$$(for f in *.rst; do aspell --personal=$(PERSONAL_DICT) --lang=en list < $$f; done | sort -u); \
	 if [ -n "$$bad" ]; then echo "Unknown words:"; echo "$$bad"; exit 1; fi
```
- **Dictionary:** reused verbatim (same `.pws`), zero conversion.
- **Pro:** no new image packages; one-line conceptual change; compatible.
- **Con (the real catch):** raw `.rst` has no markup filter in aspell (aspell ships
  tex/sgml/html/markdown modes but **no reStructuredText mode**), so directive/role names
  (`figure`, `literalinclude`, `toctree`, `:class:`, `:term:`, `inlinetex`, …) and inline
  code flag as "misspelled". Mitigate by either (a) a small pre-filter that strips RST
  markup before piping to aspell (a sed/`rst2txt` pass), or (b) adding the recurring
  markup tokens to `mvp_dict.pws`. (a) is cleaner; (b) pollutes the dictionary. Without a
  filter this option is noisy.

### Option B — `pyspelling` (doc-aware, standalone, aspell backend)
`pip install pyspelling` (add to `requirements.txt` + the Dockerfile `BUILD_DOCS` block;
not currently in the image). pyspelling wraps **aspell** (or hunspell) with real
**reStructuredText/Sphinx filters**, a YAML config, and a clean non-interactive CI exit
code. Many Sphinx projects use it.
- **Dictionary:** point its aspell backend at a wordlist. Either pass the existing
  `.pws` through aspell's `--personal`, or generate a plain wordlist once
  (`tail -n +2 mvp_dict.pws > wordlist.txt`, dropping only the header line) and reference
  it as `pyspelling`'s `dictionaries:`/`wordlists:`. The 278 words carry over.
- **Pro:** RST-aware (no markup false positives), CI-grade, keeps aspell.
- **Con:** new dep (pyspelling) + a `.spellcheck.yml`.

### Option C — `sphinxcontrib-spelling` (most Sphinx-native)
`pip install sphinxcontrib-spelling` (needs **pyenchant** + the **enchant** C library +
an aspell/hunspell dict; none currently in the image). Adds a Sphinx **`spelling`
builder** — `sphinx-build -b spelling` (a `make spelling`) — that spellchecks *during*
the Sphinx build, so it understands `.rst` natively (no markup false positives) and sees
exactly what the book publishes.
- **Dictionary:** set `spelling_word_list_filename` in `conf.py` to a plain wordlist;
  convert once with `tail -n +2 mvp_dict.pws > spelling_wordlist.txt` (strip the
  `personal_ws-1.1 …` header). Keep both files in sync, or make the `.pws` the source and
  generate the wordlist in the build.
- **Pro:** RST/Sphinx-native, integrates with the existing build, a real `-b spelling`
  target fits the "standard template" `make`-target shape.
- **Con:** heaviest new dependency (enchant C lib + pyenchant + a backend dict).

## Recommendation

- **If keeping it lightweight and dependency-free:** Option A with a small RST pre-filter,
  as a standalone **`make spellcheck`** (removed from the Sphinx catch-all).
- **If the maintainer wants it done "properly" (CI, no false positives):** Option C
  (`sphinxcontrib-spelling`, `sphinx-build -b spelling`) — it's RST-native and matches the
  standard-template `make`-target style; Option B (pyspelling) is the standalone-tool
  equivalent if a Sphinx builder isn't wanted.
- **Either way:** take spellcheck **off** the `%: Makefile spellcheck` catch-all so the
  doc build is non-interactive; run spellcheck as its own target / CI job.

## Notes / open questions

1. **New vocabulary from the ePiX migration needs adding to `mvp_dict.pws`:** `aspell
   list` already flags **`epix`** (and `ePiX`); also likely `eepic`, `elaps`, `nanobind`,
   `Liang`/`Barsky`, etc. Whichever option is chosen, add the real new terms to the
   dictionary (not markup tokens). This was previously hidden because the interactive
   check let the maintainer skip-and-forget them.
2. Confirm whether the per-build interactive prompt was **relied on** (a deliberate
   proof-read gate). If so, keep a `make spellcheck-interactive` (the old `aspell check`)
   alongside the new non-interactive one.
3. Only `aspell` is installed today (verified 2026-10-12: codespell / pyspelling /
   sphinxcontrib-spelling / pyenchant all absent) — Options B and C each add a package to
   the `BUILD_DOCS` layer.
