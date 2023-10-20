import os
from dynamodb_client import TelemetryDataTransferLogger

# Defining class for downloading blobs from an Azure Storage Container and uploading them to an S3 Bucket

class TransferAzureBlobToS3:
    def __init__(self, container_client, bucket_resource):        
        self.container_client = container_client
        self.bucket = bucket_resource

    def transfer_blobs(self, blobs, dest="", ddb_logger = None):
        '''
        Transfer blobs to a S3 bucket, while maintaining internal directory structure of Azure container

        Parameters :
            - blobs : List of (dict of) blobs to be transferred
            - dest : Path to directory in S3 bucket where the downloaded blobs will be uploaded

        Returns : True if successful, else False
        '''
        
        # print("Running TransferAzureBlobToS3.transfer_source_to_dest(",",",dest,")")
        
        if dest and not dest.endswith("/"):
            dest += '/'
        
        if dest == '/':
            dest = ""

        print("Blobs to be transferred =",blobs)
        
        blob_dest_list = []
        blob_id = ""

        blob_dest_paths = [ dest + blob["name"] for blob in blobs]
        details = {}

        if blobs[0]["name"].find("inventory") != -1 and blobs[1]["name"].find("config") != -1:
            blob_id = blobs[0]["name"][:blobs[0]["name"].find("inventory")]

            run_id = blob_id + '_'
            for ch in blob_id:
                run_id += str(ord(ch))

            blob_names = [ blob["name"] for blob in blobs]
            

            details = {
                "run_id" : run_id,
                "s3_inventory_path" : dest + blobs[0]["name"],
                "s3_config_path" : dest + blobs[1]["name"]
            }

        
        elif blobs[0]["name"].find("config") != -1 and blobs[1]["name"].find("inventory") != -1:
            blob_id = blobs[0]["name"][:blobs[0]["name"].find("config")]

            run_id = blob_id + '_'
            for ch in blob_id:
                run_id += str(ord(ch))

            blob_names = [ blob["name"] for blob in blobs]

            details = {
                "run_id" : run_id,
                "s3_inventory_path" : dest + blobs[1]["name"],
                "s3_config_path" : dest + blobs[0]["name"]
            }
         
        else:
            print("ERROR: Blob filename does not follow expected format; does not contain the substring 'inventory' or 'config'")
            return None
        

        if ddb_logger:
            init_ddb_response = ddb_logger.init_log(run_id,blob_names,blob_dest_paths)


        # Transfer each blob file iteratively
        for blob in blobs:
            blob_dest = dest + blob["name"]
            blob_dest_list.append(blob_dest)

            
            content = self.download_file_from_azure(blob["name"])
            s3_object = self.upload_file_to_s3(content,blob_dest)
            # print("S3 Object uploaded:", s3_object)    

        # Validate transfer by checking if any files at Azure source are missing at S3 bucket destination
        valid = self.validate_transfer(dest,blobs,blob_dest_list)
        if valid:
            print('Blob transfer successfully validated!')
            if ddb_logger:
                ddb_logger.log_transfer(run_id, blob_names, blob_dest_paths)
        
            return details
            
        else:
            print('Blob transfer validation failed!')
            return {}

    def download_file_from_azure(self, source):
        '''
        Download a single blob file from Azure container and read its content
        
        Parameters :
            - source : Path to blob in Azure container to be downloaded

        Returns : 
            - content : Body of blob file
        '''

        # print(f'Downloading file from Azure container; filename = {source}')
        
        blob_client = self.container_client.get_blob_client(blob=source)
        blob = blob_client.download_blob()
        # print('Downloaded blob : ' + '{ name = ' + blob.name + ', size = ' + str(blob.size) + ' }')

        content = blob.readall()
        return content

    def upload_file_to_s3(self,content,dest):
        '''
        Upload a single file to S3 bucket at specified destination
        
        Parameters :
            - content : Body of blob file
            - dest : Path to file/directory in S3 bucket where file will be uploaded

        Returns : 
            - s3_object : Boto3 S3 Object resource of the uploaded file
        '''

        # print("Uploading file to S3 bucket; bucket_name =",self.bucket.name,", file_name =",blob_dest)
        s3_object = self.bucket.put_object(Body=content, Key=dest)
        # print("Uploaded S3 Object : "+str(s3_object))

        return s3_object

    def validate_transfer(self,dest,blobs,blob_dest_list,is_directory=True):
        '''
        Validate whether Azure blobs have been successfully transferred to the S3 bucket
        
        Parameters :
            - blobs_size : Set of dicts containing blob filename and size
            - dest : Path to directory in S3 bucket where file should be uploaded, assuming ends with '/'

        Returns : 
            - valid : Boolean value representing whether file(s) were transferred successfully or not
        '''

        # print("Validating :","Azure source path =",source,", S3 bucket destination path =",dest)

        blobs_size = {}
        for blob in blobs:
            blobs_size[blob["name"]] = blob["size"] 

        if dest and not dest.endswith('/'):
            dest += '/'

    
        # Record file paths (without parent folder name), and sizes of these S3 objects
        s3_files_size = {}
        for key in blob_dest_list:
            # print(object.key)
            objects = self.bucket.objects.filter(Prefix=key)
            s3_object = None
            for obj in objects:
                s3_object = obj
                break
            
            if not s3_object:
                print("ERROR : S3 Object not found :", key)
                return False

            s3_files_size[os.path.relpath(key,dest)] = s3_object.size
        
        print("Azure blob files :",blobs_size)
        print("S3 files :",s3_files_size)
        
        valid = (blobs_size == s3_files_size)
        
        return valid