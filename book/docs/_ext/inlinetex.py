"""Sphinx extension: ``.. inlinetex::`` directive.

Lets a chapter author write LaTeX inline in an .rst file. The directive
hashes the LaTeX content (plus the requested size) to a stable filename,
calls ``texExpToPng`` to render it to ``_static/inlinetex/<hash>.png``,
and emits an image (or figure, if a caption is given) pointing at the
generated file.

Identical expressions dedupe by hash. The on-disk PNG is the cache: if
the file already exists for a given hash, ``texExpToPng`` is skipped.
"""

import hashlib
import os
import re
import subprocess
import tempfile

from docutils import nodes, utils
from docutils.parsers.rst import Directive, directives
from sphinx.util import logging


logger = logging.getLogger(__name__)

TEXEXPTOPNG_BIN = "texExpToPng"
DEFAULT_SIZE = 300
OUTPUT_SUBDIR = ("_static", "inlinetex")


def _normalize(content: str) -> str:
    return re.sub(r"\s+", " ", content).strip()


def _hash_for(content: str, size: int) -> str:
    h = hashlib.sha1()
    h.update(_normalize(content).encode("utf-8"))
    h.update(f"|size={size}".encode("utf-8"))
    return h.hexdigest()[:12]


def _generate_png(latex: str, size: int, out_path: str) -> None:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".tex", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(latex)
        tex_path = tmp.name
    try:
        result = subprocess.run(
            [
                TEXEXPTOPNG_BIN,
                "--file", tex_path,
                "--size", str(size),
                "--output", out_path,
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"texExpToPng failed (exit {result.returncode}). "
                f"latex={latex!r}. stderr={result.stderr.strip()!r}"
            )
    finally:
        try:
            os.unlink(tex_path)
        except OSError:
            pass


def _align_choice(arg):
    return directives.choice(arg, ("left", "center", "right"))


class InlineTex(Directive):
    has_content = True
    optional_arguments = 0
    required_arguments = 0

    option_spec = {
        "size": directives.positive_int,
        "align": _align_choice,
        "alt": directives.unchanged,
        "class": directives.class_option,
        "figclass": directives.class_option,
        "caption": directives.unchanged,
    }

    def run(self):
        if not self.content:
            error = self.state_machine.reporter.error(
                "inlinetex directive requires LaTeX content in its body",
                line=self.lineno,
            )
            return [error]

        latex = "\n".join(self.content)
        env = self.state.document.settings.env
        size = self.options.get("size", env.config.inlinetex_default_size)
        digest = _hash_for(latex, size)

        out_dir_abs = os.path.join(env.app.srcdir, *OUTPUT_SUBDIR)
        out_path_abs = os.path.join(out_dir_abs, f"{digest}.png")

        if not os.path.exists(out_path_abs):
            try:
                _generate_png(latex, size, out_path_abs)
                logger.info(
                    "inlinetex: generated %s for %r",
                    os.path.relpath(out_path_abs, env.app.srcdir),
                    _normalize(latex),
                )
            except FileNotFoundError:
                logger.warning(
                    "inlinetex: %s not found on PATH; "
                    "rendering source as literal block. expression=%r",
                    TEXEXPTOPNG_BIN, latex,
                )
                literal = nodes.literal_block(latex, latex)
                literal["language"] = "latex"
                return [literal]
            except RuntimeError as exc:
                error = self.state_machine.reporter.error(
                    f"inlinetex: {exc}",
                    line=self.lineno,
                )
                return [error]

        # Leading slash => relative to source root (book/docs/), so the
        # directive works from any chapter regardless of its depth.
        uri = "/" + "/".join(OUTPUT_SUBDIR) + f"/{digest}.png"

        image_opts = {}
        if "align" in self.options:
            image_opts["align"] = self.options["align"]
        image_opts["alt"] = self.options.get("alt", _normalize(latex))
        if "class" in self.options:
            image_opts["classes"] = self.options["class"]

        image = nodes.image(uri=uri, **image_opts)

        # Wrap in a figure node whenever a figure-shaped option was given.
        # Mirrors the docutils ``figure`` directive's behavior so existing
        # ``.. figure::`` callsites can be 1:1 swapped to ``.. inlinetex::``.
        if "caption" in self.options or "figclass" in self.options:
            figure = nodes.figure("", image)
            if "figclass" in self.options:
                figure["classes"].extend(self.options["figclass"])
            if "align" in self.options:
                figure["align"] = self.options["align"]
            if "caption" in self.options:
                caption_text = self.options["caption"]
                figure += nodes.caption(
                    caption_text, "", nodes.Text(caption_text)
                )
            return [figure]

        return [image]


def inlinetex_role(name, rawtext, text, lineno, inliner,
                   options=None, content=None):
    """Inline-math role: ``:inlinetex:`x^2 + y^2 = z^2``` → inline image.

    Wraps the role text in ``$ ... $`` for inline math context, hashes
    via the same scheme as the directive, generates the PNG on cache
    miss, and emits an inline ``image`` node with the
    ``inlinetex-inline`` class so a stylesheet can baseline-align it
    if needed.
    """
    env = inliner.document.settings.env
    size = env.config.inlinetex_default_size

    # docutils replaces backslashes with NULs during inline-text parsing.
    # Restore them — without this, ``\times`` arrives as ``\x00times`` and
    # texExpToPng chokes on the NUL when it runs LaTeX.
    text = utils.unescape(text, restore_backslashes=True)
    latex = f"$ {text} $"
    digest = _hash_for(latex, size)

    out_dir_abs = os.path.join(env.app.srcdir, *OUTPUT_SUBDIR)
    out_path_abs = os.path.join(out_dir_abs, f"{digest}.png")

    if not os.path.exists(out_path_abs):
        try:
            _generate_png(latex, size, out_path_abs)
            logger.info(
                "inlinetex (role): generated %s for %r",
                os.path.relpath(out_path_abs, env.app.srcdir),
                _normalize(latex),
            )
        except FileNotFoundError:
            logger.warning(
                "inlinetex (role): %s not found on PATH; "
                "rendering source as literal. expression=%r",
                TEXEXPTOPNG_BIN, latex,
            )
            return [nodes.literal(rawtext, latex)], []
        except RuntimeError as exc:
            msg = inliner.reporter.error(
                f"inlinetex role: {exc}", line=lineno,
            )
            return [inliner.problematic(rawtext, rawtext, msg)], [msg]

    uri = "/" + "/".join(OUTPUT_SUBDIR) + f"/{digest}.png"
    image = nodes.image(
        rawtext,
        uri=uri,
        alt=_normalize(latex),
        classes=["inlinetex-inline"],
    )
    return [image], []


def setup(app):
    app.add_config_value("inlinetex_default_size", DEFAULT_SIZE, "env")
    app.add_directive("inlinetex", InlineTex)
    app.add_role("inlinetex", inlinetex_role)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
