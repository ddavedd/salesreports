import MySQLdb
import sqlite3
import datetime

def get_range_of_days(cursor):
   cursor.execute("SELECT MIN(timestamp) FROM transaction_total")
   row = cursor.fetchone()
   min_date = datetime.datetime.strptime(row["MIN(timestamp)"], "%Y %m %d %H %M %S")
   cursor.execute("SELECT MAX(timestamp) FROM transaction_total")
   row = cursor.fetchone()
   max_date = datetime.datetime.strptime(row["MAX(timestamp)"], "%Y %m %d %H %M %S")
   return min_date, max_date
   
def write_to_file(output_values, output_file_name):
   text = ""
   for o in output_values:
      text += str(o[0]) + "," + str(o[1]) + "\n"
   output_file = open(output_file_name, "w")
   output_file.write(text)
   output_file.close()
   
def connect_to_database(database_type, database_path):
   if database_type.strip() == "mysql":
      try:
          db_user = "root"
          db_user_pw = "dave"
          db_name = "products"
          db_host = database_path
          connection = MySQLdb.connect(db_host, db_user, db_user_pw, db_name)
          return connection, connection.cursor(MySQLdb.cursors.DictCursor)
      except MySQLdb.DatabaseError as e:
          print "Failed to connect to mysql database, Database Error, check path"
          print e
          return None, None
      except:
          print "General Error"
          return None, None
   else:
      connection = sqlite3.connect(database_path)
      connection.row_factory = sqlite3.Row
      return connection, connection.cursor()
      
def generate_report(cursor):
   total_sales = generate_total_sales_by_day(cursor)
   write_to_file(total_sales, "total_sales.csv")
   
   product_count = generate_total_product_count(cursor)
   write_to_file(product_count, "total_product_count.csv")
   
   generate_hourly_sales(cursor)
   
   generate_daily_product_count(cursor)
   # NOTE: MUST RUN product count before item count, it creates a temporary table. Maybe make all temp tables at beginning
   generate_items_sold(cursor)
   
def generate_total_sales_by_day(cursor):
   cursor.execute("SELECT * FROM transaction_total")
   daily_sales = {}
   rows = cursor.fetchall()
   for row in rows:
      date_string = get_timestamp_date_string(row["timestamp"])
      if date_string in daily_sales:
         daily_sales[date_string] = daily_sales[date_string] + row["total"]
      else:
         daily_sales[date_string] = row["total"]
   daily_sales_list = []
   for date, sales in daily_sales.iteritems():
      daily_sales_list.append((date, sales))
   daily_sales_list.sort()
   return daily_sales_list
   
def generate_total_product_count(cursor):
   cursor.execute("SELECT * FROM transaction_item")
   transaction_item_rows = cursor.fetchall()
   product_counts = {}
   for trans_item in transaction_item_rows:
      if trans_item["is_product"]:
         if trans_item["product_id"] in product_counts:
            product_counts[trans_item["product_id"]] += trans_item["product_amount"]
         else:
            product_counts[trans_item["product_id"]] = trans_item["product_amount"]
   cursor.execute("SELECT * FROM products")
   product_rows = cursor.fetchall()
   name_value_list = []
   for product in product_rows:
      if product["product_id"] in product_counts:
         amount = product_counts[product["product_id"]]
      else:
         amount = 0
      name_value_list.append( (product["prod_name"], amount))
   name_value_list.sort()
   return name_value_list

def get_timestamp_date_string(timestamp):
   transaction_date = datetime.datetime.strptime(timestamp, "%Y %m %d %H %M %S")
   return transaction_date.strftime("%Y %m %d")

def get_transaction_id_days(cursor):
   cursor.execute("SELECT transaction_id, timestamp FROM transaction_total")
   rows = cursor.fetchall()
   id_days = {}
   for row in rows:
      id_days[row["transaction_id"]] = get_timestamp_date_string(row["timestamp"])
   return id_days
   
def generate_daily_product_count(cursor):
   sql = "CREATE TEMPORARY TABLE products_sold SELECT is_product, product_id, product_amount, timestamp FROM \
      transaction_item INNER JOIN transaction_total ON transaction_item.transaction_id=transaction_total.transaction_id"
   cursor.execute(sql)
   sql = "CREATE TEMPORARY TABLE named_products_sold SELECT * FROM products_sold NATURAL JOIN products"
   cursor.execute(sql)
   min_date, max_date = get_range_of_days(cursor)
   current_date = min_date
   day = datetime.timedelta(days=1)
   while current_date < max_date + day:
      daily_products = generate_daily_product_count_by_date(cursor, current_date)
      file_date_string = current_date.strftime("%Y-%m-%d")
      if len(daily_products)>0:
         write_to_file(daily_products, "product_count/daily_product%s.csv" % file_date_string)
      current_date += day
      
def generate_daily_product_count_by_date(cursor, date):
   date_string = date.strftime("%Y %m %d")
   sql = "SELECT prod_name, sum(product_amount) FROM named_products_sold \
      WHERE timestamp LIKE '%s%%' GROUP BY prod_name " % date_string
   cursor.execute(sql)
   product_counts = []
   for x in cursor.fetchall():
      product_counts.append([x["prod_name"],x["sum(product_amount)"]])
   product_counts.sort()
   return product_counts
   
def generate_items_sold(cursor):   
   sql = "CREATE TEMPORARY TABLE items_sold SELECT * FROM named_products_sold NATURAL JOIN items"
   cursor.execute(sql)
   min_date, max_date = get_range_of_days(cursor)
   current_date = min_date
   day = datetime.timedelta(days=1)
   while current_date < max_date + day:
      daily_items = generate_items_sold_count_by_date(cursor, current_date)
      file_date_string = current_date.strftime("%Y-%m-%d")
      if len(daily_items)>0:
         write_to_file(daily_items, "items_count/daily_items%s.csv" % file_date_string)
      current_date += day
   
def generate_items_sold_count_by_date(cursor, date):
   date_string = date.strftime("%Y %m %d")
   sql = "select item_name, sum(product_amount*item_count) from items_sold WHERE timestamp LIKE '%s%%' GROUP BY item_name" % date_string
   cursor.execute(sql)
   item_counts = []
   for x in cursor.fetchall():
      item_counts.append([x["item_name"], x["sum(product_amount*item_count)"]])
   item_counts.sort()
   return item_counts
   
def generate_hourly_sales_for_date(cursor, date, min_hour, max_hour):
   date_string = date.strftime("%Y %m %d")
   hourly_sales = []
   sql = "SELECT SUM(total) FROM transaction_total WHERE timestamp LIKE '%s%%'" % date_string
   cursor.execute(sql)
   row = cursor.fetchone()
   if row["SUM(total)"] is None:
      return None
   else:
      for hour in range(min_hour,max_hour+1):

         hour_date_string = date_string
         if hour < 10:
            hour_date_string += " 0%i" % hour
         else:
            hour_date_string += " %i" % hour
         
         sql = "SELECT SUM(total) FROM transaction_total WHERE timestamp LIKE '%s%%'" % hour_date_string
         #print sql
         cursor.execute(sql)
         row = cursor.fetchone()
         if row["SUM(total)"] is None:
            hour_amount = 0.0
         else:
            hour_amount = row["SUM(total)"]
            
         hourly_sales.append([hour, hour_amount])
      return hourly_sales
   
def generate_hourly_sales(cursor, min_hour=6, max_hour=20):
   min_date, max_date = get_range_of_days(cursor)
   time_delta = datetime.timedelta(days=1)
   date = min_date
   while date < max_date + time_delta:
      file_date_string = date.strftime("%Y-%m-%d")
      hourly_sales = generate_hourly_sales_for_date(cursor, date, min_hour, max_hour)
      if hourly_sales is not None:
         write_to_file(hourly_sales, "hourly/hourly_sales%s.csv" % file_date_string)
      date += time_delta
      
if __name__ == "__main__":
   import sys
   if len(sys.argv) != 3:
      print "Incorrect number of agruments. Correct usage is ./generate_report.py [mysql-or-sqlite] [path_to_database-or-ip_address_database]"
   else:
      db_type = sys.argv[1]
      path = sys.argv[2]
      
      print "Connecting to database on path " + str(path)
      database_connection, database_cursor = connect_to_database(db_type, path)
      if database_connection is None:
         print "Unable to connect to database, report will not be generated" 
      else:
         print "Generating report"
         generate_report(database_cursor)
         print "Report generation finished, closing database connection."
         database_connection.close()
         print "Database connection closed. Exiting"

