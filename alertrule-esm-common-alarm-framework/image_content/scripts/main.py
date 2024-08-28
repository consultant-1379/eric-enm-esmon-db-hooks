##ESM Alarm-framework code for update alert rules based on deployment-type
import logging
import os
import json
import copy
import yaml
import sys
from kubernetes import client, config

config.load_incluster_config()
v1 = client.CoreV1Api()
NAMESPACE = os.environ.get('NAMESPACE')
DEPLOYMENT_TYPE = os.environ.get('DEPLOYMENT_TYPE')
THRESHOLD_JSON_PATH = os.environ.get('THRESHOLD_JSON_PATH')

logging.basicConfig(level=logging.INFO)

def read_file(file_path):
    """read the json file and return the data as list data type
    Parameters
    ----------
    file_path : str
        json file path
    Returns
    -------
    list
        a list of dict contains the metric name and deployment based thresholds
    """
    if( os.path.isfile(file_path) and file_path.endswith(".json")):
        with open(file_path, 'r') as file:
            file_data = json.loads(file.read())
            parent_key = "".join([ f"_{letter.lower()}" if letter.isupper() else letter for letter in os.path.basename(file_path).replace(".json", "")])
            file_data = file_data[parent_key]
        return file_data
    else:
        logging.error(f"{os.path.basename(file_path)} file not found !!! ")
        return []

def get_PMAR_list(labels):
    """fetch all predefined meta alert rule list
    Paramenters
    -----------
    labels: dict
        Labels used to filter the predefined meta alert rules among the configMaps
    Returns
    -------
    list
        a list of tuple contains alert name and respective configMap name
    """
    selector_string = ','.join([f"{key}={value}" for key, value in labels.items()])
    response = v1.list_namespaced_config_map(NAMESPACE, label_selector=selector_string)
    config_map_list = []
    for item in response.items:
        alert_name = ''
        config_map_name = ''
        alert_data = list(item.data.values())
        if alert_data and len(alert_data)==1:
            alert_data = yaml.safe_load(alert_data[0])
            if "alert" in alert_data:
                alert_name = alert_data["alert"]
        config_map_name = item.metadata.name
        config_map_list.append((alert_name, config_map_name))
    return config_map_list

def read_and_update_config_map(config_map_name, alert_name, data_to_update={}):
    """Read the specific configMap and update
    Paramenters
    -----------
    config_map_name: str
        The name of configMap needs to be updated
    alert_name: str
        name of alert rule used to read and update the alert rule data
    data_to_update: dict
        contains key value pair to update in alert rule
    """
    cm = v1.read_namespaced_config_map(namespace=NAMESPACE, name=config_map_name)
    cm_data = yaml.safe_load(cm.data[f"{alert_name}.yaml"])
    modified_cm_data = copy.deepcopy(cm_data)
    for key in data_to_update:
        if key in modified_cm_data:
                modified_cm_data[key] = data_to_update[key]
    if str(cm_data) != str(modified_cm_data):
        cm_data_to_update = {"data" : {f"{alert_name}.yaml" : yaml.dump(modified_cm_data, indent=4)}}
        response = v1.patch_namespaced_config_map(namespace=NAMESPACE, name=config_map_name, body=cm_data_to_update)
        if response.metadata.resource_version:
            logging.info(f"configMap {config_map_name} updated successfully")
        else:
            logging.error(f"Update for configMap {config_map_name} failed")
    else:
        logging.info(f"ConfigMap {config_map_name} already up to date")


if __name__ == "__main__":
    try:
        # TBMV -> Type based metric values
        TBMV_dir_path = THRESHOLD_JSON_PATH
        label_for_PMAR = {"author": "Ericsson", "contenttype": "PredefinedAlertRule", "subtype" : "PredefinedMetaAlertRule"}
        TBMV_files = [os.path.join(TBMV_dir_path, file) for file in os.listdir(TBMV_dir_path) if file.endswith('.json')]
        # PMAR_list -> Predefined meta alert rule
        PMAR_list = get_PMAR_list(label_for_PMAR)
        if len(PMAR_list) == 0:
            logging.info(f"Predefined Meta Alertrule not found for Threshold Update!")
            sys.exit(0)
        for alert_name, config_map_name in PMAR_list:
            threshold = None

            for TBMV_file_path in TBMV_files:
                TBMV_data = read_file(TBMV_file_path)
                for metric_data in TBMV_data:
                    if "name" in metric_data and alert_name == metric_data["name"]:
                        for deployment in metric_data["deployment"]:
                            if "enm_deployment_type" in deployment and DEPLOYMENT_TYPE == deployment["enm_deployment_type"]:
                                if "capacity" in deployment:
                                    threshold = int(deployment["capacity"])
                                elif "threshold" in deployment:
                                    threshold = int(deployment["threshold"])

            if threshold:
                read_and_update_config_map(config_map_name, alert_name, {"threshold": threshold})
            else:
                logging.error(f"can't find the type based threshold for alert {alert_name}")

    except Exception as error:
        logging.error("{}".format(error))
