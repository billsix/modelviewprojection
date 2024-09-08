# copyright 2024 William Emerison Six

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


#!/bin/env python3

import os
from argparse import ArgumentParser

parser: ArgumentParser = ArgumentParser(
    description="Parse command line arguments",
    epilog="""
Examples: python3 texExpToPng.py --exp "E = 5 + m*c^2" --size 800 --output output.png
""",
)


group = parser.add_mutually_exclusive_group(required=True)

# Add the expression argument
group.add_argument("--exp", type=str, help="Input string")

# Add the filename argument
group.add_argument(
    "-f", "--file", type=str, help="The filename containing the expression."
)


parser.add_argument("--size", type=int, help="Image size")
parser.add_argument("--output", type=str, help="Output file")


args = parser.parse_args()

expression = None
if args.exp:
    expression = args.exp
elif args.file:
    with open(args.file, "r") as file:
        expression = file.read()

# write latex script
latex_source = (
    """
\\documentclass{standalone}
\\usepackage{amsmath}
\\begin{document}
    $ """
    + expression
    + """ $
\\end{document}"""
)

with open("formula.tex", "w") as file:
    file.write(latex_source)

os.system("latex formula.tex")

os.system(
    "dvipng -D " + str(args.size) + " -T tight -o " + args.output + " formula.dvi"
)
