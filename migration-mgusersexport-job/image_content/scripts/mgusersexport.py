###Below code connect to MongoDB and export the users in to configmap
from kubernetes import client, config
from pymongo import MongoClient
import os,logging
import sys

config.load_incluster_config()
v1 = client.CoreV1Api()

logging.basicConfig(level=logging.INFO)

PASSWORD = os.environ.get('ESM_MGADMIN_PASSWORD')
NAMESPACE = os.environ.get('NAMESPACE')


try:
  secret = v1.read_namespaced_secret("eric-cnom-document-database-mg",NAMESPACE)
  logging.info("Read the secret Successfully")
except Exception as error:
  if error.status == 404:
    logging.info("document-database-mg secret not found, so mgusersexport Job exit here ")
    logging.info("MongoDB components not found in deployment hence considering MongoDB to Postgres migration Completed")
    sys.exit()

try:
  clientdb = MongoClient(["eric-cnom-document-database-mg-0", "eric-cnom-document-database-mg-1", "eric-cnom-document-database-mg-2"], 27017, username='root', password=PASSWORD, authSource='admin', authMechanism='SCRAM-SHA-1', serverSelectionTimeoutMS=1000*5)
  clientdb.server_info()
  logging.info(f"{clientdb.HOST} connected Successfully")
except Exception as error:
  logging.error("{}".format(error))
  logging.info(f"eric-cnom-document-database-mg not connected and exit from the job")
  sys.exit()

db = clientdb['test_nodedata']
collection = db['users']
cursor = collection.find({} , {"_id":0, "tokens":0, "__v":0})
userdata = list(cursor)
configmaptemplate = {"kind": "ConfigMap", "apiVersion": "v1", "metadata": {"name": "mgusersdata", "namespace": str(NAMESPACE)}, "data": {"user_details" : str(userdata)}}
try:
  try:
    userdataConfigMap = v1.read_namespaced_config_map("mgusersdata",NAMESPACE)
    logging.info("Read the mgusersdata configmap Successfully")
    deleteConfigMap = v1.delete_namespaced_config_map("mgusersdata",NAMESPACE)
    logging.info("Deleting the mgusersdata configmap with same name if exists")
    if deleteConfigMap.status == "Success":
      userdata = v1.create_namespaced_config_map(NAMESPACE,configmaptemplate)
      logging.info("ConfigMap with MongoDB users data created Successfully")
  except Exception as error:
    if hasattr(error,"reason") and error.reason == "Not Found":
      userdata = v1.create_namespaced_config_map(NAMESPACE,configmaptemplate)
      logging.info("ConfigMap with MongoDB users data created Successfully")
    else:
      logging.error("{}".format(error))
except Exception as error:
  logging.info("Failed to create ConfigMap")
  logging.error("{}".format(error))
