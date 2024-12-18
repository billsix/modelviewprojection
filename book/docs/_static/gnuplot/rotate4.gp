set terminal svg size 600,600 fname 'Helvetica'

set output 'rotate4.svg'

set style line 1 lc rgb 'black' pt 5   # square
set linetype 11 lc rgb 'black'
set xrange [-1:1]
set yrange [-1:1]


set rmargin 10
set tmargin 5

set xlabel "Y" rotate by 0 offset 0,28
show xlabel

set ylabel "X" rotate by 0 offset 62,0
show ylabel




set zeroaxis

plot 'rotate4.dat' using 1:2 with points ls 1  notitle, "" using 3:4:(sprintf("%s", stringcolumn(5))) with labels notitle
