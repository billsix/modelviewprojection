#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <math_formula> <image_size> <output_filename>"
    echo "Example: $0 \"E = 5 + m*c^2\" 800 output.png"
    exit 1
fi

# Assign arguments to variables
MATH_FORMULA=$1
IMAGE_SIZE=$2
OUTPUT_FILENAME=$3


# Create the LaTeX file
cat <<EOF > formula.tex
\documentclass{standalone}
\usepackage{amsmath}
\begin{document}
    \$ $MATH_FORMULA \$
\end{document}
EOF

# Compile the LaTeX file to DVI
latex formula.tex

# Convert DVI to PNG using dvipng
dvipng -D $IMAGE_SIZE -T tight -o $OUTPUT_FILENAME formula.dvi
