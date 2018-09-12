#!/bin/bash
# An archive name can be specified on the command line,
# if not, a default name will be generated by appending
# date and time to "qgis-repo-full-backup_"
set -e

QGIS_BASE=qgisrepo_base_1
QGIS_ARCHIVE=$1

if [ -z "$QGIS_ARCHIVE" ]; then
  QGIS_ARCHIVE=qgis-repo-full-backup_$(date +%Y%m%d-%H%M%S).tgz
fi

ARCHIVE_DIR=$HOME/qgis-repo-backup
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

mkdir -p $ARCHIVE_DIR

echo -e "\nApplying environment..."
. ${SCRIPT_DIR}/docker-compose.env

echo -e "\nAttempting to back up ${QGIS_BASE}'s dirs with data to \n$ARCHIVE_DIR/${QGIS_ARCHIVE}..."
docker exec $QGIS_BASE \
tar -C / -cf - \
  home/${SSH_USER} \
  etc/nginx \
  etc/letsencrypt \
  etc/ssh \
  etc/ssl/nginx \
  etc/supervisor \
  etc/uwsgi \
  opt \
  usr/lib/nginx \
  var/www \
| gzip > $ARCHIVE_DIR/$QGIS_ARCHIVE

if [ ! -f $ARCHIVE_DIR/$QGIS_ARCHIVE ]; then
  echo -e "\n... backup failed"
  exit 1
fi

pushd  $ARCHIVE_DIR
  echo -e "\nPruning any archives older than most recent 7"
  ls -tp | grep -v '/$' | tail -n +8 | xargs -I {} rm -- {}
popd

if [ ! -f $ARCHIVE_DIR/$QGIS_ARCHIVE ]; then
  echo -e "\n... backup failed (pruning may have deleted most recent backup)"
  exit 1
fi
