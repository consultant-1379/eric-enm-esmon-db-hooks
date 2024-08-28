#Synchronization code for configmap and ESM DB During Initial Install
#!/usr/bin/python3
from http import cookies
import requests
import logging
import psycopg2
import os
import time
from requests.exceptions import ConnectionError
from kubernetes import client, config

config.load_incluster_config()
v1 = client.CoreV1Api()
ESM_SYNC_HOST = "eric-esm-server"
ESM_SYNC_PORT = "8585"
PASSWORD = os.environ.get('ESM_PGADMIN_PASSWORD')
NAMESPACE = os.environ.get('NAMESPACE')
RESTOREJOBLABEL = os.environ.get('LABEL')
URL_COMPONENTS = f'http://{ESM_SYNC_HOST}:{ESM_SYNC_PORT}/esm-server'
MAX_RETRY_COUNT = 3
DELAY = 10
session = requests.Session()
headers = {
    'Content-Type': 'application/json',
}
json_data = {
    'username': os.environ.get('ESM_ADMIN_USERNAME'),
    'password': os.environ.get('ESM_ADMIN_PASSWORD')
}
logging.basicConfig(level=logging.INFO)


def delete_esmAlertRule_user():
  conn = None
  try:
    conn = psycopg2.connect(
        host="postgres",
        database="eric-esm-server",
        user="postgres",
        password=PASSWORD)
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE username='esmAlertRuleuser';")
    print("Deleted user count", cur.rowcount)
    if cur.rowcount == 1:
      logging.info("Deleted the user Successfully")
    else:
      logging.info("User deletion failed")
    conn.commit()
    cur.close()
  except (Exception, psycopg2.DatabaseError) as error:
    logging.info("Failed to connect PostgresDB")
    logging.error("{}".format(error))
  finally:
    if conn is not None:
      conn.close()


def check_restore_pod_existence():
 try:
  pods = v1.list_namespaced_pod(NAMESPACE, label_selector=f"job-name={RESTOREJOBLABEL}")
  if len(pods.items):
   return True
  return False

 except Exception as error:
   logging.error("Failed to get restore pod", error)
   return False

try:
    cookies = {}
    login = {"successful": False, "retry_count": 0}
    sync_request = {"successful": False, "retry_count": 0}
    for count in range(1, MAX_RETRY_COUNT + 1):
        try:
            login_response = session.post(
                url=f'{URL_COMPONENTS}/login', headers=headers, json=json_data, verify=False)
            if login_response.status_code == 200:
                logging.info(
                    "Request to login endpoint has been successful")
                logging.info("logged in successfully")
                login["successful"] = True
                cookies = session.cookies.get_dict()
                break
            else:
                logging.info("Retrying request to login endpoint")
                print(login_response)
        except ConnectionError as err:
            logging.error(" Failed to trigger the ESM login")
            logging.error("{}".format(err))
        time.sleep(DELAY)
        login["retry_count"] = count
        logging.info(
            "Retrying to connect with ESM login service, retry_count = {}".format(count))
    if login["successful"]:
        URL = ''
        success_message = ''
        if not check_restore_pod_existence():
            URL = f'{URL_COMPONENTS}/api/alert-management/reconcileAlertRule/initialAlertRules'
            success_message = "synchronization from deployment to ESM DB is completed"
        else:
            URL = f'{URL_COMPONENTS}/api/alert-management/reconcileAlertRule/reloadAlertRules'
            success_message = "synchronization from ESM DB to Prometheus is completed"

        for count in range(1, MAX_RETRY_COUNT + 1):
            try:
                response = session.put(url=URL,
                                        cookies=cookies, headers=headers, verify=False)
                print(response.content)
                if response.status_code == 200:
                    logging.info(
                        "Request to sync endpoint has been successful")
                    logging.info(success_message)
                    sync_request["successful"] = True
                    break
                else:
                    logging.info("Retrying request to sync endpoint")
                    print(response)
            except ConnectionError as err:
                logging.error(
                    " Failed to trigger the configmap sync function")
                logging.error("{}".format(err))
            time.sleep(DELAY)
            sync_request["retry_count"] = count
            logging.info(
                "Retrying to connect with ESM reconciliation service, retry_count = {}".format(count))
        if sync_request["retry_count"] == MAX_RETRY_COUNT and not (sync_request["successful"]):
            logging.info(
                "Max retries exceeded, synchronization failed")
    else:
        logging.info("Max retries exceeded, login failed")

    delete_esmAlertRule_user()

except Exception as err:
    logging.error(
        "Error occurred while attempting to trigger the synchronization")
    logging.error("{}".format(err))
