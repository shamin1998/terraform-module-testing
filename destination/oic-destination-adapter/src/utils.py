import os
from oic_api_client import OICAPIClient, OICUploadClient

def get_oic_secret_keys(secret):

    params = {}

    params["CEC_USERNAME_SECRET_KEY"] = os.environ.get("CEC_USERNAME_SECRET_KEY")
    params["CEC_PASSWORD_SECRET_KEY"] = os.environ.get("CEC_PASSWORD_SECRET_KEY")
    params["CLIENT_ID_SECRET_KEY"] = os.environ.get("CLIENT_ID_SECRET_KEY")
    params["CLIENT_SECRET_SECRET_KEY"] = os.environ.get("CLIENT_SECRET_SECRET_KEY")
    params["COLLECTOR_ID_SECRET_KEY"] = os.environ.get("COLLECTOR_ID_SECRET_KEY")

    return params

def get_state_table_keys(params, table_resource):
    primary_key = table_resource.key_schema
    for attr in primary_key:
        if attr["KeyType"] == "HASH":
            # print("DynamoDB State Table primary hash key =", attr["AttributeName"])
            params["DYNAMODB_TABLE_HASH_KEY"] = attr["AttributeName"]
        elif attr["KeyType"] == "RANGE":
            # print("DynamoDB State Table primary range key =", attr["AttributeName"])
            params["DYNAMODB_TABLE_RANGE_KEY"] = attr["AttributeName"]

    global_secondary_key = table_resource.global_secondary_indexes[0]["KeySchema"]
    for attr in global_secondary_key:
        if attr["KeyType"] == "HASH":
            # print("DynamoDB State Table global secondary hash key =", attr["AttributeName"])
            params["DYNAMODB_TABLE_PIPELINE_KEY"] = attr["AttributeName"]
        # elif attr["KeyType"] == "RANGE":
        #     params["DYNAMODB_TABLE_RANGE_KEY"] = attr["AttributeName"]

    local_secondary_key = table_resource.local_secondary_indexes[0]["KeySchema"]
    for attr in local_secondary_key:
        if attr["KeyType"] == "RANGE":
            # print("DynamoDB State Table local secondary range key =", attr["AttributeName"])
            params["DYNAMODB_TABLE_INPUT_KEY"] = attr["AttributeName"]

    return params


def transfer_s3_to_oic_api(secret, bucket_resource, key, ddb_logger, run_id):

    
    download_path = '/tmp/' + os.path.basename(key)
    print("Downloading file to :", download_path)
    bucket_resource.download_file(key,download_path)

    file_size = os.path.getsize(download_path)
    print("Downloaded file size is :", file_size)

    if ddb_logger:
        
        response = ddb_logger.init_log(run_id,download_path,file_size)

    print("Uploading to OIC...")
    status_code, upload_url = pass_to_oic_api(secret, download_path)

    if ddb_logger:
        response = ddb_logger.log_upload(run_id,download_path,file_size)

    return status_code, upload_url

def pass_to_oic_api(secret, file_path):

    params = get_oic_secret_keys(secret)
    
    oic_client = OICUploadClient()
    
    status_code, upload_url = oic_client.task(secret[params["CEC_USERNAME_SECRET_KEY"]], secret[params["CLIENT_ID_SECRET_KEY"]],secret[params["CLIENT_SECRET_SECRET_KEY"]],file_path,secret[params["COLLECTOR_ID_SECRET_KEY"]])

    return status_code, upload_url
