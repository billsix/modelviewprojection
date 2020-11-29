set term png
set output 'rotate4.png'

set style line 1 lc rgb 'black' pt 5   # square
set linetype 11 lc rgb 'black'
set xrange [-1:1]
set yrange [-1:1]



set zeroaxis

plot 'rotate4.dat' using 1:2 with points ls 1  notitle, "" using 3:4:(sprintf("%s", stringcolumn(5))) with labels notitle
