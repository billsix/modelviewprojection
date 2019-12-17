set term png
set output 'screenspace.png'
set linetype 11 lc rgb 'black'
set border lc 11
set xrange [0:1024]
set yrange [0:768]
set object 1 rect from 100,668 to 600,168 fc rgb "white"
set object 2 rect from 650,668 to 1550,168 fc rgb "white"
plot -1000 notitle
