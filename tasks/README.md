# Tasks — modelviewprojection

Lightweight session task tracker (per the global `~/.claude/CLAUDE.md`
convention: one `tasks/<slug>.md` per task, check this dir at session start).
Completed tasks move to `tasks/archive/<YYYY>/<MM>/<DD>/`.

**Start here for orientation:** `tasks/reference/architecture-overview.md` —
the map of the tree, the subsystems, working constraints in the container,
and a where-do-I-look-for-X table pointing at the other reference docs
(book pipeline, figures, demo↔chapter inventory, tests & gates, GL gotchas,
SuperBible guide, design decisions, notable subsystems).

`tasks/` (top level, this directory) is the authoritative list of in-flight
work — the files themselves carry status. `tasks/reference/` is living
knowledge, never archived. The curated highlights of the active set are in
the repo `CLAUDE.md` › "Tasks".

## Conventions in this repo

- `tasks/` = active work, one `<slug>.md` per task (the cross-session
  tracker).
- `tasks/archive/<YYYY>/<MM>/<DD>/` = completed tasks, dated by completion;
  git history is the rest of the record. (No separate `plans/` dir or
  `HANDOFF-*` files.)
- `tasks/reference/` = durable knowledge (design rationale, subsystem maps,
  gotcha corpora) — update in place, never archive.
- Working constraints (no commits, no GL runs, etc.):
  `tasks/reference/architecture-overview.md` § "Working constraints".
