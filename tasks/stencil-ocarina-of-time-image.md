# Stencil-buffer demo — recreate the Ocarina of Time image from the boss-theme video

**Status:** ready — scope decided 2026-08-29 (see Decisions); implementation not started.
**Priority:** 6
**Difficulty:** 4
**Created:** 2026-08-29 (William Emerison Six <billsix@gmail.com> asked for it; drafted by agent)

## BLUF

Build a stencil-buffer demo that recreates an image/effect from The Legend of Zelda: Ocarina
of Time, as seen in the YouTube video the maintainer pointed at:
"The Most INSANE Boss Theme Ever Written For A Zelda Game"
(https://www.youtube.com/watch?v=egayquppRZM). Done = a runnable demo in this repo showing
the chosen effect, implemented with the stencil buffer, verified rendering (screenshot, not
just exit code).

## Context

- **The video** is a Zelda boss-*theme* (music) analysis; its footage shows the fight the
  theme belongs to. That boss theme is Bongo Bongo's — the Shadow Temple boss who is
  **invisible except when viewed through the Lens of Truth**. The agent's working guess
  (unconfirmed — Open question 1) is that "the image" to recreate is that Lens-of-Truth
  look: a circular masked region of the screen inside which an otherwise-hidden object is
  rendered. That is a textbook stencil-buffer technique — write the circle (the lens) into
  the stencil buffer, then draw the hidden geometry with a stencil test that passes only
  inside it.
- **Prior stencil art in this repo:** `src/modelviewprojection/demos/demo24/demo24.py`
  already uses the stencil buffer for planar shadows (so overlapping shadows don't
  double-darken) and shows the necessary plumbing: `glfw.window_hint(glfw.STENCIL_BITS, 8)`
  before window creation, `glClearStencil` + stencil ops in the draw loop. Read it first —
  the new demo is the same plumbing with a different stencil role (mask instead of
  shadow-count).
- **Where it would land:** demo24 is currently the highest-numbered demo, so the natural
  slot is a new `src/modelviewprojection/demos/demo25/` (Open question 2).
- **Verification** (per the repo's conventions): run headless under Xvfb, screenshot with
  ImageMagick `import`, and judge pixels — with/without the lens mask should differ visibly;
  a long-running GLFW demo is wrapped in `timeout N` (rc=124 = ran the full duration).
- Copyright note: recreate the *technique/composition* with the repo's own geometry — no
  ripped Nintendo assets in the repo.

## Decisions (William Emerison Six <billsix@gmail.com>, 2026-08-29)

1. **The effect is the Lens-of-Truth reveal** — a circular stencil mask inside which the
   otherwise-invisible object (Bongo Bongo) is rendered.
2. **It lands in the BOOK, not a demo**: a section on the stencil test illustrated with a
   **screenshot** of the effect. Possible supporting material, maintainer's ideas:
   - a **recorded video of real gameplay** captured from **Ship of Harkinian**
     (github.com/HarbourMasters/Shipwright, the OoT PC port — the same family as the
     Ghostship codebase already documented in the reference set of runClaudeInContainer,
     github.com/billsix/runClaudeInContainer);
   - a **frame capture showing the frame being built**, via **RenderDoc** or **apitrace**
     (apitrace was "the other tool" the maintainer couldn't recall: open-source GL call
     tracer/replayer; RenderDoc is the interactive single-frame debugger — better for
     inspecting stencil state, while apitrace suits whole-run traces).
   The "maybe" items are optional enrichment, not part of "done"; the screenshot in the
   stencil-test book section is the core deliverable.

## Notes for execution

- The **Ship of Harkinian gameplay capture is maintainer-gated** (needs the game assets,
  a display, and someone playing to the Shadow Temple) — treat it as a human step to
  request when the book section is drafted, not something a sandbox session can produce.
- A repo-built screenshot alternative: implement the lens effect with the repo's own
  geometry (the demo24-style stencil plumbing) and screenshot that for the book, keeping
  Nintendo assets out of the repo; the SoH footage/RenderDoc capture would then illustrate
  the real-game version alongside it.

## Open questions

None — resolved 2026-08-29 (see Decisions).
