#New user creation to authorize/authenticate ESM from CENM
import psycopg2
import json
import hmac
import hashlib
import datetime
import sys,os,logging
from kubernetes import client, config
from datetime import datetime, timezone

config.load_incluster_config()
v1 = client.CoreV1Api()

PASSWORD = os.environ.get('ESM_PGADMIN_PASSWORD')
NAMESPACE = os.environ.get('NAMESPACE')

secret = v1.read_namespaced_secret("esmui-secret",NAMESPACE)

salt = os.urandom(16).hex().encode('utf-8')
username = os.popen(f'echo {secret.data["esm-user"]}|base64 --decode').read()
password = os.popen(f'echo {secret.data["esm-pwd"]}|base64 --decode').read()

password = password.encode('utf-8')
hashedpassword = hmac.new(salt, password, hashlib.sha384).hexdigest()
salt = salt.decode('ascii')

dt= datetime.now(timezone.utc)
values = ['ALERT_RULES_CONFIG', username, 'ESMAlertRuleUser', 'local', salt, hashedpassword, dt]

sql = """INSERT INTO users("role", "username", "name", "authenticationProvider", "salt", "password", "lastLogin") VALUES (%s,%s,%s,%s,%s,%s,%s);"""

conn = None
try:
  conn = psycopg2.connect(
    host="postgres",
    database="eric-esm-server",
    user="postgres",
    password=PASSWORD)
  cur = conn.cursor()
  cur.execute(sql, tuple(values))
  conn.commit()
  cur.close()
except (Exception, psycopg2.DatabaseError) as error:
  logging.info("Failed to connect PostgresDB")
  logging.error("{}".format(error))
finally:
  if conn is not None:
    conn.close()
