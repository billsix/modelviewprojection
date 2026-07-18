# Copyright (c) 2026 William Emerison Six
#

"""Guard: dataclass fields on Actor subclasses must not shadow Actor properties.

``dataclasses`` treats ANY class attribute as a field's default value, so a
game dataclass declaring a field named after one of Actor's properties (e.g.
``pos: InitVar[...]``) silently picks up the *property object* as its
default -- which then explodes at class-definition time with "non-default
argument follows default argument" as soon as a non-default field follows
(and worse, only for SOME field orders: bunner survived by luck while cavern
and avenger crashed, 2026-07-09). That is why those fields are named
``spawn_pos``. This test makes the constraint mechanical instead of tribal:
it AST-scans every Actor-rooted dataclass in the games against the property
names AST-scanned out of ``pgzero_gl/actor.py`` -- no imports, no GL needed.
"""

import ast
import pathlib

CTC = (
    pathlib.Path(__file__).resolve().parent.parent / "ports" / "codetheclassics"
)
GAMES = sorted(CTC.glob("vol*/*/*.py"))


def actor_property_names() -> set[str]:
    tree = ast.parse((CTC / "pgzero_gl" / "actor.py").read_text())
    actor = next(
        n
        for n in tree.body
        if isinstance(n, ast.ClassDef) and n.name == "Actor"
    )
    names: set[str] = set()
    for node in actor.body:
        if isinstance(node, ast.FunctionDef) and any(
            (isinstance(d, ast.Name) and d.id == "property")
            or (isinstance(d, ast.Attribute) and d.attr == "setter")
            for d in node.decorator_list
        ):
            names.add(node.name)
    return names


def test_actor_properties_exist() -> None:
    props = actor_property_names()
    # the core pgzero surface must be present (a rename would silently
    # defang the collision check below)
    assert {"x", "y", "pos", "image", "anchor", "angle"} <= props


def test_no_dataclass_field_shadows_an_actor_property() -> None:
    props = actor_property_names()
    offenders: list[str] = []
    for game in GAMES:
        tree = ast.parse(game.read_text())
        classes = {
            n.name: n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)
        }
        # transitively Actor-rooted classes (by base-name within the module)
        actorish: set[str] = set()
        changed = True
        while changed:
            changed = False
            for name, node in classes.items():
                bases = {b.id for b in node.bases if isinstance(b, ast.Name)}
                if name not in actorish and (
                    "Actor" in bases or bases & actorish
                ):
                    actorish.add(name)
                    changed = True
        for name in actorish:
            node = classes[name]
            is_dataclass = any(
                (
                    isinstance(d, ast.Call)
                    and getattr(d.func, "id", "") == "dataclass"
                )
                or getattr(d, "id", "") == "dataclass"
                for d in node.decorator_list
            )
            if not is_dataclass:
                continue
            for stmt in node.body:
                if (
                    isinstance(stmt, ast.AnnAssign)
                    and isinstance(stmt.target, ast.Name)
                    and stmt.target.id in props
                ):
                    offenders.append(
                        f"{game.relative_to(CTC)}:{stmt.lineno}: "
                        f"{name}.{stmt.target.id} shadows "
                        f"Actor.{stmt.target.id}"
                    )
    assert not offenders, (
        "dataclass fields shadowing Actor properties (rename them, e.g. "
        "spawn_pos):\n" + "\n".join(offenders)
    )
