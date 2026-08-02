# Book config cruft — one bundled cleanup pass

**Status:** DONE 2026-08-02 (items 1–4 applied; item 5 glossary entries
**drafted** — Bill to refine in his voice). `make html` is Bill's final gate.
**Created:** 2026-07-30

## Item 5 (2026-08-02): glossary entries drafted

Replaced the `World Space` / `Modelspace` self-definitions in `glossary.rst`
with draft prose in the course's paddle-scene voice (Modelspace = geometry
relative to an object's own origin; World Space = the shared scene coordinate
system, cross-linked to Modelspace via `:term:`). All words used are common
English or already in `mvp_dict.pws` (`modelspace` etc.), so no dictionary
additions were needed — but the **aspell + `make html` gates are Bill's** to
run, and the wording is a **draft for Bill to refine** (book prose is his
voice).

## Done (2026-08-02)

1. ✅ Deleted the dead `imgmath_*` config from `conf.py` (`sphinx.ext.imgmath`
   isn't in `extensions`; math is mathjax).
2. ✅ Deleted `templates_path = ["_templates"]` from `conf.py` (no `_templates/`
   dir exists).
3. ✅ Removed `sphinx_rtd_theme` from `requirements.txt` (theme is `furo`,
   `html_theme = "furo"` in conf.py).
4. ✅ Renamed the bib key `AbstractAlegbra` → `AbstractAlgebra` in
   `references.bib`, both `:cite:` sites in `ch02.rst`, **and** the stale
   whitelist word in `mvp_dict.pws` (count header unchanged, still 278).

Static verification: `conf.py` compiles, no `imgmath`/`templates_path`/
`sphinx_rtd`/`AbstractAlegbra` left anywhere. **The real gate (`make html`)
is Bill's** (texExpToPng absent in-sandbox).

**Item 5 (glossary placeholders) is NOT done** — needs Bill's prose (see below).

Small, mostly mechanical items found in the 2026-07-30 reference-doc survey
(recorded in `tasks/reference/book-figures-and-images.md` §4). Bundled because
each alone is too small to track.

## Items

1. **Dead imgmath config in `book/docs/conf.py`** (~lines 55-57):
   `imgmath_image_format` / `imgmath_font_size` / `imgmath_latex_preamble`
   are set but `sphinx.ext.imgmath` is not in `extensions` (math goes through
   mathjax + inlinetex). Delete the three lines.
2. **`templates_path = ["_templates"]`** in `conf.py` — no `_templates/`
   directory exists. Delete the line (or create the dir if there's a reason).
3. **`sphinx_rtd_theme` in `requirements.txt`** — the theme is `furo`
   (also pinned there). Remove the rtd line; rebuild the image to confirm
   nothing else imports it.
4. **Misspelled bib key `AbstractAlegbra`** in `book/docs/references.bib` —
   rename to `AbstractAlgebra` **and update every `:cite:` site in the same
   change** (the cite sites currently depend on the misspelling; a lone
   rename breaks them silently in HTML output).
5. **Glossary placeholder entries** in `book/docs/glossary.rst`: `World
   Space` → "World space", `Modelspace` → "Modelspace" (self-definitions).
   **Needs Bill's prose** — the other entries (Frame Buffer, NDC, Screen
   Space, Event Loop) are real definitions to match.

## Gate

`make html` (full in-container build) — items 3–5 all touch build inputs; the
aspell gate will also catch any new words introduced by the glossary prose
(add to `book/docs/mvp_dict.pws` as needed).
