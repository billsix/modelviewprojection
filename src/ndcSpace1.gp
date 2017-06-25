set term png
set output 'ndcSpace1.png'
set linetype 11 lc rgb 'black'
set border lc 11
set xtics format ""
set x2tics
set xrange [0:1024]
set yrange [768:0]
set object 1 rect from 53,64 to 320,384 fc rgb "white"
set object 2 rect from 347,64 to 826,384 fc rgb "white"
plot 0 axes x2y1 notitle
