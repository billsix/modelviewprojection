# CocoGL.py
# Apple Cocoa (Objective-C) NSOpenGLView sample. Mac-specific; not
# portable to plain Python. The Python ports of the rest of the
# book use GLFW which abstracts the Cocoa setup away.
#
# OpenGL SuperBible, Chapter 20

import sys


def main() -> None:
    print("CocoGL is an Objective-C / Cocoa sample (Mac only).")
    print("See /superbible/examples/src/chapt20/CocoGL/ for the original.")
    sys.exit(0)


if __name__ == "__main__":
    main()
