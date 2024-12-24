set terminal svg size 600,600 fname 'Helvetica'

set output 'viewport.svg'
set linetype 11 lc rgb 'black'
set label "(-1,-1)" at 360,50
set label "(1,-1)" at 1400,50
set label "(-1,1)" at 360,1150
set label "(1,1)" at 1400,1150
set border lc 11
set xrange [0:1920]
set yrange [0:1200]
set object 1 rect from 360,0 to 1560,1200 fc rgb "white"

plot -10000 notitle