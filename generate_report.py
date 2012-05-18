import MySQLdb
import sqlite3
import datetime

def write_to_file(output_values, output_file_name):
   text = ""
   for o in output_values:
      text += str(o[0]) + "," + str(o[1]) + "\n"
   output_file = open(output_file_name, "w")
   output_file.write(text)
   output_file.close()
   
def connect_to_database(database_type, database_path):
   print database_type
   print "!!!"
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
   generate_total_product_count(cursor)
   generate_items_sold_count(cursor)
   generate_hourly_sales(cursor)
   generate_daily_product_count(cursor)

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
   trans_id_days =  get_transaction_id_days(cursor)
   cursor.execute("SELECT * FROM transaction_item")
   transaction_item_rows = cursor.fetchall()
   product_by_day_counts = {}

   for trans_item in transaction_item_rows:
      if trans_item["is_product"]:
         trans_date = trans_id_days[trans_item["transaction_id"]]
         if trans_date in product_by_day_counts:
            if trans_item["product_id"] in product_by_day_counts[trans_date]:
               product_by_day_counts[trans_date][trans_item["product_id"]] += trans_item["product_amount"]
            else:
               product_by_day_counts[trans_date][trans_item["product_id"]] = trans_item["product_amount"]
         else:
            product_by_day_counts[trans_date] = {trans_item["product_id"]: trans_item["product_amount"]}
            
   return product_by_day_counts
      
def generate_items_sold_count(cursor):
   pass
   
def generate_hourly_sales(cursor):
   cursor.execute("SELECT * FROM transaction_total")
   hourly_sales = {}
   rows = cursor.fetchall()
   for row in rows:
      transaction_date = datetime.datetime.strptime(row["timestamp"], "%Y %m %d %H %M %S")
      date_hour_string = transaction_date.strftime("%Y %m %d %H")
      if date_hour_string in hourly_sales:
         hourly_sales[date_hour_string] = hourly_sales[date_hour_string] + row["total"]
      else:
         hourly_sales[date_hour_string] = row["total"]
   hourly_sales_list = []
   for date_hour, sales in hourly_sales.iteritems():
      hourly_sales_list.append((date_hour, sales))
   hourly_sales_list.sort()
   return hourly_sales_list
   
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

