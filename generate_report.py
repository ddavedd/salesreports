import MySQLdb
import sqlite3
import datetime
VT_INT = 0
VT_FLOAT = 1

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
      text += reduce(lambda x,y: str(x) + "," + str(y), o) + "\n"
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

def generate_transactions(cursor):
   min_date, max_date = get_range_of_days(cursor)
   current = min_date
   delta = datetime.timedelta(days=1)
   day_trans = []
   while current < max_date:
      day_trans.append([current.strftime("%Y %m %d"), generate_daily_transactions(cursor, current)])
      current += delta
   return day_trans

def generate_daily_transactions(cursor, date):
   date_string = date.strftime("%Y %m %d")
   sql = "SELECT COUNT(*) FROM transaction_total \
      WHERE timestamp LIKE '%s%%'" % date_string
   cursor.execute(sql)
   trans_count = int(cursor.fetchone()['COUNT(*)'])
   return trans_count
   
def generate_hourly_transactions(cursor, date):
   hours = []
   for hour in range(8,20):
      hours.append([hour, generate_hour_transaction(cursor, date, hour)])
   return hours
   
def generate_hour_transaction(cursor, date, hour):
   date_string = date.strftime("%Y %m %d")
   sql = "SELECT COUNT(*) FROM transaction_total \
      WHERE timestamp LIKE '%s %s%%'" % (date_string, str(hour))  
   cursor.execute(sql)
   trans_count = int(cursor.fetchone()['COUNT(*)'])
   return trans_count
   
def generate_report(cursor):
   sales_by_month = generate_total_sales_by_month(cursor)
   write_to_file(sales_by_month, "month.csv")
   
   sales_by_week = generate_sales_by_week(cursor)
   write_to_file(sales_by_week, "week.csv")
   
   total_sales = generate_total_sales_by_day(cursor)
   write_to_file(total_sales, "total_sales.csv")

   trans = generate_transactions(cursor)
   write_to_file(trans, "transactions.csv")
   
   product_count = generate_total_product_count(cursor)
   write_to_file(product_count, "total_product_count.csv")
   
   generate_hourly_sales(cursor)
   
   generate_daily_product_count(cursor)
   # NOTE: MUST RUN product count before item count, it creates a temporary table. Maybe make all temp tables at beginning
   generate_items_sold(cursor)

def generate_sales_by_week(cursor, year=2012, min_month=5, max_month=11):
   # find initial monday to start with
   initial_date = datetime.date(year, min_month, 1)
   one_day = datetime.timedelta(days=1)
   while initial_date.weekday() != 0:
      initial_date += one_day
   # add 7 days each time
   current = initial_date
   weeks = [["Week","Sales"]]
   while current.month < max_month:
      week_sql = "SELECT SUM(total) FROM transaction_total WHERE "
      dates = []
      start = current
      for _ in range(7):
         date_string = current.strftime("%Y %m %d")
         dates.append(" timestamp LIKE '%s%%' " % date_string)
         end = current
         current += one_day
      week_sql += reduce(lambda x,y: x + " OR " + y, dates)
      
      weekly_sales = executeSqlForValue(cursor, week_sql, "SUM(total)", VT_FLOAT)
      week_text = start.strftime("%m/%d") + " - " + end.strftime("%m/%d")
      if weekly_sales > 0.01:
         weeks.append([week_text, weekly_sales])
   return weeks

def generate_total_sales_by_month(cursor, year=2012, min_month=5, max_month=11):
   monthly_sales = [["Month","Sales"]]
   for month in range(min_month, max_month + 1):
      if month < 10:
         year_month_string = "%i 0%i" % (year, month)
      else:
         year_month_string = "%i %i" % (year, month)
         
      month_sales_sql = "SELECT SUM(total) FROM transaction_total WHERE timestamp LIKE '%s%%'" % year_month_string
      month_sales = executeSqlForValue(cursor, month_sales_sql, "SUM(total)", VT_FLOAT)
      if monthly_sales > 0.01:      
         monthly_sales.append([month, month_sales])
   return monthly_sales
   
def generate_total_sales_by_day(cursor):
   min_date, max_date = get_range_of_days(cursor)
   current = min_date
   delta = datetime.timedelta(days=1)
   days = []
   while current <= max_date:
      date_string = current.strftime("%Y %m %d")
      total_sales_sql = "SELECT SUM(total) FROM transaction_total WHERE timestamp LIKE '%s%%'" % date_string
      sales = executeSqlForValue(cursor, total_sales_sql, "SUM(total)", VT_FLOAT)
      current += delta
      if sales > 0.01:
         days.append([date_string, sales])
   return days
         
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
   return [["Product","Count"]] + product_counts
   
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
   return [["Item","Count"]] + item_counts
   
def executeSqlForValue(cursor, sql, sql_select_column_str, value_type):
   cursor.execute(sql)
   if value_type == VT_INT:
      try:
         return int(cursor.fetchone()[sql_select_column_str])
      except:
         return 0
   elif value_type == VT_FLOAT:
      try:
         return float(cursor.fetchone()[sql_select_column_str])
      except:
         return 0.0
   else:
      print "Invalid value type in executeSqlForValue"
      return None
      
def generate_hourly_sales_for_date(cursor, date, min_hour, max_hour):
   date_string = date.strftime("%Y %m %d")
   hourly_sales = [["Hour","Sales","Transactions"]]
   
   for hour in range(min_hour, max_hour+1):
      hour_date_string = date_string
      if hour < 10:
         hour_date_string += " 0%i" % hour
      else:
         hour_date_string += " %i" % hour
      
      sales_sql = "SELECT SUM(total) FROM transaction_total WHERE timestamp LIKE '%s%%'" % hour_date_string
      hourly_sale = executeSqlForValue(cursor, sales_sql, "SUM(total)", VT_FLOAT) 
      
      trans_sql = "SELECT COUNT(*) FROM transaction_total WHERE timestamp LIKE '%s%%'" % hour_date_string
      hourly_trans = executeSqlForValue(cursor, trans_sql, "COUNT(*)", VT_INT)
      
      hourly_sales.append([hour, hourly_sale, hourly_trans])
   
   total_sales_sql = "SELECT SUM(total) FROM transaction_total WHERE timestamp LIKE '%s%%'" % date_string
   total_sales = executeSqlForValue(cursor, total_sales_sql, "SUM(total)", VT_FLOAT)
   
   total_trans_sql = "SELECT COUNT(*) FROM transaction_total WHERE timestamp LIKE '%s%%'" % date_string
   total_trans = executeSqlForValue(cursor, total_trans_sql, "COUNT(*)", VT_INT)
   
   return hourly_sales + [["Total", total_sales, total_trans]]
   
def generate_hourly_sales(cursor, min_hour=6, max_hour=19):
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

