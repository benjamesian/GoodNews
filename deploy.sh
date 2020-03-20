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
# Initialize a list of defined actions
ACTIONS=(clean install prepare revert)
# Construct paths to project files
PROJECT=$(CDPATH='' cd -- "${BASH_SOURCE[0]%/*}" && pwd -P)
RELEASE=${PROJECT##*/}-$(date --utc '+%Y%m%d%H%M%S')
LOGFILE=deploy.log
EXCLUDE_FILE=deploy.ignore
TARGETS_FILE=deploy.hosts
# Create a temporary work directory
WORKDIR=$(mktemp -d --tmpdir "${BASH_SOURCE[0]##*/}-XXXXX")
# Set a trap to remove the temporary directory upon exit
trap 'rm -rf -- "${WORKDIR}"' EXIT
# Chdir into the temporary directory
cd -- "${WORKDIR}"

# Initialization complete
set +o errexit

# Makes a local archive of a upload
# usage: archive
archive()
{
  local -
  set -o verbose
  { rsync -a --exclude-from="${PROJECT}/${EXCLUDE_FILE}" -- "${PROJECT}/" "${RELEASE}"
  } && {
    wait "$!" && tar -xzf - -C "${RELEASE}"
  } < <(
    gpg --decrypt "${PROJECT}/credentials.tar.gz.gpg"
  ) && {
    tar -czf "${RELEASE}.tar.gz" -- "${RELEASE}"
  }
}

# Prints usage information
# usage: usage
usage()
{
  printf 'usage: %s [clean|install|prepare||revert]\n' "${PROGRAM}"
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

# Installs the most recently uploaded release on host
# usage: install HOST
install()
{
  tee >(cat >&2) | ssh -T -- "ubuntu@$1"
} << EOF
if cd /data/releases
then
  tar -xzf '${RELEASE//\'/\'\\\'\'}.tar.gz'
  cp -au /data/current/www/static/ '${RELEASE//\'/\'\\\'\'}/www/static/'
  cp -a /data/current/scraping/theguardian/data.json '${RELEASE//\'/\'\\\'\'}/scraping/theguardian/'
  cp -a /data/current/backend/db.sqlite3 '${RELEASE//\'/\'\\\'\'}/backend/'
  if wait "$!"
  then
    tar -czf "\${REPLY}.backup.tar.gz" -- -
  fi < <(
    { find . -maxdepth 2 -type f -samefile ../current/AUTHORS -printf '%h\\0'
    } || {
      find . -maxdepth 1 -type f -name '*.tar.gz' -printf '%Ts\\t%p\\0'
    } | {
      sort --numeric-sort --reverse --zero-terminated
    } | {
      head --lines=1 --zero-terminated
    } | {
      cut --fields=2- --zero-terminated
    }
  )
  sudo --non-interactive chown -R ubuntu:ubuntu -- '${RELEASE//\'/\'\\\'\'}'
  if cd /data/current
  then
    rm -fr -- * .[^.]* ..?*
    ln -sv '../releases/${RELEASE//\'/\'\\\'\'}'/* ./
    printf '%s\\0' manifests/*.pp |
      xargs --max-args=1 --null --verbose sudo --non-interactive puppet apply
  fi
fi
exit
EOF

# Removes old release archives from a host
# usage: clean HOST
clean()
{
  tee >(cat >&2) | ssh -T -- "ubuntu@$1"
} << EOF
if cd /data/releases
then
  { find . -maxdepth 1 -type f -name '*.tar.gz' -printf '%Ts\\t%p\\0'
  } | {
    sort --numeric-sort --zero-terminated
  } | {
    head --lines=-50 --zero-terminated
  } | {
    cut --fields=2- --zero-terminated
  } | {
    xargs --max-args=1 --max-procs=0 --null --verbose rm -fr --
  }
  { find . -maxdepth 1 -type d -name 'GoodNews-*' -printf '%Ts\\t%p\\0'
  } | {
    sort --numeric-sort --zero-terminated
  } | {
    head --lines=-1 --zero-terminated
  } | {
    cut --fields=2- --zero-terminated
  } | {
    xargs --max-args=1 --max-procs=0 --null --verbose rm -fr --
  }
fi
EOF

# Reverts a host to the most recent backup
# usage: revert HOST
revert()
{
  tee >(cat >&2) | ssh -T -- "ubuntu@$1"
} << EOF
if cd /data/releases
then
  find . -maxdepth 2 -type f -samefile ../current/AUTHORS -printf '%h\\0' |
    if IFS='' read -r -d '' REPLY
    then
      rm -fr -- "\${REPLY}" "\${REPLY}.tar.gz"
    fi
  IFS='' read -r -d '' REPLY < <(
    { find . -maxdepth 1 -type f -name '*.tar.gz' -printf '%Ts\\t%p\\0'
    } | {
      sort --numeric-sort --reverse --zero-terminated
    } | {
      head --lines=1 --zero-terminated
    } | {
      cut --fields=2- --zero-terminated
    }
    printf '\\0'
  )
  tar -xzf "\${REPLY}"
  REPLY=\${REPLY%.tar.gz}
  REPLY=\${REPLY%.backup}
  if cd /data/current
  then
    rm -fr -- * .[^.]* ..?*
    ln -sv "../releases/\${REPLY}"/* ./
    printf '%s\\0' manifests/*.pp |
      xargs --max-args=1 --null --verbose sudo --non-interactive puppet apply
  fi
fi
EOF

# Applies a function asynchronysly to mutliple hosts
# usage: apply FUNCTION HOST ...
apply()
{
  local func="$1"
  local pids=()
  local host=0
  local rval=0
  shift
  while (( host++ < $# ))
  do
    {
      printf '%s: %s\n' "$(date '+%c')" "${!host}"
      {
        "${func}" "${!host}"
        printf 'Exit status: %d\n' "$?"
      } &
    } &> "${!host}.log"
    pids+=("$!")
  done
  host=0
  while (( host < $# ))
  do
    tail -f --pid="${pids[host++]}" -- "${!host}.log"
    rval+=$(("$(sed -n '$s/.*: //p' -- "${!host}.log")"))
  done
  return "${rval}"
}

# Parse options
OPTIND=1
OPTARG=''
while getopts ':h' REPLY
do
  case ${REPLY} in
    (h)
      usage
      exit 0
      ;;
    (:)
      printf >&2 '%s: -%s: option requires an argument\n' "${PROGRAM}" "${OPTARG}"
      usage >&2
      exit 2
      ;;
    (*)
      printf >&2 '%s: -%s: invalid option\n' "${PROGRAM}" "${OPTARG}"
      usage >&2
      exit 2
      ;;
  esac
done
shift "$((OPTIND - 1))"

# Check arguments
if (( $#  > 1 ))
then
  printf >&2 '%s: too many arguments\n' "${PROGRAM}"
  usage >&2
  exit 2
fi

# Load targets
if wait "$!" && IFS=$' \t\n' read -a TARGETS -d '' -r
then
  printf '%s\n' 'Targets loaded:' "${TARGETS[@]/#/$'\t'}"
else
  printf >&2 '%s: Failed to load targets\n' "${PROGRAM}"
  exit 2
fi < <(
  if sed '/^[ \t]*\(#\|$\)/d' "${PROJECT}/${TARGETS_FILE}" && printf '\0'
  then
    printf >&2 'Hosts read from %s\n' "${PROJECT}/${TARGETS_FILE}"
    exit
  fi
  exec {stdout}>&1
  exec 1>&2
  printf 'Unable to read target hosts from %s\n' "${PROJECT}/${TARGETS_FILE}"
  if [[ ! -t 1 ]]
  then
    exit 1
  fi
  printf 'Either ensure the file exists or specify targets now.\n'
  read -r -N 1 -p 'Would you like to specify a list of target hosts? [Y/n] '
  echo
  if [[ ${REPLY,} != y ]]
  then
    exit 1
  fi
  tput bold
  printf 'Hosts: (press Ctrl-D when done)'
  tput sgr0
  echo
  if ! wait "$!" && IFS=$' \t\n' read -r -a TARGETS -d ''
  then
    printf 'Whoops, an unexpected error occurred\n'
    exit 1
  fi < <(sed '/^[[:blank:]]*\(#\|$\)/d' && printf '\0')
  trap '{
  printf "%s\\n" "${TARGETS[@]}" && printf "\\0"
  } >&"${stdout}"
  ' EXIT
  read -r -N 1 -p 'Would you like to save this list? [Y/n] '
  if [[ ${REPLY,} != y ]]
  then
    exit 1
  fi
  if [[ -e ${PROJECT}/${TARGETS_FILE} ]]
  then
    read -r -N 1 -p "Overwrite ${PROJECT}/${TARGETS_FILE}? [Y/n] "
  fi
  if [[ ${REPLY,} != y ]]
  then
    exit 1
  fi
  printf 'Writing hosts to file %q...\n' "${PROJECT}/${TARGETS_FILE}"
  printf > "${PROJECT}/${TARGETS_FILE}" '%s\n' "${TARGETS[@]}"
)

if (( $# ))
then
  # Match provided action
  COMMAND=''
  for name in "${ACTIONS[@]}"
  do
    if [[ ${name} == "$1"* ]]
    then
      if [[ -n ${COMMAND} ]]
      then
        printf >&2 '%s: %q: ambiguous action\n' "${PROGRAM}" "$1"
        usage >&2
        exit 2
      fi
      COMMAND=${name}
    fi
  done
  if [[ -z ${COMMAND} ]]
  then
    printf >&2 '%s: %q: unrecognized action\n' "${PROGRAM}" "$1"
    usage >&2
    exit 2
  fi
  apply "${COMMAND}" "${TARGETS[@]}"

else
  # Perform full deployment
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
  if ! apply clean "${TARGETS[@]}"
  then
    printf >&2 '%q: Something went wrong while cleaning a target.\n' "${PROGRAM}"
    printf >&2 'See logs.\n'
  fi
  echo
fi {stdout}>&1 1> >(
  tee -a "${PROJECT}/${LOGFILE}" >&"${stdout}"
) {stderr}>&2 2> >(
  tee -a "${PROJECT}/${LOGFILE}" >&"${stderr}"
)
