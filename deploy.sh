#!/usr/bin/env bash
# Deploy snapshots of the GoodNews project
#
# For each server:
# 1. Copy a snapshot to the server's `releases' directory.
# 2. Link the snapshot in the `current' release directory.
# 3. Install unmet dependencies (i.e. `pip', `apt').
# 4. Apply configuration via puppet manifests.
########################################################

# Set up the environment.

set -o errexit    # If an error occurs during setup, exit.

if [[ -v DEBUG ]] # Enable debugging output.
then
  exec {BASH_XTRACEFD}>&2
  set -o verbose -o xtrace
fi

declare -A TARGETS
TARGETS=(
  [web-01]=35.196.167.155
  [web-02]=34.73.252.236
)
set -- "${!TARGETS[@]}"

PROJECT="$(CDPATH='' cd -- "${BASH_SOURCE[0]%/*}" && pwd -P)"
RELEASE="${PROJECT##*/}-$(date --utc '+%Y%m%d%H%M%S')"
LOGFILE="${PROJECT}/deploy.log"
EXCLUDE="${PROJECT}/deploy.ignore"
DESTDIR="/data/releases/${RELEASE}"

WORKDIR="$(mktemp -d --tmpdir "${BASH_SOURCE[0]##*/}-XXXXX")"
trap 'rm -rf -- "${WORKDIR}"' EXIT

set +o errexit    # Setup complete.

# Define a function to upload a release to a single host
# usage: deploy::upload USER@HOST
deploy::upload()
{
  ssh -t -- "$1"
  rsync -az --stats --exclude-from="${EXCLUDE}" -- "${PROJECT}/" "$1:${DESTDIR}"
} << EOF
set -o errexit
sudo --non-interactive mkdir -p /data/releases
sudo --non-interactive chown -R '${1%%@*}:${1%%@*}' /data
exit
EOF

# Define a function to install a release on a single host
# usage: deploy::install USER@HOST
deploy::install()
{
  ssh -t -- "$1"
} << EOF
set -o errexit
sudo --non-interactive chown -R '${1%%@*}:${1%%@*}' '${DESTDIR/\'/\'\\\'\'}'
rm -fr /data/current
ln -s -- '${DESTDIR/\'/\'\\\'\'}' /data/current
find /data/current/manifests -maxdepth 1 -name '*.pp' -type f -execdir \
  sudo --non-interactive puppet apply -- '{}' ';'
exit
EOF

# Upload to hosts in parallel with a separate log for each
echo 'Uploading...'
for (( INDEX = 1; INDEX <= $#; ++INDEX ))
do
  # shellcheck disable=SC2183
  { printf '%s: %s [%s]\n' "$(date '+%c')" "${!INDEX}" "${TARGETS[${!INDEX}]}"
    (deploy::upload "ubuntu@${TARGETS[${!INDEX}]}") &
  } &> "${WORKDIR}/$(printf "%0${##}d" "${INDEX}").0.log"
done
wait
cat -- "${WORKDIR}"/*.0.log

# Install on hosts in parallel with a separate log for each
echo 'Installing...'
for (( INDEX = 1; INDEX <= $#; ++INDEX ))
do
  # shellcheck disable=SC2183
  { printf '%s: %s [%s]\n' "$(date '+%c')" "${!INDEX}" "${TARGETS[${!INDEX}]}"
    (deploy::install "ubuntu@${TARGETS[${!INDEX}]}") &
  } &> "${WORKDIR}/$(printf "%0${##}d" "${INDEX}").1.log"
done
wait
cat -- "${WORKDIR}"/*.1.log

# Append to master log
cat -- "${WORKDIR}"/*.log >> "${LOGFILE}"
