# Unvendor texExpToPng — build it from a SHA-pinned git clone instead

**Status:** proposed — needs go-ahead
**Created:** 2026-07-08

## Goal

Same scheme multivariate-math adopted 2026-07-08: delete the vendored copy at
`book/docs/_static/tex_exp_to_png/` and have the Dockerfile build the tool
from `https://github.com/billsix/tex-expression-to-png.git`, checked out at a
**pinned SHA** (reproducible builds; bump deliberately when upstream moves).
This kills the three-copy sync burden (external repo ↔ mvp vendored copy ↔
anything else) that the CLAUDE.md "vendored texExpToPng" contract exists to
manage.

## Changes

1. **Dockerfile**
   - Delete `COPY book/docs/_static/tex_exp_to_png/ /tmp/tex_exp_to_png/`
     (line ~16) and its comment block.
   - In the `BUILD_DOCS` block, replace the `( cd /tmp/tex_exp_to_png &&
     meson setup/compile/install )` stanza with:
     `git clone https://github.com/billsix/tex-expression-to-png.git
     /tmp/tex_exp_to_png && cd /tmp/tex_exp_to_png && git checkout <SHA> &&
     meson setup builddir && meson compile -C builddir &&
     meson install -C builddir && rm -rf /tmp/tex_exp_to_png`.
   - **Add `git` to the dnf install** — the mvp image does not currently
     install git (verified 2026-07-08); the clone fails without it. Putting
     it in the BUILD_DOCS package list keeps lean builds lean.
   - SHA to pin: upstream HEAD at implementation time. As of 2026-07-08 the
     GitHub mirror's HEAD is `fbbd9a3fefa48ab86136ca4fba9861553289c5ee`
     (what multivariate-math pinned). **Check first** whether the mirror is
     behind the Pi origin: the local `/foo/opt/texExpToPng` working repo's
     HEAD was `ebea794d…` on 2026-07-08 — if that newer history matters
     (e.g. the `--bg/--fg` flags the book build needs — verify they're in
     the mirror's HEAD before pinning), push the mirror forward and pin the
     new SHA.
2. **Delete `book/docs/_static/tex_exp_to_png/`** — verified 2026-07-08:
   nothing in `book/docs/*.rst` or `conf.py` references the directory itself
   (conf.py only invokes the installed `texExpToPng` binary via the inlinetex
   extension), so it is not book content; it existed only to feed the
   Dockerfile COPY.
3. **CLAUDE.md** — rewrite the "vendored texExpToPng" bullet + the
   "replicate changes into the vendored copy" contract to describe the
   pinned-clone scheme instead (update the SHA when the tool changes).
4. **`tasks/crossproduct-tex-billboard-labels.md`** — its locked 2026-06-14
   decision "BUILD IT INTO THE MVP IMAGE from the vendored copy" is
   superseded by this task (still built into the image, just from the pinned
   clone).

## Notes

- The 2026-07-08 session's cache-conversion edits to the vendored copy's
  Makefile/Dockerfile (and the `.clang-format` added to fix its build) all
  become moot — the whole directory goes away. If this task lands before
  those edits are committed, they can simply be dropped.
- Gate: `make image` with default flags (`BUILD_DOCS=1`) must pass, and
  in-container `texExpToPng --exp '$x^2$' --size 300 --fg "rgb 1 1 1"
  --bg Transparent -o /tmp/x.png` must render (same headless check
  multivariate-math uses). The book build (`make html`) exercises the binary
  via inlinetex — run it if the SHA differs from what the vendored copy held.
