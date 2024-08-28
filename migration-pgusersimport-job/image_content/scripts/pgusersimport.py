#This code will import the users from MongoDB to PostgresDB
import psycopg2
import json
import datetime
import sys,os,logging
from kubernetes import client, config

logging.basicConfig(level=logging.INFO)

config.load_incluster_config()
v1 = client.CoreV1Api()

PASSWORD = os.environ.get('ESM_PGADMIN_PASSWORD')
NAMESPACE = os.environ.get('NAMESPACE')

try:
  cm = v1.read_namespaced_config_map("mgusersdata",NAMESPACE)
  logging.info("Read the ConfigMap mgusersdata Successfully and Continue further to import users")
except Exception as error:
  if error.status == 404:
    logging.info("Exiting from here, Hence the MongoDB to Postgres Migration already Completed")
    sys.exit()

userdataconfigmap = v1.read_namespaced_config_map("mgusersdata",NAMESPACE)
user_data_str = userdataconfigmap.data["user_details"]
user_data_str = user_data_str.replace("None", "null")


fields = ['role', 'username', 'name', 'surname', 'email', 'lastLogin', 'salt', 'password']
user_data_str = user_data_str.replace("\'", "\"")
user_data_str = user_data_str.replace("datetime.datetime(", "[")
user_data_str = user_data_str.replace(")", "]")

user_data = json.loads(user_data_str)

conn = None
try:
  conn = psycopg2.connect(
    host="postgres",
    database="eric-esm-server",
    user="postgres",
    password=PASSWORD)
  cur = conn.cursor()
  cur.execute("DELETE FROM users;")
  conn.commit()
  cur.close()
  logging.info("Delete the Users Successfully")
except (Exception, psycopg2.DatabaseError) as error:
  logging.info("Failed to Connect PostgresDB")
  logging.error("{}".format(error))
finally:
  if conn is not None:
    conn.close()

totaluserdatavalues = []

time_stamp_key = ["lastLogin"]

for user in user_data:
    values = []
    if "username" in user:
        for field_name in fields:
            if field_name in user:
                if field_name in time_stamp_key and user[field_name]:
                        year, month, date, hr, min, sec, micro_sec = user[field_name]
                        values.append(datetime.datetime(year, month, date, hr, min, sec, micro_sec).strftime('%Y-%m-%d %H:%M:%S'))
                else:
                    values.append(user[field_name])
            else:
                print(f'{field_name} not present in user data {user}')
    else:
        logging.info("Mandatory field username not found")

    totaluserdatavalues.append(tuple(values))

sql = """INSERT INTO users("role", "username", "name", "surname", "email", "lastLogin", "salt", "password") VALUES {values};"""
sql = sql.format(values = ','.join(map(str, totaluserdatavalues)))
sql = sql.replace("None", "null")


conn = None
try:
  conn = psycopg2.connect(
    host="postgres",
    database="eric-esm-server",
    user="postgres",
    password=PASSWORD)
  cur = conn.cursor()
  cur.execute(sql)
  cur.execute("SELECT username FROM users;")
  insertedrows = cur.fetchall()
  for row in insertedrows:
    print(row)
  conn.commit()
  cur.close()
except (Exception, psycopg2.DatabaseError) as error:
  logging.info("Failed to connect PostgresDB")
  logging.error("{}".format(error))
finally:
  if conn is not None:
    conn.close()
try:
  if len(insertedrows) == len(user_data) :
    deleteuserdatacm = v1.delete_namespaced_config_map("mgusersdata",NAMESPACE)
    logging.info("Deleted the ConfigMap Successfully")
except Exception as error:
  logging.info("Failed to delete the ConfigMap created as part of Post-Upgrade Job")
  logging.error("{}".format(error))
