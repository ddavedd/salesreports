import datetime
import re
   
def add_hyperlinks(text):
   #print text
   date_format = r'\d{4}\s\d{2}\s\d{2}'
   matches = re.findall(date_format, text)
   for match in matches:
      link_from_match = "<a href=\"" + match.replace(" ", "-") + ".html\">" + match + "</a>"
      text = text.replace(match, link_from_match)
   return text
   
def index_text(days):
   import make_compact_calendar
   html = "<html>\n"
   html += make_compact_calendar.make_compact_calendar(2012)
   x = open("tables/month.html")
   html += x.read()
   x.close()
   
   x = open("tables/week.html")
   html += x.read()
   x.close()
   
   x = open("tables/total_sales.html")
   total_sales_html = x.read()
   linked_total_sales = add_hyperlinks(total_sales_html)
   html += linked_total_sales
   x.close()
   x = open("tables/total_product_count.html")
   html += x.read()
   x.close()
   #for d in days:
   #   output_date = d.strftime("%Y-%m-%d")
   #   html += "<a href='%s.html'>%s</a><p/>" % (output_date, output_date)
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
