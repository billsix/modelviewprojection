# Copyright (c) 2018-2026 William Emerison Six
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

"""Generic GL toolkit for the Cayley-graph visualizations.

This module is **mechanism only** -- the reusable pieces a Cayley demo needs:
standard pipelines + geometry (a :class:`StandardObjects`), ``draw_*``
helpers that read the current model matrix, imgui *widgets* (``render_tree`` /
``gui_button``), the orbit camera + input, and a loop runner.  Demos drive the
matrix stack with ``pyMatrixStack`` directly -- no wrappers here for that.

It owns NO policy: not the per-frame draw choreography, not the reveal/graying
decisions, not which imgui panels exist.  Those differ per demo and live in each
demo file (which composes these helpers).  Earlier this file was a
``run(config)`` god-function with feature flags -- that conflated mechanism and
policy; this is the dissolution.
"""

from __future__ import annotations

import dataclasses
import math
import typing

# IMPORT ORDER MATTERS: glfw + OpenGL.GL MUST import before imgui_bundle (its
# own GL loader must come second, or PyOpenGL's context tracking fails at window
# setup).  Demos must get imgui via `cayley_gl.imgui`, not import imgui_bundle first.
import glfw
import numpy as np
import OpenGL.GL as GL
from imgui_bundle import imgui, imgui_ctx  # noqa: F401  (re-exported for demos)

import modelviewprojection.pyMatrixStack as ms
from modelviewprojection.mvpvisualization import _pipeline as _p

# The paddle/square + axis squash shaders use these fixed pipeline values (the
# frustum outline uses the real frustum aspect instead).
PIPELINE_FOV = 45.0
PIPELINE_ASPECT = 1.0


@dataclasses.dataclass
class Frustum:
    """A PERSPECTIVE view volume -- a truncated pyramid whose near/far cross
    sections scale with -z by tan(fov/2).  See :func:`frustum_lines`."""

    field_of_view: float = 45.0
    aspect_ratio: float = 16.0 / 9.0
    near_z: float = -2.0
    far_z: float = -50.0


@dataclasses.dataclass
class RectangularPrism:
    """An ORTHOGRAPHIC view volume -- a box (front == back == ±half_size).  Not a
    frustum: ortho has no perspective foreshortening, so the cross section is
    constant.  See :func:`rectangular_prism_lines`."""

    half_size: float = 5.0
    near_z: float = -0.5
    far_z: float = -15.5


# ---------------------------------------------------------------------------
# Window + camera.
# ---------------------------------------------------------------------------


def setup(title: str):
    """Open a window + ImGui; returns ``(window, impl, imguiio)``."""
    window, impl, imguiio = _p.setup_window(title)
    _p.install_esc_close(window)
    return window, impl, imguiio


_DEFAULT_ROT_Y = math.radians(45.0)
_DEFAULT_ROT_X = math.radians(35.264)


def make_camera(r=25.0, rot_y=_DEFAULT_ROT_Y, rot_x=_DEFAULT_ROT_X):
    return _p.Camera(r=r, rot_y=rot_y, rot_x=rot_x)


def install_scroll(window, imguiio, camera):
    _p.install_camera_scroll(window, imguiio, camera)


def orbit_input(window, imguiio, camera, prev_mouse):
    """Arrow keys + left-drag orbit the camera.  Returns the new mouse pos (or
    None when the button is up).  Pure input mechanism."""
    if glfw.get_key(window, glfw.KEY_RIGHT) == glfw.PRESS:
        camera.rot_y -= math.radians(1.0)
    if glfw.get_key(window, glfw.KEY_LEFT) == glfw.PRESS:
        camera.rot_y += math.radians(1.0)
    if glfw.get_key(window, glfw.KEY_UP) == glfw.PRESS:
        camera.rot_x -= math.radians(1.0)
    if glfw.get_key(window, glfw.KEY_DOWN) == glfw.PRESS:
        camera.rot_x += math.radians(1.0)
    new = glfw.get_cursor_pos(window)
    if glfw.PRESS == glfw.get_mouse_button(window, glfw.MOUSE_BUTTON_LEFT):
        if not imguiio.want_capture_mouse and prev_mouse:
            camera.rot_y -= 0.2 * math.radians(new[0] - prev_mouse[0])
            camera.rot_x += 0.2 * math.radians(new[1] - prev_mouse[1])
    else:
        new = None
    camera.rot_x = max(-math.pi / 2.0, min(math.pi / 2.0, camera.rot_x))
    return new


def setup_orbit_view(camera, w, h):
    """Reset the matrices and set a perspective projection + 3rd-person orbit
    view.  The demo may add a centering translate afterwards if it wants."""
    ms.set_to_identity_matrix(ms.MatrixStack.model)
    ms.set_to_identity_matrix(ms.MatrixStack.view)
    ms.set_to_identity_matrix(ms.MatrixStack.projection)
    ms.perspective(
        field_of_view=45.0,
        aspect_ratio=float(w) / float(h),
        near_z=0.1,
        far_z=10000.0,
    )
    ms.translate(ms.MatrixStack.view, 0.0, 0.0, -camera.r)
    ms.rotate_x(ms.MatrixStack.view, camera.rot_x)
    ms.rotate_y(ms.MatrixStack.view, -camera.rot_y)


def setup_ortho_2d_view(w, h, half_extent, depth=100.0):
    """Flat 2D ORTHOGRAPHIC view, square-letterboxed -- NO orbit/rotation (the
    scene is 2D, viewed head-on down -z; modelview2d).  ``half_extent`` is the
    ortho half-width (e.g. 15 for the whole scene, 1 to zoom to NDC).  ``depth``
    is a fixed view z-push so the z~=0 scene sits inside [near, far].  The
    viewport is letterboxed to a centered square so the scene keeps its aspect."""
    m = min(w, h)
    GL.glViewport(int((w - m) / 2.0), int((h - m) / 2.0), m, m)
    ms.set_to_identity_matrix(ms.MatrixStack.model)
    ms.set_to_identity_matrix(ms.MatrixStack.view)
    ms.set_to_identity_matrix(ms.MatrixStack.projection)
    ms.ortho(
        left=-half_extent,
        right=half_extent,
        bottom=-half_extent,
        top=half_extent,
        near=0.0,
        far=550.0,
    )
    ms.translate(ms.MatrixStack.view, 0.0, 0.0, -depth)


# ---------------------------------------------------------------------------
# Standard geometry + pipelines, and the draw helpers that use them.
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class StandardObjects:
    """The standard pipelines + meshes for a Cayley demo, plus draw helpers.
    Each ``draw_*`` reads the current model matrix (set by the caller via
    ``ms.set_current_matrix(ms.MatrixStack.model, ...)``)."""

    triangle_pipeline: typing.Any
    ground_pipeline: typing.Any
    axis_pipeline: typing.Any
    cube_pipeline: typing.Any
    meshes: typing.Dict[str, typing.Tuple[int, int]]
    ground: typing.Tuple[int, int]
    axis: typing.Tuple[int, int]
    sphere: typing.Tuple[int, int]
    cube: typing.Tuple[int, int]
    #: at most one view volume per demo: a perspective frustum OR an ortho prism.
    frustum: typing.Optional[Frustum] = None
    rect_prism: typing.Optional[RectangularPrism] = None
    volume_pipeline: typing.Any = None
    volume_geo: typing.Optional[typing.Tuple[int, int, int]] = None  # vao,n,vbo

    def _anim(self, p, time=None):
        if p.u_fov != -1:  # perspective squash reads fov/aspect/near/far
            GL.glUniform1f(p.u_fov, PIPELINE_FOV)
            GL.glUniform1f(p.u_aspect, PIPELINE_ASPECT)
            volume = (
                self.frustum if self.frustum is not None else self.rect_prism
            )
            if volume is not None:
                GL.glUniform1f(p.u_near, volume.near_z)
                GL.glUniform1f(p.u_far, volume.far_z)
        # u_time is INDEPENDENT of u_fov: the ortho / modelview2d squash shaders
        # use only `time` (their fov/near/far are optimized out, so u_fov == -1).
        # Gating time on u_fov used to silently disable those squashes.  Axes
        # pass time=None so they hold at 0 and never squash.
        if time is not None and p.u_time != -1:
            GL.glUniform1f(p.u_time, time)

    def draw_mesh(self, name, time=0.0):
        vao, n = self.meshes[name]
        GL.glUseProgram(self.triangle_pipeline.program)
        GL.glBindVertexArray(vao)
        _p.set_uniforms(
            self.triangle_pipeline.u_m,
            self.triangle_pipeline.u_v,
            self.triangle_pipeline.u_p,
        )
        self._anim(self.triangle_pipeline, time)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, n)

    def draw_ground(self):
        vao, n = self.ground
        GL.glUseProgram(self.ground_pipeline.program)
        GL.glBindVertexArray(vao)
        GL.glUniform3f(self.ground_pipeline.u_color, 0.1, 0.1, 0.1)
        _p.set_uniforms(
            self.ground_pipeline.u_m,
            self.ground_pipeline.u_v,
            self.ground_pipeline.u_p,
        )
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, n)

    def _emit_axis(self, r, g, b, grayed):
        GL.glUniform3f(
            self.axis_pipeline.u_color,
            *((0.5, 0.5, 0.5) if grayed else (r, g, b)),
        )
        _p.set_uniforms(
            self.axis_pipeline.u_m,
            self.axis_pipeline.u_v,
            self.axis_pipeline.u_p,
        )
        self._anim(self.axis_pipeline)  # no time -> axes never squash
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, self.axis[1])

    def draw_axis(self, grayed=False):
        GL.glUseProgram(self.axis_pipeline.program)
        GL.glBindVertexArray(self.axis[0])
        with ms.push_matrix(ms.MatrixStack.model):
            with ms.push_matrix(ms.MatrixStack.model):
                ms.rotate_z(ms.MatrixStack.model, math.radians(-90.0))
                self._emit_axis(1.0, 0.0, 0.0, grayed)
            with ms.push_matrix(ms.MatrixStack.model):
                ms.rotate_y(ms.MatrixStack.model, math.radians(90.0))
                ms.rotate_z(ms.MatrixStack.model, math.radians(90.0))
                self._emit_axis(0.0, 0.0, 1.0, grayed)
            self._emit_axis(0.0, 1.0, 0.0, grayed)
            GL.glBindVertexArray(self.sphere[0])
            GL.glUniform3f(
                self.axis_pipeline.u_color,
                *((0.5, 0.5, 0.5) if grayed else (1.0, 1.0, 1.0)),
            )
            _p.set_uniforms(
                self.axis_pipeline.u_m,
                self.axis_pipeline.u_v,
                self.axis_pipeline.u_p,
            )
            self._anim(self.axis_pipeline)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, self.sphere[1])

    def draw_cube(self):
        vao, n = self.cube
        GL.glUseProgram(self.cube_pipeline.program)
        GL.glBindVertexArray(vao)
        GL.glUniform3f(self.cube_pipeline.u_color, 1.0, 1.0, 1.0)
        _p.set_uniforms(
            self.cube_pipeline.u_m,
            self.cube_pipeline.u_v,
            self.cube_pipeline.u_p,
        )
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, n)

    def _draw_volume(self, p, time, thickness, w, h):
        vao, n, _vbo = self.volume_geo
        GL.glUseProgram(p.program)
        GL.glBindVertexArray(vao)
        GL.glUniform3f(p.u_color, 1.0, 1.0, 1.0)
        _p.set_uniforms(p.u_m, p.u_v, p.u_p)
        GL.glUniform1f(p.u_time, time)
        GL.glUniform1f(p.u_thickness, thickness)
        GL.glUniform2f(p.u_viewport, w, h)
        GL.glDrawArrays(GL.GL_LINES, 0, n)

    def draw_frustum(self, time, thickness, w, h):
        """Draw the PERSPECTIVE frustum outline (uses its fov/aspect/near/far)."""
        p = self.volume_pipeline
        GL.glUseProgram(p.program)
        GL.glUniform1f(p.u_fov, self.frustum.field_of_view)
        GL.glUniform1f(p.u_aspect, self.frustum.aspect_ratio)
        GL.glUniform1f(p.u_near, self.frustum.near_z)
        GL.glUniform1f(p.u_far, self.frustum.far_z)
        self._draw_volume(p, time, thickness, w, h)

    def draw_rect_prism(self, time, thickness, w, h):
        """Draw the ORTHOGRAPHIC box outline.  The ortho squash shaders ignore
        fov/aspect, so only near/far/time matter (fov/aspect set to pipeline
        defaults to keep the geometry shader's screenspace math well-defined)."""
        p = self.volume_pipeline
        GL.glUseProgram(p.program)
        GL.glUniform1f(p.u_fov, PIPELINE_FOV)
        GL.glUniform1f(p.u_aspect, PIPELINE_ASPECT)
        GL.glUniform1f(p.u_near, self.rect_prism.near_z)
        GL.glUniform1f(p.u_far, self.rect_prism.far_z)
        self._draw_volume(p, time, thickness, w, h)

    def rebuild_frustum(self):
        """Re-upload the perspective frustum edges after its FOV/aspect/near/far
        changed (the ortho prism has no sliders, so it never needs a rebuild)."""
        verts = frustum_lines(self.frustum)
        _vao, _n, vbo = self.volume_geo
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo)
        GL.glBufferData(
            GL.GL_ARRAY_BUFFER,
            _p.glfloat_size * verts.size,
            verts,
            GL.GL_STATIC_DRAW,
        )
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)


def build_standard(
    animated=False,
    project="project_identity.glsl",
    frustum=None,
    rect_prism=None,
) -> StandardObjects:
    """Build the standard pipelines + meshes, plus an optional view volume --
    either a perspective ``frustum`` or an orthographic ``rect_prism`` (a demo
    has at most one).  ``animated`` + ``project`` select the squash shader for
    the triangle/axis pipelines."""
    proj = project if animated else "project_identity.glsl"
    triangle = _p.build_pipeline(
        "per_vertex_color.vert",
        "passthrough.frag",
        per_vertex_color=True,
        anim=animated,
        project=proj,
    )
    ground_p = _p.build_pipeline(
        "uniform_color.vert", "passthrough.frag", color=True
    )
    axis_p = _p.build_pipeline(
        "uniform_color.vert",
        "passthrough.frag",
        color=True,
        anim=animated,
        project=proj,
    )
    cube_p = _p.build_pipeline(
        "uniform_color.vert", "passthrough.frag", color=True
    )
    meshes = {
        "paddle1": _p.make_triangle_vao(
            _p.paddle_vertices,
            r=0.578123,
            g=0.0,
            b=1.0,
            attr_position=triangle.attr_position,
            attr_color=triangle.attr_color,
        ),
        "paddle2": _p.make_triangle_vao(
            _p.paddle_vertices,
            r=1.0,
            g=1.0,
            b=0.0,
            attr_position=triangle.attr_position,
            attr_color=triangle.attr_color,
        ),
        "square": _p.make_triangle_vao(
            _p.square_vertices,
            r=0.0,
            g=0.0,
            b=1.0,
            attr_position=triangle.attr_position,
            attr_color=triangle.attr_color,
        ),
    }
    standard_objects = StandardObjects(
        triangle_pipeline=triangle,
        ground_pipeline=ground_p,
        axis_pipeline=axis_p,
        cube_pipeline=cube_p,
        meshes=meshes,
        ground=_p.make_lines_vao(
            _p.build_ground_cylinders(), ground_p.attr_position
        ),
        axis=_p.make_lines_vao(
            _p.build_axis_arrow_solid(), axis_p.attr_position
        ),
        sphere=_p.make_lines_vao(
            _p.build_origin_sphere_solid(), axis_p.attr_position
        ),
        cube=_p.make_lines_vao(
            _p.build_ndc_cube_cylinders(), cube_p.attr_position
        ),
        frustum=frustum,
        rect_prism=rect_prism,
    )
    volume = frustum if frustum is not None else rect_prism
    if volume is not None:
        vp = _p.build_pipeline(
            "uniform_color.vert",
            "passthrough_geom.frag",
            geom="thick_lines.geom",
            color=True,
            anim=True,
            screenspace=True,
            project=project,
        )
        verts = (
            frustum_lines(frustum)
            if frustum is not None
            else rectangular_prism_lines(rect_prism)
        )
        vbo = _p.make_vbo(verts, usage=GL.GL_DYNAMIC_DRAW)
        vao = _p.make_vao(
            [
                _p.AttribSpec(
                    vbo=vbo,
                    location=vp.attr_position,
                    size=_p.floatsPerVertex,
                    layout=(0, 0),
                )
            ]
        )
        standard_objects.volume_pipeline = vp
        standard_objects.volume_geo = (
            vao,
            verts.size // _p.floatsPerVertex,
            vbo,
        )
    return standard_objects


# ---------------------------------------------------------------------------
# imgui widgets (mechanism) -- the PANEL composition stays in the demo.
# ---------------------------------------------------------------------------


def gui_button(button, on_jump) -> None:
    """A highlighted (when active) jump-button for a timeline substep."""
    if button.active:
        imgui.push_style_color(imgui.Col_.button.value, (0.6, 0.2, 0.2, 1.0))
    imgui.push_id(f"{button.label}@{button.start}")
    clicked = imgui.button(button.label)
    imgui.pop_id()
    if button.active:
        imgui.pop_style_color(1)
    if clicked:
        on_jump(button.start)


def render_tree(group, on_jump) -> None:
    """Render a :class:`cayleyscene.GuiGroup` as a nested tree of jump-buttons,
    with `` o `` (the compose operator) between successive buttons so the row
    reads as function composition, e.g. ``[T] o [R_z]``.  ``on_jump(start_time)``
    is called when a button is clicked."""
    imgui.set_next_item_open(True, imgui.Cond_.once)
    if imgui.tree_node(group.title):
        for idx, b in enumerate(group.buttons):
            if idx > 0:  # show composition between successive substeps
                imgui.same_line()
                imgui.text(" o ")
                imgui.same_line()
            gui_button(b, on_jump)
        # no new_line(): the last button isn't followed by same_line(), so the
        # next widget already falls to a new row -- an explicit new_line() here
        # would add a blank gap after each composed row.
        for child in group.children:
            render_tree(child, on_jump)
        imgui.tree_pop()


# ---------------------------------------------------------------------------
# Menubar + window state (controls live in the menubar, SuperBible-ports style).
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class WindowState:
    """Window-level UI state.  ``fullscreen`` + ``saved_*`` back the F11/View
    fullscreen toggle (saving the windowed rect to restore to); ``show_graph``
    is the visibility of the floating function-composition tree panel (G / View
    -> Show Graph).  Demos without trees just ignore ``show_graph``."""

    fullscreen: bool = False
    show_graph: bool = True
    saved_x: int = 0
    saved_y: int = 0
    saved_w: int = 0
    saved_h: int = 0


def menu_action(label, key, action, *, selected=False) -> None:
    """A menubar item that also shows its keyboard shortcut (``key``, in the
    right-hand column) and an optional check mark (``selected``).  Runs
    ``action()`` once on click.  Call inside a ``begin_menu`` block."""
    clicked, _ = imgui.menu_item(label, key, selected, True)
    if clicked:
        action()


def toggle_fullscreen(window, state: WindowState) -> None:
    """Flip between windowed and exclusive fullscreen on the primary monitor,
    saving/restoring the windowed geometry (mirrors the SuperBible ports)."""
    if state.fullscreen:
        glfw.set_window_monitor(
            window,
            None,
            state.saved_x,
            state.saved_y,
            state.saved_w,
            state.saved_h,
            0,
        )
        state.fullscreen = False
    else:
        state.saved_x, state.saved_y = glfw.get_window_pos(window)
        state.saved_w, state.saved_h = glfw.get_window_size(window)
        monitor = glfw.get_primary_monitor()
        if monitor is None:
            return
        mode = glfw.get_video_mode(monitor)
        glfw.set_window_monitor(
            window,
            monitor,
            0,
            0,
            mode.size.width,
            mode.size.height,
            mode.refresh_rate,
        )
        state.fullscreen = True


def common_key(window, state: WindowState, key, action) -> None:
    """Handle the keys every demo shares: Esc quits, F11 toggles fullscreen.
    Call first from the demo's GLFW key callback, then add demo-specific keys."""
    if action != glfw.PRESS:
        return
    if key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True)
    elif key == glfw.KEY_F11:
        toggle_fullscreen(window, state)


# ---------------------------------------------------------------------------
# Loop runner (generic timing/poll/menubar/swap; the body is the demo's).
# ---------------------------------------------------------------------------


def run_loop(
    window, impl, frame, menubar=None, on_key=None, target_framerate=60
) -> None:
    """Drive the GL/ImGui loop.  ``menubar()`` (if given) draws the demo's main
    menu bar each frame; ``frame(w, h)`` draws the scene + any floating panels.
    ``on_key`` (if given) is installed as the GLFW key callback AFTER the
    GlfwRenderer, so it wins -- imgui then gets no key events, which is fine for
    these mouse-driven menus."""
    if on_key is not None:
        glfw.set_key_callback(window, on_key)
    t_prev = glfw.get_time()
    while not glfw.window_should_close(window):
        while glfw.get_time() < t_prev + 1.0 / target_framerate:
            pass
        t_prev = glfw.get_time()
        glfw.poll_events()
        impl.process_inputs()
        imgui.new_frame()
        if menubar is not None:
            menubar()
        w, h = glfw.get_framebuffer_size(window)
        GL.glViewport(0, 0, w, h)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        frame(w, h)
        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)
    _p.cleanup()
    glfw.terminate()


def _volume_edges(n, fa, fl, frr, ftt, fb, bl, brr, btt, bb) -> np.ndarray:
    """The 12 edges of a view volume (front face at z=n, back at z=fa) as a flat
    GL_LINES vertex array.  Shared by the frustum and the rectangular prism --
    they differ only in whether the front/back cross sections match."""
    edges = [
        ((fl, ftt, n), (frr, ftt, n)),
        ((frr, ftt, n), (frr, fb, n)),
        ((frr, fb, n), (fl, fb, n)),
        ((fl, fb, n), (fl, ftt, n)),
        ((bl, btt, fa), (brr, btt, fa)),
        ((brr, btt, fa), (brr, bb, fa)),
        ((brr, bb, fa), (bl, bb, fa)),
        ((bl, bb, fa), (bl, btt, fa)),
        ((fl, ftt, n), (bl, btt, fa)),
        ((frr, ftt, n), (brr, btt, fa)),
        ((fl, fb, n), (bl, bb, fa)),
        ((frr, fb, n), (brr, bb, fa)),
    ]
    verts: list = []
    for p0, p1 in edges:
        verts += [float(p0[0]), float(p0[1]), float(p0[2])]
        verts += [float(p1[0]), float(p1[1]), float(p1[2])]
    return np.array(verts, dtype=np.float32)


def frustum_lines(f: Frustum) -> np.ndarray:
    """The perspective frustum outline: corners scale with -z by tan(fov/2), so
    the back face is larger than the front."""
    ft = -f.near_z * math.tan(math.radians(f.field_of_view) / 2.0)
    fr_ = ft * f.aspect_ratio
    bt = -f.far_z * math.tan(math.radians(f.field_of_view) / 2.0)
    br = bt * f.aspect_ratio
    return _volume_edges(
        f.near_z, f.far_z, -fr_, fr_, ft, -ft, -br, br, bt, -bt
    )


def rectangular_prism_lines(b: RectangularPrism) -> np.ndarray:
    """The orthographic box outline: front == back == ±half_size (no taper)."""
    h = b.half_size
    return _volume_edges(b.near_z, b.far_z, -h, h, h, -h, -h, h, h, -h)
