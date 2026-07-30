"""Rewrite positional arguments to keyword arguments across a Python tree.

A codemod for the behaviour-faithful ports (the keyword-argument rule). For
every call in the tree whose callee can be resolved to a known signature,
positional arguments are rewritten as ``name=value`` under these rules:

* Calls with a single argument are left alone (nothing to disambiguate).
* Calls using ``*args`` / ``**kwargs`` splats are left alone.
* **Project APIs** (functions and dataclasses defined in the tree, PyOpenGL's
  Python-level convenience functions, imgui_bundle, glfw): every positional
  argument is keyworded.
* **Library callees** (numpy, the standard library, builtins, anything else
  resolved through an imported module): the required leading parameters stay
  positional, so ``np.cross(a, b)`` and ``re.sub(p, r, s)`` keep their shape;
  only parameters that have a default (``dtype=``, ``axis=``, ``mode=``,
  ``start=``) are keyworded.
* PyOpenGL's raw ctypes functions and its array-converting ``Wrapper``
  functions reject keyword arguments at the call layer (verified under a live
  GL context), so they are left positional and counted as exempt.
* Positional-only parameters and arguments that would land in a callee's
  ``*args`` are never keyworded.

The edit is a pure insertion of ``name=`` in front of each argument's first
token (found with ``tokenize``, so parenthesised or multi-line arguments are
handled), which keeps comments and layout; ``ruff format`` reflows afterwards.
Running the script twice must report zero insertions on the second run.

When to run: ``--check`` before and after editing anything under a tree that
is under the rule (the Red Book 9e tree; §10 lists it);
without ``--check`` to apply the rewrite after adding a demo or a helper, or
to bring another port tree under the same rule.

Usage (from anywhere, with the project venv so numpy/glfw/imgui/OpenGL
import)::

    python tools/keywordify.py [--check] [--verbose] [TREE]

``TREE`` defaults to ``ports/openglsuperbiblev4`` under the repo root;
in-repo callees are resolved from the tree's own top-level ``_*.py`` modules.
``--check`` writes nothing and exits 1 if any insertion would be made.
"""

from __future__ import annotations

import argparse
import ast
import builtins
import importlib
import inspect
import io
import pathlib
import re
import sys
import tokenize
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

REPO: pathlib.Path = (
    pathlib.Path(__file__).resolve().parents[1]
)  # tools/
DEFAULT_TREE: pathlib.Path = REPO / "ports" / "openglsuperbiblev4"

#: Module aliases whose callees get the project rule (keyword everything).
PROJECT_MODULES: frozenset[str] = frozenset({"glfw", "imgui_bundle.imgui"})


@dataclass(frozen=True, slots=True)
class Sig:
    """What the codemod needs to know about one callee."""

    family: str
    posonly: tuple[str, ...]
    regular: tuple[str, ...]
    defaulted: frozenset[str]
    has_vararg: bool
    project_rule: bool

    def keyword_for(self, index: int, n_positional: int) -> str | None:
        """Keyword for the positional argument at ``index``; None = leave."""
        if n_positional > len(self.posonly) + len(self.regular):
            return None  # the tail would land in *args (or is an error)
        if index < len(self.posonly):
            return None
        name: str = self.regular[index - len(self.posonly)]
        if not self.project_rule and name not in self.defaulted:
            return None
        return name


@dataclass(slots=True)
class Insertion:
    row: int
    col: int
    text: str


@dataclass(slots=True)
class Report:
    args_keyworded: int = 0
    calls_rewritten: int = 0
    files_changed: int = 0
    by_family: Counter[str] = field(default_factory=Counter)
    skipped: Counter[str] = field(default_factory=Counter)
    skipped_callees: Counter[tuple[str, str]] = field(default_factory=Counter)
    rewrites: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------
# Signatures from in-repo source (parsed, never imported: the modules open GL)
# --------------------------------------------------------------------------


def _sig_from_arguments(
    args: ast.arguments, drop_first: bool, family: str
) -> Sig:
    posonly: list[str] = [a.arg for a in args.posonlyargs]
    regular: list[str] = [a.arg for a in args.args]
    all_positional: list[str] = posonly + regular
    if drop_first and all_positional:
        dropped: str = all_positional.pop(0)
        if posonly and posonly[0] == dropped:
            posonly.pop(0)
        else:
            regular.pop(0)
    defaulted_names: list[str] = all_positional[
        len(all_positional) - len(args.defaults) :
    ]
    return Sig(
        family=family,
        posonly=tuple(posonly),
        regular=tuple(regular),
        defaulted=frozenset(defaulted_names),
        has_vararg=args.vararg is not None,
        project_rule=True,
    )


def _is_dataclass_decorator(node: ast.expr) -> ast.Call | ast.Name | None:
    if isinstance(node, ast.Name) and node.id == "dataclass":
        return node
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "dataclass"
    ):
        return node
    return None


def _dataclass_sig(
    cls: ast.ClassDef, classes: dict[str, ast.ClassDef], family: str
) -> Sig | None:
    """Fields of a ``@dataclass`` in ``__init__`` order, bases first."""
    decorator: ast.Call | ast.Name | None = None
    for d in cls.decorator_list:
        decorator = _is_dataclass_decorator(d)
        if decorator is not None:
            break
    if decorator is None:
        return None
    kw_only: bool = isinstance(decorator, ast.Call) and any(
        k.arg == "kw_only"
        and isinstance(k.value, ast.Constant)
        and k.value.value is True
        for k in decorator.keywords
    )
    names: list[str] = []
    defaulted: set[str] = set()
    for base in cls.bases:
        if isinstance(base, ast.Name) and base.id in classes:
            base_sig: Sig | None = _dataclass_sig(
                classes[base.id], classes, family
            )
            if base_sig is None:
                return None
            names.extend(base_sig.regular)
            defaulted.update(base_sig.defaulted)
        elif not (isinstance(base, ast.Name) and base.id == "object"):
            return None
    for stmt in cls.body:
        if not isinstance(stmt, ast.AnnAssign) or not isinstance(
            stmt.target, ast.Name
        ):
            continue
        if "ClassVar" in ast.unparse(stmt.annotation):
            continue
        if (
            isinstance(stmt.value, ast.Call)
            and isinstance(stmt.value.func, ast.Name)
            and stmt.value.func.id == "field"
            and any(
                k.arg == "init"
                and isinstance(k.value, ast.Constant)
                and k.value.value is False
                for k in stmt.value.keywords
            )
        ):
            continue
        names.append(stmt.target.id)
        if stmt.value is not None:
            defaulted.add(stmt.target.id)
    if kw_only:
        names = []
    return Sig(
        family=family,
        posonly=(),
        regular=tuple(names),
        defaulted=frozenset(defaulted),
        has_vararg=False,
        project_rule=True,
    )


def _class_sig(
    cls: ast.ClassDef, classes: dict[str, ast.ClassDef], family: str
) -> Sig | None:
    sig: Sig | None = _dataclass_sig(cls, classes, family)
    if sig is not None:
        return sig
    for stmt in cls.body:
        if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__":
            return _sig_from_arguments(stmt.args, True, family)
    return None


def source_table(tree: ast.Module, family: str) -> dict[str, Sig]:
    """Callable names defined in a module, by name (ambiguous names dropped)."""
    functions: dict[str, list[ast.FunctionDef]] = {}
    classes: dict[str, ast.ClassDef] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.setdefault(node.name, []).append(node)
        elif isinstance(node, ast.ClassDef):
            classes[node.name] = node
    table: dict[str, Sig] = {}
    for name, defs in functions.items():
        sigs: set[Sig] = {
            _sig_from_arguments(d.args, False, family) for d in defs
        }
        if len(sigs) == 1:
            table[name] = sigs.pop()
    for name, cls in classes.items():
        cls_sig: Sig | None = _class_sig(cls, classes, family)
        if cls_sig is not None:
            table[name] = cls_sig
    return table


# --------------------------------------------------------------------------
# Signatures from live objects (third-party libraries and PyOpenGL)
# --------------------------------------------------------------------------


def sig_from_signature(
    signature: inspect.Signature, family: str, project_rule: bool, drop: int = 0
) -> Sig:
    params: list[inspect.Parameter] = list(signature.parameters.values())[drop:]
    posonly: list[str] = [p.name for p in params if p.kind is p.POSITIONAL_ONLY]
    regular: list[str] = [
        p.name for p in params if p.kind is p.POSITIONAL_OR_KEYWORD
    ]
    defaulted: frozenset[str] = frozenset(
        p.name for p in params if p.default is not p.empty
    )
    return Sig(
        family=family,
        posonly=tuple(posonly),
        regular=tuple(regular),
        defaulted=defaulted,
        has_vararg=any(p.kind is p.VAR_POSITIONAL for p in params),
        project_rule=project_rule,
    )


_PYBIND_PARAM: re.Pattern[str] = re.compile(
    r"^(\*{0,2})([A-Za-z_][A-Za-z0-9_]*)\s*(?::[^=]*)?(=.*)?$"
)


def sig_from_pybind_doc(obj: Any, name: str, family: str) -> Sig | None:
    """Parse the first overload of a pybind11 docstring signature line."""
    doc: str = obj.__doc__ or ""
    match: re.Match[str] | None = re.search(
        rf"^(?:\d+\. )?{re.escape(name)}\((.*)\)\s*->", doc, re.MULTILINE
    )
    if match is None:
        return None
    # split the parameter list on top-level commas only
    params: list[str] = []
    depth: int = 0
    current: list[str] = []
    for ch in match.group(1):
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            params.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        params.append("".join(current).strip())
    regular: list[str] = []
    defaulted: set[str] = set()
    has_vararg: bool = False
    for p in params:
        if not p:
            continue
        m: re.Match[str] | None = _PYBIND_PARAM.match(p)
        if m is None:
            return None
        stars, pname, default = m.groups()
        if stars:
            has_vararg = has_vararg or stars == "*"
            continue
        regular.append(pname)
        if default:
            defaulted.add(pname)
    return Sig(
        family=family,
        posonly=(),
        regular=tuple(regular),
        defaulted=frozenset(defaulted),
        has_vararg=has_vararg,
        project_rule=True,
    )


def gl_kind(obj: Any) -> str:
    """raw / Wrapper / lazy / function — how PyOpenGL built this callable."""
    mro: list[str] = [c.__name__ for c in type(obj).__mro__]
    if "_NullFunctionPointer" in mro:
        return "raw"
    if "Wrapper" in mro:
        return "Wrapper"
    if type(obj).__module__ == "OpenGL.lazywrapper":
        return "lazy"
    if inspect.isfunction(obj):
        return "function"
    return "other"


def gl_python_function(obj: Any) -> Any | None:
    """The Python ``def`` behind a lazy wrapper (its first parameter is the
    base operation, dropped by the caller)."""
    for attr in ("wrapperFunction",):
        fn: Any = getattr(obj, attr, None) or getattr(type(obj), attr, None)
        if inspect.isfunction(fn):
            return fn
    for value in vars(type(obj)).values():
        if inspect.isfunction(value) and value.__name__ == type(obj).__name__:
            return value
    return None


class Resolver:
    """Turns a call's ``func`` expression into a ``Sig`` (or a skip reason)."""

    def __init__(self, inrepo: dict[str, dict[str, Sig]]) -> None:
        self.inrepo: dict[str, dict[str, Sig]] = inrepo
        # The C accelerator's Curry hides ``wrapperFunction``; the pure-Python
        # one exposes it. Signatures are identical either way, so analyse
        # with the accelerator off (this must run before OpenGL.GL imports).
        opengl: Any = importlib.import_module("OpenGL")
        opengl.USE_ACCELERATE = False
        self.gl: Any = importlib.import_module("OpenGL.GL")
        self.cache: dict[tuple[str, ...], Sig | str] = {}

    def module(self, dotted: str) -> Any | None:
        try:
            return importlib.import_module(dotted)
        except Exception:  # noqa: BLE001 — unimportable: resolve as unknown
            return None

    def from_object(
        self, obj: Any, name: str, family: str, project_rule: bool
    ) -> Sig | str:
        if family == "imgui":
            # pybind11 reports ``(*args, **kwargs)`` to inspect; the real
            # parameter names are only in the docstring's signature line
            sig: Sig | None = sig_from_pybind_doc(obj, name, family)
            return sig if sig is not None else "no-signature"
        try:
            return sig_from_signature(
                inspect.signature(obj), family, project_rule
            )
        except (TypeError, ValueError):
            return "no-signature"

    def from_gl(self, name: str) -> Sig | str:
        obj: Any = getattr(self.gl, name, None)
        if obj is None:
            return "unknown-gl-name"
        kind: str = gl_kind(obj)
        if kind in ("raw", "Wrapper"):
            return f"gl-{kind}"
        if kind == "lazy":
            fn: Any | None = gl_python_function(obj)
            if fn is None:
                return "gl-lazy-unresolved"
            return sig_from_signature(inspect.signature(fn), "gl", True, drop=1)
        if kind == "function":
            return sig_from_signature(inspect.signature(obj), "gl", True)
        return "gl-other"

    def resolve(
        self, chain: tuple[str, ...], aliases: dict[str, str]
    ) -> Sig | str:
        key: tuple[str, ...] = (aliases.get(chain[0], chain[0]), *chain[1:])
        if key in self.cache:
            return self.cache[key]
        result: Sig | str = self._resolve(key)
        self.cache[key] = result
        return result

    def _resolve(self, key: tuple[str, ...]) -> Sig | str:
        head: str = key[0]
        rest: tuple[str, ...] = key[1:]
        if head in self.inrepo:
            if len(rest) != 1:
                return "inrepo-nested-attribute"
            return self.inrepo[head].get(rest[0], "inrepo-unknown-name")
        if head in ("OpenGL.GL", "_common.GL"):
            if len(rest) != 1:
                return "gl-nested-attribute"
            return self.from_gl(rest[0])
        family: str = head.split(".")[0]
        project_rule: bool = head in PROJECT_MODULES
        obj: Any | None = self.module(head)
        if obj is None:
            # `from X import Y`: head is "X.Y" — import X, take attribute Y
            parent, _, leaf = head.rpartition(".")
            parent_mod: Any | None = self.module(parent) if parent else None
            if parent_mod is None:
                return "unknown-module"
            obj = getattr(parent_mod, leaf, None)
            if obj is None:
                return "unknown-attribute"
            family = parent.split(".")[0]
        if head == "imgui_bundle.imgui":
            family = "imgui"  # pybind11: signatures come from the docstrings
        for attr in rest:
            obj = getattr(obj, attr, None)
            if obj is None:
                return "unknown-attribute"
        if not callable(obj):
            return "not-callable"
        return self.from_object(obj, key[-1], family, project_rule)


# --------------------------------------------------------------------------
# Per-file work
# --------------------------------------------------------------------------


def import_aliases(tree: ast.Module) -> dict[str, str]:
    """Local name -> dotted module (or ``module.attr``) for every import."""
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                aliases[a.asname or a.name.split(".")[0]] = a.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            for a in node.names:
                aliases[a.asname or a.name] = f"{node.module}.{a.name}"
    return aliases


def attribute_chain(node: ast.expr) -> tuple[str, ...] | None:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return tuple(reversed(parts))
    return None


def callee_shape(node: ast.expr) -> str:
    """Why an unresolvable callee is unresolvable, for the report."""
    if isinstance(node, ast.Attribute):
        return "method-on-expression"
    if isinstance(node, ast.Subscript):
        return "subscript-call"
    if isinstance(node, ast.Call):
        return "call-result-call"
    return type(node).__name__.lower() + "-call"


def argument_starts(
    tokens: list[tokenize.TokenInfo],
    token_index: dict[tuple[int, int], int],
    open_paren_at: tuple[int, int],
    n_positional: int,
) -> list[tuple[int, int]]:
    """Start (row, col) of the first ``n_positional`` argument segments."""
    i: int = token_index[open_paren_at]
    assert tokens[i].string == "(", tokens[i]
    depth: int = 0
    starts: list[tuple[int, int]] = []
    expecting_start: bool = True
    i += 1
    while i < len(tokens):
        tok: tokenize.TokenInfo = tokens[i]
        if tok.type in (
            tokenize.NL,
            tokenize.NEWLINE,
            tokenize.COMMENT,
            tokenize.INDENT,
            tokenize.DEDENT,
        ):
            i += 1
            continue
        if expecting_start:
            if tok.type == tokenize.OP and tok.string == ")" and depth == 0:
                break
            starts.append(tok.start)
            if len(starts) == n_positional:
                break
            expecting_start = False
        if tok.type == tokenize.OP:
            if tok.string in "([{":
                depth += 1
            elif tok.string in ")]}":
                if depth == 0:
                    break
                depth -= 1
            elif tok.string == "," and depth == 0:
                expecting_start = True
        i += 1
    return starts


def byte_to_char_col(line: str, byte_col: int) -> int:
    return len(line.encode("utf-8")[:byte_col].decode("utf-8", "ignore"))


def rewrite_file(
    path: pathlib.Path,
    resolver: Resolver,
    local_table: dict[str, Sig],
    report: Report,
    verbose: bool,
) -> list[Insertion]:
    src: str = path.read_text(encoding="utf-8")
    tree: ast.Module = ast.parse(src)
    aliases: dict[str, str] = import_aliases(tree)
    lines: list[str] = src.splitlines(keepends=True)
    tokens: list[tokenize.TokenInfo] = list(
        tokenize.generate_tokens(io.StringIO(src).readline)
    )
    token_index: dict[tuple[int, int], int] = {
        t.start: i for i, t in enumerate(tokens)
    }
    insertions: list[Insertion] = []
    rel: str = str(path.relative_to(REPO))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        n_args: int = len(node.args) + len(node.keywords)
        if n_args < 2:
            report.skipped["single-argument"] += 1
            continue
        if any(isinstance(a, ast.Starred) for a in node.args) or any(
            k.arg is None for k in node.keywords
        ):
            report.skipped["starred"] += 1
            continue
        if not node.args:
            report.skipped["already-keyword-only"] += 1
            continue
        sig: Sig | str
        if isinstance(node.func, ast.Name):
            if node.func.id in local_table:
                sig = local_table[node.func.id]
            elif node.func.id in aliases:
                sig = resolver.resolve((node.func.id,), aliases)
            elif hasattr(builtins, node.func.id):
                sig = resolver.from_object(
                    getattr(builtins, node.func.id),
                    node.func.id,
                    "builtins",
                    False,
                )
            else:
                sig = "unknown-name"
        else:
            chain: tuple[str, ...] | None = attribute_chain(node.func)
            if chain is None or chain[0] not in aliases:
                sig = callee_shape(node.func)
            else:
                sig = resolver.resolve(chain, aliases)
        callee: str = ast.unparse(node.func)
        if isinstance(sig, str):
            report.skipped[sig] += 1
            report.skipped_callees[(sig, callee)] += 1
            continue
        n_positional: int = len(node.args)
        names: list[str | None] = [
            sig.keyword_for(i, n_positional) for i in range(n_positional)
        ]
        if not any(names):
            reason: str = (
                "library-required-params"
                if not sig.project_rule
                else "vararg-or-posonly"
            )
            report.skipped[reason] += 1
            report.skipped_callees[(reason, callee)] += 1
            continue
        # a keyword may not precede a positional: once we keyword argument i,
        # every later positional must be keyworded too (or none of them)
        first: int = next(i for i, n in enumerate(names) if n)
        if any(n is None for n in names[first:]):
            report.skipped["would-order-keyword-before-positional"] += 1
            continue
        existing: set[str] = {k.arg for k in node.keywords if k.arg}
        if existing & {n for n in names if n}:
            report.skipped["duplicate-keyword"] += 1
            continue
        end_lineno: int = node.func.end_lineno or node.func.lineno
        func_end: tuple[int, int] = (
            end_lineno,
            byte_to_char_col(
                lines[end_lineno - 1], node.func.end_col_offset or 0
            ),
        )
        paren_idx: int | None = next(
            (
                i
                for i in range(token_index.get(func_end, 0), len(tokens))
                if tokens[i].start >= func_end
                and tokens[i].type == tokenize.OP
                and tokens[i].string == "("
            ),
            None,
        )
        if paren_idx is None:
            report.skipped["paren-not-found"] += 1
            continue
        starts: list[tuple[int, int]] = argument_starts(
            tokens, token_index, tokens[paren_idx].start, n_positional
        )
        if len(starts) != n_positional:
            report.skipped["segment-count-mismatch"] += 1
            continue
        for (row, col), name in zip(starts, names, strict=True):
            if name is None:
                continue
            insertions.append(Insertion(row, col, f"{name}="))
            report.args_keyworded += 1
            report.by_family[sig.family] += 1
            if verbose:
                report.rewrites.append(f"{rel}:{row}: {callee}({name}=)")
        report.calls_rewritten += 1
    return insertions


def apply_insertions(src: str, insertions: list[Insertion]) -> str:
    lines: list[str] = src.splitlines(keepends=True)
    offsets: list[int] = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    out: str = src
    for ins in sorted(insertions, key=lambda i: (i.row, i.col), reverse=True):
        pos: int = offsets[ins.row - 1] + ins.col
        out = out[:pos] + ins.text + out[pos:]
    return out


def main() -> int:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "tree", nargs="?", type=pathlib.Path, default=DEFAULT_TREE
    )
    parser.add_argument("--check", action="store_true", help="report only")
    parser.add_argument("--verbose", action="store_true")
    ns: argparse.Namespace = parser.parse_args()
    tree_root: pathlib.Path = ns.tree.resolve()

    files: list[pathlib.Path] = sorted(tree_root.rglob("*.py"))
    # in-repo modules: every top-level module of the tree, keyed by module name
    inrepo: dict[str, dict[str, Sig]] = {}
    for p in files:
        if p.parent == tree_root:
            inrepo[p.stem] = source_table(
                ast.parse(p.read_text(encoding="utf-8")), "inrepo"
            )
    resolver: Resolver = Resolver(inrepo)
    report: Report = Report()
    for path in files:
        local_table: dict[str, Sig] = source_table(
            ast.parse(path.read_text(encoding="utf-8")), "inrepo"
        )
        insertions: list[Insertion] = rewrite_file(
            path, resolver, local_table, report, ns.verbose
        )
        if not insertions:
            continue
        report.files_changed += 1
        if ns.check:
            continue
        new_src: str = apply_insertions(
            path.read_text(encoding="utf-8"), insertions
        )
        ast.parse(new_src)  # the rewrite must still be valid Python
        path.write_text(new_src, encoding="utf-8")

    verb: str = "would keyword" if ns.check else "keyworded"
    print(  # noqa: T201 CLI output
        f"{verb} {report.args_keyworded} arguments in "
        f"{report.calls_rewritten} calls across {report.files_changed} files"
    )
    for fam, n in sorted(report.by_family.items()):
        print(f"  {fam:10s} {n:5d} arguments")  # noqa: T201 CLI output
    print("skipped calls, by reason:")  # noqa: T201 CLI output
    for reason, n in report.skipped.most_common():
        print(f"  {reason:40s} {n:5d}")  # noqa: T201 CLI output
    if ns.verbose:
        print("skipped callees (reason, callee, count):")  # noqa: T201
        for (reason, callee), n in report.skipped_callees.most_common():
            print(f"  {reason:32s} {callee:40s} {n:5d}")  # noqa: T201
        for line in report.rewrites:
            print(line)  # noqa: T201 CLI output
    return 1 if ns.check and report.args_keyworded else 0


if __name__ == "__main__":
    sys.exit(main())
