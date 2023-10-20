# Reference : https://wwwin-github.cisco.com/spa-ie/Collectorless_Collection_Pipeline/Syslog Data Upload/Formatter1/Postman_request.py
# Date : 07/26/2023

import requests
import json
from base64 import b64encode
import os

class OICUploadClient:
    def __init__(self):
        pass    

    def tori_token(self, client, secret):
        url = "https://api-cx.cisco.com/torii-auth/v1/token"
        payload = {
            "grantType": "client_credentials",
            "clientId": client.strip(),
            "secret": secret.strip(),
            "scope": "api.bcs.manage",
            "claim": "ccoid"
        }
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result_token = response.json()['accessToken']
        return result_token

    def cxd_token(self, token, cspc_license):
        url = f"https://api-cx.cisco.com/oic/collectorless/api/v1/token/{cspc_license}"
        payload = {}
        headers = {
            'Authorization': f'Bearer {token}'
        }
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        return response.json()['data']['token']

    def upload_oic(self, username, cxd_token, cspc_license, oic_file):
        try:
            # url = f"https://cxd.cisco.com/home/{username}_{oic_file}"
            url = f"https://cxd-v1.cisco.com/home/{username}_{os.path.basename(oic_file)}"
            headers = {
                'Content-Type': 'application/gzip'
            }
            with open(oic_file, 'rb') as f:

                response = requests.put(url, headers=headers, auth=(cspc_license, cxd_token), data=f)
                response.raise_for_status()
                if response.ok:
                    print(
                        f'UPLOAD WAS SUCCESSFULLL (STATUS CODE: {response.status_code})\nPlease check url below:\nhttps://tac-highway.cisco.com/api/files/{cspc_license}/')
                    os.remove(oic_file)

                    return response.status_code, f"https://tac-highway.cisco.com/api/files/{cspc_license}/"

        except Exception as e:
            print(f"error : {e}")
            return e, ""

    def task(self, username, client, secret, oic_file, cspc_id):
        """
        

        Replace this docstring with your documentation.

        This task is run by the bdblib library, full doc and examples at:
        https://scripts.cisco.com/doc/
        Browse more examples in BDB starting with "bdblib_":
        https://scripts.cisco.com/ui/browse/used/0/bdblib_

        For more information on Python Type Hints see the doc and examples at:
        https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html
        """

        token = self.tori_token(client, secret)
        upload_token = self.cxd_token(token, cspc_id)
        status_code, upload_url = self.upload_oic(username, upload_token, cspc_id, oic_file)

        return status_code, upload_url


class OICAPIClient:
    def __init__(self):
        pass

    # Acquire Access Token, using CLIENT_ID and CLIENT_SECRET and CCO credentials
    def request_access_token(self, cec_username, cec_password, client_id, client_secret):
        
        if not cec_username.endswith('@cisco.com'):
            cec_username += "@cisco.com"

        try:
            
            url = f"https://cloudsso.cisco.com/as/token.oauth2?grant_type=password&client_id={client_id}&client_secret={client_secret}&username={cec_username}&password={cec_password}"

            payload={}
            headers = {
            'Cache-Control': 'no-cache',
            # 'Cookie': 'PF=upiz0Lvf6ouZzJc9fN3sXT'
            }

            print("Requesting Access Token")
            response = requests.request("POST", url, headers=headers, data=payload)
            print("Response :",response.text)
            response_dict = json.loads(response.text)
            access_token = response_dict['access_token']
            print("Retrieved OIC Access Token :", access_token)

            return access_token
        
        except Exception as err:
            print("[ERROR] :",err)
            return None
        
    def request_upload_token(self, access_token, collector_id):
        try:
            url = f"https://api.cisco.com/oiccollectorless/v1/token/{collector_id}"

            payload = {}
            headers = {
            'Authorization': "Bearer %s" %access_token
            }
            
            print("Requesting upload token:",headers)
            response = requests.request("POST", url, headers=headers, data=payload)
            print("Response:",response)
            response_dict = json.loads(response.text)
            upload_token = response_dict['token']
            print("Retrieved OIC Upload Token :", upload_token)
            
            return upload_token
        
        except Exception as err:
            print("[ERROR] :",err)
            return None
        
    def upload_file_to_cxd(self, upload_token, collector_id, filename, dir_path = "./"):
        try:
            usrPass = "%s:%s" % (collector_id, upload_token)
            b64Val = b64encode(bytes(f'{usrPass}',encoding='ascii')).decode('ascii')

            url = f'https://cxd.cisco.com/home/{filename}'
            headers = {
                'Authorization': f'Basic {b64Val}'
            }

            if not dir_path.endswith('/'):
                dir_path += '/'
            
            with open(filename, 'rb') as data:
                response = requests.request("PUT", url, headers=headers, data=data)

            response_text = response.text
            print("Uploading file",filename,"to OIC, Response :", response_text)
            
            return response_text
        
        except Exception as err:
            print("[ERROR] :",err)
            return None
        
    def get_upload_status(self, access_token, collector_id):
        try:
            url = f"https://api.cisco.com/oiccollectorless/v1/status/{collector_id}"

            payload = {}
            headers = {
            'Authorization': "Bearer %s" %access_token
            }

            response = requests.request("GET", url, headers=headers, data=payload)

            response_dict = json.loads(response.text)
            upload_state = response_dict['data'][0]['state']
            upload_filename = response_dict['data'][0]['filename']
            print("OIC Uploading", upload_filename, ", State :", upload_state)
            
            return upload_state, upload_filename
        
        except Exception as err:
            print("[ERROR] :",err)
            return None
        