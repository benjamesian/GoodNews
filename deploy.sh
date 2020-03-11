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

if ! (( $# ))
then
  set -- '35.196.167.155' '34.73.252.236'
fi

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
  ssh -- "$1"
  rsync -az --stats --exclude-from="${EXCLUDE}" -- "${PROJECT}/" "$1:${DESTDIR}"
} << EOF
sudo --non-interactive mkdir -p /data/releases
sudo --non-interactive chown -R '${1%%@*}:${1%%@*}' /data
exit
EOF

# Define a function to install a release on a single host
# usage: deploy::install USER@HOST
deploy::install()
{
  ssh -- "$1"
} << EOF
sudo --non-interactive chown -R '${1%%@*}:${1%%@*}' '${DESTDIR/\'/\'\\\'\'}'
rm -fr /data/current
ln -s -- '${DESTDIR/\'/\'\\\'\'}' /data/current
find /data/current/manifests -maxdepth 1 -name '*.pp' -type f -execdir \
  sudo --non-interactive puppet apply -- '{}' ';'
exit
EOF

# Upload to hosts in parallel with a separate log for each
printf '# Uploading to:\n'
for (( INDEX = 1; INDEX <= $#; ++INDEX ))
do
  printf '%s\n' "${!INDEX}"
  { printf '%s: %s\n' "$(date '+%c')" "${!INDEX}"
    (deploy::upload "ubuntu@${!INDEX}") &
  } &> "${WORKDIR}/$(printf "%0${##}d" "${INDEX}").0.output"
done
wait
cat -- "${WORKDIR}"/*.0.output

# Install on hosts in parallel with a separate log for each
printf '# Installing on:\n'
for (( INDEX = 1; INDEX <= $#; ++INDEX ))
do
  printf '%s\n' "${!INDEX}"
  { printf '%s: %s\n' "$(date '+%c')" "${!INDEX}"
    (deploy::install "ubuntu@${!INDEX}") &
  } &> "${WORKDIR}/$(printf "%0${##}d" "${INDEX}").1.output"
done
wait
cat -- "${WORKDIR}"/*.1.output

# Append to master log
cat -- "${WORKDIR}"/*.output >> "${LOGFILE}"
