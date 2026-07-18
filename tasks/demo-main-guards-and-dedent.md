# Main-guard the demos, and `:dedent:` the book includes that excerpt them

**Status:** proposed — **on hold, and the approach itself is not settled.** Bill approved
it in principle 2026-07-18 ("option 1 sounds great"), then revisited: *"we'll get to that
later, after everything from [the `N` pass] is done. I'm still unsure if what I've
suggested is the best path."*

**Created:** 2026-07-18
**Enables:** [doctests-everywhere](doctests-everywhere.md) — this is its prerequisite

**So: do not start this until the `N` naming pass is finished, and when picking it up,
re-open the approach before writing any code.** The plan below is sound but it is one of
several, and it is the most invasive — it touches 30 demo files *and* 129 book includes.
Weigh the alternatives in the "Alternatives" section first.

## Goal

Make every demo **importable without side effects**, so `pytest --doctest-modules` can
collect the whole tree, `pytest.ini`'s `testpaths` collapses to `src tests` with no
allow-list, and doctests can then be written anywhere including in the demos themselves.

## Why the demos are currently uncollectable

`--doctest-modules` **imports** whatever it collects, and the demos are top-level
scripts that run at import:

- `demos/demo01.py:27` calls `sys.exit()` at module level. This does not fail a test — it
  kills the pytest process with `INTERNALERROR`.
- The rest enter their GLFW render loop on import.
- `mvpvisualization/` and `wxapp*.py` open windows for the same reason.

`pytest.ini` works around this with an explicit allow-list of importable library
modules, documented there as a workaround pointing at this task.

## Why it is not just "add a main guard"

**The demos are the book's source.** Measured 2026-07-18:

| | count |
|---|---|
| `literalinclude` directives in `book/docs/` | 181 |
| ...pointing at `demos/` | **129** |
| demo files carrying `doc-region` markers | 21 of 30 |
| `doc-region` markers inside `demos/` | 258 |
| includes currently using `:dedent:` | **0** |

The markers wrap individual statements for excerpting, e.g. `demo01.py`:

```python
# doc-region-begin initialize glfw
if not glfw.init():
    sys.exit()
# doc-region-end initialize glfw
```

Putting that inside `def main():` (or a bare `if __name__ == "__main__":`) indents it by
four, and with no `:dedent:` anywhere the **book would render indented code**. For
demo01 — chapter 1, whose whole point is "here is a flat script you read top to bottom"
— that is a pedagogical regression, not a cosmetic one.

**Indentation is unavoidable if we want import-safety.** There is no module-level
early-return; anything that halts execution on import (`raise SystemExit`, `sys.exit()`)
is exactly what breaks pytest today. So the answer is to indent the source and dedent at
include time.

## Alternatives to weigh before committing (Bill is undecided, 2026-07-18)

The goal is only "demos are importable without side effects, so doctests can be
collected tree-wide." Main guards + `:dedent:` achieves it but is the highest-churn
route. Options, cheapest first:

1. **Status quo — keep the `pytest.ini` allow-list.** Cost: zero. Loss: demos can never
   host a doctest, and the list needs a line whenever a new library module appears
   (rare). Honestly defensible; the allow-list is small and documented.
2. **Move the runnable demos out of the importable package** — e.g. a top-level
   `demos/` (or `scripts/`) directory outside `src/modelviewprojection/`. Then nothing
   under `src/` executes on import, `testpaths = src tests` works with no list, and no
   demo file changes shape at all. **Costs: 129 book `literalinclude` paths change**
   (a mechanical path edit, no `:dedent:` needed), plus anything importing across the
   boundary. Worth pricing — it may be less total churn than option 4 and it leaves the
   demos as flat scripts, which is the pedagogical point.
3. **Doctests live in `tests/`, not in the demos.** Write the examples as ordinary test
   files that import the library. Cost: zero structural change. Loss: the example stops
   sitting next to the code it documents, which is most of a doctest's value.
4. **Main guards + `:dedent:`** — the plan below. Correct end state, highest churn: 30
   demo files reshaped and 129 book includes edited, and the demos stop being flat
   top-to-bottom scripts, which chapter 1 explicitly teaches.

**Decision criteria:** does the book render identically? does a demo still read like a
flat script in the text? how many files change? Option 2 is the one that has not been
priced yet and may dominate option 4 — measure it before defaulting to the plan below.

## Plan

1. **Confirm Sphinx supports bare `:dedent:`.** Since Sphinx 4.1, `:dedent:` with no
   value strips the common leading whitespace automatically; older versions need an
   explicit count. Check the pinned version in the image before writing 129 of them —
   if it is older, either pin a count or upgrade.
2. **Capture a baseline of the rendered book** (`make html`, and the PDF if it is
   cheap). This change must alter *nothing* visible; a before/after diff of the rendered
   output is the real gate, not a successful build.
3. **Main-guard the demos, one at a time.** Keep imports and function/class defs at
   module level — only the *executable* statements move. Preferred shape:

   ```python
   def main() -> None:
       ...            # the former top-level body, doc-regions and all
   if __name__ == "__main__":
       main()
   ```

   Watch for module-level names that inner functions close over: moving a constant into
   `main()` turns it into a local and breaks any function that referenced it globally.
   Those must stay at module level (they are usually outside the doc-regions anyway).
4. **Add `:dedent:` to the 129 demo-targeted includes** as the guards land, file by
   file, so the book never sits broken between steps.
5. **Rebuild the docs and diff against the baseline.** Zero visible change is the pass
   condition.
6. **Then** collapse `pytest.ini` to `testpaths = src tests`, delete the allow-list and
   its explanatory comment, and confirm the suite still passes headless.
7. `mvpvisualization/` and `wxapp*.py` need the same treatment; they have far fewer book
   includes, so they are the easy follow-on.

## Related

`tasks/ctc-game-main-guard-and-clean-exit.md` proposes the identical change for the
Code-the-Classics ports. Same transformation, same motivation — worth doing in one sweep
or two deliberately consistent ones. The ports are **not** book-excerpted, so they have
none of the `:dedent:` complication.

## Gates

- `make format` clean; `pytest` green headless **and** with a display.
- **The docs build with the repo's default flags** (`BUILD_DOCS=1`, so TeX Live — slow)
  and the rendered output is unchanged versus the baseline.
- After step 6, `pytest.ini` contains no per-directory list, and a deliberately broken
  doctest in a *demo* turns the suite red (proving demos are now collected).
