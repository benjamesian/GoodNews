#!/usr/bin/env bash
# Deploy snapshots of the GoodNews project
#
# For each server:
# 1. Copy a snapshot to the server's `releases' directory.
# 2. Link the snapshot in the `current' release directory.
# 4. Apply configuration via puppet manifests.
########################################################

# Set up the environment.

set -o errexit      # If an error occurs, exit.

if [[ -v DEBUG ]]   # Enable debugging output if `DEBUG' is defined.
then
  exec {BASH_XTRACEFD}>&2
  set -o verbose -o xtrace
fi
if ! (( $# ))       # Set remote targets if none were supplied as arguments.
then
  set -- '35.196.167.155' '34.73.252.236'
fi
PROJECT="$(CDPATH='' cd -- "${BASH_SOURCE[0]%/*}" && pwd -P)"
RELEASE="${PROJECT##*/}-$(date --utc '+%Y%m%d%H%M%S')"
LOGFILE="${PROJECT}/deploy.log"
EXCLUDE="${PROJECT}/deploy.ignore"
WORKDIR="$(mktemp -d --tmpdir "${BASH_SOURCE[0]##*/}-XXXXX")"
trap 'rm -rf -- "${WORKDIR}"' EXIT
cd -- "${WORKDIR}"  # Enter temporary working directory

set +o errexit      # Environment setup complete.

# Define a function to make a local archive of a release
# usage: deploy::archive
deploy::archive()
{
  rsync --archive --exclude-from="${EXCLUDE}" -- "${PROJECT}/" "${RELEASE}"
  gpg --decrypt "${PROJECT}/credentials.tar.gz.gpg" | tar -xzf - -C "${RELEASE}"
  tar -czf "${RELEASE}.tar.gz" -- "${RELEASE}"
}

# Define a function to upload a release to a single host
# usage: deploy::upload HOST
deploy::upload()
{
  ssh -T -- "ubuntu@$1"
  scp -- "${RELEASE}.tar.gz" "ubuntu@$1:/data/releases/"
} << EOF
sudo --non-interactive mkdir -pm 0755 /data
sudo --non-interactive mkdir -pm 0755 /data/releases
sudo --non-interactive chown -hR ubuntu:ubuntu /data
exit
EOF

# Define a function to install a release on a single host
# usage: deploy::install HOST
deploy::install()
{
  ssh -T -- "ubuntu@$1"
} << EOF
cd /data/releases
tar -xzf '${RELEASE/\'/\'\\\'\'}.tar.gz'
sudo --non-interactive chown -R ubuntu:ubuntu -- '${RELEASE/\'/\'\\\'\'}'
cp -LpR -- /data/current '${RELEASE/\'/\'\\\'\'}.old'
rm -fr /data/current
tar -czf '${RELEASE/\'/\'\\\'\'}.old.tar.gz' -- '${RELEASE/\'/\'\\\'\'}.old'
rm -fr -- '${RELEASE/\'/\'\\\'\'}.old'
mkdir -pm 0755 /data/current
cd /data/current
ln -s '../releases/${RELEASE/\'/\'\\\'\'}'/* .
printf '%s\0' manifests/*.pp |
  xargs -n 1 --null --verbose sudo --non-interactive puppet apply
exit
EOF

# Locally archive a current copy of the project repo
echo 'Creating local archive'
deploy::archive | tee -a "${LOGFILE}"

# Upload to hosts in parallel with a separate log for each
echo
for (( INDEX = 1; INDEX <= $#; ++INDEX ))
do
  printf 'Uploading archive to %s\n' "${!INDEX}"
  { printf '%s: %s\n' "$(date '+%c')" "${!INDEX}"
    (deploy::upload "${!INDEX}") &
  } &> "$(printf "%0${##}d" "${INDEX}").logfile"
done
wait
cat -- *.logfile | tee -a "${LOGFILE}"

# Install on hosts in parallel with a separate log for each
echo
for (( INDEX = 1; INDEX <= $#; ++INDEX ))
do
  printf 'Installing release on %s\n' "${!INDEX}"
  { printf '%s: %s\n' "$(date '+%c')" "${!INDEX}"
    (deploy::install "${!INDEX}") &
  } &> "$(printf "%0${##}d" "${INDEX}").logfile"
done
wait
cat -- *.logfile | tee -a "${LOGFILE}"
