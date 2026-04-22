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

import wx
import wx.glcanvas
from OpenGL import GL

# --- Tab Panels for the Notebook ---


class AnimationControlTab(wx.Panel):
    """The first tab, controlling movement."""

    def __init__(self, parent, opengl_panel):
        super().__init__(parent)
        self.opengl_panel = opengl_panel

        sizer = wx.BoxSizer(wx.VERTICAL)

        # Checkbox to toggle animation
        toggle_checkbox = wx.CheckBox(self, label="Enable Rotation")
        toggle_checkbox.SetValue(True)
        self.Bind(wx.EVT_CHECKBOX, self.on_toggle_animation, toggle_checkbox)
        sizer.Add(toggle_checkbox, 0, wx.ALL, 10)

        # Slider for speed
        speed_label = wx.StaticText(self, label="Rotation Speed:")
        speed_slider = wx.Slider(self, value=5, minValue=1, maxValue=20)
        self.Bind(wx.EVT_SLIDER, self.on_speed_change, speed_slider)
        sizer.Add(speed_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        sizer.Add(speed_slider, 0, wx.EXPAND | wx.ALL, 10)

        self.SetSizer(sizer)

    def on_toggle_animation(self, event):
        self.opengl_panel.set_animation_enabled(event.IsChecked())

    def on_speed_change(self, event):
        self.opengl_panel.set_rotation_speed(event.GetEventObject().GetValue())


class ColorControlTab(wx.Panel):
    """The second tab, controlling color."""

    def __init__(self, parent, opengl_panel):
        super().__init__(parent)
        self.opengl_panel = opengl_panel

        sizer = wx.BoxSizer(wx.VERTICAL)

        color_label = wx.StaticText(self, label="Rectangle Color:")
        sizer.Add(color_label, 0, wx.ALL, 10)

        # Radio buttons for color choice
        self.rb_cyan = wx.RadioButton(self, label="Cyan", style=wx.RB_GROUP)
        self.rb_red = wx.RadioButton(self, label="Red")
        self.rb_green = wx.RadioButton(self, label="Green")
        self.rb_cyan.SetValue(True)  # Default selection

        self.Bind(wx.EVT_RADIOBUTTON, self.on_color_change)

        sizer.Add(self.rb_cyan, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        sizer.Add(self.rb_red, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        sizer.Add(self.rb_green, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        self.SetSizer(sizer)

    def on_color_change(self, event):
        if self.rb_cyan.GetValue():
            self.opengl_panel.set_color(0.0, 1.0, 1.0)
        elif self.rb_red.GetValue():
            self.opengl_panel.set_color(1.0, 0.0, 0.0)
        elif self.rb_green.GetValue():
            self.opengl_panel.set_color(0.0, 1.0, 0.0)


# --- Main Control Panel with Notebook ---


class TabbedControlPanel(wx.Panel):
    """A panel that holds the wx.Notebook widget."""

    def __init__(self, parent, opengl_panel):
        super().__init__(parent)

        # Create the notebook
        notebook = wx.Notebook(self)

        # Create the individual tab panels
        tab1 = AnimationControlTab(notebook, opengl_panel)
        tab2 = ColorControlTab(notebook, opengl_panel)
        tab3 = wx.Panel(notebook)  # A simple placeholder panel

        # Add the tabs to the notebook
        notebook.AddPage(tab1, "Animation")
        notebook.AddPage(tab2, "Color")
        notebook.AddPage(tab3, "Misc")

        # Use a sizer to make the notebook fill the TabbedControlPanel
        sizer = wx.BoxSizer()
        sizer.Add(notebook, 1, wx.EXPAND)
        self.SetSizer(sizer)


# --- OpenGL Panel (with one new method) ---


class OpenGLPanel(wx.glcanvas.GLCanvas):
    """The OpenGL rendering panel, now with color control."""

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

        # Animation state
        self.rotation_angle = 0
        self.rotation_speed = 5
        self.is_enabled = True
        self.color = (0.0, 1.0, 1.0)  # Initial color (cyan)

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
        if self.context and self.GetSizer() and self.IsShownOnScreen():
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
        # Use the current color
        GL.glColor3f(self.color[0], self.color[1], self.color[2])
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
        """A new method to control the rectangle's color."""
        self.color = (r, g, b)


# --- Main Frame using wx.SplitterWindow ---


class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(
            None, title="Resizable & Tabbed Control Demo", size=(1000, 600)
        )

        # Create the SplitterWindow
        self.splitter = wx.SplitterWindow(self)

        # Create the panels that will go in the splitter
        self.opengl_panel = OpenGLPanel(self.splitter)
        self.control_panel = TabbedControlPanel(
            self.splitter, self.opengl_panel
        )

        # Split the window vertically and set initial sash position
        self.splitter.SplitVertically(
            self.opengl_panel, self.control_panel, 700
        )

        # Set a minimum pane size to prevent one side from disappearing
        self.splitter.SetMinimumPaneSize(200)

        # A sizer to make the splitter fill the entire frame
        sizer = wx.BoxSizer()
        sizer.Add(self.splitter, 1, wx.EXPAND)
        self.SetSizer(sizer)

        self.Centre()
        self.Show()


if __name__ == "__main__":
    app = wx.App(False)
    frame = MainFrame()
    app.MainLoop()
