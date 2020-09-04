#!/usr/bin/env bash
# Deploy snapshots of the GoodNews project
#
# For each server:
# 1. (local)  Make an archive of the current repository.
# 2. (remote) Create necessary directories on each target.
# 3. (local)  Upload a copy of the archive to each target.
# 4. (remote) Extract the repo & copy in persistent files.
# 5. (remote) Archive the existing version and replace it.
# 6. (remote) Apply puppet manifests.
# 7. (remote) Remove old archives.
# 8. (local)  Remove temporary files and exit.
########################################################

# Enable debugging output if `DEBUG' is defined
if [[ -v DEBUG ]]
then
  exec {BASH_XTRACEFD}>&2
  set -o xtrace
fi

# Initialize environment (exit upon unhandled errors)
set -o errexit

# Define program name and available commands
PROGRAM=${BASH_SOURCE[0]##*/}
ACTIONS=('clean' 'revert')

# Construct paths to project files
PROJECT=$(CDPATH='' cd -- "${BASH_SOURCE[0]%/*}" && pwd -P)
RELEASE=${PROJECT##*/}-$(date --utc '+%Y%m%d%H%M%S')
LOGFILE=${PROJECT}/deploy.log
EXCLUDE_FILE=.gitignore
PERSIST_FILE=deploy.keep
TARGETS_FILE=deploy.hosts

# Create a temporary working directory and remove it upon exit
WORKDIR=$(mktemp --directory --tmpdir -- "${BASH_SOURCE[0]##*/}-XXXXX")
trap 'rm -rf -- "${WORKDIR}"' EXIT

# Chdir into the temporary directory
cd -- "${WORKDIR}"

# Initialization complete
set +o errexit


# Prints usage information
# usage: usage
usage()
{
  local IFS='|'
  printf 'usage: %q %s\n' "${PROGRAM}" "[${ACTIONS[*]}]"
}


# Makes a local archive of in the temporary working directory
# usage: archive
archive()
{
  local -
  set -o verbose
  rsync --archive --exclude-from="${PROJECT}/${EXCLUDE_FILE}" -- \
    "${PROJECT}/" "${RELEASE}" && {
    wait "$!"                  &&
    tar -xzf - -C "${RELEASE}" &&
    tar -czf "${RELEASE}.tar.gz" -- "${RELEASE}"
  } < <(gpg --decrypt "${RELEASE}/credentials.tar.gz.gpg")
}


# Prepares a host and uploads a release
# usage: prepare HOST
upload()
{
  tee >(cat >&2) | ssh -T -- "ubuntu@$1"
  local -
  set -o verbose
  scp -v -- "${RELEASE}.tar.gz" "ubuntu@$1:/data/releases/"
} << EOF
sudo --non-interactive --set-home mkdir -pm 0755 /data
sudo --non-interactive --set-home mkdir -pm 0755 /data/releases
sudo --non-interactive --set-home chown -hR ubuntu:ubuntu /data
exit
EOF


# Installs the most recently uploaded release on host
# usage: install HOST
install()
{
  tee >(cat >&2) | ssh -T -- "ubuntu@$1"
} << EOF
if cd /data/releases
then
  tar -xzf '${RELEASE//\'/\'\\\'\'}.tar.gz'
  find -H . -maxdepth 2 -samefile ../current/AUTHORS -printf '%h\\0' |
    if IFS='' read -r -d ''
    then
      tar -czf "\${REPLY}.backup.tar.gz" -- "\${REPLY}"
      cd -- '${RELEASE//\'/\'\\\'\'}' &&
        rsync --archive --recursive --update --verbose \
          --files-from='${PERSIST_FILE//\'/\'\\\'\'}'  \
          ../"\${REPLY}/" ./
    fi
  sudo --non-interactive --set-home chown -R ubuntu:ubuntu -- '${RELEASE//\'/\'\\\'\'}'
  cd /data/current && {
    rm -fr -- * .[^.]* ..?*
    ln -sv '../releases/${RELEASE//\'/\'\\\'\'}'/* ./
  } &&
    printf '%s\\0' manifests/*.pp |
      xargs --max-args=1 --null --verbose sudo --non-interactive --set-home puppet apply
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
  find . -maxdepth 1 -type f -name '*.tar.gz' -printf '%Ts\\t%p\\0' |
    sort --numeric-sort --zero-terminated                           |
    head --lines=-50 --zero-terminated                              |
    cut --fields=2- --zero-terminated                               |
    xargs --max-args=1 --max-procs=0 --null --verbose rm -f --

  find . -mindepth 1 -maxdepth 1 -type d -printf '%Ts\\t%p\\0' |
    sort --numeric-sort --zero-terminated                      |
    head --lines=-1 --zero-terminated                          |
    cut --fields=2- --zero-terminated                          |
    xargs --max-args=1 --max-procs=0 --null --verbose rm -fr --
fi
exit
EOF


# Reverts a host to the most recent backup
# usage: revert HOST
revert()
{
  tee >(cat >&2) | ssh -T -- "ubuntu@$1"
} << EOF
if cd /data/releases
then
  find -H . -maxdepth 2 -samefile ../current/AUTHORS -printf '%h\\0' |
    if IFS='' read -r -d ''
    then
      rm -fr -- "\${REPLY}" "\${REPLY}.tar.gz" "\${REPLY}.backup.tar.gz"
    fi

  find . -maxdepth 1 -type f -name '*.backup.tar.gz' -printf '%Ts\\t%p\\0' |
    sort --numeric-sort --zero-terminated --reverse                        |
    head --lines=1 --zero-terminated                                       |
    cut --fields=2- --zero-terminated                                      |
    if IFS='' read -r -d ''
    then
      tar -xzf "\${REPLY}"
      cd /data/current && {
        rm -fr -- * .[^.]* ..?*
        ln -sv "../releases/\${REPLY%.backup.tar.gz}"/* ./
      } &&
        printf '%s\\0' manifests/*.pp |
          xargs --max-args=1 --null --verbose sudo --non-interactive --set-home puppet apply
    fi
fi
EOF


# Applies a function to mutliple targets asynchronysly
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
    } &> "${host}.log"
    pids+=("$!")
  done
  host=0
  while (( host < $# ))
  do
    tail -f --pid="${pids[host++]}" -- "${host}.log"
    rval+=$(( $(sed -n '$s/.*: //p' -- "${host}.log") ))
  done
  return "${rval}"
}


# Gets target hosts from file or stdin if file does not exist
# usage: targets FILE
targets()
{
  if sed 2> /dev/null '/^[ \t]*\(#\|$\)/d' "$1"
  then
    printf 1>&2 'Hosts read from %s\n' "$1"
    exit 0
  fi
  exec {stdout}>&1 1>&2
  printf 'Unable to read hosts from %s\n' "$1"
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
  echo 'Hosts: (Press Ctrl-D when done)'
  if wait "$!"
  then
    IFS=$' \t\n' mapfile -t TARGETS
  else
    echo 'Whoops! an unexpected error occurred.'
    exit 1
  fi < <(
    sed 2> /dev/null '/^[ \t\n]*\(#\|$\)/d'
  )
  trap 'printf >&"${stdout}" "%s\\n" "${TARGETS[@]}"' EXIT
  read -r -N 1 -p 'Would you like to save this list? [Y/n] '
  echo
  if [[ ${REPLY,} != y ]]
  then
    exit 1
  fi
  if [[ -e $1 ]]
  then
    read -r -N 1 -p "Overwrite $1? [Y/n] "
    echo
  fi
  if [[ ${REPLY,} != y ]]
  then
    exit 1
  fi
  printf 'Writing hosts to file %q...\n' "$1"
  printf > "$1" '%s\n' "${TARGETS[@]}"
}

# Parse command options
#
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
    Perform  ;;
  esac
done
shift "$((OPTIND - 1))"


# Check argument count
#
if (( $#  > 1 ))
then
  printf >&2'%s: too many arguments\n' "${PROGRAM}"
  usage >&2
  exit 2
fi


# Read targets from a file or, if no such file exists, stdin
#
if wait "$!"
then
  IFS=$' \t\n' mapfile -t TARGETS
  printf '%s\n' 'Targets loaded:' "${TARGETS[@]}"
else
  printf >&2 'Failed to load targets.\n'
  exit 2
fi < <(
  targets "${PROJECT}/${TARGETS_FILE}"
)


# Match provided action
#
if (( $# ))
then
  ACTION=''
  for name in "${ACTIONS[@]}"
  do
    [[ ${name} == "$1"* ]] || continue
    if [[ -n ${ACTION} ]]
    then
      printf '%s: %q: ambiguous action\n' "${PROGRAM}" "$1"
      usage
      exit 2
    fi >&2
    ACTION=${name}
  done
  if [[ -z ${ACTION} ]]
  then
    printf '%s: %q: unrecognized action\n' "${PROGRAM}" "$1"
    usage
    exit 2
  fi >&2
  apply "${ACTION}" "${TARGETS[@]}"

# Execute full deployment sequence
#
else
  echo 'Archiving...'
  if ! archive
  then
    printf >&2 '%q: Failed to create an arhive.\n' "${PROGRAM}"
    exit 1
  fi
  echo
  echo 'Uploading...'
  if ! apply upload "${TARGETS[@]}"
  then
    printf >&2 '%q: Error occurred while uploading to a target.\n' "${PROGRAM}"
  fi
  echo
  echo 'Installing...'
  if ! apply install "${TARGETS[@]}"
  then
    printf >&2 '%q: Error occurred while installing to a target.\n' "${PROGRAM}"
  fi
  echo
  echo 'Cleaning...'
  if ! apply clean "${TARGETS[@]}"
  then
    printf >&2 '%q: Error occurred while cleaning a target.\n' "${PROGRAM}"
  fi
  echo
fi {stdout}>&1 {stderr}>&2 \
  1> >(tee -a "${LOGFILE}" >&"${stdout}") \
  2> >(tee -a "${LOGFILE}" >&"${stderr}")
