set term png
set output 'ndcSpace2.png'
set linetype 11 lc rgb 'black'
set border lc 11
set xtics format ""
set x2tics
set xrange [0:1920]
set yrange [1200:0]
set object 1 rect from 240,150 to 1680,1050 fc rgb "white"
plot 0 axes x2y1 notitle
