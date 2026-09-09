# Book: link each chapter to the assignment that exercises it

**Status:** proposed — needs go-ahead (the prose is Bill's voice, and half of this is a decision
only he can make)
**Priority:** 6
**Difficulty:** 2
**Created:** 2026-09-09, split out of `tasks/archive/2026/09/09/assignments-1-and-2-review.md` when
that closed — all four assignments are current now, so the question of how the book points at them
is the remaining piece.

## BLUF

**No chapter mentions any assignment.** `grep -rn "assignment" book/docs/ch*.rst` is empty. Two of
the four assignments are already pages in the toctree, positioned right after the chapter that
teaches them, but nothing in the prose sends a reader to them; the other two have no page at all.
Done = a reader finishing a chapter knows there is an exercise for it, and the two unpublished
assignments have an explicit disposition.

## Context — the current state

Four student-facing files, all brought up to date 2026-09-08/09 (they use `gacalc` + `mathutils`
and the shared `util/` helpers exactly as the demos do):

| assignment | exercises | book status |
|---|---|---|
| `assignments/assignment1.py` | drawing in NDC; "draw whatever you'd like" | **published** as `programmingproj1`, in the toctree **between ch02 and ch03** |
| `assignments/demo02/vec1.py` | `translate`/`uniform_scale`/`compose`/`inverse` as `m*x + b` | **published** as `mathhomework1`, in the toctree **between ch05 and ch06** |
| `assignments/assignment2-screenspace.py` | NDC → screen space, and keeping the aspect ratio | **no page** |
| `assignments/assignment3-strafe.py` | strafing a 3-D camera (built on demo18) | **no page** |

Three of them carry a deliberate exercise hole (assignment 1 does not — it is a worked-example
gallery). See `CLAUDE.md` › Assignments.

## The two halves

**1. Cross-link the two that are already published — cheap, no decision needed.** The toctree
already puts them in the right place; the chapters just never say so. Add a sentence at the end of
**ch02** pointing at `programmingproj1`, and at the end of **ch05** pointing at `mathhomework1`,
using `:doc:` (a `:ref:` needs a label; `:doc:` takes the document name directly).

**2. Decide what happens to the two with no page — this is the real question.** Each has a natural
chapter:

- **`assignment2-screenspace.py` ↔ ch03** ("Window Resizing and Proportionality"). This pairing is
  worth more than proximity: ch03 solves the non-square-window problem with
  `draw_in_square_viewport` (letterbox the viewport), and the assignment solves the *same* problem
  the other way — hand OpenGL screen coordinates and do the NDC→screen mapping yourself, with
  `KEEP_ASPECT_RATIO` toggling between distorting and not. Two answers to one problem is a good
  thing for a chapter to point at.
- **`assignment3-strafe.py` ↔ ch18** ("3D Perspective"). It *is* demo18's scene and pipeline with
  the strafe removed, so it lands naturally at the end of that chapter.

Options for each: (a) give it a page in the toctree like the other two, (b) mention it in the
chapter's prose with a path but no page, (c) leave it unmentioned. Note (a) has a cost the other
two already pay — a published assignment is under the doc-region regime, so its code becomes
book-visible and edits to it change a page.

## Verify

`make html` in the container (the `:doc:` targets must resolve — a bad one is a warning, not an
error, so check the build log), and confirm the new links render in both light and dark furo.

## Open questions

1. **The two unpublished assignments** — give each a page (like `programmingproj1`/`mathhomework1`),
   mention them in prose only, or leave them out? *(Recommend a page for
   `assignment2-screenspace` — the two-answers-to-one-problem pairing with ch03 is genuinely
   instructive — and prose-only for `assignment3-strafe`, since its value is doing it, not reading
   it.)*
2. **Wording** — the two existing assignment pages are titled "Programming Project #1" and a math
   homework; should the new links use that vocabulary, or something plainer like "Try it yourself"?
   *(Yours; the prose is your voice.)*

## Related

- `tasks/archive/2026/09/09/assignments-1-and-2-review.md` — the work that brought all four
  assignments current; this question was its last loose end.
- `tasks/reference/demo-chapter-inventory.md` §5 — which assignments the book publishes today.
- `CLAUDE.md` › Assignments — the per-file state and the standing "leave the holes alone" rule.
