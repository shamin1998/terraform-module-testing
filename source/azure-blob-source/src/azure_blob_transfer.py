import os

import boto3
import logging
from utils import *
from blob_transfer_client import TransferAzureBlobToS3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def lambda_handler(event,context):
  
    # Log details of AWS EventBridge trigger event
    logger.info("Handler triggered : { " + "event.id = " + event['id'] + ", event.time = " + event['time'] + " }")

    # Read environment variables; DynamoDB, Azure and S3 parameters
    params = read_env_variables()
    params["FUNCTION_NAME"] = context.function_name

    # Get credentials from AWS Secrets Manager
    secret = get_secret(params["ASM_SECRET_NAME"], params["AWS_REGION_NAME"])
    
    # Create Boto3 DynamoDB Table resource to access log table
    dynamodb_resource = boto3.resource('dynamodb')
    table_resource = dynamodb_resource.Table(params["DYNAMODB_TABLE_NAME"])
    params = get_state_table_keys(params,table_resource)

    # Create Azure SDK ContainerClient to access blobs in Azure Storage
    container_client = create_azure_container_client(secret, params)
    
    if not container_client:
        logger.info("Azure SDK authentication credentials invalid. Please provide one of the following sets; \n 1. (`azure_storage_account_name`, `azure_container_name`, `azure_sas_token`) \n 2. (`azure_container_url`) \n 3. (`azure_connection_string`, `azure_container_name`)")
        return None
    
    # Create boto3 S3 Bucket Resource to access objects in given bucket
    s3_resource = boto3.resource('s3')
    bucket_resource = s3_resource.Bucket(params["S3_BUCKET_NAME"])

    # Connect to boto3 SQS Queue Resource to send messages to trigger the transformation adapter
    sqs_resource = boto3.resource('sqs')
    queue_resource = sqs_resource.Queue(params["SQS_QUEUE_URL"])

    # Download blobs from Azure containre and upload to S3 bucket
    run_set_list = copy_azure_container(params,table_resource,container_client,bucket_resource, queue_resource)
    
    if run_set_list == []:
        logger.info("ERROR : Blob transfer unsuccessful!")
        return False
    
    elif run_set_list == None:
        print("All blobs already transferred. Exiting.")
        return None
    
    else:
        print("All blobs transferred successfully!")

        return True

def copy_azure_container(params,table_resource,container_client,bucket_resource, queue_resource):
    '''
    Check the latest blob which was logged as transferred successfully (if any), and transfer all blobs created after it

    Parameters :
        - params : Dict of required Azure and AWS resource parameters
        - table_resource : Boto3 DynamoDB Table Resource of log table
        - container_client : Azure SDK ContainerClient for authenticated access to blobs in Azure Storage
        - bucket_resource : Boto3 S3 Bucket Resource where blobs are to be uploaded

    Returns : 
     - if successful : True
     - if unsuccessful : False
     - if all blobs already transferred : None
    '''

    # Create TelemetryDataTransferLogger object to easily update and query DynamoDB log table
    ddb_logger = TelemetryDataTransferLogger(table_resource, pipeline_key = params["DYNAMODB_TABLE_PIPELINE_KEY"], pipeline_uuid = params["PIPELINE_UUID"], hash_key = params["DYNAMODB_TABLE_HASH_KEY"], range_key = params["DYNAMODB_TABLE_RANGE_KEY"], function_name = params["FUNCTION_NAME"], input_key = params["DYNAMODB_TABLE_INPUT_KEY"], s3_bucket_name = params["S3_BUCKET_NAME"])

    # Get list of blobs in the Azure container and store needed properties
    blobs = []
    blobs_properties = container_client.list_blobs(name_starts_with = params["AZURE_PARENT_FOLDER"])

    for blob in blobs_properties:
        blobs.append({
            "name" : blob.name,
            "size" : blob.size,
            "creation_time" : blob.creation_time
            })
    
    if not blobs:
        logger.info("ERROR: No blobs found in Azure Container")
        return []

    # Sort blobs in ascending order of their time of creation
    if not params["SEARCH_OPTIMIZATION"]:
        print("Sorting blobs by creation time...")
        blobs = sorted(blobs, key=lambda x: x['creation_time'])

    elif params["SEARCH_OPTIMIZATION"] == "transfer_latest":
        print("Reversing blob list...")
        blobs.reverse()

    # Check if log table is empty, implying none of the blobs have been transferred yet
    none_transferred = ddb_logger.is_empty()
    if none_transferred:
        print("No blobs logged as successfully transferred.")
        blobs_to_transfer = blobs

    else:
        blob_set_format = params["BLOB_SET_FORMAT"].split(',')
        # blobs_to_transfer = get_latest_blob_set(blobs, blob_set_format)
        blobs_to_transfer = get_blobs_to_transfer(ddb_logger, blobs, input_file_key = params["DYNAMODB_TABLE_INPUT_KEY"], consecutive=(params["SEARCH_OPTIMIZATION"] == "assume_ordered"))
        if blobs_to_transfer == None:
            logger.info("ERROR : DynamoDB table logs don't match expected adapter state.")
            return []
        
        elif blobs_to_transfer == []:
            return None

    transfer_client = TransferAzureBlobToS3(container_client, bucket_resource)    

    # blob_run_sets = [blobs_to_transfer]
    blob_run_sets = group_inventory_config_blobs(blobs_to_transfer, consecutive=(params["SEARCH_OPTIMIZATION"] == "assume_ordered"))
    run_set_list = []

    for blob_set in blob_run_sets:
        details = transfer_client.transfer_blobs(blob_set,dest=params["S3_DEST_FOLDER"], ddb_logger=ddb_logger)

        if details == {}:
            print("ERROR: Could not transfer blobs :",blob_set)
            return []

        else:
            print("Transferred blobs successfully :",details)
            run_set_list.append(details)

            sqs_response = trigger_transformation_adapter(queue_resource, details)
            print("SQS send message response :",sqs_response)
    
    return run_set_list



