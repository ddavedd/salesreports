import datetime

def index_text(days):
   html = "<html>\n"
   x = open("tables/total_sales.html")
   html += x.read()
   x.close()
   x = open("tables/total_product_count.html")
   html += x.read()
   x.close()
   for d in days:
      output_date = d.strftime("%Y-%m-%d")
      html += "<a href='%s.html'>%s</a><p/>" % (output_date, output_date)
   html += "</html>"
   x = open("html/index.html", "w")
   x.write(html)
   x.close()

if __name__=="__main__":
   total_sales = open("total_sales.csv")
   days = []
   for x in total_sales.readlines():
      days.append( datetime.datetime.strptime(x.split(",")[0].strip(), "%Y %m %d"))
   index_text(days)
   #
   for d in days:
      html = "<html>\n"
      # get all tables from tables folder
      output_date = d.strftime("%Y-%m-%d")
      prefixes = ["daily_product", "daily_items", "hourly_sales"]
      for p in prefixes:
         x = open("tables/" + p + output_date + ".html")
         html += x.read()
         x.close()
      html += "</html>\n"
      x = open("html/" + output_date + ".html", "w")
      x.write(html)
      x.close()
         

   
      
