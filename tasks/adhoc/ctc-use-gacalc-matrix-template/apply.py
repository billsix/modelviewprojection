#!/usr/bin/env python3
"""Delete the ten per-game `MatrixTemplate` copies and build `MODEL` with
gacalc's `to_matrix_template` (gacalc >= 0.0.20). One-shot codemod for
tasks/ctc-use-gacalc-matrix-template.md. Idempotent: re-running is a no-op.
Run from the repo root:  python3 tasks/adhoc/ctc-use-gacalc-matrix-template/apply.py
Then `ruff check --fix` (drops now-unused imports) and `ruff format`.
"""
import re, pathlib, subprocess

# The comment block + the ~50-line MatrixTemplate class (byte-identical across
# all ten engines): remove from the comment's first line through the class's
# final `return m`.
CLASS_RE = re.compile(
    r"\n# The sprite's model matrix.*?\n        return m\n",
    re.S,
)

MODEL_OLD = """MODEL: MatrixTemplate = MatrixTemplate.compile(
    compose(
        [
            translate(b=_TX * g3.Vector.e_1 + _TY * g3.Vector.e_2),
            scale_non_uniform(_W, _H, 1),
        ]
    ),
    (_TX, _TY, _W, _H),
)"""

MODEL_NEW = """MODEL: MatrixTemplate = compose(
    [
        translate(b=_TX * g3.Vector.e_1 + _TY * g3.Vector.e_2),
        scale_non_uniform(_W, _H, 1),
    ]
).to_matrix_template(g3.Vector, (_TX, _TY, _W, _H))"""

root = pathlib.Path(
    subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).decode().strip()
)
files = sorted(
    p for p in root.glob("ports/codetheclassics/vol*/**/*.py")
    if "class MatrixTemplate" in p.read_text()
)
changed = 0
for f in files:
    s = f.read_text()
    new = CLASS_RE.sub("\n", s, count=1)
    new = new.replace(MODEL_OLD, MODEL_NEW)
    if "MatrixTemplate" in new and "from gacalc.transforms import (\n    MatrixTemplate," not in new:
        new = new.replace("from gacalc.transforms import (\n",
                          "from gacalc.transforms import (\n    MatrixTemplate,\n", 1)
    if new != s:
        f.write_text(new)
        changed += 1
        print("rewrote", f.relative_to(root))
print(f"{changed} file(s) changed ({len(files)} had MatrixTemplate)")
