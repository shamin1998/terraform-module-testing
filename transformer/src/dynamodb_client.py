from datetime import datetime
import json
from boto3.dynamodb.conditions import Key, Attr
import os

# Defining class for logging successful transfers in a DynamoDB table and querying log table
class TelemetryDataTransferLogger:
    def __init__(self, table_resource, pipeline_key = None, pipeline_uuid = None, hash_key = None, range_key = None, function_name = None, input_key = None, sort_index = None, timestamp_key = None, s3_bucket_name = None):
        
        self.table = table_resource

        # Set primary partition key of DynamoDB table, expected to be name of Lambda function
        if hash_key:
            self.hash_key = hash_key
        if function_name:
            self.function_name = function_name
        
        # Set primary sort key of DynamoDB table, expected to be timestamp of log
        if range_key:
            self.range_key = range_key
        
        # Set the attribute of DynamoDB table which will record the pipeline UUID
        if pipeline_key:
            self.pipeline_key = pipeline_key
        if pipeline_uuid:
            self.pipeline_uuid = pipeline_uuid
        
        # Set the attribute of DynamoDB table which will record the path in the Azure container to the blob being logged
        if input_key:
            self.input_key = input_key

        # Set the name of the S3 bucket to which all blobs are to be uploaded
        if s3_bucket_name:
            self.s3_bucket_name = s3_bucket_name
            

    # Boolean function which returns True if there are no logs in the table, else False
    def is_empty(self):
        table_scan = self.table.scan()
        # print("Table scan items :",table_scan["Items"])

        item_count = table_scan["Count"]
        # print("DynamoDB table item Count =",item_count)

        return item_count == 0

    def init_log(self,run_id,input_files):
        '''
        Initialize log of blob transfer in 'PENDING' status with desired attributes

        Parameters :
         - blob : A dict containing the name and size of the blob to be transferred
         - s3_bucket_dest_path : Path to the location in the S3 bucket where the blob will be uploaded            

        Returns : 
         - run_id : An ID specifying a pipeline 'run', to help track the processing of specific Azure input_files through the pipeline
        '''

        current_time = str(datetime.now())

        # Generate the run_id, currently using a naive approach to ensure a 1:1 mapping of blob to run_id
        
        item = {
            self.hash_key : self.function_name,
            self.range_key : current_time,
            self.pipeline_key : self.pipeline_uuid,
            'run_id' : run_id,
            self.input_key : ','.join(input_files),
            's3_bucket_name' : self.s3_bucket_name,
            'adapter_state' : 'PENDING',
            'description' : f"Initializing transformer..."
            }

        # print("Logging Initialization of Transfer :",json.dumps(item))

        ddb_response = self.table.put_item(Item = item)
        # print("DynamoDB Table put response :",ddb_response)

        return ddb_response

    # Log successful transfer
    def log_transfer(self,run_id,input_files,s3_bucket_dest_path):
        '''
        Log successfully transferred blob

        Parameters :
         - run_id : An ID specifying a pipeline 'run', to help track the processing of specific Azure input_files through the pipeline
         - blob : A dict containing the name and size of the blob to be transferred
         - s3_bucket_dest_path : Path to the location in the S3 bucket where the blob will be uploaded            

        Returns : 
         - ddb_response : Response of Boto3 DynamoDB Table `put_item` request
        '''


        current_time = str(datetime.now())

        # print("Logging Successful Transfer :",blob)

        item = {
            self.hash_key : self.function_name,
            self.range_key : current_time,
            self.pipeline_key : self.pipeline_uuid,
            'run_id' : run_id,
            self.input_key : ','.join(input_files),
            's3_bucket_name' : self.s3_bucket_name,
            'output_path' : s3_bucket_dest_path,
            'adapter_state' : 'COMPLETED',
            'description' : f"Successfully transferred!"
            }

        # print("Logging Completed Transfer :",json.dumps(item))

        ddb_response = self.table.put_item(Item = item)
        # print("DynamoDB Table put response :",ddb_response)

        return ddb_response
    
    # Get name of the last blob transferred from the latest log in the table
    def latest_source_transferred(self):
        
        print("Retrieving latest log")
        ddb_response = self.table.query(Limit = 1, KeyConditionExpression = Key(self.hash_key).eq(self.function_name), ScanIndexForward = False)

        if not ddb_response["Items"]:
            print("ERROR! No items found in log table")
            return False
        
        print("Latest transfer log :",ddb_response["Items"][0])
        
        return ddb_response["Items"][0]
    
    def get_pending_sources(self,log_table_hash_key,azure_parent_name,log_table_range_key):

        print("Checking 'PENDING' logs under azure_parent_name :",azure_parent_name)
        ddb_response = self.table.query(KeyConditionExpression = (Key(log_table_hash_key).eq(azure_parent_name) & Key(log_table_range_key).begins_with(azure_parent_name)), FilterExpression =  Key('transfer_status').eq('PENDING'))

        if not ddb_response["Items"]:
            print("No PENDING sources found under", log_table_hash_key," :",azure_parent_name)
            return None
        
        print("'PENDING' sources :",ddb_response["Items"])
        return ddb_response["Items"]

# # Boolean function which returns True if passed source name has not been logged transferred
#     def check_not_transferred(self,blob_name):
        
#         # print("Retrieving key =", azure_source_name)

#         ddb_response = self.table.query(KeyConditionExpression = (Key(self.hash_key).eq(self.function_name) & Key(log_table_range_key).eq(azure_source_name)))
        
#         if not ddb_response["Items"]:
#             return True
        
#         if ddb_response["Items"][-1]['transfer_status'] == 'PENDING':
#             return True
        
#         return False

