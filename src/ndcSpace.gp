set term png
set output 'ndcSpace.png'
set linetype 11 lc rgb 'black'
set border lc 11
set xtics format ""
set x2tics
set xrange [-1.0:1.0]
set yrange [-1.0:1.0]
set object 1 rect from -.75,0.75 to .75,-.75 fc rgb "white"
plot -50 axes x2y1 notitle
