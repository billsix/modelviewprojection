set terminal svg size 600,600 fname 'Helvetica'

set output 'screenspace2.svg'
set linetype 11 lc rgb 'black'
set border lc 11
set xrange [0:1920]
set yrange [0:1200]
set object 1 rect from 100,1100 to 600,600 fc rgb "white"
set object 2 rect from 650,1100 to 1550,600 fc rgb "white"
plot -10000 notitle