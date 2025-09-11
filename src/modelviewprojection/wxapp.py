import math
import time

import numpy as np
import wx
import wx.glcanvas as wxgl
from OpenGL import GL

vertex_shader_src = """
#version 330 core
layout (location = 0) in vec3 position;
layout (location = 1) in vec3 color;
uniform float angle;
out vec3 vColor;
void main()
{
    mat2 rot = mat2(cos(angle), -sin(angle),
                    sin(angle),  cos(angle));
    vec2 rotated = rot * position.xy;
    gl_Position = vec4(rotated, position.z, 1.0);
    vColor = color;
}
"""

fragment_shader_src = """
#version 330 core
in vec3 vColor;
out vec4 FragColor;
void main()
{
    FragColor = vec4(vColor, 1.0);
}
"""


class GLPanel(wxgl.GLCanvas):
    def __init__(self, parent):
        attribs = [
            wxgl.WX_GL_RGBA,
            wxgl.WX_GL_DOUBLEBUFFER,
            wxgl.WX_GL_DEPTH_SIZE,
            24,
            wxgl.WX_GL_CORE_PROFILE,
            wxgl.WX_GL_MAJOR_VERSION,
            3,
            wxgl.WX_GL_MINOR_VERSION,
            3,
        ]
        super().__init__(parent, attribList=attribs)
        self.context = wxgl.GLContext(self)

        self.init = False
        self.angle = 0.0
        self.speed = 1.0  # radians per second

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(16)  # ~60 FPS
        self.last_time = time.time()

    def OnPaint(self, event):
        wx.PaintDC(self)
        self.SetCurrent(self.context)

        if not self.init:
            self.InitGL()
            self.init = True

        self.OnDraw()
        self.SwapBuffers()

    def OnTimer(self, event):
        now = time.time()
        dt = now - self.last_time
        self.last_time = now
        self.angle += self.speed * dt
        self.Refresh(False)

    def compile_shader(self, source, shader_type):
        shader = GL.glCreateShader(shader_type)
        GL.glShaderSource(shader, source)
        GL.glCompileShader(shader)
        if not GL.glGetShaderiv(shader, GL.GL_COMPILE_STATUS):
            error = GL.glGetShaderInfoLog(shader).decode()
            raise RuntimeError(f"Shader compile error: {error}")
        return shader

    def InitGL(self):
        # Compile shaders
        vs = self.compile_shader(vertex_shader_src, GL.GL_VERTEX_SHADER)
        fs = self.compile_shader(fragment_shader_src, GL.GL_FRAGMENT_SHADER)
        self.program = GL.glCreateProgram()
        GL.glAttachShader(self.program, vs)
        GL.glAttachShader(self.program, fs)
        GL.glLinkProgram(self.program)
        if not GL.glGetProgramiv(self.program, GL.GL_LINK_STATUS):
            error = GL.glGetProgramInfoLog(self.program).decode()
            raise RuntimeError(f"Program link error: {error}")
        GL.glDeleteShader(vs)
        GL.glDeleteShader(fs)

        # Triangle data (pos + color)
        vertices = np.array(
            [
                # positions       # colors
                0.0,
                0.6,
                0.0,
                1.0,
                0.0,
                0.0,
                -0.6,
                -0.6,
                0.0,
                0.0,
                1.0,
                0.0,
                0.6,
                -0.6,
                0.0,
                0.0,
                0.0,
                1.0,
            ],
            dtype=np.float32,
        )

        self.VAO = GL.glGenVertexArrays(1)
        VBO = GL.glGenBuffers(1)

        GL.glBindVertexArray(self.VAO)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, VBO)
        GL.glBufferData(
            GL.GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL.GL_STATIC_DRAW
        )

        stride = 6 * vertices.itemsize
        offset = GL.ctypes.c_void_p(0)

        # Position attribute
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, False, stride, offset)
        GL.glEnableVertexAttribArray(0)

        # Color attribute
        offset = GL.ctypes.c_void_p(3 * vertices.itemsize)
        GL.glVertexAttribPointer(1, 3, GL.GL_FLOAT, False, stride, offset)
        GL.glEnableVertexAttribArray(1)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        GL.glBindVertexArray(0)

        GL.glClearColor(0.1, 0.1, 0.1, 1.0)

    def OnDraw(self):
        w, h = self.GetClientSize()

        dw = self.GetContentScaleFactor()
        GL.glViewport(0, 0, int(w * dw), int(h * dw))
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        GL.glUseProgram(self.program)
        angle_loc = GL.glGetUniformLocation(self.program, "angle")
        GL.glUniform1f(angle_loc, self.angle)

        GL.glBindVertexArray(self.VAO)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 3)
        GL.glBindVertexArray(0)


class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="wxPython OpenGL 3.3 Example", size=(600, 500))
        panel = wx.Panel(self)

        # --- Menu Bar ---
        menubar = wx.MenuBar()

        # Application menu
        app_menu = wx.Menu()
        quit_item = app_menu.Append(wx.ID_EXIT, "Quit\tCtrl+Q")
        self.Bind(wx.EVT_MENU, self.on_quit, quit_item)
        menubar.Append(app_menu, "Application")

        # Edit menu
        edit_menu = wx.Menu()
        prefs_item = edit_menu.Append(wx.ID_PREFERENCES, "Preferences...\tCtrl+,")
        self.Bind(wx.EVT_MENU, self.on_preferences, prefs_item)
        menubar.Append(edit_menu, "Edit")

        self.SetMenuBar(menubar)

        # --- Layout with canvas and controls ---
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)

        self.canvas = GLPanel(panel)
        vbox.Add(self.canvas, 1, wx.EXPAND | wx.ALL, 5)

        # Buttons
        btn1 = wx.Button(panel, label="Pause")
        btn2 = wx.Button(panel, label="Reverse")
        btn3 = wx.Button(panel, label="Reset")
        self.slider = wx.Slider(
            panel, value=60, minValue=0, maxValue=360, style=wx.SL_HORIZONTAL
        )

        hbox.Add(btn1, 1, wx.ALL, 5)
        hbox.Add(btn2, 1, wx.ALL, 5)
        hbox.Add(btn3, 1, wx.ALL, 5)

        vbox.Add(hbox, 0, wx.EXPAND)
        vbox.Add(self.slider, 0, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(vbox)

        # Bind events
        btn1.Bind(wx.EVT_BUTTON, self.on_pause)
        btn2.Bind(wx.EVT_BUTTON, self.on_reverse)
        btn3.Bind(wx.EVT_BUTTON, self.on_reset)
        self.slider.Bind(wx.EVT_SLIDER, self.on_slide)

        self.paused = False

    # --- Menu handlers ---
    def on_quit(self, event):
        self.Close()

    def on_preferences(self, event):
        wx.MessageBox(
            "Preferences dialog would go here.",
            "Preferences",
            wx.OK | wx.ICON_INFORMATION,
        )

    # --- Button/slider handlers ---
    def on_pause(self, event):
        self.paused = not self.paused
        self.canvas.speed = (
            0.0 if self.paused else self.slider.GetValue() * math.pi / 180.0
        )

    def on_reverse(self, event):
        self.canvas.speed *= -1

    def on_reset(self, event):
        self.canvas.angle = 0.0

    def on_slide(self, event):
        if not self.paused:
            self.canvas.speed = self.slider.GetValue() * math.pi / 180.0


class MyApp(wx.App):
    def OnInit(self):
        frame = MainFrame()
        frame.Show()
        return True


if __name__ == "__main__":
    app = MyApp(False)
    app.MainLoop()
