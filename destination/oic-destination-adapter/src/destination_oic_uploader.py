import os
# import sys
import boto3
import json
from urllib.parse import unquote_plus
from dynamodb_client import OICUploadLogger

# PROJECT_ROOT = os.path.abspath(os.path.join(
#                   os.path.dirname(__file__), 
#                   os.pardir)
# )
# print("PROJECT ROOT :",PROJECT_ROOT)
# sys.path.append(PROJECT_ROOT+'/test')

from utils import *
from test_oic_uploader import TestOICAPIClient
from botocore.exceptions import ClientError

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


def lambda_handler(event,context):
    # print(event)
    params = {}
    params["PIPELINE_UUID"] = os.environ.get('PIPELINE_UUID')
    params["FUNCTION_NAME"] = context.function_name

    secret = get_secret(secret_name = os.environ.get("ASM_SECRET_GROUP_NAME"), region_name = os.environ.get("AWS_REGION_NAME"))

    message = json.loads(event["Records"][0]["body"])
    run_id = message["run_id"]

    bucket = os.environ.get("S3_TRANSFORMER_TO_DESTINATION_BUCKET")
    filepath = unquote_plus(message["s3_filepath"])
    # size = event["Records"][0]["s3"]["object"]["size"]
    print("S3 Bucket :", bucket)
    print("Filepath Key :", filepath) #, ", file size =",size)
    
    # Create Boto3 DynamoDB Table resource to access log table
    dynamodb_resource = boto3.resource('dynamodb')
    params["DYNAMODB_TABLE_NAME"] = os.environ.get("DYNAMODB_TABLE_NAME")
    table_resource = dynamodb_resource.Table(params["DYNAMODB_TABLE_NAME"])
    params = get_state_table_keys(params,table_resource)
    ddb_logger = OICUploadLogger(table_resource, pipeline_key = params["DYNAMODB_TABLE_PIPELINE_KEY"], pipeline_uuid = params["PIPELINE_UUID"], hash_key = params["DYNAMODB_TABLE_HASH_KEY"], range_key = params["DYNAMODB_TABLE_RANGE_KEY"], function_name = params["FUNCTION_NAME"], input_key = params["DYNAMODB_TABLE_INPUT_KEY"])
    # ddb_logger = None

    s3_resource = boto3.resource('s3')
    bucket_resource = s3_resource.Bucket(bucket)

    # s3_client = boto3.client('s3')
    # bucket_files = s3_client.list_objects(Bucket = bucket)
    # print("Bucket Client Objects:",bucket_files)

    if os.path.basename(filepath).find("test") != -1:
        print("!!!!!!!!!! TEST file detected. Using mock OIC API... !!!!!!!!!!!!!")
        test_client = TestOICAPIClient()
        status_code, upload_url = test_client.test_complete_flow(secret=secret, filename=filepath, bucket_resource=bucket_resource, ddb_logger=ddb_logger, run_id = run_id)
    else:
        print("Initialising upload to OIC API")
        status_code, upload_url = transfer_s3_to_oic_api(secret, bucket_resource, filepath,ddb_logger, run_id)
    # print("Upload status code:",status_code)

if __name__ == "__main__":
    event = {
        "Records" : [
            {
                "s3" : {
                    "bucket" : {
                        "name" : "test-blob-storage-bucket"
                    },
                    "object" : {
                        "key" : "TEST_chunk.zip",
                        "size" : "1300"
                    }
                }
            }
        ]
    }

    context = None
    os.environ["PIPELINE_UUID"] = "123456789"
    os.environ["ASM_SECRET_GROUP_NAME"] = "DTE_Secret"
    os.environ["AWS_REGION_NAME"] = "us-east-1"
    # os.environ["DYNAMODB_TABLE_NAME"] = ""
    os.environ["CEC_USERNAME_SECRET_KEY"] = "oic_cec_username"
    os.environ["CEC_PASSWORD_SECRET_KEY"] = "oic_cec_password"
    os.environ["CLIENT_ID_SECRET_KEY"] = "oic_client_id"
    os.environ["CLIENT_SECRET_SECRET_KEY"] = "oic_client_secret"
    os.environ["COLLECTOR_ID_SECRET_KEY"] = "oic_collector_id"

    lambda_handler(event, context)