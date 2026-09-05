#!/usr/bin/env python3
# Copyright (c) 2026 William Emerison Six
#
# Codemod for tasks/codetheclassics-tighten-games.md (maintainer decision,
# 2026-09-05): turn each tightened game's GL-resource classes into DATACLASSES
# OF STATE built by FACTORY FUNCTIONS. A hand-rolled __init__ that computes a
# dozen attributes from one or two inputs (compile + link a program, query its
# uniforms, upload a quad) becomes:
#
#   * `Uniforms`  -- the seven uniform locations, one named value (was u_*)
#   * `GLBuffer`  -- a vertex array + its vertex buffer (was quad_vao/quad_vbo,
#                    prim_vao/prim_vbo)
#   * `Renderer`  -- a @dataclass(slots=True, eq=False) of width/height/ortho/
#                    program/uniforms/quad[/prim] (+ the per-frame fb size)
#   * `make_renderer(width, height)` -- the factory that does the GL work, in
#                    the SAME GL call order as the old __init__, then constructs
#   * `Image`     -- a dataclass of (rgba, _tex) with width/height properties,
#                    built by `load_image(path)` / `image_from_rgba(arr)`
#   * the fixed-function `Renderer1x` (boing_gl1) likewise, with its own
#     `make_renderer` so the two boing files keep the same window line.
#
# Idempotent: every replacement asserts it applies exactly once, and a file that
# already carries `def make_renderer(` is skipped. Run from the repo root:
#   python tasks/adhoc/codetheclassics-tighten-games/renderer_dataclasses.py <game.py>...
# Behaviour-preserving by construction (frame gate proves it per game).

import sys
from pathlib import Path


def rep(s: str, old: str, new: str, optional: bool = False) -> str:
    n = s.count(old)
    if optional and n == 0:
        return s
    assert n == 1, (n, old[:70])
    return s.replace(old, new)


UNIFORMS_AND_BUFFER = '''
@dataclass(slots=True, eq=False)
class Uniforms:
    """The shader program's uniform locations, queried once after linking."""

    ortho: int
    model: int
    tint: int
    use_tex: int
    tex: int
    tex_off: int
    tex_scale: int


@dataclass(slots=True, eq=False)
class GLBuffer:
    """A vertex array object and the vertex buffer it reads 2-D positions
    (attribute 0) from."""

    vao: int
    vbo: int


def _link_program() -> int:
    """Compile both shaders and link them into a program; raise on failure."""
    vs: int = _compile(src=_VERT, kind=GL.GL_VERTEX_SHADER)
    fs: int = _compile(src=_FRAG, kind=GL.GL_FRAGMENT_SHADER)
    program: int = GL.glCreateProgram()
    GL.glAttachShader(program, vs)
    GL.glAttachShader(program, fs)
    GL.glLinkProgram(program)
    if GL.glGetProgramiv(program, GL.GL_LINK_STATUS) != GL.GL_TRUE:
        raise RuntimeError(GL.glGetProgramInfoLog(program).decode())
    GL.glDeleteShader(vs)
    GL.glDeleteShader(fs)
    return program


def _make_buffer(data: NDArray[np.float32] | None) -> GLBuffer:
    """Create a VAO + VBO of 2-D positions at attribute 0; ``data`` fills a
    static buffer, ``None`` leaves a dynamic one to be filled per draw."""
    vao: int = GL.glGenVertexArrays(1)
    vbo: int = GL.glGenBuffers(1)
    GL.glBindVertexArray(vao)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo)
    if data is not None:
        GL.glBufferData(
            GL.GL_ARRAY_BUFFER, data.nbytes, data, GL.GL_STATIC_DRAW
        )
    GL.glEnableVertexAttribArray(0)
    GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
    return GLBuffer(vao, vbo)

'''

RENDERER_CLASS = '''@dataclass(slots=True, eq=False)
class Renderer:
    """The GL state a frame needs: the program, its uniforms, the unit-quad
    buffer{prim_doc} and the pixel-space projection. Built by
    :func:`make_renderer` once the GL context exists.
    """

    #: logical (game) pixels
    width: int
    height: int
    #: Maps pixel space to NDC (row-major; uploaded transposed).
    ortho: NDArray[np.float32]
    program: int
    uniforms: Uniforms
    #: The unit quad [0,1]x[0,1] as two triangles -- every sprite's geometry
    quad: GLBuffer{prim_field}
    #: Framebuffer pixels -- may exceed logical on HiDPI / scaled displays.
    #: Updated every begin_frame from the real framebuffer size.
    fb_width: int = field(init=False)
    fb_height: int = field(init=False)

    def __post_init__(self) -> None:
        self.fb_width = self.width
        self.fb_height = self.height
'''

FACTORY = '''

def make_renderer(width: int, height: int) -> Renderer:
    """Build the renderer for a ``width`` x ``height`` pixel game: link the
    program, query its uniforms, upload the unit quad{prim_doc2}, set the blend
    state. Needs a current GL context."""
    program: int = _link_program()
    uniforms = Uniforms(
        ortho=GL.glGetUniformLocation(program, "uOrtho"),
        model=GL.glGetUniformLocation(program, "uModel"),
        tint=GL.glGetUniformLocation(program, "uTint"),
        use_tex=GL.glGetUniformLocation(program, "uUseTex"),
        tex=GL.glGetUniformLocation(program, "uTex"),
        tex_off=GL.glGetUniformLocation(program, "uTexOffset"),
        tex_scale=GL.glGetUniformLocation(program, "uTexScale"),
    )
    quad_verts: NDArray[np.float32] = np.array(
        [0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1], dtype=np.float32
    )
    quad = _make_buffer(quad_verts){prim_make}
    GL.glEnable(GL.GL_BLEND)
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    GL.glDisable(GL.GL_DEPTH_TEST)
    return Renderer(
        width,
        height,
        ortho_pixels(width=width, height=height),
        program,
        uniforms,
        quad,{prim_arg}
    )
'''

OLD_INIT_HEAD = '''class Renderer:
    """Owns the GL program and the unit-quad buffer.

    Created once, after the GL context exists (see the main block).
    """

    def __init__(self, width: int, height: int) -> None:
        self.width = width  # logical (game) pixels
        self.height = height
        # Framebuffer pixels -- may exceed logical on HiDPI / scaled displays.
        # Updated every begin_frame from the real framebuffer size.
        self.fb_width = width
        self.fb_height = height
        self.ortho = ortho_pixels(width=width, height=height)

        vs: int = _compile(src=_VERT, kind=GL.GL_VERTEX_SHADER)
        fs: int = _compile(src=_FRAG, kind=GL.GL_FRAGMENT_SHADER)
        self.program = GL.glCreateProgram()
        GL.glAttachShader(self.program, vs)
        GL.glAttachShader(self.program, fs)
        GL.glLinkProgram(self.program)
        if GL.glGetProgramiv(self.program, GL.GL_LINK_STATUS) != GL.GL_TRUE:
            raise RuntimeError(GL.glGetProgramInfoLog(self.program).decode())
        GL.glDeleteShader(vs)
        GL.glDeleteShader(fs)

        self.u_ortho = GL.glGetUniformLocation(self.program, "uOrtho")
        self.u_model = GL.glGetUniformLocation(self.program, "uModel")
        self.u_tint = GL.glGetUniformLocation(self.program, "uTint")
        self.u_use_tex = GL.glGetUniformLocation(self.program, "uUseTex")
        self.u_tex = GL.glGetUniformLocation(self.program, "uTex")
        self.u_tex_off = GL.glGetUniformLocation(self.program, "uTexOffset")
        self.u_tex_scale = GL.glGetUniformLocation(self.program, "uTexScale")

        # Unit quad [0,1]x[0,1] as two triangles (location 0 = aPos).
        quad: NDArray[np.float32] = np.array(
            [0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1], dtype=np.float32
        )
        self.quad_vao = GL.glGenVertexArrays(1)
        self.quad_vbo = GL.glGenBuffers(1)
        GL.glBindVertexArray(self.quad_vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.quad_vbo)
        GL.glBufferData(
            GL.GL_ARRAY_BUFFER, quad.nbytes, quad, GL.GL_STATIC_DRAW
        )
        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
'''
OLD_PRIM = '''
        # Dynamic buffer for the debug overlay{s}'s {what} (raw pixel coords).
        self.prim_vao = GL.glGenVertexArrays(1)
        self.prim_vbo = GL.glGenBuffers(1)
        GL.glBindVertexArray(self.prim_vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.prim_vbo)
        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
'''
OLD_INIT_TAIL = '''
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glDisable(GL.GL_DEPTH_TEST)

    def begin_frame('''

OLD_IMAGE = '''class Image:
    """A loaded image: CPU pixels now, GL texture on first draw."""

    def __init__(self, path: str) -> None:
        self.path = path
        # Decode with Pillow + convert("RGBA").  This correctly turns palette
        # (mode "P") transparency and grayscale/LA into a real alpha channel --
        # imageio drops palette transparency (returns 3-channel RGB), which made
        # transparent sprite backgrounds render as opaque white boxes.
        arr: NDArray[Any] = np.array(PILImage.open(path).convert("RGBA"))
        self.rgba: NDArray[np.uint8] = np.ascontiguousarray(
            arr.astype(np.uint8)
        )
        self.height: int = int(self.rgba.shape[0])
        self.width: int = int(self.rgba.shape[1])
        self._tex: int | None = None
'''
NEW_IMAGE = '''@dataclass(slots=True, eq=False)
class Image:
    """A loaded image: CPU pixels now, GL texture on first draw. Built by
    :func:`load_image` (or :func:`image_from_rgba` for rendered text)."""

    #: H x W x 4 uint8 pixels, straight alpha
    rgba: NDArray[np.uint8]
    #: The GL texture name, uploaded lazily by gl_texture()
    _tex: int | None = field(default=None, init=False)

    @property
    def width(self) -> int:
        return int(self.rgba.shape[1])

    @property
    def height(self) -> int:
        return int(self.rgba.shape[0])
'''
OLD_FROM_RGBA = '''    @classmethod
    def from_rgba(cls, arr: NDArray[Any]) -> Image:
        """Build an Image from an HxWx4 uint8 array (rendered text)."""
        obj: Image = cls.__new__(cls)
        obj.path = ""  # not from a file
        obj.rgba = np.ascontiguousarray(arr.astype(np.uint8))
        obj.height, obj.width = int(obj.rgba.shape[0]), int(obj.rgba.shape[1])
        obj._tex = None
        return obj

'''
IMAGE_FACTORIES = '''

def load_image(path: str) -> Image:
    """Decode the image file at ``path`` into an :class:`Image`."""
    # Decode with Pillow + convert("RGBA").  This correctly turns palette
    # (mode "P") transparency and grayscale/LA into a real alpha channel --
    # imageio drops palette transparency (returns 3-channel RGB), which made
    # transparent sprite backgrounds render as opaque white boxes.
    return image_from_rgba(np.array(PILImage.open(path).convert("RGBA")))


def image_from_rgba(arr: NDArray[Any]) -> Image:
    """Wrap an H x W x 4 array (e.g. rendered text) as an :class:`Image`."""
    return Image(np.ascontiguousarray(arr.astype(np.uint8)))
'''


def convert(path: Path) -> None:
    s = path.read_text()
    if "def make_renderer(" in s:
        print(f"{path}: already converted")
        return
    # ---- Renderer (3.3 core) ----
    if OLD_INIT_HEAD in s:
        has_prim = "self.prim_vao = GL.glGenVertexArrays(1)" in s
        prim_doc = ", the dynamic overlay buffer" if has_prim else ""
        prim_field = (
            "\n    #: A dynamic buffer the debug overlays fill per draw\n    prim: GLBuffer"
            if has_prim else ""
        )
        prim_doc2 = " and an empty dynamic buffer" if has_prim else ""
        prim_make = "\n    prim = _make_buffer(None)" if has_prim else ""
        prim_arg = "\n        prim," if has_prim else ""
        head = RENDERER_CLASS.format(prim_doc=prim_doc, prim_field=prim_field)
        s = rep(s, OLD_INIT_HEAD, head)
        # the prim block (bunner: "overlay's outlines"; soccer: "overlays' lines")
        for variant in (OLD_PRIM.format(s="", what="outlines"),
                        OLD_PRIM.format(s="s", what="lines")):
            s = rep(s, variant, "", optional=True)
        s = rep(s, OLD_INIT_TAIL, "\n    def begin_frame(")
        # factory after the class: insert before the sprite/window section that follows
        end = s.index("\n\n\n# ===== window and GL context =====")
        s = s[:end] + FACTORY.format(prim_doc2=prim_doc2, prim_make=prim_make, prim_arg=prim_arg).rstrip("\n") + s[end:]
        # helpers before the class
        s = rep(s, "\n\n@dataclass(slots=True, eq=False)\nclass Renderer:", UNIFORMS_AND_BUFFER + "\n@dataclass(slots=True, eq=False)\nclass Renderer:")
        # attribute renames inside the methods
        for old, new in (
            ("self.u_ortho", "self.uniforms.ortho"), ("self.u_model", "self.uniforms.model"),
            ("self.u_tint", "self.uniforms.tint"), ("self.u_use_tex", "self.uniforms.use_tex"),
            ("self.u_tex_off", "self.uniforms.tex_off"), ("self.u_tex_scale", "self.uniforms.tex_scale"),
            ("self.u_tex,", "self.uniforms.tex,"), ("self.quad_vao", "self.quad.vao"),
            ("self.prim_vao", "self.prim.vao"), ("self.prim_vbo", "self.prim.vbo"),
        ):
            s = s.replace(old, new)
        s = rep(s, "renderer: SpriteRenderer = Renderer(WIDTH, HEIGHT)",
                "renderer: SpriteRenderer = make_renderer(WIDTH, HEIGHT)")
    # ---- Renderer1x (fixed function, boing_gl1) ----
    elif "class Renderer1x:" in s:
        s = rep(s, '''class Renderer1x:
    """Fixed-function (OpenGL 1.x) renderer; the same interface as boing.py's
    ``Renderer``."""

    def __init__(self, width: int, height: int) -> None:
        self.width = width  # logical (game) pixels
        self.height = height
        # Framebuffer pixels -- may exceed logical on HiDPI / scaled displays.
        # Updated every begin_frame from the real framebuffer size.
        self.fb_width = width
        self.fb_height = height
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glDisable(GL.GL_DEPTH_TEST)
        # Fixed-function texture env: texture * glColor (matches the 3.3 path's
        # frag = texture * uTint).
        GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)
''', '''@dataclass(slots=True, eq=False)
class Renderer1x:
    """Fixed-function (OpenGL 1.x) renderer; the same interface as boing.py's
    ``Renderer``. Built by :func:`make_renderer` once the GL context exists.
    """

    #: logical (game) pixels
    width: int
    height: int
    #: Framebuffer pixels -- may exceed logical on HiDPI / scaled displays.
    #: Updated every begin_frame from the real framebuffer size.
    fb_width: int = field(init=False)
    fb_height: int = field(init=False)

    def __post_init__(self) -> None:
        self.fb_width = self.width
        self.fb_height = self.height
''')
        end = s.index("\n\n\n# ===== window and GL context =====")
        s = s[:end] + '''


def make_renderer(width: int, height: int) -> Renderer1x:
    """Build the renderer for a ``width`` x ``height`` pixel game: set the
    blend state and the fixed-function texture environment (texture * glColor,
    matching the 3.3 path's frag = texture * uTint). Needs a current GL
    context."""
    GL.glEnable(GL.GL_BLEND)
    GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
    GL.glDisable(GL.GL_DEPTH_TEST)
    GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)
    return Renderer1x(width, height)''' + s[end:]
        s = rep(s, "renderer: SpriteRenderer = Renderer1x(WIDTH, HEIGHT)",
                "renderer: SpriteRenderer = make_renderer(WIDTH, HEIGHT)")
    else:
        raise SystemExit(f"{path}: no renderer __init__ found")
    # ---- Image ----
    s = rep(s, OLD_IMAGE, NEW_IMAGE)
    s = rep(s, OLD_FROM_RGBA, "", optional=True)
    end = s.index("        return cast(int, self._tex)\n") + len("        return cast(int, self._tex)\n")
    s = s[:end] + IMAGE_FACTORIES + s[end:]
    s = rep(s, ', Image\n)\n', ', load_image\n)\n', optional=True)
    s = rep(s, '"images", ("png", "gif", "jpg", "jpeg", "bmp"), Image', '"images", ("png", "gif", "jpg", "jpeg", "bmp"), load_image', optional=True)
    s = s.replace("Image.from_rgba(", "image_from_rgba(")
    path.write_text(s)
    print(f"{path}: converted")


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        convert(Path(arg))
