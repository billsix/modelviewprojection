# GLView.py
# GLView is a Win32 MFC dialog application that renders OpenGL into
# a child window with a startup pixel-format chooser dialog. It's
# fundamentally an MFC sample — not portable. This stub prints a
# notice and exits.
#
# OpenGL SuperBible, Chapter 19
# Python port of GLView.cpp by Richard S. Wright Jr.

import sys


def main() -> None:
    print("GLView is a Win32 MFC sample (no portable equivalent).")
    print("See /superbible/examples/src/chapt19/GLView/ for the original")
    print("(~928 lines across GLView.cpp, GLViewDlg.cpp, GLWindow.cpp,")
    print("GLViewPixFormatDlg.cpp).")
    sys.exit(0)


if __name__ == "__main__":
    main()
