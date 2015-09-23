#!/bin/bash

. $(dirname $0)/collect-common.sh

[ $# -ne 2 ] && {
    usage
    exit 1
}

interval=$1
duration=$2

dest=${TOOLNAME}_$(ts).gz
trap "rm -f $dest.pid" SIGINT SIGTERM SIGHUP
# get the header.
$TOOLNAME ext -i 1 -c 1|grep -v '-'|awk -F '|' '{print $2}'|grep -v ^$|sed 's/Variable_name/Timestamp/g'|tr '\n' ' '|sed 's/  */ /g'|sed 's/^ //g' > $dest.header
# now get the capture 
$TOOLNAME ext -i $interval -c $duration | awk -F '|' '{print $3}'|sed 's/^ //g'|sed 's/  *$/ /g'|grep -v ^$|sed 's/^ $/_/g' |tr '\n' ' '| sed "s/Value/|`date '+%Y-%m-%d_%H:%M:%S'`/g" | tr '|' '\n'| grep -v ^$|sed 's/^  *//g' |sed 's/  */ /g'| gzip -c > $dest &
echo $! > $dest.pid
pid=$!
# save the pid so we can monitor disk space while the tool runs, and
# terminate it if needed. 
monitor_disk_space $pid

rm -f $dest.pid 2>/dev/null

   

