"""Hand-reviewed edits for citations of other repos' task docs (group 2).

Each entry was read in context (data/cross-repo-report.txt). An entry either
repoints a task the other repo has since archived, or puts that repo's GitHub
URL where the citation named it only as "gacalc", by a directory path, or by
a wrong URL. Each ``old`` must occur exactly once in its file. Already-applied
entries are skipped, so a second run changes nothing.

Usage (from the repo root):
    python3 -I tasks/adhoc/repoint-dangling-task-doc-paths/cross_repo_edits.py
"""

import pathlib

ROOT: pathlib.Path = pathlib.Path(__file__).resolve().parents[3]
GA: str = "github.com/billsix/geometricalgebra"
RC: str = "github.com/billsix/runClaudeInContainer"
A: str = "tasks/archive/"

EDITS: list[tuple[str, str, str]] = [
    (
        "tasks/archive/2026/07/22/precise-product-types-coefficient-cleanup.md",
        "(gacalc `tasks/.../typed-product-helper-functions.md`, 2026-07-21)",
        f"({GA} `{A}2026/07/21/typed-product-helper-functions.md`)",
    ),
    (
        "tasks/archive/2026/09/05/myriapod-rotate-90-degrees-local.md",
        "geometricalgebra `tasks/add-quarter-turn-to-g2.md` — because",
        f"{GA} `{A}2026/09/06/add-quarter-turn-to-g2.md` — because",
    ),
    (
        "tasks/archive/2026/09/05/myriapod-rotate-90-degrees-local.md",
        "- geometricalgebra `tasks/add-quarter-turn-to-g2.md` — the",
        f"- {GA} `{A}2026/09/06/add-quarter-turn-to-g2.md` — the",
    ),
    (
        "tasks/archive/2026/09/06/swap-myriapod-rotate90-to-gacalc.md",
        "the gacalc feature task `tasks/add-quarter-turn-to-g2.md`",
        f"the gacalc feature task `{A}2026/09/06/add-quarter-turn-to-g2.md`",
    ),
    (
        "Makefile",
        "Scoped to this pair ONLY. See runClaudeInContainer\n"
        "# tasks/add-shell-exec-target.md for the design.",
        f"Scoped to this pair ONLY. See\n# {RC}\n"
        f"# {A}2026/08/29/add-shell-exec-target.md for the design.",
    ),
    (
        "tasks/archive/2026/07/23/perspective-inlinetex-malformed-directives.md",
        "See `github.com/billsix/texExpToPng`",
        "See `github.com/billsix/tex-expression-to-png`",
    ),
    (
        "tasks/mathutils-helpers-via-gacalc.md",
        "- gacalc `tasks/archive/2026/08/24/area-volume-content.md`",
        f"- gacalc ({GA}) `{A}2026/08/24/area-volume-content.md`",
    ),
    (
        "tasks/archive/2026/09/08/mathutils-angle-helpers-via-gacalc-measures.md",
        "`tasks/area-volume-content.md` / "
        "`explicit-symbolic-tests-and-helper-cleanup.md`",
        f"`{A}2026/08/24/area-volume-content.md` / "
        f"`{A}2026/08/25/explicit-symbolic-tests-and-helper-cleanup.md`",
    ),
    (
        "tasks/sphinx-docstrings-google-and-rendering.md",
        "- `tasks/docstrings-for-sphinx.md`",
        f"- `{A}2026/09/26/docstrings-for-sphinx.md`",
    ),
    (
        "tasks/archive/2026/08/13/adopt-unsuffixed-gacalc-graded-types.md",
        "(its `tasks/drop-graded-type-dimension-suffixes.md`)",
        f"(its `{A}2026/08/13/drop-graded-type-dimension-suffixes.md`)",
    ),
    (
        "tasks/archive/2026/09/08/dangling-book-code-includes.md",
        "(`geometricalgebra/tasks/emit-doc-region-markers.md`)",
        f"({GA} `{A}2026/07/21/emit-doc-region-markers.md`)",
    ),
    (
        "tasks/archive/2026/09/08/dangling-book-code-includes.md",
        "geometricalgebra `tasks/mark-basis-constants-for-doc-regions.md`",
        f"{GA} `{A}2026/11/04/mark-basis-constants-for-doc-regions.md`",
    ),
    (
        "tasks/archive/2026/09/06/pointlike-type-study.md",
        "filed there as `tasks/fast-numeric-equality.md`",
        f"filed there ({GA}) as `{A}2026/09/09/fast-numeric-equality.md`",
    ),
    (
        "tasks/reference/notable-subsystems.md",
        "(geometricalgebra `tasks/fast-numeric-equality.md`)",
        f"({GA} `{A}2026/09/09/fast-numeric-equality.md`)",
    ),
    (
        "tasks/reference/point-type-decision.md",
        "filed as `tasks/fast-numeric-equality.md` in the gacalc repo",
        f"filed as `{A}2026/09/09/fast-numeric-equality.md` in the gacalc "
        f"repo ({GA})",
    ),
    (
        "tasks/archive/2026/07/09/ctc-shim-dynamism-audit.md",
        "`tasks/generated-dispatch-fast-paths.md`",
        f"`{A}2026/07/18/generated-dispatch-fast-paths.md`",
    ),
    (
        "tasks/github-actions-release-ci.md",
        "› `tasks/github-actions-ci.md`",
        f"› `{A}2026/09/26/github-actions-ci.md`",
    ),
    (
        "tasks/reference/book-and-docs-pipeline.md",
        "filed as `tasks/mark-basis-constants-for-doc-regions.md`)",
        f"filed as {GA}\n  `{A}2026/11/04/mark-basis-constants-for-doc-regions.md`)",
    ),
    (
        "tasks/archive/2026/09/06/renderer-model-matrix-from-gacalc.md",
        "geometricalgebra `tasks/matrix-template-compile-once.md`",
        f"{GA} `{A}2026/09/06/matrix-template-compile-once.md`",
    ),
    (
        "tasks/archive/2026/11/04/minimal-nested-image.md",
        "runClaudeInContainer `tasks/minimal-image-for-nested-podman-standard.md`",
        f"{RC} `{A}2026/11/15/minimal-image-for-nested-podman-standard.md`",
    ),
    (
        "tasks/archive/2026/07/09/gacalc-math-migration.md",
        "`/geometricalgebra/tasks/port-animation-layer-from-mvp.md`",
        f"{GA} `{A}2026/06/08/port-animation-layer-from-mvp.md`",
    ),
    (
        "tasks/archive/2026/07/09/math-demos-section-crossproduct-and-proof.md",
        "`geometricalgebra/tasks/show-mult-expand-numerators-not-denominators.md`",
        f"{GA} `{A}2026/06/15/show-mult-expand-numerators-not-denominators.md`",
    ),
    (
        "tasks/archive/2026/10/12/apply-python-coding-standard.md",
        "`tasks/split-python-standard-project-specifics.md`",
        f"`{A}2026/10/12/split-python-standard-project-specifics.md`",
    ),
    (
        "tasks/archive/2026/09/06/ty-0072-strictness-sweep.md",
        "`tasks/ty-invariance-transform-factories-bind-v.md`",
        f"`{A}2026/09/06/ty-invariance-transform-factories-bind-v.md`",
    ),
    (
        "tasks/archive/2026/06/13/update-emacs-packages-target.md",
        "(`spimulator/tasks/update-emacs-packages-target.md`,\n"
        "> `texExpToPng/tasks/update-emacs-packages-target.md`)",
        f"(github.com/billsix/spimulator `{A}2026/06/14/update-emacs-packages-target.md`,\n"
        f"> github.com/billsix/tex-expression-to-png "
        f"`{A}2026/06/14/update-emacs-packages-target.md`)",
    ),
    (
        "tasks/reference/design-decisions.md",
        "(see gacalc `tasks/reference/approximate-float-equality.md`)",
        f"(see {GA} `tasks/reference/approximate-float-equality.md`)",
    ),
    (
        "tasks/archive/2026/06/01/ports-render-options-to-imgui.md",
        "[`../tasks/ports-replace-cli-with-imgui.md`]"
        "(../tasks/ports-replace-cli-with-imgui.md)",
        f"`{A}2026/06/14/ports-replace-cli-with-imgui.md`",
    ),
    (
        "tasks/archive/2026/06/01/ports-render-options-to-imgui.md",
        "[`../tasks/ports-keyboard-standardization.md`]"
        "(../tasks/ports-keyboard-standardization.md)",
        f"`{A}2026/06/14/ports-keyboard-standardization.md`",
    ),
]


def main() -> None:
    """Apply each edit once; report applied, skipped and failed counts."""
    applied: int = 0
    skipped: int = 0
    for name, old, new in EDITS:
        path: pathlib.Path = ROOT / name
        text: str = path.read_text()
        match (text.count(old), new in text):
            case (1, _):
                path.write_text(text.replace(old, new))
                applied += 1
            case (0, True):
                skipped += 1
            case (count, _):
                raise SystemExit(f"{name}: old string occurs {count} times")
    print(f"applied {applied}, already applied {skipped}, of {len(EDITS)}")


if __name__ == "__main__":
    main()
