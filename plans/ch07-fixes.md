# Plan: ch07 (Rotations) fixes

**Status:** planned. **Type:** book prose. **Effort:** trivial.
**Source:** ch07–09 drift audit.

## Findings + changes (`book/docs/ch07.rst`)
1. **Line 59 — visible TODO marker in the text.** `.. TODO -- discuss method
   chaining`. Either write the method-chaining note or remove the marker so it
   doesn't ship. (Decide with Bill what the intended content was.)
2. **Line 203 — LaTeX typo.** `\vec{r}(\vec{a}; theta) = …` — first `theta` is
   missing its backslash, so it renders as the word "theta" instead of θ; the
   rest of the same equation uses `\theta`. Fix to `\theta`.

## Related (handled by other plans, not here)
- e_1/e_2 used but unexplained in ch07 → `plans/book-explain-natural-basis.md`.
- Whether ch07's rotation prose matches `rotate()`'s actual parallel/perpendicular
  decomposition (`cos θ·v + sin θ·rotate_90(v)`) — worth checking while editing;
  if the prose hand-waves it, that's a content gap to raise with Bill.

## Verification
`grep -n "TODO\|(\\\\vec{a}; theta)" book/docs/ch07.rst` returns nothing after.
Prose/LaTeX only; Bill renders via `make html` (the `\theta` fix only shows in
the built math).
</content>
