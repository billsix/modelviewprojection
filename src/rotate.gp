set term png
set output 'rotate.png'

set polar
set xtics axis nomirror
set ytics axis nomirror
unset rtics
set samples 160

set zeroaxis

set trange [0:pi/4]

plot      1  notitle
