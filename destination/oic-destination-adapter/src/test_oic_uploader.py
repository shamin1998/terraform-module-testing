import os
import sys
# from base64 import b64encode
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch
import json
import requests

PROJECT_ROOT = os.path.abspath(os.path.join(
                  os.path.dirname(__file__), 
                  os.pardir)
)
# print(PROJECT_ROOT+'/src')
sys.path.append(PROJECT_ROOT+'/src')

from oic_api_client import OICAPIClient
from utils import transfer_s3_to_oic_api

class MockOICResponse():
    def __init__(self):
        self.text = json.dumps({
            "access_token" : "test_access_token",
            "token" : "test_upload_token",
            "data" : [ { 
                "state" : "test_state",
                "filename" : "test_filename"
                } ]
            })

class TestOICAPIClient(unittest.TestCase):

    @patch('oic_api_client.requests')
    def test_complete_flow(self, mock_requests, secret=None, filename=None, bucket_resource=None, ddb_logger=None, run_id = None):
        mock_requests.request = MagicMock(return_value = MockOICResponse())
        # print("mock_requests.request.text =",mock_requests.request().text)
        
        test_cec_username = 'test_user'
        test_cec_password = 'test_password'
        test_client_id = 'test_cid'
        test_client_secret = 'test_secret'
        test_collector_id = 'test_collector_id'

        if not secret:
            secret = {
                'oic_cec_username' : test_cec_username,
                'oic_cec_password' : test_cec_password,
                'oic_client_id' : test_client_id,
                'oic_client_secret' : test_client_secret,
                'oic_collector_id' : test_collector_id
            }

        if not filename:
            filename = 'testfile.txt'
        
        if not bucket_resource:
            bucket_resource = MagicMock()
            
        upload_state = transfer_s3_to_oic_api(secret,bucket_resource,filename,ddb_logger,run_id)

        # bucket_resource.download_file.assert_called_once_with(filename, '/tmp/' + os.path.basename(filename))

        mock_response = MockOICResponse()
        self.assertEqual(upload_state,json.loads(mock_response.text)["data"][0]["state"])

        return upload_state

    # Test for TestOICAPIClient.request_access_token method
    @patch('oic_api_client.requests')
    def test_access_token_retrieval(self, mock_requests, test_cec_username = None, test_cec_password = None, test_client_id = None, test_client_secret = None):

        if not test_cec_username:
            test_cec_username = 'test_user'
        if not test_cec_password:
            test_cec_password = 'test_password'
        if not test_client_id:
            test_client_id = 'test_cid'
        if not test_client_secret:
            test_client_secret = 'test_secret'

        mock_requests.request = MagicMock(return_value = MockOICResponse())

        oic_client = OICAPIClient()
        access_token = oic_client.request_access_token(test_cec_username,test_cec_password,test_client_id,test_client_secret)

        test_cec_username += "@cisco.com"
        url = f"https://cloudsso.cisco.com/as/token.oauth2?grant_type=password&client_id={test_client_id}&client_secret={test_client_secret}&username={test_cec_username}&password={test_cec_password}"
        payload={}
        headers = {
            'Cache-Control': 'no-cache',
            # 'Cookie': 'PF=upiz0Lvf6ouZzJc9fN3sXT'
            }
        mock_requests.request.assert_called_with("POST", url, headers, payload)
        self.assertEqual(access_token,'test_access_token')

        return access_token

    # Test for TestOICAPIClient.request_upload_token method
    @patch('oic_api_client.requests')
    def test_upload_token_retrieval(self, mock_requests, test_access_token = None, test_collector_id = None):

        if not test_access_token:
            test_access_token = 'test_access_token'
        if not test_collector_id:            
            test_collector_id = 'test_cid'

        mock_requests.request = MagicMock(return_value = MockOICResponse())

        oic_client = OICAPIClient()
        upload_token = oic_client.request_upload_token(test_access_token,test_collector_id)

        url = f"https://api.cisco.com/oiccollectorless/v1/token/{test_collector_id}"

        payload = {}
        headers = {
        'Authorization': "Bearer %s" %test_access_token
        }
        mock_requests.request.assert_called_with("POST", url, headers, payload)
        self.assertEqual(upload_token,'test_upload_token')

        return upload_token
    
    # Test for TestOICAPIClient.upload_file_to_cxd method
    @patch('oic_api_client.requests')
    def test_file_upload(self, mock_requests, test_upload_token = None, test_collector_id = None, test_filename = None):

        if not test_upload_token:
            test_upload_token = 'test_upload_token'
        if not test_collector_id:
            test_collector_id = 'test_cid'
        if not test_filename:
            test_filename = 'testfile_3_6.txt'
        # test_filedata = 'test_data'

        # with open(test_filename, "w") as f:
        #     f.write(test_filedata)
        #     f.close()

        mock_requests.request = MagicMock(return_value = MockOICResponse())

        oic_client = OICAPIClient()
        response_text = oic_client.upload_file_to_cxd(test_upload_token,test_collector_id,test_filename)

        # usrPass = "%s:%s" % (test_collector_id, test_upload_token)
        # b64Val = b64encode(bytes(f'{usrPass}',encoding='ascii')).decode('ascii')
        # url = f'https://cxd.cisco.com/home/{test_filename}'
        # headers = {
        #     'Authorization': f'Basic {b64Val}'
        # }
        # with open(test_filename, 'rb') as data:
        mock_requests.request.assert_called() #_with("PUT", url, headers, data)
        self.assertEqual(response_text,MockOICResponse().text)

    # Test for TestOICAPIClient.get_upload_status method
    @patch('oic_api_client.requests')
    def test_upload_status_checking(self, mock_requests, test_access_token = None, test_collector_id = None):

        if not test_access_token:
            test_access_token = 'test_access_token'
        
        if not test_collector_id:
            test_collector_id = 'test_cid'
        
        mock_requests.request = MagicMock(return_value = MockOICResponse())

        oic_client = OICAPIClient()
        response_state, response_filename = oic_client.get_upload_status(test_access_token,test_collector_id)

        url = f"https://api.cisco.com/oiccollectorless/v1/status/{test_collector_id}"
        payload = {}
        headers = {
        'Authorization': "Bearer %s" %test_access_token
        }
        
        mock_requests.request.assert_called_with("GET", url, headers, payload)
        self.assertEqual(response_state,'test_state')
        self.assertEqual(response_filename,'test_filename')

        return response_state, response_filename

if __name__ == "__main__":

    task("shamagga","868cb5ce-b8ae-45e1-ab30-cdffdc1b2592", "GgnEM9Ekze6aYKRLhmoyQrmbjJsM1Z3t", "chunk_1.zip", "CSP0009067049")
    # url = "https://scripts.cisco.com/api/v2/jobs/OIC_manual_upload"

    # file_content = open("chunk_1.zip", "r")

    # payload = {
    #     # "srId" : "CSP0009067049",
    #     "input" : {
    #         # "oic_file" : file_content,
    #         "cspc_id" : "CSP0009067049",
    #         "client" : "868cb5ce-b8ae-45e1-ab30-cdffdc1b2592",
    #         "secret" : "GgnEM9Ekze6aYKRLhmoyQrmbjJsM1Z3t"
    #     }
    #     # "clientId" : "868cb5ce-b8ae-45e1-ab30-cdffdc1b2592"
    # }

    # response = requests.post(url, params=payload, data = file_content)
    # print(response.content)