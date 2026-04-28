# ES_example.py
# Chapter 22 covers OpenGL ES — the embedded-systems profile used on
# phones, embedded devices, etc. ES_example is a Symbian/embedded-
# specific demo that requires an ES context, EGL setup, and a
# platform shell that Python's GLFW doesn't provide. PyOpenGL has no
# built-in ES bindings either. Skip with a note.
#
# OpenGL SuperBible, Chapter 22

import sys


def main() -> None:
    print("ES_example is an OpenGL ES (embedded) sample.")
    print("Requires EGL/ES bindings that aren't available via GLFW+PyOpenGL.")
    print("See /superbible/examples/src/chapt22/ES_example/ for the original.")
    sys.exit(0)


if __name__ == "__main__":
    main()
