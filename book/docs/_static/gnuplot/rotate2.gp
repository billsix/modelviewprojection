set term png
set output 'rotate2.png'

set style line 1 lc rgb 'black' pt 5   # square
set linetype 11 lc rgb 'black'

set polar
unset xtics
unset ytics
unset rtics
set samples 160

set zeroaxis

set trange [pi/2:3*pi/4]

set trange [0:pi/4]

set label "(1,0)" at .9,.05
set label "(Y, -X) = (cos(angle),sin(angle))" at .4,.8

set label "(.4,0)" at .32,.05
set label "(Y, -X) = (.4*cos(angle),.4*sin(angle))" at .0,.4

set rmargin 10
set bmargin 5

set xlabel "X" rotate by 0 offset 0,-2
show xlabel

set ylabel "Y" rotate by 0 offset 62,0
show ylabel



plot      1  notitle, .4  notitle, 'rotate2.dat' using 1:2 with points ls 1  notitle
