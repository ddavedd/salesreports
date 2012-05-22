

def convert_csv_to_table(input_file):
   # from csv
   html = "<table border=1>\n"
   for x in csv_file.readlines():
      html += "<tr>\n"
      items = x.split(",")
      for item in items:
         html += "\t<td>" + item.strip() + "</td>\n"
      html += "</tr>\n"
   html += "</table>\n"
   return html
   
if __name__=="__main__":
   import sys
   for i in range(1,len(sys.argv)):
      filename = sys.argv[i]
      csv_file = open(filename)
      table = convert_csv_to_table(filename)
      csv_file.close()
      out_filename = filename.split("/")[-1].split(".")[0] + ".html"
      out_file = open("tables/" + out_filename, "w")
      out_file.write(table)
      out_file.close()
