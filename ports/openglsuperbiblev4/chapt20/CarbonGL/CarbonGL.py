# CarbonGL.py
# CarbonGL is an Apple Carbon (deprecated, Mac-only API) sample.
# Carbon was removed in macOS 10.15 (2019); there's no portable
# Python equivalent worth replicating. This stub prints a notice.
#
# OpenGL SuperBible, Chapter 20
# Python port of CarbonGL.cpp

import sys


def main() -> None:
    print(
        "CarbonGL is a deprecated Apple Carbon sample (no portable equivalent)."
    )
    print("See /superbible/examples/src/chapt20/CarbonGL/ for the original.")
    sys.exit(0)


if __name__ == "__main__":
    main()
