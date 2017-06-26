set term png
set output 'monitor.png'
set linetype 11 lc rgb 'black'
set border lc 11
unset xtics
set x2tics
set xrange [0:1024]
set yrange [768:0]
plot -10000 axes x2y1 notitle