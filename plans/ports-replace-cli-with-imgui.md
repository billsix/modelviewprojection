# Plan: Replace command-line inputs with ImGui controls in SuperBible ports

**Status:** not started — task #36. Recorded 2026-04-28.

**Scope:** SuperBible ports under `/mvp/ports/openglsuperbiblev4/` only.

## What

Audit SuperBible ports for `argparse` / `sys.argv` / `os.environ`-driven configuration and convert each to an `imgui_bundle` control. Demos should be runnable with no flags and configured live in the running window.

## Why

Students shouldn't have to read help output or pass flags to see different states of a demo — every option should be visible and toggleable in the running window. Reduces friction for students just running demos to follow along with the textbook.

## How

1. `grep -rn "argparse\|sys.argv\|getopt" /mvp/ports/openglsuperbiblev4/` to find any CLI-driven port.
2. For each hit, replace the CLI parsing with default values and add ImGui sliders / checkboxes / radio buttons in the demo's main loop.
3. The menubar from [ports-imgui-menubar.md](ports-imgui-menubar.md) is a natural place to surface these — either as menu items or as a "Controls" floating window the menubar toggles.

## Scope

- Touch only ports that currently take CLI args. From a quick mental scan of the session, most ports don't — they're already self-contained. But any that do (and any future port) should follow the convention.
- Coordinate with the menubar task: the ImGui setup added by that task is the same setup used here, so they should land together or in a known order.

## Open questions

- Are there ports that legitimately need a CLI arg (e.g., to specify a data file path)? If so, ImGui file picker via `imgui_bundle`'s file dialog, or a menu "Open…" item — but most ports load assets from a fixed path next to the demo anyway, so unlikely to come up.
