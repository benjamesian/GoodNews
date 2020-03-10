#!/usr/bin/env bash
# Deploy snapshots of the GoodNews project
#
# For each server:
# 1. Copy a snapshot to the server's `releases' directory.
# 2. Link the snapshot in the `current' release directory.
# 3. Install unmet dependencies (i.e. `pip', `apt').
# 4. Apply configuration via puppet manifests.
########################################################

if [[ -v DEBUG ]]
then
  set -o verbose -o xtrace
fi

set -o errexit
declare -A SERVERS

PROJECT="$(CDPATH='' cd -- "${BASH_SOURCE[0]%/*}" && pwd -P)"
SERVERS=(
  ['web-01']='35.196.167.155'
  ['web-02']='34.73.252.236'
)
LOGFILE="${PROJECT}/deploy.log"
RELEASE="GoodNews-$(date --utc '+%Y%m%d%H%M%S')"
DESTDIR="/data/releases/${RELEASE}"
WORKDIR="$(mktemp -d --tmpdir "${BASH_SOURCE[0]##*/}-XXXXXX")"

trap 'rm -rf -- "${WORKDIR}"' EXIT
set +o errexit

parallel -i rsync -ahz --info=flist1,progress2,stats2 --log-file="${LOGFILE}" \
  "${PROJECT}/" "ubuntu@{}:${DESTDIR}" -- "${SERVERS[@]}"

for ID in "${!SERVERS[@]}"
do
  mkfifo -- "${WORKDIR}/i${ID}"
  (< "${WORKDIR}/i${ID}" ssh -tt "ubuntu@${SERVERS[${ID}]}"
  )> "${WORKDIR}/o${ID}" &
done

tee -a "${WORKDIR}"/i* << EOF
set -e
mkdir -p /data/current /data/releases
cd /data
if test -d /data/releases/${RELEASE}
then
  cd current
  ln -snf ../releases/${RELEASE}/*/ .
  cd manifests
  parallel sudo --non-interactive puppet apply -- *.pp
fi
exit
EOF

wait
cat "${WORKDIR}"/o*
