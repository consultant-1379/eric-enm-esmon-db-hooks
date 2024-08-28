#Synchronization code for relod configmap with alert-rules in ESM DB
import psycopg2
import os
import logging
import sys
import requests
import time
import hashlib
import hmac
from psycopg2.extras import RealDictCursor
from http import cookies
from requests.exceptions import ConnectionError
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)

esm_user_name =  os.environ.get('ESM_ADMIN_USERNAME')
esm_user_password =  os.environ.get('ESM_ADMIN_PASSWORD')
NAMESPACE = os.environ.get('NAMESPACE')

def reload_alert_rules():
    global esm_user_password
    global esm_user_name
    ESM_SYNC_HOST = "eric-esm-server"
    ESM_SYNC_PORT = "8585"
    URL = f'http://{ESM_SYNC_HOST}:{ESM_SYNC_PORT}/esm-server'
    MAX_RETRY_COUNT = 3
    DELAY = 10
    session = requests.Session()
    headers = {
        'Content-Type': 'application/json',
    }
    json_data = {
        'username': esm_user_name,
        'password': esm_user_password
    }
    try:
        cookies = {}
        login = {"successful": False, "retry_count": 0}
        sync_request = {"successful": False, "retry_count": 0}
        for count in range(1, MAX_RETRY_COUNT + 1):
            try:
                login_response = session.post(
                    url=f'{URL}/login', headers=headers, json=json_data, verify=False)
                if login_response.status_code == 200:
                    logging.info(
                        "Request to login endpoint has been successful")
                    login["successful"] = True
                    cookies = session.cookies.get_dict()
                    break
                else:
                    logging.info("Retrying request to login endpoint")
                    print(login_response)
            except ConnectionError as err:
                logging.error(
                    " Failed to trigger the ESM login \n {}".format(err))
            time.sleep(DELAY)
            login["retry_count"] = count
            logging.info(
                "Retrying to connect with ESM login service, retry_count = {}".format(count))
        if login["successful"]:
            for count in range(1, MAX_RETRY_COUNT + 1):
                try:
                    response = session.put(url=f'{URL}/api/alert-management/reconcileAlertRule/reloadAlertRules',
                                           cookies=cookies, headers=headers, verify=False)
                    print(response.content)
                    if response.status_code == 200:
                        logging.info(
                            "synchronization from ESM DB to configmap is completed")
                        sync_request["successful"] = True
                        break
                    else:
                        logging.info("Retrying request to sync endpoint")
                        print(response)
                except ConnectionError as err:
                    logging.error(
                        " Failed to trigger the alertrule sync function \n {}".format(err))
                time.sleep(DELAY)
                sync_request["retry_count"] = count
                logging.info(
                    "Retrying to connect with ESM login service, retry_count = {}".format(count))
            if sync_request["retry_count"] == MAX_RETRY_COUNT and not (sync_request["successful"]):
                logging.info(
                    "Max retries exceeded, synchronization failed")
        else:
            logging.info("Max retries exceeded, login failed")
    except Exception as err:
        logging.error(
            "Error occurred while attempting to trigger the synchronization \n {}".format(err))

#To create the ESM AlertRule user to authenticate the reload API in ESM
def create_user_data():
    try:
        global esm_user_password
        global esm_user_name
        salt = os.urandom(16).hex().encode('utf-8')
        encoded_esm_user_password = esm_user_password.encode('utf-8')
        hashed_password = hmac.new(salt, encoded_esm_user_password, hashlib.sha384).hexdigest()
        salt = salt.decode('ascii')
        dt = datetime.now(timezone.utc)
        user_data = ['ALERT_RULES_CONFIG', esm_user_name,
                     'ESMAlertRuleUser', 'local', salt, hashed_password, dt]
        return user_data
    except Exception as err:
        print("Exception occurred in create user data ", err)
class PostgresDB():
    def __init__(self, host, database, user, password):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.conn = None
        self.conn = psycopg2.connect(
          host=self.host,
          database=self.database,
          user=self.user,
          password=self.password, cursor_factory=RealDictCursor)
        self.cur = self.conn.cursor()
       
    def check_user(self, user_name):
            self.cur.execute(
                f"SELECT * FROM users WHERE username='{user_name}';")
            db_response = self.cur.fetchone()
            if not db_response:
              return False
            db_response = dict(db_response)
            if "username" in db_response and db_response["username"] == user_name:
                return True
            else:
                return False
              
    def insert_user(self, user_data):
            sql = """INSERT INTO users("role", "username", "name", "authenticationProvider", "salt", "password", "lastLogin") VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING username;"""
            self.cur.execute(sql, tuple(user_data))
            inserted_user_data = self.cur.fetchone()
            inserted_user_data = dict(inserted_user_data)
            inserted_user_name = inserted_user_data["username"]
            self.conn.commit()
            if inserted_user_name == user_data[1]:
                return True
            else:
                return False
              
    def clean(self):
            if self.cur is not None:
                self.cur.close()
            if self.conn is not None:
                self.conn.close()
            
if __name__ == "__main__":
  try:
    pg_password = os.environ.get('ESM_PGADMIN_PASSWORD')
    retry_count = 0
    pg = None
    DELAY = 10
    for retry_count in range(1,4):
      try:
        pg = PostgresDB("postgres", "eric-esm-server", "postgres",  pg_password)
        if pg.conn.status == 1:
          break
      except (Exception, psycopg2.DatabaseError) as error:
        logging.error("Exception occurred in postgres db connection".format(error))
        logging.info("Retrying to connect with DB, count {}".format(retry_count))
      time.sleep(DELAY)
    if retry_count == 3 and pg == None:
      logging.info("Max Retries exceeded to connect with DB and Job exit here")
      sys.exit()
    logging.info("We are connected to postgresDB")
    user_status = pg.check_user(esm_user_name)
    if user_status:
      reload_alert_rules()
    else:
      user_data = create_user_data()
      insert_status = pg.insert_user(user_data)
      if insert_status:
        reload_alert_rules()
    pg.clean()
  except Exception as error:
    logging.error("{}".format(error))
  
