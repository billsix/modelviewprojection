set term png
set output 'monitor2.png'
set linetype 11 lc rgb 'black'
set border lc 11
set xtics format ""
set x2tics
set xrange [0:1920]
set yrange [1200:0]
plot -10000 axes x2y1 notitle