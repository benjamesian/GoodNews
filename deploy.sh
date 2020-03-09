#!/usr/bin/env bash
#
# Deploy GoodNews
#
# 1. Copy files to servers at /data/releases/GoodNews-%Y-%m-%dT%H:%M:%S
# 2. On each server symlink release subdirectories into /data/current
# 3. Apply puppet manifests

servers=(
  35.196.167.155
  34.73.252.236
)
datetime="$(date --utc '+%FT%H')"
tmpdir="$(mktemp -d --tmpdir "${0##*/}-XXXXXXXX")"
trap 'rm -rf -- "${tmpdir}"' EXIT
printf '%s\0' "${servers[@]}" |
  xargs -0 -P 0 -I {} rsync -avz . ubuntu@{}:/data/releases/GoodNews-"$datetime"

for id in "${!servers[@]}"
do
  mkfifo -- "$tmpdir/$id-in"
  (ssh -t ubuntu@"${servers[$id]}") <"$tmpdir/$id-in" >"$tmpdir/$id-out" &
done
tee -a "$tmpdir"/*-in << EOF
mkdir -p /data/current /data/releases
cd /data
if test -d releases/GoodNews-$datetime
then
  cd current
  ln -snf ../releases/GoodNews-$datetime/*/ .
  cd manifests
  printf '%s\0' *.pp | xargs -0 -I {} puppet apply {}
fi
exit
EOF
wait
cat "$tmpdir"/*-out
