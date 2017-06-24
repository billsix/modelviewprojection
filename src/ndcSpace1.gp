set term png
set output 'ndcSpace1.png'
set linetype 11 lc rgb 'black'
set border lc 11
set xtics format ""
set x2tics
set xrange [0:1024]
set yrange [768:0]
set object 1 rect from 128,96 to 896,672 fc rgb "white"
plot 0 axes x2y1 notitle
