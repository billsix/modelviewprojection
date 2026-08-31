# pixbufobj port renders "multiple spinning images" (not like the C++)

**Status:** open — **REPRODUCED on the maintainer's hardware GPU 2026-08-31** ("spinning but
not clean", observed during the PBO-crash verification run; still does NOT reproduce in the
sandbox's software GL). Newly practical debugging path: `make shell-exec CMD="python ports/…/
pixbufobj.py"` from the sandbox reaches the host display (verified 2026-08-31), so
instrumented builds can now be iterated with the maintainer watching, instead of waiting for
dedicated host sessions.
**Priority:** 5
**Difficulty:** 6

## Symptom (Bill)

`ports/openglsuperbiblev4/chapt18/pixbufobj/` — the C++ original shows **one** motion-blurred
rotating album cover; the Python port appears to show **multiple overlapping spinning copies**
on Bill's hardware. Reported to persist even with motion blur unchecked in the imgui menu.
(Bill confirmed the C++ with motion blur OFF is a single clean rotating image.)

This is **behavioural fidelity**, separate from the PBO-readback crash (that one is fixed —
see `tasks/ports-pbo-floattex-runtime-crashes.md`).

## What was established 2026-08-02 (the useful part for resuming)

**C++ ground truth** (verified; full trace in the source repo's
`tasks/reference/chapt18-advanced-buffers.md`, github.com/billsix/OpenGLSuperBibleV4Code):
one full-window quad; `useMotionBlur = GL_TRUE`, `usePBOs = GL_FALSE` by default; rotation is
applied to **unit 0 only** and accumulates; the "trail" is a 3-frame feedback ring
(readback → attenuate ÷4 → re-upload to units 1/2, which keep identity texcoords). With blur
OFF the C++ copies unit-0's rotation to unit 1 and binds unit 1 to the reservoir, disables
unit 2 → one clean rotating quad.

**The port's state is provably identical to the C++** (instrumented headlessly, blur off):
- Draw-time: units 0 & 1 both enabled, bound to texture 1, carrying the **same** rotation
  matrix; unit 2 disabled; `BLEND` off; viewport full 512².
- The unit-1 matrix copy (`glGetFloatv(GL_TEXTURE_MATRIX)` → `glLoadMatrixf`) **works**
  (unit0 and unit1 matrices byte-identical each frame).
- Texture 1 at draw time: `WRAP_S = CLAMP_TO_BORDER`, `BORDER_COLOR = (0,0,0,0)` — same as C++.

**Could NOT reproduce the bug in the sandbox (software Mesa / llvmpipe).** The port renders
**one clean rotating album in BOTH blur modes** — the window corners are pixel-verified pure
black `srgb(0,0,0)` (so `CLAMP_TO_BORDER` is in effect), the centre is the reservoir. The
earlier "two images" reading of the screenshots was wrong: the light-blue is the album cover's
own watercolour rotating *with* the album; the true out-of-[0,1] corners are black.

**Attempted C++ side-by-side:** built the C++ `pixbufobj` (blur-off variant) from source in the
sandbox (freeglut/-devel + gcc), but **freeglut won't render under Xvfb** (`X Error: BadAtom`,
black capture) — so no direct headless comparison. (GLFW-based Python demos screenshot fine;
the freeglut C++ ones don't, under Xvfb.)

## Working conclusion

Given the port's GL state is provably identical to the C++ and it renders correctly under
llvmpipe, the "multiple images" is most likely **hardware/driver-specific** to Bill's Mesa/GPU
— an edge case in texture-matrix rotation + multitexture (`GL_ADD`) + `CLAMP_TO_BORDER` that
llvmpipe doesn't exhibit — or tied to interactive state (imgui toggling / resize) the
non-interactive headless run doesn't reach.

## To resume (needs Bill's hardware)

1. Does it repro on a **fresh start with blur off** (before touching anything), or only after
   toggling/resizing? Immediately, or does it build up over seconds?
2. Give Bill a small **instrumented build** to run on his GPU: dump per-unit enable/bound-tex/
   texture-matrix + `GL_TEXTURE_WRAP_S`/`BORDER_COLOR` + `glGetString(GL_RENDERER)` at draw
   time, and grab a screenshot — compare that trace/pixels to the llvmpipe run captured here.
3. If it's the feedback ring (blur on), compare the trail frame-by-frame vs the C++ built on
   the same GPU; if it's `CLAMP_TO_BORDER` on hardware Mesa, try setting `GL_TEXTURE_BORDER_COLOR`
   explicitly and/or check whether the corners go non-black on his GPU.

## Related

- `tasks/ports-pbo-floattex-runtime-crashes.md` — the PBO crash (fixed) + texfloat (instrumented).
- `tasks/reference/superbible-ports-guide.md` › "Port fidelity" — the running list of ports
  that don't match the C++.
- C++ reference set: github.com/billsix/OpenGLSuperBibleV4Code `tasks/reference/`.
