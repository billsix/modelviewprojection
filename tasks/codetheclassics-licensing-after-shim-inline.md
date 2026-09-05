# Code-the-Classics licensing after the shim inline/re-extract

**Status:** actionable — **DECIDED 2026-09-05 (William Emerison Six <billsix@gmail.com>): BSD-2-Clause** for the inlined engine code (permissive; matches the existing `ports/codetheclassics/LICENSE` declaration for the per-game files). No longer blocked. Remaining: the ~15-min mechanical header pass (drop the interim pygame-LGPL headers, apply BSD-2-Clause) — awaiting go-ahead to execute. Maintainer confirmed 2026-09-04 the pygame-LGPL courtesy should be dropped (the shim is his clean-room code, and inline+strip has dissolved its "pygame reimplementation" identity per game).
**Priority:** 3
**Difficulty:** 3

## Findings (2026-09-04) — the license state is now concrete

Checked the actual files (not assumed):

- **`ports/codetheclassics/LICENSE` already exists and declares** "the per-game files under vol1/
  and vol2/ ... licensed under the BSD 2-Clause License", © Eben Upton et al. (Vol 1 © 2019 Eben
  Upton). So the **mandatory game attribution is already present** at the directory level — good.
- **But each game `.py` header carries `SPDX-License-Identifier: LGPL-2.1-only`** (the inlined
  shim's), which now **contradicts its own directory LICENSE** (which says those files are
  BSD-2-Clause). That inconsistency is the concrete bug to fix — and it confirms the maintainer's
  instinct that the license shouldn't "stay the same."
- **mvp's project code is GPLv2** (root `LICENSE`: "Source Code Under GNU General public license
  v2", © 2016-2026 William Emerison Six; docs under GFDL 1.3). Demos/`src` carry **no per-file
  SPDX** — they rely on the root LICENSE.
- **The dissolution point (maintainer, 2026-09-04):** each per-game file now contains BSD-2 game
  code **plus** the maintainer's inlined engine (formerly the LGPL shim). Steps 1-2 already made
  each engine game-specific (stripped, dataclass-ified, loop absorbed — boing dropped `Actor`
  entirely), so calling any of them "a clean-room reimplementation of the pygame APIs" is no longer
  accurate. Drop that framing.

**The recommended resolution** (pending Open Q1): make each per-game file uniformly the SAME
license as its directory LICENSE already declares — **BSD-2-Clause** — with **dual copyright**
(© Eben Upton et al. for the game portion, © William Emerison Six for the inlined engine/port),
and drop the LGPL SPDX + the "pygame reimplementation" wording. Update `ports/codetheclassics/LICENSE`
to note the inlined engine is © Six under the chosen license. This aligns the file headers with
the directory LICENSE that already governs them, so it reads as *fixing an inconsistency* rather
than *setting new policy*. **The one real fork is Open Q1 below.**

## BLUF

Sort out per-file licensing now that the `pgzero_gl` shim is inlined into each game (step 1) and
will be re-extracted (step 3). Two distinct bodies of code with two distinct licensing stories:

- **The `pgzero_gl` shim is the maintainer's OWN clean-room reimplementation** of the pygame /
  PyGame-Zero *APIs* (copies no pygame source). APIs aren't copyrightable, so the LGPL-2.1 header
  it currently carries was a *courtesy* match to pygame, **not a legal obligation** — the
  maintainer owns the copyright and may relicense it freely ("we no longer care about their
  licence", 2026-09-04). Drop the LGPL-2.1 + "under the same license as pygame" framing; adopt the
  maintainer's chosen license (see Open question 1).
- **The Code-the-Classics games are genuine DERIVATIVE work** of the upstream games (© Eben Upton
  et al. / Raspberry Pi Press). Their upstream license **must** be retained in-file with
  attribution — this is a real obligation, not a choice.

**Critical gap this task exists to fix:** the step-1 inline pasted the shim's **LGPL-2.1 header at
the top of every game file**, so today each game file's SPDX header advertises the *shim's*
license while the game's own upstream © appears only in prose docstrings ("originals (c)
Raspberry Pi Press and authors"). That **under-represents the mandatory game attribution** in the
header and mislabels BSD-derivative game code as LGPL. Best fixed **alongside step 3 (re-extract)**,
which removes the shim code from the game files so each file is single-license again.

## Context (read first)

- **Current header state** (e.g. `ports/codetheclassics/vol1/boing/boing.py:1-6`, and identically
  the other 9 games + the new `boing_gl1.py`): `SPDX-License-Identifier: LGPL-2.1-only`,
  `Copyright (c) 2026 William Emerison Six`, "a clean-room reimplementation of the pygame /
  PyGame Zero APIs, under the same license as pygame (GNU LGPL v2.1)", pointing at
  `src/modelviewprojection/pgzero_gl/LICENSE`. **This header describes the SHIM, not the game** —
  a step-1 inlining artifact.
- **What the games actually are:** behaviour-faithful ports of Code-the-Classics Vol 1 & 2
  (`CLAUDE.md` › Code-the-Classics: "10 faithful game ports ... (BSD-2-Clause, © Eben Upton et
  al.)"). Upstream: `github.com/raspberrypipress/Code-the-Classics-Vol1`.
- **What the shim is:** `src/modelviewprojection/pgzero_gl/` — the maintainer's clean-room
  pygame/pgzero API reimplementation, LGPL-2.1 by prior choice, © William Emerison Six.
- **Related initiative:** `tasks/pgzero-gl-inline-strip-reextract.md` — step 3 re-extracts the
  shim from the inlined games. This licensing cleanup should ride with it (single-license-per-file
  falls out of the re-extraction).

## The legal reasoning (be precise, verify — don't guess)

- **Clean-room API reimplementation → maintainer's original work.** Reproducing an API surface
  without copying the implementation is original authorship (APIs aren't copyrightable; cf. Google
  v. Oracle). So the shim's license is the maintainer's to set; pygame's LGPL does not reach it.
  **Caveat to verify:** confirm the shim truly copied no pygame/pgzero *source* (it was authored
  as a clean-room reimpl — spot-check before relying on this).
- **BSD-2-Clause derivative → retain the notice.** BSD-2-Clause requires "redistributions of
  source code must retain the above copyright notice, this list of conditions and the following
  disclaimer." So every game source file (a derivative) must carry the Code-the-Classics ©
  + license text (or a compliant SPDX + a retained LICENSE). **Verify the upstream license is
  actually BSD-2-Clause** against the Code-the-Classics repo before writing headers — `CLAUDE.md`
  says so, but confirm (licenses are not something to take on secondhand).

## Plan (execute only after Open question 1 is answered; ideally folded into step 3)

1. **Game files** — header carries `SPDX-License-Identifier: BSD-2-Clause`, the Code-the-Classics
   copyright (© Eben Upton et al. / Raspberry Pi Press), AND the port authorship (© William
   Emerison Six for the port), plus a retained `LICENSE` for the BSD text under
   `ports/codetheclassics/`. Keep the "faithful port of <game>" note.
2. **Shim (re-extracted library)** — header carries the maintainer's chosen license (Open Q1),
   © William Emerison Six; drop the "under the same license as pygame (LGPL v2.1)" wording and the
   pygame LICENSE pointer. Update `src/modelviewprojection/pgzero_gl/LICENSE` accordingly.
3. **Sequencing** — do this **as part of step 3**: re-extraction removes the shim code from the
   game files, so afterward each game file is purely BSD-derivative (+ port ©) and the shared
   library is purely the maintainer's license — no mixed-license-per-file to reconcile. Doing it
   before step 3 means every inlined file needs a *dual* header (BSD game + maintainer's shim),
   which is messier and thrown away at re-extraction.
4. **Interim honesty (optional, cheap):** if step 3 is far off, at minimum correct the game
   headers now so BSD-derivative game code isn't advertised as LGPL — but this is the throwaway
   dual-header state, so prefer waiting for step 3.

## Code in question — the exact files + headers (for the mechanical pass)

**Files carrying the interim LGPL header** (`SPDX-License-Identifier: LGPL-2.1-only`) — the 10
games + the GL 1.x companion, all to be corrected:
- `ports/codetheclassics/vol1/{boing,cavern,myriapod,bunner,soccer}/<game>.py`
- `ports/codetheclassics/vol1/boing/boing_gl1.py`
- `ports/codetheclassics/vol2/{kinetix,avenger,eggzy,leadingedge,beatstreets}/<game>.py`

**Current header (all of the above; e.g. `boing.py:1-6`):**
```
# Copyright (c) 2026 William Emerison Six
# SPDX-License-Identifier: LGPL-2.1-only
# Generated by Claude (Anthropic); a clean-room reimplementation of the pygame /
# PyGame Zero APIs, under the same license as pygame (GNU LGPL v2.1).
# Full license text: src/modelviewprojection/pgzero_gl/LICENSE.
# License source: https://raw.githubusercontent.com/pygame/pygame/main/docs/LGPL.txt
```
Wrong for a game file: it describes the shim, cites pygame's LGPL, and **contradicts**
`ports/codetheclassics/LICENSE` (which declares these files BSD-2-Clause).

**Recommended replacement (BSD-2-Clause, dual copyright):**
```
# Code the Classics port: <game> (with its rendering engine inlined).
#
# Game code derived from Raspberry Pi Press's "Code the Classics":
#   (c) 2019 Eben Upton et al. (vol 1)  /  (c) 2020 Eben Upton et al. (vol 2)
# Inlined rendering engine: (c) 2026 William Emerison Six.
# SPDX-License-Identifier: BSD-2-Clause
# Full license text: ports/codetheclassics/LICENSE.
```
(Use the vol-appropriate CtC copyright line; drop the pygame-LGPL citation and the
`pgzero_gl/LICENSE` pointer. The header is otherwise identical across all files bar the game name
+ vol line — so a small codemod does the whole pass.)

**Also:** append one line to `ports/codetheclassics/LICENSE` noting the inlined rendering engine in
each per-game file is © William Emerison Six under the same BSD-2-Clause.

**The shim SOURCE** (`src/modelviewprojection/pgzero_gl/*.py`, still LGPL-2.1) is a **separate**
question, handled at step 3 (re-extract): once re-extracted it takes the maintainer's chosen
license; until then it stays as-is (it's the source the games were inlined from).

## Open questions

1. **THE decision — license for the maintainer's inlined engine code: BSD-2-Clause vs GPLv2.**
   **BSD-2-Clause** folds the engine under the directory LICENSE the per-game files already live
   under, so the whole file becomes BSD-2 with dual © (tidiest, permissive, removes the
   contradiction). **GPLv2** matches the mvp project's own copyleft — but then the per-game files
   diverge from their BSD-2 directory LICENSE (which would also need updating) and the ports
   acquire copyleft. *Recommendation: **BSD-2-Clause** — it aligns with what
   `ports/codetheclassics/LICENSE` already declares and keeps the ports permissive; choose GPLv2
   only if you deliberately want the ports under the project's copyleft.* This is a
   permissive-vs-copyleft policy call, so it's yours; everything else is ready.
2. ~~Confirm the Code-the-Classics upstream license is BSD-2-Clause~~ → **CONFIRMED**:
   `ports/codetheclassics/LICENSE` reproduces the BSD-2-Clause text, © Eben Upton et al. (Vol 1
   © 2019 Eben Upton), "from the upstream Debian packaging."
3. **Sequence:** the header fix no longer needs to wait for step 3 — the directory LICENSE already
   declares BSD-2, so aligning the file headers to it is a standalone consistency fix that can land
   now (one pass over the 10 games + `boing_gl1.py` + the shim source). Still fine to bundle with
   step 3. *Recommend: its own small commit once Q1 is answered.*

## Related

- `tasks/pgzero-gl-inline-strip-reextract.md` — step 3 re-extract (the natural home for this).
- `tasks/archive/2026/09/05/pgzero-gl-boing-gl14.md` — `boing_gl1.py` inherits the same interim LGPL header; it is in
  scope for this cleanup along with the other 10 game files.
- `CLAUDE.md` › Code-the-Classics — records the games as BSD-2-Clause, © Eben Upton et al., and the
  shim as LGPL-2.1 (both to be updated when this lands).
