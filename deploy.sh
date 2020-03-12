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
WORKDIR="$(mktemp -d --tmpdir "${BASH_SOURCE[0]##*/}-XXXXX")"
trap 'rm -rf -- "${WORKDIR}"' EXIT

set +o errexit    # Setup complete.

# Define a function to make a local archive of a release
# usage: deploy::archive
deploy::archive()
{
  tee >(cat - >&2) | bash
} << EOF
rsync -a --exclude-from="${EXCLUDE}" -- "${PROJECT}/" "${WORKDIR}/${RELEASE}"
tar -czf "${WORKDIR}/${RELEASE}.tar.gz" -C "${WORKDIR}" -- "${RELEASE}"
EOF

# Define a function to upload a release to a single host
# usage: deploy::upload USER@HOST
deploy::upload()
{
  tee >(cat - >&2) | ssh -T -- "ubuntu@$1"
  scp -- "${WORKDIR}/${RELEASE}.tar.gz" "ubuntu@$1:/data/releases"
} << EOF
sudo --non-interactive mkdir -p /data/current /data/releases
sudo --non-interactive chown -R ubuntu:ubuntu /data
exit
EOF

# Define a function to install a release on a single host
# usage: deploy::install USER@HOST
deploy::install()
{
  tee >(cat - >&2) | ssh -T -- "ubuntu@$1"
} << EOF
cd /data/releases
tar -xzf '${RELEASE/\'/\'\\\'\'}.tar.gz'
sudo --non-interactive chown -R ubuntu:ubuntu '${RELEASE/\'/\'\\\'\'}'
cd /data/current
rm -fr *
ln -s '/data/releases/${RELEASE/\'/\'\\\'\'}'/* .
find /data/current/manifests -maxdepth 1 -name '*.pp' -type f -execdir \
  sudo --non-interactive puppet apply -- '{}' ';'
exit
EOF

# Locally archive a current copy of the project repo
# shellcheck disable=SC2154
deploy::archive &> "${WORKDIR}/0.output"
cat -- "${WORKDIR}"/0.output

# Upload to hosts in parallel with a separate log for each
printf 'Uploading to:\n'
for (( INDEX = 1; INDEX <= $#; ++INDEX ))
do
  printf '%s\n' "${!INDEX}"
  { printf '%s: %s\n' "$(date '+%c')" "${!INDEX}"
    (deploy::upload "${!INDEX}") &
  } &> "${WORKDIR}/1.$(printf "%0${##}d" "${INDEX}").output"
done
wait
cat -- "${WORKDIR}"/1.*.output

# Install on hosts in parallel with a separate log for each
printf 'Installing on:\n'
for (( INDEX = 1; INDEX <= $#; ++INDEX ))
do
  printf '%s\n' "${!INDEX}"
  { printf '%s: %s\n' "$(date '+%c')" "${!INDEX}"
    (deploy::install "${!INDEX}") &
  } &> "${WORKDIR}/2.$(printf "%0${##}d" "${INDEX}").output"
done
wait
cat -- "${WORKDIR}"/2.*.output

# Append to master log
cat -- "${WORKDIR}"/*.output >> "${LOGFILE}"
