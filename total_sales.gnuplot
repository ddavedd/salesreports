set datafile separator ","
set xdata time
set timefmt "%Y %m %d"
set style data histogram
set yrange [0:]
set boxwidth 1
set xtic rotate by -45
set terminal png
set output "total_sales.png"
plot "total_sales.csv" using 1:2 with boxes

