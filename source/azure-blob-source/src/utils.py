from azure.storage.blob import ContainerClient
from blob_transfer_client import TransferAzureBlobToS3
from dynamodb_client import TelemetryDataTransferLogger
import os
import json
import boto3
from botocore.exceptions import ClientError
import re

def get_secret(secret_name,region_name):

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response['SecretString']
    print("Secret retrieved")

    return json.loads(secret)


def read_env_variables():
    params = {}

    params["PIPELINE_UUID"] = os.environ.get('PIPELINE_UUID')
    params["AWS_REGION_NAME"] = os.environ.get('AWS_REGION_NAME')
    params["SEARCH_OPTIMIZATION"] = os.environ.get("SEARCH_OPTIMIZATION")

    params["ASM_SECRET_NAME"] = os.environ.get('ASM_SECRET_GROUP_NAME')
    print("ASM_SECRET_NAME =",params["ASM_SECRET_NAME"])
    params["DYNAMODB_TABLE_NAME"] = os.environ.get('DYNAMODB_TABLE_NAME')
    
    print('State DynamoDB Table name = ' + params["DYNAMODB_TABLE_NAME"])

    params["AZURE_CONTAINER_URL_SECRET_KEY"] = os.environ.get('AZURE_CONTAINER_URL_SECRET_KEY')
    params["AZURE_ACCOUNT_SECRET_KEY"] = os.environ.get('AZURE_ACCOUNT_SECRET_KEY')   # Name of Azure storage account which owns the blobs to be transferred
    params["AZURE_CONTAINER_SECRET_KEY"] = os.environ.get('AZURE_CONTAINER_SECRET_KEY')   # Name of Azure container where the blobs to be transferred are present
    params["AZURE_SAS_TOKEN_SECRET_KEY"] = os.environ.get('AZURE_SAS_TOKEN_SECRET_KEY')
    params["BLOB_SET_FORMAT"] = os.environ.get("BLOB_SET_FORMAT")
    params["AZURE_PARENT_FOLDER"] = os.environ.get('AZURE_PARENT_FOLDER')     # Name of parent folder (assuming telemetry data structure, i.e. all blobs to be transferred should be present in this parent folder)
    if os.path.normpath(params["AZURE_PARENT_FOLDER"]) in [".", "/"]:
        params["AZURE_PARENT_FOLDER"] = ""

    azure_creds = []
    for key in params.keys():
        if key.startswith("AZURE"):
            azure_creds.append({key : params[key]})

    print("Azure storage parameters :",azure_creds)

    params["S3_BUCKET_NAME"] = os.environ.get('S3_SOURCE_TO_TRANSFORMER_BUCKET')   # Name of AWS S3 bucket where the file/directory is to be uploaded
    params["S3_DEST_FOLDER"] = os.environ.get('S3_SOURCE_BUCKET_DEST_FOLDER') if os.environ.get('S3_SOURCE_BUCKET_DEST_FOLDER') else ""  # Path to directory in S3 bucket where file(s) will be uploaded
    if os.path.normpath(params["S3_DEST_FOLDER"]) in [".", "/"]:
        params["S3_DEST_FOLDER"] = ""

    print("Destination S3 Bucket parameters : " + "{ S3_BUCKET_NAME = " + params["S3_BUCKET_NAME"] + ", S3_DEST_FOLDER = " + params["S3_DEST_FOLDER"] + " }")

    params["SQS_QUEUE_URL"] = os.environ.get('SQS_QUEUE_URL')   # Path to directory in S3 bucket where file(s) will be uploaded
    print("SQS Queue URL : " + params["SQS_QUEUE_URL"])

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

def create_azure_container_client(secret, params):

    container_client = None

    if "AZURE_CONTAINER_URL_SECRET_KEY" in params.keys():
        
        container_client = ContainerClient.from_container_url(secret[params["AZURE_CONTAINER_URL_SECRET_KEY"]])
        print("Connected to Azure container using container URL")
        # params["AZURE_CONTAINER_NAME"] = secret["azure_container_url"][secret["azure_container_url"].index(".net/") + len(".net/") : secret["azure_container_url"].index("?")] 

    elif all(params[p] for p in ["AZURE_ACCOUNT_SECRET_KEY", "AZURE_CONTAINER_SECRET_KEY", "AZURE_SAS_TOKEN_SECRET_KEY"]):
        
        container_url = "https://" + secret[params["AZURE_ACCOUNT_SECRET_KEY"]] + ".blob.core.windows.net/" + secret[params["AZURE_CONTAINER_SECRET_KEY"]] + '?' + secret[params["AZURE_SAS_TOKEN_SECRET_KEY"]]
        container_client = ContainerClient.from_container_url(container_url)
        print("Connected to Azure container using SAS token")
    
    else:
        print("ERROR: Azure container keys not found in environment variables")
    # elif 'azure_connection_string' in secret.keys() and params["AZURE_CONTAINER_NAME"]:
       
    #     from azure.storage.blob import BlobServiceClient
    #     blob_service_client = BlobServiceClient.from_connection_string(secret['azure_connection_string'])
    #     container_client = blob_service_client.get_container_client(params["AZURE_CONTAINER_NAME"])

    return container_client

def get_blobs_to_transfer(ddb_logger, blobs, input_file_key, consecutive=True):
    '''
    Check the latest blob which was logged as transferred successfully, and return list of all blobs created after it

    Parameters :
        - ddb_logger : Custom class object for to easily query the DynamoDB log table
        # - input_key : Attribute in log table storing the blob name
        - blobs : List of all lobs in Azure container, sorted by their time of creation

    Returns : 
     - blobs_to_transfer : List of blobs to be transferred this time
    '''

    if not consecutive:
        return get_all_blobs_not_transferred(ddb_logger, blobs)

    blobs_to_transfer = []

    last_state_record = ddb_logger.latest_source_transferred()
    if not last_state_record:
        return None

    last_record = last_state_record[input_file_key].split(',')
    last_blob_transferred = last_record[0]
    print("Last blob logged as successully transferred:", last_blob_transferred)

    index = len(blobs) - 1
    while index >= 0:
        if blobs[index]["name"] == last_blob_transferred:
            break
        else:
            index -= 1
    
    if index == len(blobs) - 1:
        # print("All blobs already transferred. Exiting.")
        return []
    
    elif index >= 0:
        if last_state_record['adapter_state'] == "COMPLETED":
            blobs_to_transfer = blobs[index+1:]
        elif last_state_record['adapter_state'] == "PENDING":
            print("Last blob not logged as successfully transferred. Adding it to list of blobs to be transferred this time to retry. Latest log :", last_state_record)
            if index == 0:
                blobs_to_transfer = blobs[index:]
            else:
                blobs_to_transfer = blobs[index-1:]

    else:
        print("ERROR: Last blob logged as transferred not found in Azure Container")
        return None
    
    return blobs_to_transfer

def group_inventory_config_blobs(blobs_to_transfer,consecutive=True):

    print("Grouping inventory+config files...")
    blob_run_sets = []

    for i, blob in enumerate(blobs_to_transfer):
        # print("Checking",blob["name"])
        if blob["name"].find('inventory') != -1:
            # print("Detected inventory")
            config_flag = False
            if i == 0 or not consecutive:
                config_blob_list = blobs_to_transfer
            
            else:
                config_blob_list = blobs_to_transfer[i-1:]
                
            for config_blob in config_blob_list:
                
                if config_flag:
                    break
                # print("Checking for config",config_blob["name"])
                if config_blob["name"].find('config') != -1:
                    # print("Detected config")
                    if blob["name"][:blob["name"].find('inventory')] == config_blob["name"][:config_blob["name"].find('config')]:
                        # print("Detected set")
                        blob_run_sets.append([blob, config_blob])
                        config_flag = True
    
    print("Detected inventory+config sets:", blob_run_sets)
    return blob_run_sets

def find_blob_set_match(ref, blob_format, blobs):
    print("Detecting matching blob format:", blob_format, ", ref =", ref)
    for blob in blobs:
        blob_ref = blob["name"][:blob["name"].find('_')]
        print("Checking blob:", blob, ", blob_ref =", blob_ref)
        if re.search(blob_format,blob["name"]):
            print("regex match!")
            if ref == blob_ref:
                print("Detected match!")
                return blob
    
    return None

def get_latest_blob_set(blobs, blob_set_format):

    print("Detecting blob set format:", blob_set_format)
    blob0_format = blob_set_format[0]
    blob_set = []

    for i, blob in enumerate(blobs):
        print("Checking blob0:", blob)
        if re.search(blob0_format,blob["name"]):
            print("Detected blob0")
            blob_set.append(blob)
            ref = blob["name"][:blob["name"].find('_')]

            if i == 0:
                match_blobs = blobs[1:]
            else:
                match_blobs = blobs[i-1:]

            for blob_format in blob_set_format[1:]:
                blob_set.append(find_blob_set_match(ref, blob_format, match_blobs))
            
            break
    
    return blob_set


def get_all_blobs_not_transferred(ddb_logger, input_key, blobs):

    blobs_to_transfer = []

    for blob in blobs:
        if ddb_logger.check_not_transferred(blob["name"]):
            blobs_to_transfer.append(blob)

    return blobs_to_transfer

def trigger_transformation_adapter(queue_resource, details):

    '''
    Publish a message to SNS Topic with details of transferred data in a S3 Bucket

    Parameters :
        - topic_resource : Boto3 SNS Topic Resource to publish events for triggering the tranformation adapter

    Returns : Boto3 SNS Topic publish method response
    '''    

    message = json.dumps(details)

    sqs_response = queue_resource.send_message(MessageBody = message)

    return sqs_response

if __name__ == "__main__":

    blobs = [
        {
            "name" : "2023-10-18_inventory.csv"
        },
        {
            "name" : "2023-10-18_config.csv"
        }
    ]

    blob_set_format = [".*_inventory.csv", ".*_config.csv"]

    print(get_latest_blob_set(blobs,blob_set_format))

################################################################################
# Extra functions (currently unused)
################################################################################

def transfer_single_source(params,table_resource,container_client,bucket_resource):
    '''
    Transfer blobs in a specified Azure container directory; calculate which file or directory to transfer this time from Azure Storage to given S3 bucket, and execute transfer

    Parameters :
        - params : Dict of required Azure and AWS parameters
        - table_resource : Boto3 DynamoDB Table Resource of log table
        - container_client : Azure SDK ContainerClient for authenticated access to blobs in Azure Storage
        - bucket_resource : Boto3 S3 Bucket Resource where blobs are to be uploaded

    Returns : 
     - if successful : Path to transferred blob/folder in S3 bucket
     - if unsuccessful : None
     - if all blobs already transferred : "#DONE#"
    '''
    log_hash_key = params["PIPELINE_UUID"]
    azure_source_name = get_source_to_transfer(table_resource,container_client, params["DYNAMODB_TABLE_NAME"], params["DYNAMODB_TABLE_SORT_INDEX"],params["DYNAMODB_TABLE_HASH_KEY"],log_hash_key,params["DYNAMODB_TABLE_RANGE_KEY"])
    if not azure_source_name:
        logger.info('All folders in Azure Storage parent folder "'+ params["AZURE_PARENT_FOLDER"] +'" already transferred. Exiting!')

        return "#DONE#"
        
    logger.info('Azure source file/folder to be transferred = ' + azure_source_name)

    s3_bucket_dest_folder_path = params["S3_DEST_FOLDER"] if params["S3_DEST_FOLDER"].endswith('/') else params["S3_DEST_FOLDER"] + '/'
    initialize_log(table_resource, params["DYNAMODB_TABLE_TIMESTAMP_KEY"], params["DYNAMODB_TABLE_HASH_KEY"], params["AZURE_PARENT_FOLDER"],params["DYNAMODB_TABLE_RANGE_KEY"],azure_source_name,params["S3_BUCKET_NAME"],s3_bucket_dest_folder_path+os.path.basename(os.path.normpath(azure_source_name)))

    s3_dest_path = transfer_blobs(container_client, bucket_resource, azure_source_name, params["S3_DEST_FOLDER"])

    if s3_dest_path:
        log_successful_transfer(table_resource, params["DYNAMODB_TABLE_TIMESTAMP_KEY"], params["DYNAMODB_TABLE_HASH_KEY"], params["AZURE_PARENT_FOLDER"],params["DYNAMODB_TABLE_RANGE_KEY"], azure_source_name)

    return s3_dest_path

def initialize_log(table_resource,DYNAMODB_TABLE_TIMESTAMP_KEY,DYNAMODB_TABLE_HASH_KEY,AZURE_PARENT_FOLDER,DYNAMODB_TABLE_RANGE_KEY,azure_source_name,S3_BUCKET_NAME,S3_DEST_PATH):
    
    tdt_logger = TelemetryDataTransferLogger(table_resource)

    ddb_response = tdt_logger.init_log(DYNAMODB_TABLE_TIMESTAMP_KEY,DYNAMODB_TABLE_HASH_KEY,AZURE_PARENT_FOLDER,DYNAMODB_TABLE_RANGE_KEY,azure_source_name,S3_BUCKET_NAME,S3_DEST_PATH)

    return ddb_response

def check_unsuccessfull_transfer(ddb_logger,DYNAMODB_TABLE_HASH_KEY,AZURE_PARENT_FOLDER,DYNAMODB_TABLE_RANGE_KEY):
    
    unsuccessful_transfers = ddb_logger.get_pending_sources(DYNAMODB_TABLE_HASH_KEY,AZURE_PARENT_FOLDER,DYNAMODB_TABLE_RANGE_KEY)

    if unsuccessful_transfers:
        return unsuccessful_transfers[0][DYNAMODB_TABLE_RANGE_KEY]
    
    else:
        return None

def get_source_to_transfer(table_resource,container_client, DYNAMODB_TABLE_NAME, DYNAMODB_TABLE_SORT_INDEX, DYNAMODB_TABLE_HASH_KEY, AZURE_PARENT_FOLDER, DYNAMODB_TABLE_RANGE_KEY):

    ddb_logger = TelemetryDataTransferLogger(table_resource)
    parent_folder_path = AZURE_PARENT_FOLDER if AZURE_PARENT_FOLDER.endswith('/') else AZURE_PARENT_FOLDER + '/'
    if ddb_logger.is_empty():
        # print('AZURE_PARENT_FOLDER =',AZURE_PARENT_FOLDER)
        print('No rows detected in DynamoDB table ' + DYNAMODB_TABLE_NAME)
        for child_folder in container_client.walk_blobs(parent_folder_path, delimiter='/'):
            # print("Detected source for transfer : ", child_folder.name)
            azure_source_name = child_folder.name
            return azure_source_name

    pending_source = check_unsuccessfull_transfer(ddb_logger, DYNAMODB_TABLE_HASH_KEY, AZURE_PARENT_FOLDER, DYNAMODB_TABLE_RANGE_KEY)
    if pending_source:
        print("'PENDING' source found :",pending_source)
        return pending_source

    next_source_name = source_after_last_transfer(ddb_logger,container_client, DYNAMODB_TABLE_SORT_INDEX, DYNAMODB_TABLE_HASH_KEY, AZURE_PARENT_FOLDER, DYNAMODB_TABLE_RANGE_KEY)

    # If None found, check whether there's any source in the parent folder that hasn't been transferred
    if not next_source_name:
        next_source_name = get_source_not_transferred(ddb_logger,container_client, DYNAMODB_TABLE_HASH_KEY, AZURE_PARENT_FOLDER, DYNAMODB_TABLE_RANGE_KEY)
    
    return next_source_name


def source_after_last_transfer(ddb_logger,container_client, DYNAMODB_TABLE_SORT_INDEX, DYNAMODB_TABLE_HASH_KEY, AZURE_PARENT_FOLDER,DYNAMODB_TABLE_RANGE_KEY):
    
    '''
    Get the the name of the folder/file to be transferred using the last source transfer log

    Parameters :
        - ddb_logger : TelemetryDataTransferLogger instance
        - container_client : Azure SDK client to connect to Azure Storage Container
        - DYNAMODB_TABLE_NAME : Name of DynamoDB log table
        - DYNAMODB_TABLE_SORT_INDEX : Name of DynamoDB log table's global secondary index which is sorted by timestamp
        - AZURE_PARENT_FOLDER : Name of 'parent folder' in the Azure Storage Container from which all blobs are to be transferred


    Returns : (If all blobs in the 'parent folder' are already logged transferred, returns None.)
        - azure_source_name : Name of the next file/folder, after the latest one transferred. 
    '''    
    
    parent_folder_path = AZURE_PARENT_FOLDER if AZURE_PARENT_FOLDER.endswith('/') else AZURE_PARENT_FOLDER + '/'

    azure_source_name = None

    # Get name of latest source transferred
    last_source = ddb_logger.latest_source_transferred(DYNAMODB_TABLE_SORT_INDEX,DYNAMODB_TABLE_HASH_KEY,AZURE_PARENT_FOLDER)
    if not last_source:
        return None
    
    last_source_name = last_source[DYNAMODB_TABLE_RANGE_KEY]
    print("Last source transferred =",last_source_name)
    
    # Find the next file/folder in the same parent folder
    found_flag = False
    for source in container_client.walk_blobs(parent_folder_path, delimiter='/'):
        
        if found_flag:
            azure_source_name = source.name
            break
        if source.name == last_source_name:
            found_flag = True
    
    # Verify the next source hasn't been transferred yet, if it hasn't, return its name
    if azure_source_name:
        not_transferred = ddb_logger.check_not_transferred(DYNAMODB_TABLE_HASH_KEY, AZURE_PARENT_FOLDER,DYNAMODB_TABLE_RANGE_KEY,azure_source_name)
        if not_transferred:
            return azure_source_name
    
    return azure_source_name


def get_source_not_transferred(ddb_logger,container_client, DYNAMODB_TABLE_HASH_KEY, AZURE_PARENT_FOLDER, DYNAMODB_TABLE_RANGE_KEY):
    
    '''
    Get the the name of the folder/file to be transferred by iterating and returning the first source which hasn't been logged transferred

    Parameters :
        - ddb_logger : TelemetryDataTransferLogger instance
        - container_client : Azure SDK client to connect to Azure Storage Container
        - DYNAMODB_TABLE_NAME : Name of DynamoDB log table
        - AZURE_PARENT_FOLDER : Name of 'parent folder' in the Azure Storage Container from which all blobs are to be transferred


    Returns :  (If all blobs in the 'parent folder' are already logged transferred, returns None.)
        - azure_source_name : Name of any file/folder in the parent folder, that hasn't been transferred.
    '''    

    parent_folder_path = AZURE_PARENT_FOLDER if AZURE_PARENT_FOLDER.endswith('/') else AZURE_PARENT_FOLDER + '/'

    azure_source_name = None
    
    for child_folder in container_client.walk_blobs(parent_folder_path, delimiter='/'):
        not_transferred = ddb_logger.check_not_transferred(DYNAMODB_TABLE_HASH_KEY, AZURE_PARENT_FOLDER,DYNAMODB_TABLE_RANGE_KEY, child_folder.name)

        if not_transferred:
            azure_source_name = child_folder.name
            break
    
    return azure_source_name

def transfer_blobs(container_client,bucket_resource,azure_source_name,S3_DEST_FOLDER):
    '''
    Transfer a blob (file or directory) from Azure container to a specified location in a S3 bucket

    Parameters :
        - container_client : Azure SDK client to connect to Azure Storage Container
        - bucket_resource : Boto3 S3 Bucket resource to connect to the S3 bucket to be transferred to
        - azure_source_name : Name of the Azure blob file or directory to be transferred
        - S3_DEST_FOLDER : Path to folder in S3 bucket where the blobs will be uploaded

    Returns : Boolean value representing whether transfer was successully executed and validated, or not
    '''    

    transfer_client = TransferAzureBlobToS3(container_client, bucket_resource)
    dest_path = transfer_client.transfer_source_to_dest(source=azure_source_name, dest=S3_DEST_FOLDER)
    # assert(dest_path != None)
    
    return dest_path

def log_successful_transfer(table_resource, DYNAMODB_TABLE_TIMESTAMP_KEY, DYNAMODB_TABLE_HASH_KEY, AZURE_PARENT_FOLDER, DYNAMODB_TABLE_RANGE_KEY, azure_source_name):

    '''
    Update log to mark status as 'COMPLETED'

    Parameters :
        - table_resource : Boto3 DynamoDB Table resource to connect to log table
        - AZURE_PARENT_FOLDER : Name of 'parent folder' in the Azure Storage Container from which all blobs are to be transferred
        - azure_source_name : Name of the Azure blob file or directory to be transferred


    Returns : Boto3 DynamoDB Table update_item method response
    '''    

    ddb_logger = TelemetryDataTransferLogger(table_resource)

    ddb_response = ddb_logger.log_transfer(DYNAMODB_TABLE_TIMESTAMP_KEY,DYNAMODB_TABLE_HASH_KEY,AZURE_PARENT_FOLDER,DYNAMODB_TABLE_RANGE_KEY,azure_source_name)

    return ddb_response

