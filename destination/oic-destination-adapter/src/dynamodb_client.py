from datetime import datetime
import json
from boto3.dynamodb.conditions import Key, Attr

# Defining class for logging successful transfers in a DynamoDB table and querying log table
class OICUploadLogger:
    def __init__(self, table_resource, pipeline_key = None, pipeline_uuid = None, hash_key = None, range_key = None, function_name = None, input_key = None, sort_index = None, timestamp_key = None, s3_bucket_name = None):
        
        self.table = table_resource

        if pipeline_key:
            self.pipeline_key = pipeline_key
        if pipeline_uuid:
            self.pipeline_uuid = pipeline_uuid

        if hash_key:
            self.hash_key = hash_key
        

        if range_key:
            self.range_key = range_key
        if function_name:
            self.function_name = function_name
        
        if input_key:
            self.input_key = input_key
        
        # if sort_index:
        #     self.sort_index = sort_index
        # if timestamp_key:
        #     self.timestamp_key = timestamp_key
        
        if s3_bucket_name:
            self.s3_bucket_name = s3_bucket_name
            

    # Boolean function which returns True if there are no logs in the table, else False
    def is_empty(self):
        table_scan = self.table.scan()
        # print("Table scan items :",table_scan["Items"])

        item_count = table_scan["Count"]
        print("DynamoDB table item Count =",item_count)

        return item_count == 0

    def init_log(self,run_id,filename,filesize,log_table_timestamp_key=None,log_table_hash_key=None,log_table_range_key=None,s3_bucket_name=None):
        '''
        Initialize log entry in 'PENDING' status with needed attributes

        Parameters :
         - azure_parent_name            

        Returns : run_id
        '''

        current_time = str(datetime.now())

        # run_id = ""
        # run_id = filename[5:]
        # # for ch in filename[5:]:
        #     run_id += str(ord(ch))

        item = {
            self.hash_key : self.function_name,
            self.range_key : current_time,
            self.pipeline_key : self.pipeline_uuid,
            'run_id' : run_id,
            self.input_key : filename,
            # 's3_bucket_name' : self.s3_bucket_name,
            # 'output_path' : s3_bucket_dest_path,
            'adapter_state' : 'PENDING',
            'description' : f"Initializing OIC upload: size = {filesize}"
            }

        print("Logging Initialization of OIC upload :",json.dumps(item))

        ddb_response = self.table.put_item(Item = item)
        # print("DynamoDB Table put response :",ddb_response)

        return ddb_response

    # Add log record to table, attributes passed through arguments
    def log_upload(self,run_id,filename,filesize,log_table_timestamp_key=None,log_table_hash_key=None,azure_parent_name=None,log_table_range_key=None,azure_source_name=None):
        current_time = str(datetime.now())

        # print("Marking Successful Transfer :",filename)

        item = {
            self.hash_key : self.function_name,
            self.range_key : current_time,
            self.pipeline_key : self.pipeline_uuid,
            'run_id' : run_id,
            self.input_key : filename,
            # 's3_bucket_name' : self.s3_bucket_name,
            # 'output_path' : s3_bucket_dest_path,
            'adapter_state' : 'COMPLETED',
            'description' : f"Successfully initialized upload: size = {filesize}"
            }

        print("Logging Initialized Upload :",json.dumps(item))

        ddb_response = self.table.put_item(Item = item)
        # print("DynamoDB Table put response :",ddb_response)

        return ddb_response
    
    # Boolean function which returns True if passed source name has not been logged transferred
    def check_not_transferred(self,log_table_hash_key,azure_parent_name,log_table_range_key,azure_source_name):
        
        # print("Retrieving key =", azure_source_name)

        ddb_response = self.table.query(KeyConditionExpression = (Key(log_table_hash_key).eq(azure_parent_name) & Key(log_table_range_key).eq(azure_source_name)))
        
        if not ddb_response["Items"]:
            return True
        
        if ddb_response["Items"][-1]['transfer_status'] == 'PENDING':
            return True
        
        return False

    # Get name of the last source trnsferred from the latest log in the table
    def latest_source_transferred(self,log_table_sort_index=None,log_table_hash_key=None,azure_parent_name=None):
        
        print("Retrieving latest log")
        ddb_response = self.table.query(Limit = 1, KeyConditionExpression = Key(self.hash_key).eq(self.function_name), ScanIndexForward = False)

        if not ddb_response["Items"]:
            print("ERROR! No items found under (local secondary) partition", self.hash_key)
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


