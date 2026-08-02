# Consider removing nbsphinx (redundant with myst_nb)

**Status:** proposed — deferred (Bill: "not yet"), revisit later
**Priority:** 7
**Difficulty:** 3
**Created:** 2026-08-02

## Why

`book/docs/conf.py`'s `extensions` list enables **both `nbsphinx` and `myst_nb`**. Both
register `.ipynb` as a source suffix, which normally raises *"source_suffix '.ipynb' is
already registered"*. Today the build tolerates it and **`myst_nb` is the active handler**
(confirmed by the `_build/jupyter_execute/` output). `nbsphinx` is effectively dead weight.

**This is a latent footgun.** The book's notebook cross-references rely on MyST target
syntax (`(label)=`), which only works because myst_nb parses the markdown cells. If a
version bump or import-order change ever let nbsphinx claim `.ipynb`, those markdown cells
would be parsed as CommonMark, every notebook `:ref:` would become an "undefined label",
and the failure would be silent (no `-W` in the book build). Removing nbsphinx makes the
handler unambiguous.

See `tasks/reference/notebook-sphinx-integration.md` for the full mechanism.

## Proposed steps (when picked up)

1. Remove `"nbsphinx"` from the `extensions` list in `book/docs/conf.py`.
2. Check whether `nbsphinx` is still needed anywhere: grep for `nbsphinx`-specific config
   (`nbsphinx_*` keys) or directives; remove any that are now dead. Drop `nbsphinx` from
   `requirements.txt` if nothing else uses it (and reconsider whether the Dockerfile pulls
   it as a distro/pip dep).
3. Rebuild `make html` in the container and verify:
   - all three notebooks (`plot2d`, `framebuffer`, `ndc`) still render with executed output;
   - the notebook `:ref:` links still resolve (grep the build log for `undefined label`,
     and the generated HTML for `id="framebufferlabel"` etc.);
   - no new warnings.
4. If anything regresses, restore nbsphinx and record what nbsphinx was doing that myst_nb
   doesn't.

## Notes

- Low risk, high clarity payoff, but not urgent — the current setup works. Deferred by Bill
  on 2026-08-02.
