# Plan: ch14 fixes

**Status:** PARTIAL — caption :133 (`+.py`) and the grammar/pronoun fixes
(:102,:227,:229,:322) done 2026-05-27. **Still open: the "define vector class"
doc-region relabel — bigger than first thought.** That region is referenced by
**7 chapters** (ch04, 05, 06, 07, 08, 14, 18), all currently pulling the first
match (`Vector1D`); relabeling the 3 mathutils regions uniquely means deciding
which `Vector` class each of the 7 should display — a per-chapter pedagogical
call (proposed default: ch04–08 → `Vector2D`, ch14/ch18 → `Vector3D`). Needs
Bill's confirmation before touching 7 chapters. Coordinate with the
natural-basis task (which also touches these class regions).
**Type:** book prose + caption + doc-region label.
**Source:** ch13–15 drift audit (verified).

## Findings + changes (`book/docs/ch14.rst` unless noted)

1. **Line 133 — caption missing `.py`.** `:caption:
   src/modelviewprojection/mathutils` → `…/mathutils.py` (siblings at lines 156,
   177, 197, 209 are correct). Same class of bug recurs in ch16:194 (see
   `plans/ch16-fixes.md`).
2. **Lines 129-133 — doc-region label collision pulls the wrong class.** The
   `literalinclude` uses `:start-after: doc-region-begin define vector class`, but
   that label appears **3 times** in `mathutils.py` (around Vector1D@204,
   Vector2D@219, Vector3D@238); Sphinx grabs the **first** (Vector1D), so a
   chapter that says "Vector data will now have an X, Y, and Z component"
   (line 106) shows only `Vector1D(x: float)`. **Fix at the source:** give the
   three regions unique labels (e.g. `define vector1d class` / `…vector2d…` /
   `…vector3d…`) in `mathutils.py` and point ch05/ch06/ch14 at the right one.
   *This is a shared mathutils edit — coordinate with `tasks/archive/ch05-translate-section-fixes.md`
   and `plans/book-explain-natural-basis.md` (which also touches these classes).*
3. **Grammar/pronoun.** Line 227 "the **paddles** have a z-coordinate" should be
   "the **square** has…" (copied from the paddle section above). Line 229 "do a
   sequence transformations" → "a sequence **of** transformations". Lines 102 and
   322 "**They** direction of the rotation" → "**The** direction".

## Verification
- After relabeling: confirm ch14's include now shows the 3D class —
  `grep -n "define vector" src/modelviewprojection/mathutils.py book/docs/ch05.rst book/docs/ch06.rst book/docs/ch14.rst` and check every referrer points at a real, unique label (no "Cannot find region" at build).
- `grep -n "They direction\|sequence transformations\|the paddles have a z" book/docs/ch14.rst` → empty after.
- Bill renders via `make html`.
</content>
