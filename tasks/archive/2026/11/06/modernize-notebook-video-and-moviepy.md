# Modernize the notebook's movie generation (done)

The NDC notebook (`src/modelviewprojection/notebooksrc/ndc.py`) made its animation
with `moviepy.ImageSequenceClip(...).write_videofile(..., codec="libx264")`. moviepy
caps `pillow<12`, but Python 3.15 only has cp315 pillow wheels at ≥12.3.0 (we pin
`Pillow==13.0.0`), so unpinned moviepy had backtracked to the ancient 1.0.3; an
interim fix pinned `moviepy==2.1.1` + a Dockerfile uv `--override` of the cap.

## What was done (William Emerison Six <billsix@gmail.com>, 2026-11-06)
Dropped moviepy entirely in favour of **`imageio.v3`**, which was already a
dependency, has no pillow cap, and removed the need for the override:

- `ndc.py`: `iio.imwrite("animation.mp4", np.stack(frames_np), fps=60,
  codec="libx264", macro_block_size=1)` (and the dead `np_frames` line removed).
  Output format kept as mp4/libx264 so the book's HTML embed and PDF are unchanged.
- The **v3** API with a single stacked `ndarray` is used, not v2 `mimwrite`: v2's
  typed stub takes an invariant `List[ArrayLike]`, which `ty` rejects for
  `list[np.ndarray]` (`no-matching-overload`); v3's
  `imwrite(Union[ArrayLike, List[ArrayLike]], **kwargs)` type-checks cleanly.
- `macro_block_size=1` keeps the exact 400×300 frame size silently; the default
  pads the height to a multiple of 16 and prints a stderr warning that corrupts the
  LaTeX-captured notebook output (the reason moviepy had used `logger=None`).
- `requirements.txt`: removed `moviepy`, added `imageio-ffmpeg==0.8.1` (its wheel
  bundles ffmpeg, keeping the image offline/self-contained).
- `Dockerfile`: removed the pillow-cap `--override` (only moviepy needed it).
- Decision recorded in `tasks/reference/design-decisions.md`.

## Verification
Fresh lean image (`make image MINIMAL_IMAGE=1`, EXIT=0): moviepy absent,
imageio-ffmpeg 0.8.1 present; `python ndc.py` → `animation.mp4` = 400×300, 60 fps,
120 frames; `ty check ndc.py` passes.
