# Book config cruft — one bundled cleanup pass

**Status:** not started
**Created:** 2026-07-30

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
