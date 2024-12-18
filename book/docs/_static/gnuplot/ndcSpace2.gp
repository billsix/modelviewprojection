set terminal svg size 600,600 fname 'Helvetica'

set output 'ndcSpace2.svg'
set linetype 11 lc rgb 'black'
set border lc 11
unset xtics
set x2tics
set xrange [0:1920]
set yrange [1200:0]
set object 1 rect from 240,150 to 1680,1050 fc rgb "white"
plot 0 axes x2y1 notitle
