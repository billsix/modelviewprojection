# Plan: fix verified prose typos in ch02 / ch03

**Status:** complete
**Completed:** 2026-05-27 — 6 typos fixed (ch02:77,79,189,464; ch03:185,232); `ch02:464` truncated sentence reworded to "…take the inverse of any directed edge that you traverse against its direction."
**Type:** book prose (editorial).
**Source finding:** `tasks/book-code-drift-ch1-6.md` item C. All six lines were
read directly and confirmed.

## Context
Six small but real prose errors in the two intro chapters. Grouped into one plan
because they are the same kind of mechanical edit; each is an exact-string
replacement with no code impact.

## Edits

`book/docs/ch02.rst`
| Line | Current | Fix |
|------|---------|-----|
| 77 | `"glColor3f" is a function sets a global variable` | `… is a function that sets a global variable` |
| 79 | `Lets make the first` | `Let's make the first` |
| 189 | `the the programmer would have to` | `the programmer would have to` |
| 464 | `of any directed edge that you against.` | sentence is truncated — needs the missing verb (likely `… that you traverse against.`); **confirm intended wording with Bill** since the meaning is ambiguous |

`book/docs/ch03.rst`
| Line | Current | Fix |
|------|---------|-----|
| 185 | `because of the existing class to glClearColor.` | `… existing call to glClearColor.` |
| 232 | `will be mapped the the region of screen coordinates` | `will be mapped to the region of screen coordinates` |

## Notes
- Line numbers may shift if other ch02/ch03 edits land first; match on the
  surrounding text, not the number.
- `ch02.rst:464` is the only non-mechanical one — it's a broken sentence, not a
  one-word typo. Hold that one for Bill's intended phrasing.

## Verification
- rst-only; no test/lint impact. A quick `grep -n "the the\|Lets make\|function sets\|class to glClearColor\|mapped the the" book/docs/ch02.rst book/docs/ch03.rst` should return nothing after the edits.
- Bill confirms rendering via `make html`.
</content>
