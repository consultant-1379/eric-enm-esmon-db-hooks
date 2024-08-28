##Adding new column in postgres table to update Enable/Disable status for alertrules
#!/usr/bin/python3
import psycopg2
import time,os,logging
logging.basicConfig(level=logging.INFO)

PASSWORD = os.environ.get('ESM_PGADMIN_PASSWORD')
MAX_RETRY_COUNT = 3
DELAY = 10
conn = None
try:
    for retry_count in range(0,MAX_RETRY_COUNT+1):
        alteration_successful = False
        count = retry_count
        if retry_count > 0:
            time.sleep(DELAY)
            logging.info("Retrying to connect postgres database,retry_count = {}".format(retry_count))
        try:
          conn = psycopg2.connect(
            host="postgres",
            database="eric-esm-server",
            user="postgres",
            password=PASSWORD)
          cur = conn.cursor()
          table_name = "alertrules"
          column_name = "alertRuleStatus"
          cur.execute(f"ALTER TABLE IF EXISTS {table_name} ADD COLUMN IF NOT EXISTS \"{column_name}\" TEXT DEFAULT 'Enabled' NOT NULL;")
          cur.execute(f"SELECT column_name, column_default, is_nullable, data_type  FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}' and column_name='{column_name}';")
          response = cur.fetchall()
          conn.commit()
          print(response)
          if column_name in response[0]:
            alteration_successful = True
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
          logging.info("Failed to connect PostgresDB")
          logging.error("{}".format(error))
        finally:
          if conn is not None:
            conn.close()
        if alteration_successful:
          logging.info("Alteration of table Succeeded")
          break
    if retry_count == MAX_RETRY_COUNT and not(alteration_successful):
      logging.info("Max retries exceeded and alteration of table Failed")
except Exception as e:
    logging.error("Error occurred while altering the alertrule table")
    logging.error("{}".format(e))
