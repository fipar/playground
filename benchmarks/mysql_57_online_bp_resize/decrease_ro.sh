#!/bin/bash

run_test()
{
[ $# -eq 0 ] && return 
echo "buffer pool $1 test"
sudo ./restore_datadir.sh 
./mysql_config.sh normal
nohup ./runsb_ro.sh run &> sb_ro_bp_${1}.txt &
sleep 120
./mysql_config.sh $1
sleep 120
kill $(ps -ef|grep sysbench|awk '{print $2}')
}

run_test decreased

