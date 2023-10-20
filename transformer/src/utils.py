import os
from collections import OrderedDict
import json
import pandas as pd
import glob
import shutil
import pkg_resources
import re
import pprint
import logging
import zipfile
from zipfile import ZipFile, ZIP_DEFLATED
LOGGER = logging.getLogger(__name__ + ".acimib_builder")


Nexus_device=['Nexus']
IOS_device=['ASR', 'ISR', '2921']
IOS_XR_device=['88','NCS']


def Nexus(PID, Version):
    return "Cisco NX-OS(tm) {PID}, Software (NXOS 32-bit), Version {Version}, RELEASE SOFTWARE Copyright (c) 2002-2022 by Cisco Systems, Inc.".format(
        PID=PID,
        Version=Version
    )

def IOS(PID, Version):
    return "Cisco IOS Software, {PID} Software (X86_64_LINUX_IOSD-UNIVERSALK9-M), Version {Version}, RELEASE SOFTWARE (fc3) Technical Support: http://www.cisco.com/techsupport Copyright (c) 1986-2021 by Cisco Systems, Inc.".format(
        PID=PID,
        Version=Version
    )

def IOS_XR(PID, Version):
    return "Cisco IOS XR Software ({PID}), Version {Version} Copyright (c) 2013-2019 by Cisco Systems, Inc.".format(
        PID=PID,
        Version=Version
    )


def create_vendors_oid_tree_dict():
    filename = pkg_resources.resource_filename(__name__, "CISCO-ENTITY-VENDORTYPE-OID-MIB.my")

    oid_tree_dict_in = {"CISCOENTITYVENDORTYPEOIDMIB": {'parent_oid': False, 'oid_current': "1.3.6.1.4.1.9.12.3"},
                        "CISCOPRODUCTS": {'parent_oid': False, 'oid_current': "1.3.6.1.4.1.9.1"}}
    with open(filename, "r", encoding='utf8') as outfile:
        temp_data = outfile.readlines()
        for line in temp_data:
            oid_group = re.search(r'^(\S+)\s+OBJECT IDENTIFIER\s+::=\s+\{\s+(\S+)\s+(\S+)\s+\}(\s+--(.*?)\s*$){0,1}',
                                  line)
            if oid_group:
                oid_tree_dict_in[oid_group.group(1).upper()] = {'parent_oid': oid_group.group(2).upper(),
                                                                'oid_current': oid_group.group(3)}
    # TODO : fix var name reused
    filename = pkg_resources.resource_filename(__name__, "CISCO-PRODUCTS-MIB.my")

    with open(filename, "r", encoding='utf8') as outfile:
        temp_data = outfile.readlines()
        for line in temp_data:
            oid_group = re.search(r'^(\S+)\s+OBJECT IDENTIFIER\s+::=\s+\{\s+(\S+)\s+(\S+)\s+\}(\s+--(.*?)\s*$){0,1}',
                                  line)
            if oid_group:
                oid_tree_dict_in[oid_group.group(1).upper()] = {'parent_oid': oid_group.group(2).upper(),
                                                                'oid_current': oid_group.group(3)}

    return oid_tree_dict_in

def create_vendors_oid_tree_dict_sysobjectid():
    oid_tree_dict_in1 = {"CISCOENTITYVENDORTYPEOIDMIB": {'parent_oid': False, 'oid_current': "1.3.6.1.4.1.9.12.3"},
                        "CISCOPRODUCTS": {'parent_oid': False, 'oid_current': "1.3.6.1.4.1.9.1"}}
    filename = pkg_resources.resource_filename(__name__, "CISCO-PRODUCTS-MIB.my")

    with open(filename, "r", encoding='utf8') as outfile:
        temp_data = outfile.readlines()
        for line in temp_data:
            oid_group = re.search(r'^(\S+)\s+OBJECT IDENTIFIER\s+::=\s+\{\s+(\S+)\s+(\S+)\s+\}(\s+--(.*?)\s*$){0,1}',
                                  line)
            if oid_group:
                oid_tree_dict_in1[oid_group.group(1).upper()] = {'parent_oid': oid_group.group(2).upper(),
                                                                'oid_current': oid_group.group(3)}

    return oid_tree_dict_in1

def find_vendor_type_oid_sysobjectid(oid_tree_dict: dict, model_name: str) -> str:
    complete_oid=""
    model_name = model_name.replace('-', '')
    model_name = re.sub(r"/.*", "", model_name)
    for key in oid_tree_dict.keys():
        if re.search(model_name, key):
            print("Key for sysobjectid",key)
            complete_oid = oid_tree_dict[key]['oid_current']
            parent_oid = oid_tree_dict[key]['parent_oid']
            while parent_oid:
                complete_oid = oid_tree_dict[parent_oid]['oid_current'] + '.' + complete_oid
                parent_oid = oid_tree_dict[parent_oid]['parent_oid']

    return complete_oid

def find_vendor_type_oid(oid_tree_dict: dict, model_name: str) -> str:

    model_name=model_name.upper()
    complete_oid = oid_tree_dict[model_name]['oid_current']
    parent_oid = oid_tree_dict[model_name]['parent_oid']
    while parent_oid:
        complete_oid = oid_tree_dict[parent_oid]['oid_current'] + '.' + complete_oid
        parent_oid = oid_tree_dict[parent_oid]['parent_oid']

    return complete_oid

def ent_physical_vendor_type_chassis(oid_tree_dict, modelname):
    model_name = 'cevChassis' + modelname.replace('-', '')
    # print("model_name", model_name)
    if 'APIC' in model_name:
        physical_vendor_type = '1.3.6.1.4.1.9.1.2238'
    else:
        try:
            physical_vendor_type = find_vendor_type_oid(oid_tree_dict, model_name)
        except Exception as e:
            LOGGER.warning("Exception : {error} - no oid found for model name : {mn}".format(mn=model_name,
                                                                                             error=e))
            physical_vendor_type = "0.0.0"

    return physical_vendor_type

def ent_physical_vendor_type_container(modelname) -> str:
    if modelname == "eqptLCSlot":
        return ".1.3.6.1.4.1.9.12.3.1.5.123"
    elif modelname == "eqptSupCSlot" or modelname == "eqptSysCSlot" or modelname == "eqptFCSlot":
        return ".1.3.6.1.4.1.9.12.3.1.5.122"
    else:
        return ""

def ent_physical_vendor_type_module(oid_tree_dict, modelname) -> str:
    base_name = "cevModule"
    model_name = base_name + modelname.replace('-', '')
    # print("model_name", model_name)
    try:
        vendor_type = find_vendor_type_oid(oid_tree_dict, model_name)
    except KeyError:
        vendor_type = "0.0.0"
    if vendor_type=="0.0.0":
        new_model_name = "cev" + modelname.replace('-', '') + "FixedModule"
        print("new Model",new_model_name)
        try:
            vendor_type = find_vendor_type_oid(oid_tree_dict, new_model_name)
        except KeyError:
            LOGGER.warning("Exception : no oid found for Supervisor Card model name : {mn}".format(
                mn=model_name))
    return vendor_type

def ent_physical_vendor_type_fan(oid_tree_dict, modelname) -> str:
    base_name = "cevFan"
    model_name = base_name + modelname.replace('-', '')
    # print("model_name",model_name)
    try:
        vendor_type = find_vendor_type_oid(oid_tree_dict, model_name)
    except KeyError:
        vendor_type = "0.0.0"

    if not vendor_type:
        model_name = model_name + "Tray"
        try:
            vendor_type = find_vendor_type_oid(oid_tree_dict, model_name)
        except KeyError:
            LOGGER.warning("Exception : no oid found for Ft model name : {mn}".format(mn=model_name))
            vendor_type = "0.0.0"

    return vendor_type

def ent_physical_vendor_type_powerSupply(oid_tree_dict, modelname) -> str:
        base_name = "cevPowerSupply"
        model_name = base_name + modelname.replace('-', '')
        # print("model_name", model_name)
        try:
            vendor_type = find_vendor_type_oid(oid_tree_dict, model_name)
        except KeyError:
            LOGGER.warning("Exception : no oid found for Psu model name : {mn}".format(mn=model_name))
            vendor_type = "0.0.0"
        return vendor_type

def create_metadata(baseDir):
    files = glob.glob(f'{baseDir}/*/')
    for folderpath in files:
        with open(folderpath + "/metadata.json", "w") as f:
            data = {
                "collectorless_connector_name": "legacy",
                "collectorless_connector_version": "0.0.0",
                "nms_version": "0.0.0"
            }
            res = json.dumps(data)
            f.write(res)

def zip_output(baseDir):
    files = glob.glob(f'{baseDir}/*/')
    for folder in files:
        ziph = ZipFile( f'/tmp/Output/{folder.split("/")[3]}.zip', 'w', ZIP_DEFLATED)
        # path= './output'
        length = len(folder)
        # ziph is zipfile handle
        for root, dirs, files in os.walk(folder):
            folder = root[length:]
            for file in files:
                if file.startswith('config'):
                    filename="show_running-config"    # to get flatfile
                    ziph.write(os.path.join(root, file), os.path.join(folder, filename))
                elif file.startswith('inventory'):
                    filename="MIBS"    # to get flatfile
                    ziph.write(os.path.join(root, file), os.path.join(folder, filename))
                else:
                    ziph.write(os.path.join(root, file), os.path.join(folder, file))
            for dir in dirs:
                ziph.write(os.path.join(root, dir), os.path.join(folder, dir))
        ziph.close()
        
      

def delete_folder(baseDir):
    folder = glob.glob(f'{baseDir}/*')
    print(folder)
    for filename in folder:
        if os.path.isdir(filename):
            print(filename)
            shutil.rmtree(filename)


POD_NODE_entPhysicalClass = {
    'LC': 9,  # Module
    'FC': 9,  # Module
    'SupC': 9,  # Module
    'SysC': 9,  # Module
    'RP': 9,  # Module
    'SC': 9,  # Module
    'module': 9,  # Module
    'Module': 9,  # Module
    'Slot': 9,  # Module
    'subslot': 9,  # Module
    'Chassis': 3,  # Chassis
    'CISCO': 3,  # Chassis
    'Rack': 3,  # Chassis
    'LCSlot': 5,  # Container
    'FCSlot': 5,  # Container
    'SupCSlot': 5,  # Container
    'SysCSlot': 5,  # Container
    'PsuSlot': 5,  # Container
    'FtSlot': 5,  # Container
    'PM': 6,  # powerSupply
    'PT': 6,  # powerSupply
    'Power': 6,  # powerSupply
    'Ft': 7,  # Fan
    'Fan': 7,  # Fan
    'CPU': 12,  # CPU
    'LeafP': 10,  # Port
    'SFP': 10,  # Port
    'Supervisor': 10,  # Port
    'FabP': 10,  # Port
    'GigabitEthernet': 10,  # Port
    'Sensor': 8  # Sensor
}

Module = ['LC','FC','SupC','RP','SC','module','Module','Slot', 'subslot', 'CPU']
Chassis = ['Chassis','CISCO','Rack']
Container = ['LCSlot','FCSlot','SupCSlot','SysCSlot','PsuSlot','FtSlot']
PowerSupply = ['PM','PT','Power']
Fan = ['Ft','Fan', 'FT']
# Cpu = ['CPU']
Port = ['LeafP','SFP','Supervisor','FabP','GigabitEthernet']
Sensor = ['Sensor']

def get_state_table_keys(params, table_resource):

    primary_key = table_resource.key_schema

    for attr in primary_key:
        if attr["KeyType"] == "HASH":
            print("DynamoDB State Table primary hash key =", attr["AttributeName"])
            params["DYNAMODB_TABLE_HASH_KEY"] = attr["AttributeName"]
        elif attr["KeyType"] == "RANGE":
            print("DynamoDB State Table primary range key =", attr["AttributeName"])
            params["DYNAMODB_TABLE_RANGE_KEY"] = attr["AttributeName"]

    global_secondary_key = table_resource.global_secondary_indexes[0]["KeySchema"]
    for attr in global_secondary_key:
        if attr["KeyType"] == "HASH":
            print("DynamoDB State Table global secondary hash key =", attr["AttributeName"])
            params["DYNAMODB_TABLE_PIPELINE_KEY"] = attr["AttributeName"]
        # elif attr["KeyType"] == "RANGE":
        #     params["DYNAMODB_TABLE_RANGE_KEY"] = attr["AttributeName"]

    local_secondary_key = table_resource.local_secondary_indexes[0]["KeySchema"]
    for attr in local_secondary_key:
        if attr["KeyType"] == "RANGE":
            print("DynamoDB State Table local secondary range key =", attr["AttributeName"])
            params["DYNAMODB_TABLE_INPUT_KEY"] = attr["AttributeName"]

    return params
