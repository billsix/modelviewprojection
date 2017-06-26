set term png
set output 'screenspace2.png'
set linetype 11 lc rgb 'black'
set border lc 11
unset xtics
set x2tics
set xrange [0:1920]
set yrange [1200:0]
set object 1 rect from 100,100 to 600,600 fc rgb "white"
set object 2 rect from 650,100 to 1550,600 fc rgb "white"

plot -10000 axes x2y1 notitle