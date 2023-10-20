import json
import sys
import csv
import boto3
from utils import *
import pandas as pd
import os
from dynamodb_client import TelemetryDataTransferLogger


def config_data(device,filepath):
    data = pd.read_csv(filepath)
    row_value = data.iloc[:, 0]
    config_dict={}
    for device in row_value:
        value = data.groupby(row_value).get_group(device)
        config_clean = value.iloc[:, 1].str.replace(r'%%+', '\n', regex=True)
        config_dict[device]=config_clean


    return config_dict.get(device)


def lambda_handler(event, context):
    # TODO implement
    print("EVENT:",event)
    params = {}
    params["FUNCTION_NAME"] = context.function_name
    params["PIPELINE_UUID"] = os.environ.get("PIPELINE_UUID")
    params["S3_BUCKET_NAME"] = os.environ.get("S3_SOURCE_TO_TRANSFORMER_BUCKET")
    
    message = json.loads(event["Records"][0]["body"])
    run_id = message["run_id"]

    bucket_name = params["S3_BUCKET_NAME"]
    inventory_filepath = message["s3_inventory_path"]
    inventory_filename = inventory_filepath[:inventory_filepath.find('.')]
    config_filepath = message["s3_config_path"]
    # config_filename = config_filepath[:config_filepath.find('.')]
    filename = inventory_filename[:inventory_filename.find("_inventory")]

    # Create Boto3 DynamoDB Table resource to access log table
    params["DYNAMODB_TABLE_NAME"] = os.environ.get("DYNAMODB_TABLE_NAME")
    dynamodb_resource = boto3.resource('dynamodb')
    table_resource = dynamodb_resource.Table(params["DYNAMODB_TABLE_NAME"])
    params = get_state_table_keys(params,table_resource)
    input_files = [inventory_filepath, config_filepath]

    ddb_logger = TelemetryDataTransferLogger(table_resource, pipeline_key = params["DYNAMODB_TABLE_PIPELINE_KEY"], pipeline_uuid = params["PIPELINE_UUID"], hash_key = params["DYNAMODB_TABLE_HASH_KEY"], range_key = params["DYNAMODB_TABLE_RANGE_KEY"], function_name = params["FUNCTION_NAME"], input_key = params["DYNAMODB_TABLE_INPUT_KEY"], s3_bucket_name = params["S3_BUCKET_NAME"])
    response = ddb_logger.init_log(run_id, input_files)
    print("Initialised DynamoDB Log response:", response)

    s3_resource = boto3.resource('s3')
    bucket_resource = s3_resource.Bucket(bucket_name)
    
    download_path = '/tmp/' + os.path.basename(inventory_filepath)
    
    print("Downloading inventory file", inventory_filepath)
    bucket_resource.download_file(inventory_filepath,download_path)
    
    config_download_path = '/tmp/' + os.path.basename(config_filepath)
    
    print("Downloading config file", config_filepath)
    bucket_resource.download_file(config_filepath,config_download_path)

    data = pd.read_csv(download_path)
    device=data.groupby('DeviceName')
    OID_tree = create_vendors_oid_tree_dict()
    ip=data.iloc[0]['ManagementIP']

    print("OID tree created")

    size = len(device)
    count=0
    chunksize=1
    dirname = '/tmp/Output/chunk_' + str(chunksize)
    if not os.path.exists(dirname):
        os.makedirs(dirname)


    for name, group in device:

        print(name)
        print(group)
        new_file_content = ""
        devicename = list(set(data.DeviceName))[0]
        new_line1 = f'.1.3.6.1.2.1.1.5.0 = STRING: {devicename}'
        new_file_content += new_line1 + "\n"
        IpAddress = list(set(data.ManagementIP))[0]
        new_line2 = f'.1.3.6.1.2.1.4.20.1.1.{IpAddress} = IpAddress: {IpAddress}'
        new_file_content += new_line2 + "\n"
        print(devicename)
        chassis_index = data.Name[
            (data.Name == "Chassis") | (data.Name == "Rack 0") | (data.Name == "Supervisor(slot 1)")]
        if not chassis_index.empty:
            index_value = chassis_index.index[0]
        else:
            index_value = -1

        # Sysdescription
        PID = data.PId.iloc[index_value]
        Platform = data.HardwareSku.iloc[index_value]
        Version = data.OSVersion.iloc[index_value]
        print(PID, "___", Platform, "____", Version)
        if any(word in Platform for word in Nexus_device):
            new_line9 = f'.1.3.6.1.2.1.1.1.0 = STRING: {Nexus(PID, Version)}'
            new_file_content += new_line9 + "\n"
        elif any(word in Platform for word in IOS_device):
            new_line9 = f'.1.3.6.1.2.1.1.1.0 = STRING: {IOS(PID, Version)}'
            new_file_content += new_line9 + "\n"
        elif any(word in Platform for word in IOS_XR_device):
            new_line9 = f'.1.3.6.1.2.1.1.1.0 = STRING: {IOS_XR(PID, Version)}'
            new_file_content += new_line9 + "\n"
        else:
            new_line9 = f'.1.3.6.1.2.1.1.1.0 = STRING: Cisco Device'
            new_file_content += new_line9 + "\n"

        # sysobjectid
        OID_tree1 = create_vendors_oid_tree_dict_sysobjectid()
        oid = find_vendor_type_oid_sysobjectid(OID_tree1, data.PId.iloc[index_value])
        print("find OID relevant to PID")
        if oid:
            new_line8 = f'.1.3.6.1.2.1.1.2.0 = OID: .{oid}'
            new_file_content += new_line8 + "\n"
        else:
            value = ent_physical_vendor_type_chassis(OID_tree, data.PId.iloc[index_value])
            new_line8 = f'.1.3.6.1.2.1.1.2.0 = OID: {value}'
            new_file_content += new_line8 + "\n"

        # physicalentity table
        for i, n in enumerate(data.PId):
            new_line3 = f'.1.3.6.1.2.1.47.1.1.1.1.13.{i + 1} = STRING: "{n}"'
            new_file_content += new_line3 + "\n"
        for j, m in enumerate(data.SerialNo):
            new_line4 = f'.1.3.6.1.2.1.47.1.1.1.1.11.{j + 1} = STRING: "{m}"'
            new_file_content += new_line4 + "\n"
        for k, l in enumerate(data.OSVersion):
            new_line5 = f'.1.3.6.1.2.1.47.1.1.1.1.10.{k + 1} = STRING: "{l}"'
            new_file_content += new_line5 + "\n"
        for x, y in enumerate(data.Description):
            new_line6 = f'.1.3.6.1.2.1.47.1.1.1.1.2.{x + 1} = STRING: "{y}"'
            new_file_content += new_line6 + "\n"
        for o, p in enumerate(data.VId):
            new_line7 = f'.1.3.6.1.2.1.47.1.1.1.1.8.{o + 1} = STRING: "{p}"'
            new_file_content += new_line7 + "\n"

        # Physical class
        for a, b in enumerate(data.Name):
            for key, value in POD_NODE_entPhysicalClass.items():
                if (key in b):
                    new_file_content += f'.1.3.6.1.2.1.47.1.1.1.1.5.{a + 1} = INTEGER: {value}' + "\n"
                    break
            if re.match('0\/\d+$', b):
                new_file_content += f'.1.3.6.1.2.1.47.1.1.1.1.5.{a + 1} = INTEGER: 9' + "\n"

        # Physical containID
        for c, d in enumerate(data.Name):
            if index_value == c:
                new_file_content += f'.1.3.6.1.2.1.47.1.1.1.1.4.{c + 1} = INTEGER: 0' + "\n"
            else:
                new_file_content += f'.1.3.6.1.2.1.47.1.1.1.1.4.{c + 1} = INTEGER: {index_value + 1}' + "\n"

        # physical vendor type
        for e, f in enumerate(data.Name):
            # print("vendorOID element", e, f)
            if any(word in f for word in Fan):
                vendor_type = ent_physical_vendor_type_fan(OID_tree, data.PId.iloc[e])
                new_file_content += f'.1.3.6.1.2.1.47.1.1.1.1.3.{e + 1} = OID: .{vendor_type}' + "\n"
            elif any(word in f for word in PowerSupply):
                vendor_type = ent_physical_vendor_type_powerSupply(OID_tree, data.PId.iloc[e])
                new_file_content += f'.1.3.6.1.2.1.47.1.1.1.1.3.{e + 1} = OID: .{vendor_type}' + "\n"
            elif any(word in f for word in Module):
                vendor_type = ent_physical_vendor_type_module(OID_tree, data.PId.iloc[e])
                new_file_content += f'.1.3.6.1.2.1.47.1.1.1.1.3.{e + 1} = OID: .{vendor_type}' + "\n"
            elif any(word in f for word in Chassis):
                vendor_type = ent_physical_vendor_type_chassis(OID_tree, data.PId.iloc[e])
                new_file_content += f'.1.3.6.1.2.1.47.1.1.1.1.3.{e + 1} = OID: .{vendor_type}' + "\n"
            else:
                new_file_content += f'.1.3.6.1.2.1.47.1.1.1.1.3.{e + 1} = OID: .0.0.0' + "\n"
        print(new_file_content)


        count = count + 1
        if (count > 1000):
            count = 1000 - count
            chunksize = chunksize + 1
            dirname='/tmp/Output/chunk_' + str(chunksize)
            if not os.path.exists(dirname):
                os.makedirs(dirname)



        baseDir='/tmp/Output/chunk_' + str(chunksize)
        folderName = name
        UserPath = os.path.join(baseDir, folderName)
        if not os.path.exists(os.path.join(baseDir, folderName)):
            os.makedirs(UserPath)
        config=config_data(folderName,config_download_path)
        config.to_csv(UserPath + "/show_running-config", index=False, header=None, quoting=csv.QUOTE_NONE,
                escapechar='\x1f')
        with open(UserPath + "/metadata.json", "w") as f:
            data1 = {
                "IPAddress": ip,  # Use ManagementIP
                "PrimaryDeviceName": value,  # Use DeviceName
            }
            res = json.dumps(data1)
            f.write(res)
        writing_file = open(UserPath + "/MIBS", "w")
        writing_file.write(new_file_content)
        writing_file.close()

    create_metadata('/tmp/Output')
    print("metadata created")
    zip_output('/tmp/Output')
    print("zipped created")
    
    delete_folder('/tmp/Output')

    zipfile ="/tmp/Output"
    zip_files=(os.listdir(zipfile))
    print(zip_files)
    
    
    out_bucket = os.environ.get("S3_TRANSFORMER_TO_DESTINATION_BUCKET")
    # out_bucket = "test-transformer-out-bucket"
    
    # bucket_resource = s3_resource.Bucket(out_bucket)
    
    # response = bucket_resource.put_object(Body=zipfile, Key="chunk.zip")
    
    for files in zip_files:
        print("Upoading file:", files)
        s3_key = filename + "_" + files
        response = s3_resource.meta.client.upload_file("/tmp/Output/"+files, out_bucket, s3_key)
        
        print(response)

        response = ddb_logger.log_transfer(run_id, input_files, s3_key)
        print("Logged successful transfer DynamoDB response:", response)

        sqs_resource = boto3.resource('sqs')
        queue_resource = sqs_resource.Queue(os.environ.get("SQS_QUEUE_URL"))
        details = {
            "run_id" : run_id,
            "s3_filepath" : s3_key
        }
        message = json.dumps(details)
        response = queue_resource.send_message(MessageBody = message)
        print("SQS response:",response)
        
    
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
