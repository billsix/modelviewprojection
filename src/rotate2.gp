set term png
set output 'rotate2.png'

set polar
set xtics axis nomirror
set ytics axis nomirror
unset rtics
set samples 160

set zeroaxis

set trange [pi/2:3*pi/4]

plot      1  notitle
