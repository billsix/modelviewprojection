# Port the SuperBible v4 "directional light far away" treatment to lit demos

**Status:** blocked
**Priority:** 6
**Difficulty:** 4
**Started:** 2026-08-27 (William Emerison Six <billsix@gmail.com>)
**Blocked on:** the maintainer's visual-convention choice (directional marker: arrow-from-infinity vs
sphere) + which target demos. **Q1 (which SB4 demo) is now ANSWERED** by
`tasks/reference/lighting-and-shading.md`: it's **`ports/openglsuperbiblev4/chapt05/shadow/shadow.py:41`**
(`light_pos` w = 0.0 = directional). So only the aesthetic/convention half remains.
**Recheck:** the marker-convention + target-demo questions are answered (maintainer-gated;
`/recheck-blocked` surfaces it).

## Goal

Maintainer's idea, verbatim: *"Find demo from super Bible. 4. That deals with directional lights far
away, Port that over to any demo that uses directional lights, the light source one should only be used
for actual light sources."*

## Context (investigation 2026-08-27)

- **This refines archived `2026/06/14/ports-visible-light-source.md`** — that task added a *positional*
  light **marker** (a sphere) to all lit ports. This bullet's rule: a **directional** light (far away,
  `Lw==0`) should NOT get a positional sphere marker — only actual *positional* sources should. demo22
  already special-cases directional at `demos/demo22/demo22.py:1132`.
- SB4 lit/shadow family (reference `tasks/reference/superbible-ports-guide.md`): Block, litjet, shadow,
  shinyjet, the sphereworlds, pyramid, fogged, multisample, SphereWorld32; **chapt05 = the lighting
  chapter** — likely where the "directional far away" demo lives. Edition = **v4 / 4th ed. (Wright,
  2007)**; upstream at `github.com/billsix/OpenGLSuperBibleV4Code`.
- Adjacent active: `ports-ux-pass.md`, `superbible-full-port.md`.

## Plan (draft — after questions)

- [ ] Identify the SB4 directional-far demo (Q1); adopt its treatment in the target demos (Q2); apply the
      "directional → no positional marker; positional → sphere" convention (Q3).

## Open questions

1. **Which SB4 demo** shows "directional lights far away"? (chapt05 candidates, or a sun in
   solar/sphereworld?) — need the exact demo name.
2. **Which target demos** get the directional treatment?
3. **Desired visual convention** for a directional light (arrow-from-infinity vs sphere)?
