set terminal svg  fname 'Helvetica'

set output 'monitor.svg'
set size ratio -1
set linetype 11 lc rgb 'black'
set border lc 11
set xrange [0:1024]
set yrange [0:768]
plot -10000 notitle