"""Runtime parser for the Thunderbird C++ data files.

The SuperBible source ships hand-modeled mesh data as 9000-line C++
files (body.cpp, glass.cpp) that are just big arrays of vertex,
normal, texture, and face-index data. The C++ demo links these as
extern arrays. The Python ports parse them at first import via simple
regex + ast.literal_eval so we don't need to maintain a separate
data file.

Used by thunderbird.py, thundergl.py, vbo.py in chapt11. Each calls
load_model(directory) and gets numpy arrays back.
"""

from __future__ import annotations

import ast
import os
import re
from typing import Dict

import numpy as np

# Cache parsed data per directory so re-imports are cheap
_cache: Dict[str, Dict[str, np.ndarray]] = {}


def _parse_array(text: str, name: str, dtype) -> np.ndarray:
    """Find a C++ array declaration like
        short face_indicies[3704][9] = { {1,2,3,...}, ... };
    and return it as a numpy ndarray of the given dtype.
    """
    # Locate the declaration; the body runs from the first '{' after '='
    # to the matching closing '};'.
    pattern = re.compile(
        r"\b" + re.escape(name) + r"\s*\[\d+\](?:\s*\[\d+\])?\s*=\s*",
        re.MULTILINE,
    )
    m = pattern.search(text)
    if not m:
        raise ValueError(f"Could not find array {name!r} in source")

    # Walk forward from the equals sign to the matching '};'
    start = text.index("{", m.end())
    depth = 0
    i = start
    while i < len(text):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
        i += 1
    else:
        raise ValueError(f"Unterminated body for {name!r}")

    body = text[start:end]
    # Strip C++ // line comments and /* block */ comments
    body = re.sub(r"//[^\n]*", "", body)
    body = re.sub(r"/\*.*?\*/", "", body, flags=re.DOTALL)
    # Strip C float suffix (1.23f -> 1.23) and translate {} to []
    body = re.sub(r"(\d)\s*[fF]\b", r"\1", body)
    body = body.replace("{", "[").replace("}", "]")
    return np.array(ast.literal_eval(body), dtype=dtype)


def load_model(directory: str) -> Dict[str, np.ndarray]:
    """Parse body.cpp and glass.cpp from the given directory; return a
    dict with the four body arrays and four glass arrays."""
    if directory in _cache:
        return _cache[directory]

    body_path = os.path.join(directory, "body.cpp")
    glass_path = os.path.join(directory, "glass.cpp")

    with open(body_path) as f:
        body_text = f.read()
    with open(glass_path) as f:
        glass_text = f.read()

    data = {
        "face_indices": _parse_array(body_text, "face_indicies", np.int32),
        "vertices": _parse_array(body_text, "vertices", np.float32),
        "normals": _parse_array(body_text, "normals", np.float32),
        "textures": _parse_array(body_text, "textures", np.float32),
        "face_indices_glass": _parse_array(
            glass_text, "face_indiciesGlass", np.int32),
        "vertices_glass": _parse_array(
            glass_text, "verticesGlass", np.float32),
        "normals_glass": _parse_array(
            glass_text, "normalsGlass", np.float32),
        "textures_glass": _parse_array(
            glass_text, "texturesGlass", np.float32),
    }
    _cache[directory] = data
    return data
