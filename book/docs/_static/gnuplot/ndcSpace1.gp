set terminal svg  fname 'Helvetica'

set output 'ndcSpace1.svg'
set size ratio -1
set linetype 11 lc rgb 'black'
set border lc 11
set xrange [0:1024]
set yrange [0:768]
set object 1 rect from 53,704 to 320,384 fc rgb "white"
set object 2 rect from 347,704 to 826,384 fc rgb "white"
plot 0 notitle
