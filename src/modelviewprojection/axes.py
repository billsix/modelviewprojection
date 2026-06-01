"""draw_unit_axes -- a unit-length basis gizmo (X red, Y green, Z blue)
drawn at the current modelview origin.  Useful for visualizing what
the current transform is doing to the basis vectors -- drop a call
inside any glPushMatrix/glPopMatrix block to "see" the local frame.

Ported from gltDrawUnitAxes in the OpenGL SuperBible's gltools.  Each
axis is a cylinder shaft tipped with a cone arrowhead, and a small
white sphere marks the origin.
"""

import math

import OpenGL.GL as GL


def _draw_solid_cylinder(
    base_radius: float, top_radius: float, height: float, slices: int
) -> None:
    """Cylinder side surface, oriented along +Z (replacement for gluCylinder)."""
    GL.glBegin(GL.GL_QUAD_STRIP)
    for i in range(slices + 1):
        a = 2.0 * math.pi * float(i) / slices
        c, s = math.cos(a), math.sin(a)
        GL.glNormal3f(c, s, 0.0)
        GL.glVertex3f(c * base_radius, s * base_radius, 0.0)
        GL.glVertex3f(c * top_radius, s * top_radius, height)
    GL.glEnd()


def _draw_solid_cone(base: float, height: float, slices: int) -> None:
    """Cone with apex on +Z and base disk closing the bottom."""
    GL.glBegin(GL.GL_TRIANGLE_FAN)
    GL.glNormal3f(0.0, 0.0, 1.0)
    GL.glVertex3f(0.0, 0.0, height)
    for i in range(slices + 1):
        a = 2.0 * math.pi * float(i) / slices
        GL.glVertex3f(math.cos(a) * base, math.sin(a) * base, 0.0)
    GL.glEnd()
    # Base disk
    GL.glBegin(GL.GL_TRIANGLE_FAN)
    GL.glNormal3f(0.0, 0.0, -1.0)
    GL.glVertex3f(0.0, 0.0, 0.0)
    for i in range(slices, -1, -1):
        a = 2.0 * math.pi * float(i) / slices
        GL.glVertex3f(math.cos(a) * base, math.sin(a) * base, 0.0)
    GL.glEnd()


def _draw_solid_sphere(radius: float, slices: int, stacks: int) -> None:
    """Solid sphere centered at the origin -- the white ball marking the
    origin, like the gluSphere call at the end of gltDrawUnitAxes.  Emits
    (lat1, lat0) per slice so the outward face winds CCW under the default
    glFrontFace(GL_CCW)."""
    for i in range(stacks):
        lat0 = math.pi * (-0.5 + float(i) / stacks)
        lat1 = math.pi * (-0.5 + float(i + 1) / stacks)
        s0, c0 = math.sin(lat0), math.cos(lat0)
        s1, c1 = math.sin(lat1), math.cos(lat1)
        GL.glBegin(GL.GL_QUAD_STRIP)
        for j in range(slices + 1):
            lng = 2.0 * math.pi * float(j) / slices
            cl, sl = math.cos(lng), math.sin(lng)
            GL.glNormal3f(cl * c1, sl * c1, s1)
            GL.glVertex3f(radius * cl * c1, radius * sl * c1, radius * s1)
            GL.glNormal3f(cl * c0, sl * c0, s0)
            GL.glVertex3f(radius * cl * c0, radius * sl * c0, radius * s0)
        GL.glEnd()


def draw_unit_axes(scale: float = 1.0) -> None:
    """Draw a unit-length basis at the current modelview origin:
    +X red, +Y green, +Z blue.  Each axis is a thin cylinder shaft
    with a cone arrowhead at the tip; a small white sphere sits at the
    origin.  Call inside any glPushMatrix/glPopMatrix block to visualize
    the current coordinate frame.

    *scale* multiplies all geometry proportionally -- pass <1.0 for a
    smaller gizmo that fits inside a nested local frame.
    """
    rod_radius = 0.05 * scale
    cone_radius = 0.12 * scale
    rod_length = 0.85 * scale
    cone_length = 0.15 * scale

    # Force solid fill for the gizmo geometry regardless of the caller's
    # polygon mode (demo19e renders the rest of its scene as wireframe).
    GL.glPushAttrib(GL.GL_POLYGON_BIT)
    GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_FILL)

    # +X axis -- red, rotate +90 about Y so the +Z-aligned cylinder
    # points along +X
    GL.glColor3f(1.0, 0.0, 0.0)
    GL.glPushMatrix()
    GL.glRotatef(90.0, 0.0, 1.0, 0.0)
    _draw_solid_cylinder(rod_radius, rod_radius, rod_length, 20)
    GL.glTranslatef(0.0, 0.0, rod_length)
    _draw_solid_cone(cone_radius, cone_length, 20)
    GL.glPopMatrix()

    # +Y axis -- green, rotate -90 about X so the cylinder points along +Y
    GL.glColor3f(0.0, 1.0, 0.0)
    GL.glPushMatrix()
    GL.glRotatef(-90.0, 1.0, 0.0, 0.0)
    _draw_solid_cylinder(rod_radius, rod_radius, rod_length, 20)
    GL.glTranslatef(0.0, 0.0, rod_length)
    _draw_solid_cone(cone_radius, cone_length, 20)
    GL.glPopMatrix()

    # +Z axis -- blue, default cylinder orientation
    GL.glColor3f(0.0, 0.0, 1.0)
    GL.glPushMatrix()
    _draw_solid_cylinder(rod_radius, rod_radius, rod_length, 20)
    GL.glTranslatef(0.0, 0.0, rod_length)
    _draw_solid_cone(cone_radius, cone_length, 20)
    GL.glPopMatrix()

    # White ball at the origin -- gltDrawUnitAxes finished with a small
    # gluSphere.  The 0.10 radius keeps the same ~2x-rod proportion as
    # the SuperBible original (otherwise the sphere disappears into the
    # axis shafts).
    GL.glColor3f(1.0, 1.0, 1.0)
    _draw_solid_sphere(0.10 * scale, 15, 15)

    GL.glPopAttrib()
