# RThread.py
# RThread.cpp demonstrates Win32 multithreaded OpenGL with WGL
# extensions: a worker thread does all the rendering while the main
# thread handles the message pump. WGL contexts are Win32-only — the
# pthread/POSIX path with GLFW would be a different demo entirely.
# This stub prints a notice and exits; see the C++ source for the
# original.
#
# OpenGL SuperBible, Chapter 19
# Python port of RThread.cpp by Richard S. Wright Jr.

import sys


def main() -> None:
    print("RThread is a Win32-only multithreaded WGL demo.")
    print("See /superbible/examples/src/chapt19/RThread/RThread.cpp")
    print("for the original (~376 lines).")
    print("Python equivalent would require a different design (GLFW")
    print("requires that all GL calls happen on the same thread that")
    print("called glfw.make_context_current).")
    sys.exit(0)


if __name__ == "__main__":
    main()
