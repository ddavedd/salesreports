rm hourly/*
rm product_count/*
rm items_count/*
rm total_sales.csv
rm total_product_count.csv
mkdir hourly
mkdir items_count
mkdir tables
mkdir product_count
mkdir html
python generate_report.py mysql 127.0.0.1
python convert_to_table.py hourly/*
python convert_to_table.py product_count/*
python convert_to_table.py items_count/*
python convert_to_table.py total_sales.csv
python convert_to_table.py total_product_count.csv
python convert_to_table.py month.csv
python convert_to_table.py week.csv
python make_site.py
cd html
#ftp -nvi sitename << END_SCRIPT
#user (user) (password)
#cd (output_directory)
#mput *.html
#bye
#END_SCRIPT

