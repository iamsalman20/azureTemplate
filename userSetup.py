import os
import requests
import optparse
import json
import string
import random

parser = optparse.OptionParser()
parser.add_option('-p', '--passwd', action="store", dest="passwd", help="vmadminpasswd", default="spam")
    
options, args = parser.parse_args()

def passwd_generator(size, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size)) 
	
   
DNS = "https://127.0.0.1/backend"
URL_login = DNS + "/login"
URL_sshGen = DNS + "/api/keypair/generate"
URL_users = DNS + "/api/users"
login_data = {"username": "admin", "password": options.passwd }
USER = 'salman'
dirName = 'sshKeys'
passFile = 'passwds.txt'
existingUserFileName = 'exisUsers.json'

TOKEN = requests.post(URL_login, headers={"Content-Type":"application/json"}, json=login_data, verify=False)
if not os.path.exists(dirName):
    os.makedirs(dirName)
    
if os.path.exists(dirName + '/' + passFile):
  os.remove(dirName + '/' + passFile)
  
  
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
  
with open('users.json') as json_file:
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
		pubFileName = os.path.join(dirName, userName + '.key.pub')
		pub = open( pubFileName, 'w' )
		pub.write( pubKey  )
		pub.close()
		priFileName = os.path.join(dirName, userName + '.key')
		pri = open( priFileName, 'w' )
		pri.write( priKey  )
		pri.close()
		userPass = passwd_generator(32)
		passwdFileName = os.path.join(dirName, passFile)
		pas = open( passwdFileName, 'a' )
		pas.write( userName + ': ' + userPass + '\n' )
		pas.close()
		user_data = {"username": userName, "password": userPass, "enableUploadDir": True, "bucketName": bucketName, "path": userName, "pubSsh": pubKey }
		requests.post(URL_users, headers={"Content-Type":"application/json", "authorization": "Bearer " + TOKEN.text}, json=user_data, verify=False)

