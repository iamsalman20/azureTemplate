import os
import requests
import optparse
import json
import string
import random
import subprocess
import urllib2


parser = optparse.OptionParser()
parser.add_option('-p', '--passwd', action="store", dest="passwd", help="vmadminpasswd", default="spam")
parser.add_option('-c', '--clientId', action="store", dest="clientId", help="SP_clientId", default="spam")
parser.add_option('-s', '--clientSec', action="store", dest="clientSec", help="SP_clientSec", default="spam")
parser.add_option('-t', '--tenantId', action="store", dest="tenantId", help="tenantId", default="spam")
parser.add_option('-n', '--storageName', action="store", dest="storageName", help="backendstorageName", default="spam")
parser.add_option('-k', '--storageKey', action="store", dest="storageKey", help="backendstorageKey", default="spam")
    
options, args = parser.parse_args()

def passwd_generator(size, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size)) 
	
   
DNS = "https://127.0.0.1/backend"
URL_login = DNS + "/login"
URL_sshGen = DNS + "/api/keypair/generate"
URL_users = DNS + "/api/users"
URL_config = DNS + "/api/configuration"
login_data = {"username": "admin", "password": options.passwd }
config_data = {"azureStorageName": options.storageName, "azureStorageKey": options.storageKey, "usesAzureStorageKey": True }
existingUserFileName = 'exisUsers.json'
newUsersFile = 'users.json'

response = urllib2.urlopen('https://raw.githubusercontent.com/iamsalman20/azureTemplate/master/users.json')
users = open( 'newUsersFile', 'w' )
users.write( response.read() )
users.close()

TOKEN = requests.post(URL_login, headers={"Content-Type":"application/json"}, json=login_data, verify=False)

requests.put(URL_config, headers={"Content-Type":"application/json", "authorization": "Bearer " + TOKEN.text}, json=config_data, verify=False)
  
existing_users = requests.get(URL_users, headers={"Content-Type":"application/json", "authorization": "Bearer " + TOKEN.text}, verify=False)
use = open( existingUserFileName, 'w' )
use.write( existing_users.text )
use.close()
exisUsersList = []

with open(existingUserFileName) as json_users:
    exiusers = json.load(json_users)
    for u in exiusers['users']:
    	userName= u['username']
    	exisUsersList.append(userName)
    	
if os.path.exists(existingUserFileName):
  os.remove(existingUserFileName)

logincmd = ['az', 'login', '--service-principal','--username', options.clientId, '--password', options.clientSec, '--tenant', options.tenantId]
subprocess.call(logincmd)


with open('newUsersFile') as json_file:
    users = json.load(json_file)
    for p in users['users']:
    	userName= p['name']
    	if userName in exisUsersList :
    		print("User Already exists")
    	else:
    		print("Creating User...")
    		bucketName = p['bucket_name']
        	sshKeys = requests.get(URL_sshGen, headers={"Content-Type":"application/json", "authorization": "Bearer " + TOKEN.text}, verify=False)
		jsonKeys = json.loads(sshKeys.text)
		pubKey = jsonKeys['publicKey']
		priKey = jsonKeys['privateKey']
		secpubKey = userName + 'pub'
		secpriKey = userName + 'pri'
		keyvaultcmd = ['az', 'keyvault', 'secret', 'set', '--name', secpubKey, "--vault-name", 'uatsftp-keyvault', '--value', pubKey]
		subprocess.call(keyvaultcmd)
		keyvaultcmd = ['az', 'keyvault', 'secret', 'set', '--name', secpriKey, "--vault-name", 'uatsftp-keyvault', '--value', priKey]
		subprocess.call(keyvaultcmd)
		userPass = passwd_generator(32)
		secPwdKey = userName + 'pwd'
		keyvaultcmd = ['az', 'keyvault', 'secret', 'set', '--name', secPwdKey, "--vault-name", 'uatsftp-keyvault', '--value', userPass]
		subprocess.call(keyvaultcmd)
		user_data = {"username": userName, "password": userPass, "enableUploadDir": True, "bucketName": bucketName, "path": userName, "pubSsh": pubKey }
		requests.post(URL_users, headers={"Content-Type":"application/json", "authorization": "Bearer " + TOKEN.text}, json=user_data, verify=False)

