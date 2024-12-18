set terminal svg size 600,600 fname 'Helvetica'
set size ratio 1.0

set output 'modelspace.svg'
set linetype 11 lc rgb 'black'
set border lc 11
set xrange [-4.0:4.0]
set yrange [-4.0:4.0]
set object 1 rect from -1.0,-3.0 to 1.0,3.0 fc rgb "white"
plot -100000 notitle
