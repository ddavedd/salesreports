set style data histograms
set style fill solid 1.0
set boxwidth 1
set yrange [0:]
set terminal png
set title "Sales"
set xlabel "Hour"
set ylabel "Sales Hourly"
set output "hourly_graphs/FILENAME.png"
plot "hourly/FILENAME" using 2:xticlabels(1) notitle lc rgb "blue"
