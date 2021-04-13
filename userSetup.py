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
logFile = 'userSetupLogs.txt'
logsFolder = '/home/ubuntu/installationLogs'

if not os.path.exists(logsFolder):
    os.makedirs(logsFolder)

logs = open( os.path.join(logsFolder, logFile), 'w' )

TOKEN = requests.post(URL_login, headers={"Content-Type":"application/json"}, json=login_data, verify=False)
logs.write( 'Successfully Logged in with Token: ' + TOKEN.text)
logs.write( '\nUpdating Storage Account Configs\n' )

requests.put(URL_config, headers={"Content-Type":"application/json", "authorization": "Bearer " + TOKEN.text}, json=config_data, verify=False)
  
existing_users = requests.get(URL_users, headers={"Content-Type":"application/json", "authorization": "Bearer " + TOKEN.text}, verify=False)

use = open( existingUserFileName, 'w' )
use.write( existing_users.text )
use.close()
exisUsersList = []

logs.write( 'Currently configured users: \n')
with open(existingUserFileName) as json_users:
    exiusers = json.load(json_users)
    for u in exiusers['users']:
    	userName= u['username']
    	exisUsersList.append(userName)
    	logs.write(userName + '\n')
    	
if os.path.exists(existingUserFileName):
  os.remove(existingUserFileName)

logs.write( 'Logging into azure using service principal \n' )
logincmd = ['az', 'login', '--service-principal','--username', options.clientId, '--password', options.clientSec, '--tenant', options.tenantId]
subprocess.call(logincmd)


with open(newUsersFile) as json_file:
    users = json.load(json_file)
    for p in users['users']:
    	userName= p['name']
    	if userName in exisUsersList :
    		logs.write( 'User ' + userName + ' already exists \n' )
    	else:
    		bucketName = p['bucket_name']
    		logs.write( 'Generating SSH Keys for user: ' + userName + '\n' )
        	sshKeys = requests.get(URL_sshGen, headers={"Content-Type":"application/json", "authorization": "Bearer " + TOKEN.text}, verify=False)
		jsonKeys = json.loads(sshKeys.text)
		pubKey = jsonKeys['publicKey']
		priKey = jsonKeys['privateKey']
		secpubKey = userName + 'pub'
		secpriKey = userName + 'pri'
		logs.write( 'Saving Pub and pri keys into keyvault for user: ' + userName + '\n' )
		keyvaultcmd = ['az', 'keyvault', 'secret', 'set', '--name', secpubKey, "--vault-name", 'uatsftp-keyvault', '--value', pubKey]
		subprocess.call(keyvaultcmd)
		keyvaultcmd = ['az', 'keyvault', 'secret', 'set', '--name', secpriKey, "--vault-name", 'uatsftp-keyvault', '--value', priKey]
		subprocess.call(keyvaultcmd)
		userPass = passwd_generator(32)
		secPwdKey = userName + 'pwd'
		logs.write( 'Saving SFTP Passwd into Keyvault for user: ' + userName + '\n' )
		keyvaultcmd = ['az', 'keyvault', 'secret', 'set', '--name', secPwdKey, "--vault-name", 'uatsftp-keyvault', '--value', userPass]
		subprocess.call(keyvaultcmd)
		user_data = {"username": userName, "password": userPass, "enableUploadDir": True, "bucketName": bucketName, "path": userName, "pubSsh": pubKey }
		logs.write( 'Creating User... ' + userName + '\n' )
		requests.post(URL_users, headers={"Content-Type":"application/json", "authorization": "Bearer " + TOKEN.text}, json=user_data, verify=False)
logs.close()
