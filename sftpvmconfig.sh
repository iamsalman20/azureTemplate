#!/usr/bin/env bash
DNS="https://127.0.0.1/backend"
wget "https://raw.githubusercontent.com/iamsalman20/azureTemplate/master/users.json"
CONFIG_FILE="users.json"
while getopts ":P:K:S:" opt; do
    case "${opt}" in
        P)
            admin_password=${OPTARG}
            ;;
        K)
            blob_account_key=${OPTARG}
            ;;
        S)
            storage_account=${OPTARG}
            ;;
        \? )
      	    echo "Invalid option: $OPTARG" 1>&2
            ;;
    esac
done
shift $((OPTIND-1))

echo "${admin_password}" >> /home/ubuntu/scriptoutput.txt
echo "${blob_account_key}" >> /home/ubuntu/scriptoutput.txt
echo "${storage_account}" >> /home/ubuntu/scriptoutput.txt

TOKEN=$(curl -X POST "${DNS}/login" -H 'Content-Type: application/json' -d '{ "username": "admin", "password": "'${admin_password}'" }' -k)
curl -X PUT "${DNS}/api/configuration" -H 'Content-Type: application/json'  -H "authorization: Bearer ${TOKEN}" -d '{ "usesAzureStorageKey": true, "azureStorageKey": "'${blob_account_key}'", "azureStorageName": "'${storage_account}'" }' -k



ALL_USERS=$(curl -X GET "${DNS}/api/users" -H 'Content-Type: application/json' -H "authorization: Bearer ${TOKEN}" -k)

jq -r -c '.users[]' "${CONFIG_FILE}" | while read RAW_USER; do
    USER_PROPS=$(echo ${RAW_USER} | tr -d '\r')
    USER=$(jq -n $USER_PROPS | jq -r .name)
    BUCKET_NAME=$(jq -n $USER_PROPS | jq -r .bucket_name)
    if [[ ! $(echo $ALL_USERS | jq -r --arg USER "$USER" '.users[]  | select(.username==$USER)') ]]; then
        echo "creating new user: ${USER}" >> /home/ubuntu/scriptoutput.txt
#        SSH_KEY=$(curl -X GET "${DNS}/api/keypair/generate" \
#            -H 'Content-Type: application/json' \
#            -H "authorization: Bearer ${TOKEN}" \
#            -k)

 #       PUB_KEY=$(echo "${SSH_KEY}" | jq -r .publicKey)
 #       PRI_KEY=$(echo "${SSH_KEY}" | jq -r .privateKey)

  #      echo "${PUB_KEY}" > "${USER}.key.pub"
  #      echo "${PRI_KEY}" > "${USER}.key"

  #      az keyvault secret set --name "vm${postfix}${USER}pub" --vault-name "${KEYVAULT_NAME}" --file "${USER}.key.pub"
  #      az keyvault secret set --name "vm${postfix}${USER}pri" --vault-name "${KEYVAULT_NAME}" --file "${USER}.key"

   #     rm "${USER}.key.pub"
    #    rm "${USER}.key"
            
        # TODO put in function
    #    USER_PASSWORD=$(date +%s | sha256sum | base64 | head -c 32 ; echo)
    #    az keyvault secret set --name "vm${postfix}${USER}pwd" --vault-name ${KEYVAULT_NAME} --value ${USER_PASSWORD}

 #       curl -X POST "${DNS}/api/users" \
#            -H 'Content-Type: application/json' \
  #          -H "authorization: Bearer ${TOKEN}" \
  #          -d '{"username":"'${USER}'","password":"'${USER_PASSWORD}'","enableUploadDir":true,"bucketName":"'${BUCKET_NAME}'","path":"'${USER}'","pubSsh":"'"${PUB_KEY}"'"}' \
  #          -k
    fi
done
