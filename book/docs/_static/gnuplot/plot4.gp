set terminal svg  fname 'Helvetica'

set output 'plot4.svg'
set linetype 11 lc rgb 'black'
set border lc 11
set xrange [-1:1]
set yrange [-1:1]
plot 'plot4.dat' using 1:2 with lines notitle, "" using 3:4:(sprintf("(%.1f, %.1f) + %s", $1, $5, stringcolumn(6))) with labels notitle , "" using 1:2 with point pt 7 notitle
