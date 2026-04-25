# Copyright (c) 2026 William Emerison Six
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import os

import wx
import wx.aui
import wx.glcanvas
import wx.xrc as xrc
from OpenGL import GL

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


pwd = os.path.dirname(os.path.abspath(__file__))


def _load_xrc():
    """Return the cached XmlResource."""
    if not hasattr(_load_xrc, "_res"):
        _load_xrc._res = xrc.XmlResource(os.path.join(pwd, "wxapp2.xrc"))
    return _load_xrc._res


# ---------------------------------------------------------------------------
# Tab panels — layout from XRC, behaviour wired in Python
# ---------------------------------------------------------------------------


class AnimationControlTab(wx.Panel):
    """Animation controls tab. Layout from XRC."""

    def __init__(self, parent, opengl_panel):
        wx.Panel.__init__(self)
        _load_xrc().LoadPanel(self, parent, "AnimationControlTab")

        self.opengl_panel = opengl_panel

        self.chk_enable = xrc.XRCCTRL(self, "chk_enable_rotation")
        self.sld_speed = xrc.XRCCTRL(self, "sld_speed")

        self.Bind(wx.EVT_CHECKBOX, self.on_toggle_animation, self.chk_enable)
        self.Bind(wx.EVT_SLIDER, self.on_speed_change, self.sld_speed)

    def on_toggle_animation(self, event):
        self.opengl_panel.set_animation_enabled(event.IsChecked())

    def on_speed_change(self, event):
        self.opengl_panel.set_rotation_speed(self.sld_speed.GetValue())


class ColorControlTab(wx.Panel):
    """Color controls tab. Layout from XRC."""

    def __init__(self, parent, opengl_panel):
        wx.Panel.__init__(self)
        _load_xrc().LoadPanel(self, parent, "ColorControlTab")

        self.opengl_panel = opengl_panel

        self.rb_cyan = xrc.XRCCTRL(self, "rb_cyan")
        self.rb_red = xrc.XRCCTRL(self, "rb_red")
        self.rb_green = xrc.XRCCTRL(self, "rb_green")

        self.Bind(wx.EVT_RADIOBUTTON, self.on_color_change)

    def on_color_change(self, event):
        if self.rb_cyan.GetValue():
            self.opengl_panel.set_color(0.0, 1.0, 1.0)
        elif self.rb_red.GetValue():
            self.opengl_panel.set_color(1.0, 0.0, 0.0)
        elif self.rb_green.GetValue():
            self.opengl_panel.set_color(0.0, 1.0, 0.0)


class ControlPanel(wx.Panel):
    """Plain panel + plain notebook, safe to use as an AUI dockable pane."""

    def __init__(self, parent, opengl_panel):
        super().__init__(parent)

        notebook = wx.Notebook(self)

        tab1 = AnimationControlTab(notebook, opengl_panel)
        tab2 = ColorControlTab(notebook, opengl_panel)
        tab3 = wx.Panel(notebook)  # placeholder

        notebook.AddPage(tab1, "Animation")
        notebook.AddPage(tab2, "Color")
        notebook.AddPage(tab3, "Misc")

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(notebook, 1, wx.EXPAND)
        self.SetSizer(sizer)


class OpenGLPanel(wx.glcanvas.GLCanvas):
    """OpenGL rendering panel. Cannot live in XRC (needs custom attribList)."""

    def __init__(self, parent):
        attribList = [
            wx.glcanvas.WX_GL_RGBA,
            wx.glcanvas.WX_GL_DOUBLEBUFFER,
            wx.glcanvas.WX_GL_DEPTH_SIZE,
            24,
        ]
        super().__init__(
            parent, attribList=attribList, style=wx.FULL_REPAINT_ON_RESIZE
        )
        self.context = wx.glcanvas.GLContext(self)
        self.init_gl = False

        self.rotation_angle = 0
        self.rotation_speed = 5
        self.is_enabled = True
        self.color = (0.0, 1.0, 1.0)

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
        self.timer.Start(16)

    def on_paint(self, event):
        wx.PaintDC(self)
        wx.glcanvas.GLContext.SetCurrent(self.context, self)
        if not self.init_gl:
            self.initialize_opengl()
            self.init_gl = True
        self.on_draw()

    def on_size(self, event):
        width, height = self.GetSize()
        if self.context and self.IsShownOnScreen():
            wx.glcanvas.GLContext.SetCurrent(self.context, self)
            GL.glViewport(0, 0, width, height)
        event.Skip()

    def on_timer(self, event):
        if self.is_enabled:
            self.rotation_angle += self.rotation_speed / 50.0
            if self.rotation_angle > 360:
                self.rotation_angle -= 360
            self.Refresh(False)

    def initialize_opengl(self):
        GL.glClearColor(0.0, 0.0, 0.0, 1.0)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glOrtho(-1, 1, -1, 1, -1, 1)
        GL.glMatrixMode(GL.GL_MODELVIEW)

    def on_draw(self):
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        GL.glLoadIdentity()
        GL.glRotatef(self.rotation_angle, 0.0, 0.0, 1.0)
        GL.glBegin(GL.GL_QUADS)
        GL.glColor3f(*self.color)
        GL.glVertex2f(-0.5, -0.5)
        GL.glVertex2f(0.5, -0.5)
        GL.glVertex2f(0.5, 0.5)
        GL.glVertex2f(-0.5, 0.5)
        GL.glEnd()
        self.SwapBuffers()

    def set_rotation_speed(self, speed):
        self.rotation_speed = speed

    def set_animation_enabled(self, is_enabled):
        self.is_enabled = is_enabled

    def set_color(self, r, g, b):
        self.color = (r, g, b)


class MainFrame(wx.Frame):
    def __init__(self):
        # Two-phase XRC construction
        wx.Frame.__init__(self)
        _load_xrc().LoadFrame(self, None, "MainFrame")

        # AuiManager manages the frame's client area
        self._mgr = wx.aui.AuiManager(self)

        # Central pane: OpenGL canvas
        self.opengl_panel = OpenGLPanel(self)
        self._mgr.AddPane(
            self.opengl_panel, wx.aui.AuiPaneInfo().CenterPane().Name("opengl")
        )

        self.control_panel = ControlPanel(self, self.opengl_panel)
        self._mgr.AddPane(
            self.control_panel,
            wx.aui.AuiPaneInfo()
            .Right()
            .Name("controls")
            .Caption("Controls")
            .BestSize(wx.Size(300, -1))
            .MinSize(wx.Size(200, 200))
            .Floatable(True)
            .Dockable(True)
            .CloseButton(False),
        )

        self._mgr.Update()

        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Show()

    def on_close(self, event):
        self._mgr.UnInit()
        event.Skip()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = wx.App(False)
    frame = MainFrame()
    app.MainLoop()
