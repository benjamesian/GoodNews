#!/usr/bin/env bash
# Deploy snapshots of the GoodNews project
#
# For each server:
# 1. Copy a snapshot to the server's `releases' directory.
# 2. Link the snapshot in the `current' release directory.
# 4. Apply configuration via puppet manifests.
########################################################

# Enable debugging output if `DEBUG' is defined
if [[ -v DEBUG ]]
then
  exec {BASH_XTRACEFD}>&2
  set -o verbose -o xtrace
fi

# Initialize environment (exit upon unhandled errors)
set -o errexit

# Get the name of this script
PROGRAM=${BASH_SOURCE[0]##*/}

# Construct paths to project files
PROJECT=$(CDPATH='' cd -- "${BASH_SOURCE[0]%/*}" && pwd -P)
RELEASE=${PROJECT##*/}-$(date --utc '+%Y%m%d%H%M%S')
LOGFILE=${PROJECT}/deploy.log
EXCLUDE_FILE=${PROJECT}/deploy.ignore
TARGETS_FILE=${PROJECT}/deploy.hosts

# Create a temporary work directory 
WORKDIR=$(mktemp -d --tmpdir "${BASH_SOURCE[0]##*/}-XXXXX")

# Set a trap to remove the temporary directory upon exit
trap 'rm -rf -- "${WORKDIR}"' EXIT

# Chdir into the temporary directory
cd -- "${WORKDIR}"

# Read in a list of target hosts
if IFS=$' \t\n' read -a TARGETS -d '' -r
then
  printf >&2 '%s\n' 'Targets loaded:' "${TARGETS[@]}" 
else
  printf >&2 'Exiting.\n'
  exit 1
fi < <(
if sed '/^[[:blank:]]*\(#\|$\)/d' "${TARGETS_FILE}" && printf '\0'
then
  printf >&2 'Hosts read from %s\n' "${TARGETS_FILE}" 
  exit
fi
exec {stdout}>&1
exec 1>&2
printf 'Unable to read target hosts from %s\n' "${TARGETS_FILE}"
printf 'Either ensure the file exists or specify targets now.\n'
read -r -N 1 -p 'Would you like to specify a set of target hosts? [Y/n] '
echo
if [[ ${REPLY,} != y ]]
then
  exit 1
fi
tput bold
printf 'Hosts: (press Ctrl-D when done)'
tput sgr0
echo
if ! IFS=$' \t\n' read -r -a TARGETS -d ''
then
  printf 'Whoops, an error occurred.\n'
  exit 1
fi < <(sed '/^[[:blank:]]*\(#\|$\)/d' && printf '\0')
trap '{
printf "%s\\n" "${TARGETS[@]}" && printf "\\0"
} >&"${stdout}"
' EXIT
read -r -N 1 -p 'Would you like to save this list? [Y/n] '
echo
if [[ ${REPLY,} != y ]]
then
  exit 0
fi
if [[ -e ${TARGETS_FILE} ]] && ! mv -b -- "${TARGETS_FILE}" "${TARGETS_FILE}.old"
then
  printf 'Failed to unlink existing file %q...\n' "${TARGETS_FILE}"
else
  printf 'Writing hosts to file %q...\n' "${TARGETS_FILE}"
  printf > "${TARGETS_FILE}" '%s\n' "${TARGETS[@]}"
fi
)

# Initialization complete
set +o errexit

# Makes a local archive of a upload
# usage: archive
archive()
{
  local -
  set -o verbose
  if rsync -a --exclude-from="${EXCLUDE_FILE}" -- "${PROJECT}/" "${RELEASE}"
  then
    if wait "$!"
    then
      if tar -xzf - -C "${RELEASE}"
      then
        if tar -czf "${RELEASE}.tar.gz" -- "${RELEASE}"
        then
          return 0
        fi
      fi
    fi < <(gpg --decrypt "${PROJECT}/credentials.tar.gz.gpg")
  fi
  return 1
}

# Prepares a host to recieve a release
# usage: prepare HOST
prepare()
{
  tee >(cat >&2) | ssh -T -- "ubuntu@$1"
} << EOF
sudo --non-interactive mkdir -pm 0755 /data
sudo --non-interactive mkdir -pm 0755 /data/releases
sudo --non-interactive chown -hR ubuntu:ubuntu /data
exit
EOF

# Uploads an archived release to a host
# usage: upload HOST
upload()
{
  local -
  set -o verbose
  scp -- "${RELEASE}.tar.gz" "ubuntu@$1:/data/releases/"
}

# Installs an uploaded release on host
# usage: install HOST
install()
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

# Removes old release directories from a host
# usage: clean HOST
cleanup()
{
  tee >(cat >&2) | ssh -T -- "ubuntu@$1"
} << EOF
find /data/releases/ -maxdepth 1 -mindepth 1 -type d -printf '%Ts\\t%p\\0' |
  sort --numeric-sort --zero-terminated |
  head --lines=-2 --zero-terminated |
  cut --fields=2 --zero-terminated |
  xargs --max-args=1 --max-procs=0 --null --verbose rm -fr --
EOF

# Applies a function asynchronysly to mutliple hosts
# usage: apply FUNCTION HOST ...
apply()
{
  local func="$1"
  local pids=()
  local rval=0
  while shift && (( $# ))
  do
    { printf '%s: %s\n' "$(date '+%c')" "$1"
      "${func}" "$1" &
    } &> "$#.log"
    pids+=("$!")
  done
  while (( ${#pids[@]} ))
  do
    if ! wait -- "${pids[0]}"
    then
      rval+=1
    fi
    cat -- "${#pids[@]}.log"
    pids=("${pids[@]:1}")
  done
  return "$((rval))"
}

# Copy standard output and standard error to a log file
exec {stdout}>&1 1> >(tee -a "${LOGFILE}" >&"${stdout}")
exec {stderr}>&2 2> >(tee -a "${LOGFILE}" >&"${stderr}")

echo 'Archiving...'
if ! archive
then
  printf >&2 '%q: Failed to create an arhive.\n' "${PROGRAM}"
  printf >&2 'Exiting...\n'
  exit 1
fi
echo
echo 'Preparing...'
if ! apply prepare "${TARGETS[@]}"
then
  printf >&2 '%q: Something went wrong while preparing a target.\n' "${PROGRAM}"
  printf >&2 'See logs.\n'
fi
echo
echo 'Uploading...'
if ! apply upload "${TARGETS[@]}"
then
  printf >&2 '%q: Ran into trouble while uploading to a target.\n' "${PROGRAM}"
  printf >&2 'See logs.\n'
fi
echo
echo 'Installing...'
if ! apply install "${TARGETS[@]}"
then
  printf >&2 '%q: Ran into trouble while installing to a target.\n' "${PROGRAM}"
  printf >&2 'See logs.\n'
fi
echo
echo 'Cleaning...'
if ! apply cleanup "${TARGETS[@]}"
then
  printf >&2 '%q: Something went wrong while cleaning a target.\n' "${PROGRAM}"
  printf >&2 'See logs.\n'
fi
echo
echo 'Done!'
