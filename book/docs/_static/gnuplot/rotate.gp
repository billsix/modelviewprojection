set terminal svg size 800,600 fname 'Helvetica' 

set output 'rotate.svg'

set style line 1 lc rgb 'black' pt 5   # square
set linetype 11 lc rgb 'black'

set polar
set xtics axis nomirror
set ytics axis nomirror
unset rtics
set samples 160

set zeroaxis

set trange [pi/2:3*pi/4]

set trange [0:pi/4]

set label "(1,0)" at 0.9,0.05
set label "(X,Y) = (cos(angle),sin(angle))" at 0.4,0.8

set label "(0.5,0)" at 0.32,0.05
set label "(X,Y) = (0.5*cos(angle),0.5*sin(angle))" at 0.0,0.4

set rmargin 10
set tmargin 5

set xlabel "Y" rotate by 0 offset 0,28
show xlabel

set ylabel "X" rotate by 0 offset 62,0
show ylabel




plot      1  notitle, 0.5  notitle, 'rotate.dat' using 1:2 with points ls 1  notitle
