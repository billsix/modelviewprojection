#!/usr/bin/env python3
# Copyright (c) 2026 William Emerison Six
#
# The stricter-than-the-gate check for the SuperBible v4 AppState refactor.
# tools/check_local_annotations.py enforces an annotation on every ordinary
# binding; this task also wants types at the sites that checker exempts, and
# no module globals rebound from functions.  Reports, per file:
#   global/nonlocal   any `global` or `nonlocal` statement
#   unpack            an assignment whose target is a tuple/list (use an
#                     annotated intermediate plus indexed reads instead)
#   loop-target       a `for` target name with no annotation earlier in the
#                     same scope (declare `name: T` above the loop)
#   with-target       a `with ... as name` with no earlier annotation
#   param / return    a def parameter (not self/cls) or return with no
#                     annotation
# Exempt: the discard name `_`, comprehension and `except ... as` targets
# (the language has no place for a type there), and lambdas.
#
# Usage: strict_annotations.py <file-or-dir> [...]; exit 1 if anything found.

import ast
import pathlib
import sys
import typing

Scope = typing.Union[ast.Module, ast.FunctionDef, ast.AsyncFunctionDef]


def scope_nodes(scope: Scope) -> typing.Iterator[ast.AST]:
    """Walk ``scope`` without descending into nested functions/classes."""
    stack: list[ast.AST] = list(scope.body)
    while stack:
        node: ast.AST = stack.pop()
        yield node
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            continue
        stack.extend(ast.iter_child_nodes(node))


def target_names(target: ast.AST) -> list[ast.Name]:
    return [node for node in ast.walk(target) if isinstance(node, ast.Name)]


def check_scope(scope: Scope, path: pathlib.Path) -> list[str]:
    annotated: set[str] = set()
    if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
        arguments: ast.arguments = scope.args
        arg: ast.arg
        for arg in [
            *arguments.posonlyargs,
            *arguments.args,
            *arguments.kwonlyargs,
            *([arguments.vararg] if arguments.vararg else []),
            *([arguments.kwarg] if arguments.kwarg else []),
        ]:
            annotated.add(arg.arg)
    problems: list[str] = []
    # source order, so "annotated earlier" means earlier in the file
    node: ast.AST
    for node in sorted(
        scope_nodes(scope), key=lambda n: getattr(n, "lineno", 0)
    ):
        where: str = f"{path}:{getattr(node, 'lineno', 0)}"
        match node:
            case ast.AnnAssign(target=ast.Name(id=name)):
                annotated.add(name)
            case ast.Global() | ast.Nonlocal():
                problems.append(f"{where}: global/nonlocal")
            case ast.Assign(targets=targets) if any(
                isinstance(t, (ast.Tuple, ast.List)) for t in targets
            ):
                problems.append(f"{where}: unpack")
            case ast.For(target=target) | ast.AsyncFor(target=target):
                name_node: ast.Name
                for name_node in target_names(target):
                    if name_node.id != "_" and name_node.id not in annotated:
                        problems.append(
                            f"{where}: loop-target {name_node.id}"
                        )
            case ast.With(items=items) | ast.AsyncWith(items=items):
                item: ast.withitem
                for item in items:
                    if item.optional_vars is None:
                        continue
                    for name_node in target_names(item.optional_vars):
                        if (
                            name_node.id != "_"
                            and name_node.id not in annotated
                        ):
                            problems.append(
                                f"{where}: with-target {name_node.id}"
                            )
            case _:
                pass
    return problems


def check_file(path: pathlib.Path) -> list[str]:
    tree: ast.Module = ast.parse(path.read_text(), filename=str(path))
    problems: list[str] = check_scope(tree, path)
    node: ast.AST
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            problems.extend(check_scope(node, path))
            args: ast.arguments = node.args
            arg: ast.arg
            for arg in [*args.posonlyargs, *args.args, *args.kwonlyargs]:
                if arg.annotation is None and arg.arg not in ("self", "cls"):
                    problems.append(
                        f"{path}:{node.lineno}: param {node.name}({arg.arg})"
                    )
            for arg in [a for a in (args.vararg, args.kwarg) if a]:
                if arg.annotation is None:
                    problems.append(
                        f"{path}:{node.lineno}: param {node.name}(*{arg.arg})"
                    )
            if node.returns is None and node.name != "__init__":
                problems.append(f"{path}:{node.lineno}: return {node.name}")
    return problems


def main() -> None:
    paths: list[pathlib.Path] = []
    arg: str
    for arg in sys.argv[1:]:
        root: pathlib.Path = pathlib.Path(arg)
        paths.extend(sorted(root.rglob("*.py")) if root.is_dir() else [root])
    problems: list[str] = [p for path in paths for p in check_file(path)]
    print("\n".join(problems))
    print(f"{len(problems)} problem(s) in {len(paths)} file(s)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
