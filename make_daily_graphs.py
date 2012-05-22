import datetime
import subprocess

start_date = datetime.date(2012, 4, 30)
end_date = datetime.date(2012,5,31)
current_date = start_date
day = datetime.timedelta(days=1)
while current_date < end_date:
   string_date = current_date.strftime("%Y-%m-%d")
   current_date += day
   
   cat = subprocess.Popen(["cat","hourly_sales.gnuplot"], stdout=subprocess.PIPE)
   sed = subprocess.Popen(["sed","s/FILENAME/%s.data/" % string_date], stdin=cat.stdout, stdout=subprocess.PIPE)
   plot = subprocess.Popen(["gnuplot"], stdin=sed.stdout)
   cat.stdout.close()
   sed.stdout.close()

