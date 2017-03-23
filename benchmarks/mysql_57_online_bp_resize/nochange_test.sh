#!/bin/bash

run_test()
{
[ $# -eq 0 ] && return 
echo "buffer pool nochange test"
sudo ./restore_datadir.sh 
./mysql_config.sh normal
nohup ./runsb.sh run &> sb_bp_${1}.txt &
sleep 240
kill $(ps -ef|grep sysbench|awk '{print $2}')
}

run_test nochange
