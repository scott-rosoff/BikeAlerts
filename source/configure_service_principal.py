import json
import os

def configure_service_principal(file_path):
    if file_path == "" or file_path is None:
        print("Empty or Null path for Service Principal Keys provided")

    f = open(file_path)
    data = json.load(f)
    os.environ['AZURE_CLIENT_ID'] = data['AZURE_CLIENT_ID']
    os.environ['AZURE_TENANT_ID'] = data['AZURE_TENANT_ID']
    os.environ['AZURE_CLIENT_SECRET'] = data['AZURE_CLIENT_SECRET']
    return
