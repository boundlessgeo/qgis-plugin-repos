#!/bin/bash


if [ ! -d ~/supervisor_logs ]; then
    mkdir ~/supervisor_logs
    chmod 777 ~/supervisor_logs
fi

if [ -z "${SSH_CONFIG_NAME+x}" ]; then
  echo "SSH_CONFIG_NAME env var is not defined"
  exit 1
fi

echo -e "\nApplying environment..."
. docker-compose.env

echo -e "\nAttempting to shutdown any existing containers/volumes..."
docker-compose down -v

set -e

echo -e "\nRunning detached containers..."
docker-compose up -d

# CONTAINER_IP=`docker inspect --format '{{ .NetworkSettings.Networks.qgisrepo_default.IPAddress }}' qgisrepo_base_1`

# sed -i -e "s/172.[0-9]\+.0../${CONTAINER_IP}/g" ~/.ssh/config
# sudo sed -i -e "s/172.[0-9]\+.0../${CONTAINER_IP}/g" /etc/hosts

if [ "$1" == "load" ]; then
  echo -e "\nRemotely loading test plugins..."
  sleep 5
  ./www-data/resources/plugins-xml/scripts/load-test-plugins-remote.sh "${SSH_CONFIG_NAME}"
fi
