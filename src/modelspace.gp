set size ratio 1.0
set term png
set output 'modelspace.png'
set linetype 11 lc rgb 'black'
set border lc 11
set xrange [-40.0:40.0]
set yrange [-40.0:40.0]
set object 1 rect from -10.0,-30.0 to 10.0,30.0 fc rgb "white"
plot -100000 notitle
