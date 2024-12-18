set terminal svg size 600,600 fname 'Helvetica'

set output 'ndcSpace.svg'
set linetype 11 lc rgb 'black'
set border lc 11
set xrange [-1.0:1.0]
set yrange [-1.0:1.0]
set object 1 rect from -.895,.833 to -.375,0.0 fc rgb "white"
set object 2 rect from -.322,.833 to .614,0.0 fc rgb "white"
plot -50 notitle
