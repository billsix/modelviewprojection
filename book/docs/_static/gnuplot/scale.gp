set terminal svg size 600,600 fname 'Helvetica'

set output 'scale.svg'

set style line 1 lc rgb 'black' pt 5   # square
set linetype 11 lc rgb 'black'
set border lc 11
set xrange [0:10]
set yrange [0:10]

plot 'scale.dat' using 1:2 with points ls 1  notitle, "" using 3:4:(sprintf("%s", stringcolumn(5))) with labels notitle
