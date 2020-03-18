#!/usr/bin/env bash
# Deploy snapshots of the GoodNews project
#
# For each server:
# 1. Copy a snapshot to the server's `releases' directory.
# 2. Link the snapshot in the `current' release directory.
# 4. Apply configuration via puppet manifests.
########################################################

# If `DEBUG' is defined, enable debugging output
if [[ -v DEBUG ]]
then
  exec {BASH_XTRACEFD}>&2
  set -o verbose -o xtrace
fi

# Initialize environment. If an error occurs, exit
set -o errexit

# Specify remote targets
TARGETS=(
  #35.196.167.155
  34.73.252.236
)

# Configure global parameters
PROJECT=$(CDPATH='' cd -- "${BASH_SOURCE[0]%/*}" && pwd -P)
LOGFILE=${PROJECT}/deploy.log
EXCLUDE=${PROJECT}/deploy.ignore
RELEASE=${PROJECT##*/}-$(date --utc '+%Y%m%d%H%M%S')
if ! (( ${ARCHIVE_MAX-0} > 0 )) 2> /dev/null
then
  ARCHIVE_MAX=-1
fi

# Create a temporary work directory
WORKDIR=$(mktemp -d --tmpdir "${BASH_SOURCE[0]##*/}-XXXXX")

# Remove temporary files upon exit
trap 'rm -rf -- "${WORKDIR}"' EXIT

# Enter temporary working directory
cd -- "${WORKDIR}"

# Initialization complete
set +o errexit

# Makes a local archive of a release
# usage: deploy::archive
deploy::archive()
{
  local -
  set -o verbose
  rsync --archive --exclude-from="${EXCLUDE}" -- "${PROJECT}/" "${RELEASE}"
  gpg --decrypt "${PROJECT}/credentials.tar.gz.gpg" | tar -xzf - -C "${RELEASE}"
  tar -czf "${RELEASE}.tar.gz" -- "${RELEASE}"
}

# Prepares a host recieve a release
# usage: deploy::prepare HOST
deploy::prepare()
{
  tee >(cat >&2) | ssh -T -- "ubuntu@$1"
} << EOF
sudo --non-interactive mkdir -pm 0755 /data
sudo --non-interactive mkdir -pm 0755 /data/releases
sudo --non-interactive chown -hR ubuntu:ubuntu /data
exit
EOF

# Uploads an archived release to a host
# usage: deploy::release HOST
deploy::release()
{
  local -
  set -o verbose
  scp -- "${RELEASE}.tar.gz" "ubuntu@$1:/data/releases/"
}

# Installs an uploaded release on host
# usage: deploy::install HOST
deploy::install()
{
  tee >(cat >&2) | ssh -T -- "ubuntu@$1"
} << EOF
if cd /data/releases
then
  find -H . -maxdepth 2 -type f -samefile ../current/AUTHORS -printf '%h\\0' |
    if IFS='' read -r -d '' REPLY
    then
      mv -- "\${REPLY}" "\${REPLY}.backup"
      tar -czf "\${REPLY}.backup.tar.gz" -- "\${REPLY}.backup"
      rm -fr "\${REPLY}.backup"
    fi
  tar -xzf '${RELEASE//\'/\'\\\'\'}.tar.gz'
  sudo --non-interactive chown -R ubuntu:ubuntu -- '${RELEASE//\'/\'\\\'\'}'
  if cd /data/current
  then
    rm -fr -- * .[^.]* ..?*
    ln -sv '../releases/${RELEASE//\'/\'\\\'\'}'/* .
    printf '%s\\0' manifests/*.pp |
      xargs --max-args=1 --null --verbose sudo --non-interactive puppet apply
  fi
fi
exit
EOF

# Removes old archives. ARCHIVE_MAX to specifies how many to keep (default: 7)
# usage: clean HOST
deploy::cleanup()
{
  tee >(cat >&2) | ssh -T -- "ubuntu@$1"
} << EOF
if (( ${ARCHIVE_MAX:-0} > 0 ))
then
  find /data/releases -maxdepth 1 -iregex '.*\\.t\\(ar\\.\\)\\?g' -printf '%Ts\\t%p\\0' |
    sort --numeric-sort --zero-terminated |
    head --lines=$((-1*ARCHIVE_MAX)) --zero-terminated |
    cut --fields=2 --zero-terminated |
    xargs --max-args=1 --max-procs=0 --null --verbose rm -f --
fi
find /data/releases/ -maxdepth 1 -mindepth 1 -type d -printf '%Ts\\t%p\\0' |
  sort --numeric-sort --zero-terminated |
  head --lines=-2 --zero-terminated |
  cut --fields=2 --zero-terminated |
  xargs --max-args=1 --max-procs=0 --null --verbose rm -fr --
EOF

# Applies a function asynchronysly to mutliple hosts
# usage: deploy::execute FUNCTION HOST ...
deploy::execute()
{
  local func="$1"
  local pids=( )
  while shift && (( $# ))
  do
    { printf '%s: %s\n' "$(date '+%c')" "$1"
      "${func}" "$1" &
    } &> "$#.log"
    pids+=("$!")
  done
  while (( ${#pids[@]} ))
  do
    wait -- "${pids[0]}"
    cat -- "${#pids[@]}.log"
    pids=("${pids[@]:1}")
  done
}

# Copy standard output and standard error to a log file
exec {stdout}>&1 1> >(tee -a "${LOGFILE}" >&"${stdout}")
exec {stderr}>&2 2> >(tee -a "${LOGFILE}" >&"${stderr}")

echo 'Archiving...'
deploy::archive
echo
echo 'Preparing...'
deploy::execute deploy::prepare "${TARGETS[@]}"
echo
echo 'Uploading...'
deploy::execute deploy::release "${TARGETS[@]}"
echo
echo 'Installing...'
deploy::execute deploy::install "${TARGETS[@]}"
echo
echo 'Cleaning...'
deploy::execute deploy::cleanup "${TARGETS[@]}"
echo
echo 'Done!'
