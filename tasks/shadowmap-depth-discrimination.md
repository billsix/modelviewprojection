# Make shadow-map depth values visually distinguishable (debug view)

**Status:** not-started — logged 2026-05-29 (Bill). Investigate (done below) + design an
option to visually discriminate close depth values; confirm approach with Bill before building.

## Symptom (Bill)

In the shadow-map demos' "show shadow map" debug view, depth values are drawn as grayscale.
When two different objects sit at **very close depths** (from the light's POV) their grays are
nearly identical, so a human viewer **can't tell them apart**. Want a way to visually
discriminate them — even just a toggle/checkbox that pushes similar values further apart.

## Where (both affected, same debug view)

- `ports/openglsuperbiblev4/chapt14/shadowmap/shadowmap.py` — `M` key toggles `show_shadow_map`;
  `render_scene` (the `if show_shadow_map:` branch, ~line 213) draws the depth texture on a
  fullscreen quad with `GL_REPLACE`.
- `ports/openglsuperbiblev4/chapt18/fboshadowmap/fboshadowmap.py` — identical `M`-key view
  (~line 191).

Both set `glTexParameteri(GL_TEXTURE_2D, GL_DEPTH_TEXTURE_MODE, GL_INTENSITY)` in `setup_rc`,
so sampling the depth texture yields a **grayscale intensity = depth**.

## Root causes (two, compounding)

1. **Grayscale has poor perceptual resolution** for nearby values — adjacent depths look the
   same gray.
2. **Perspective depth is nonlinear** — most of the [0,1] depth range is compressed up near the
   far plane, so genuine spatial separations between objects map to *tiny* intensity differences.
   This is why "close objects" are nearly indistinguishable rather than just subtly different.

## Goal

An **optional** remap (default OFF, so the faithful grayscale view is preserved) that makes
close depth values visually distinct. The demos are key-driven (S/M/C/F/X/Y/Z), so a new key
(e.g. **`D`** = "distinct") is the consistent UI; an imgui checkbox is the alternative if/when
these ports get the imgui treatment (the CLI→imgui task, #36, now folded into tasks/ports-ux-pass.md Phase 3).

## Candidate techniques (pick one or cycle through)

- **A. False-color ramp / heatmap** — map depth → a color gradient (e.g. blue→cyan→green→
  yellow→red, or "turbo"). Best perceptual separation; most legible. Recommended primary.
- **B. Contour banding** — `fract(depth * N)` produces repeating bands; a tiny depth delta
  shifts position within a band → shows up as a visibly different shade / contour line. Great
  for seeing *relative* ordering of close surfaces.
- **C. Contrast stretch + linearization** — convert nonlinear depth back to linear eye-space
  distance and stretch [near,far] (or [observed min,max]) to [0,1]. Directly attacks cause #2;
  can combine with A or B.

## Implementation paths (these are OpenGL 1.4 FIXED-FUNCTION demos)

- **Preferred: a tiny GLSL fragment shader used ONLY for the debug quad** when the option is on
  — sample the depth texture, apply A/B/C, output color. Localized deviation limited to the
  debug view; the repo already uses shaders from ch15 on, so the pattern exists. Keeps the main
  render path fixed-function and faithful.
- **Fixed-function-pure alternative (no shader):** read the depth back
  (`glGetTexImage`/`glReadPixels`), compute min/max, remap on the CPU into an RGB image, and
  `glDrawPixels` it. Heavier and the depth-readback of a `GL_DEPTH_COMPONENT` copy can be fiddly,
  but it preserves ch14's no-shader character.
- A 1D **palette/color-table** in pure FF (`glColorTable`/`glPixelMap` + `GL_MAP_COLOR`) is
  possible but awkward and driver-dependent — not recommended.

## Plan / next steps
1. Decide WITH BILL: shader-based debug remap (simpler, cleaner, slight FF deviation) vs
   FF-pure CPU readback (faithful, heavier). Pedagogically this is an educational debug aid,
   matching the existing "M = show shadow map" intent.
2. Add a toggle (key `D`, default OFF) — possibly cycling Off → false-color → banding.
3. Implement the remap in the `show_shadow_map` branch of BOTH shadowmap.py and fboshadowmap.py
   (factor the shared bit if it stays small).
4. Bill verifies visually (needs a display — can't be confirmed in-container).

## Notes
- Keep the default grayscale view untouched (faithful to SuperBible). This is additive.
- Surfaced during the geometry-extraction work ([[extract-data-generation]]) when Bill ran the
  shadow-map demos; unrelated to that refactor.
