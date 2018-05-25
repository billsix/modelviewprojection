set term png
set output 'rotate2.png'

set style line 1 lc rgb 'black' pt 5   # square
set linetype 11 lc rgb 'black'

set polar
set xtics axis nomirror
set ytics axis nomirror
unset rtics
set samples 160

set zeroaxis

set trange [pi/2:3*pi/4]

set label "(0,1)" at -0.05,0.9
set label "(-sin(angle),cos(angle))" at -0.9,0.6

set label "(0,0.4)" at -0.05,0.35
set label "(0.4*-sin(angle),0.4*cos(angle))" at -0.7,0.2


plot      1  notitle, 0.4  notitle, 'rotate2.dat' using 1:2 with points ls 1  notitle
