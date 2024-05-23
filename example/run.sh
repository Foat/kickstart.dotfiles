#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

# I prefer to store all secrets on a self-hosted Bitwarden server.
# Below is an example of how to get environment variables from the Bitwarden CLI.
# For the ability to work with JSON (Bitwarden CLI output), you need to have the `jq` CLI installed on your system.

# set -eo pipefail
# if [[ -z "${BW_SESSION}" ]]; then
#   echo "Logging in to Bitwarden..."
#   BW_SESSION=$(bw login --raw)
#
#   # Check if the login was successful
#   if [ $? -ne 0 ]; then
#       echo "Login failed!"
#       exit 1
#   fi
# fi
# set -euo pipefail
#
# echo "Getting env vars from Bitwarden..."
# bw sync
# ITEM_INFO=$(bw get item my-secret-item)
# export TEMP_ITEM_PASSWORD="$(echo $ITEM_INFO | jq -r '.login.password')"
#
# get_field() {
#     local FIELD_ID=$1
#     local FIELD=$(echo $ITEM_INFO | jq -r ".fields | .[] | select(.name == \"$FIELD_ID\") | .value")
#     echo $FIELD
# }
#
# export TEMP_ITEM_FIELD="$(get_field 'field')"

# Here is an example of how to work with multiline variables.
# We need to encode them with base64 so that we can store them as env vars.
export TEMP_RCLONE_HOME=$(echo "Multiline start
Some multiline content
Multiline end" | base64)

export TEMP_EXAMPLE_ENV="My example env var"

printenv | grep "^TEMP_"

echo "Running setup..."
python3 kdf.py "$@"
