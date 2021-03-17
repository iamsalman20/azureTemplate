#!/usr/bin/env bash
DNS="https://127.0.0.1/backend"
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
