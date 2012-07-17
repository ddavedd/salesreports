import datetime

def make_compact_calendar(year):
   html = "<table>\n"
   count = 0
   for month in range(4,12):
      if count % 4 == 0:
         html += "</tr>\n<tr>\n"
      html += "<td>\n" + make_month_links(year, month) + "</td>\n"
      count += 1
   return html + "</tr></table>"
   
def make_month_links(year, month):
   start_date = datetime.date(year, month, 1)
   days = []
   html = "<table border=1>\n"
   html += "\t<tr><th colspan=7>" + start_date.strftime("%B") + "</th></tr>\n"
   html += "\t<tr><th>M</th><th>Tu</th><th>W</th><th>Th</th><th>F</th><th>S</th><th>Su</th></tr>\n"
   
   initial = start_date.weekday()
   for i in range(initial):
      days.append(None)
      
   delta = datetime.timedelta(days=1)
   current = start_date
   while current.month == start_date.month:
      if current.weekday() == 6:
         days.append( str(current.day) )
      else:
         days.append("<a href=\"" + current.strftime("%y-%m-%d") + "\">" + str(current.day) + "</a>")
      current += delta
   
   
   day_count = 0
   for d in days:
      if day_count == 0:
         html += "<tr>\n"
      if d is None:
         html += "<td></td>\n"
      else:
         html += "<td>" + d + "</td>\n"
      if day_count == 6:
         html += "</tr>\n"
         day_count = 0
      else:
         day_count += 1
   html += "</table>\n"
   return html

if __name__=="__main__":
   calendar_html = make_compact_calendar(2012)
   x = open("calendar.html", "w")
   x.write(calendar_html)
   x.close()
