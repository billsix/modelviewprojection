set terminal svg size 600,600 fname 'Helvetica'

set output 'plot2.svg'
set linetype 11 lc rgb 'black'
set border lc 11
set xrange [-1:1]
set yrange [-1:1]
plot 'plot2.dat' using 1:2 with lines notitle, "" using 3:4:(sprintf("(%.1f, %.1f)", $1, $2)) with labels notitle , "" using 1:2 with point pt 7 notitle
