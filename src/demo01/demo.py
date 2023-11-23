# Copyright (c) 2018-2022 William Emerison Six
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# begin 20134134fb054ac6764edfb4764935b86f20a795
import sys

# end 20134134fb054ac6764edfb4764935b86f20a795
# begin 6901922753dbf8df496fd46ae4a0eeb4e6243ef4
from OpenGL.GL import (
    glMatrixMode,
    glLoadIdentity,
    GL_PROJECTION,
    GL_MODELVIEW,
    glClear,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    glViewport,
    glClearColor,
)

# end 6901922753dbf8df496fd46ae4a0eeb4e6243ef4

# begin 4b5a486083da608751701fa7e42e37bbc4cfd06e
import glfw

# end 4b5a486083da608751701fa7e42e37bbc4cfd06e

# begin 0c30d0c1c7c793e097bcfb46208f14998d77dd0a
if not glfw.init():
    sys.exit()
# end 0c30d0c1c7c793e097bcfb46208f14998d77dd0a

# begin cbb5da55f24c88b41c195f36bbbf99969e95765c
glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 1)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 4)
# end cbb5da55f24c88b41c195f36bbbf99969e95765c

# begin d1e099847a03149e01d2ec4dc42bb261524b2a95
window = glfw.create_window(500, 500, "ModelViewProjection Demo 1", None, None)
# end d1e099847a03149e01d2ec4dc42bb261524b2a95

# begin a9948cba6a31fd1774c1a0e1ae634bbad8c6c7f3
if not window:
    glfw.terminate()
    sys.exit()
# end a9948cba6a31fd1774c1a0e1ae634bbad8c6c7f3

# begin 7ddbe862d3ff7b6ee489ac7ac565b8a5e72f7f9f
glfw.make_context_current(window)
# end 7ddbe862d3ff7b6ee489ac7ac565b8a5e72f7f9f

# begin 63277c9f3b6e8071722b93baf8e77bb8ee6c677d
def on_key(window, key, scancode, action, mods):
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, 1)


# end 63277c9f3b6e8071722b93baf8e77bb8ee6c677d

glfw.set_key_callback(window, on_key)

# begin 788fae9aeb2ebe9e911e2c3f6399f1b51a0bd956
glClearColor(0.0, 0.0, 0.0, 1.0)
# end 788fae9aeb2ebe9e911e2c3f6399f1b51a0bd956

# begin a3fdb44a76cc8a6b843c780a68e00366176eadab
glMatrixMode(GL_PROJECTION)
glLoadIdentity()
glMatrixMode(GL_MODELVIEW)
glLoadIdentity()
# end a3fdb44a76cc8a6b843c780a68e00366176eadab


# begin b203706b4d71815e8490a9a65ff9fe1fe1db38cd
while not glfw.window_should_close(window):
    glfw.poll_events()

    width, height = glfw.get_framebuffer_size(window)
    glViewport(0, 0, width, height)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glfw.swap_buffers(window)
# end b203706b4d71815e8490a9a65ff9fe1fe1db38cd

glfw.terminate()
