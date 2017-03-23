#!/bin/bash

run_test()
{
[ $# -eq 0 ] && return 
echo "buffer pool $1 test"
sudo ./restore_datadir.sh 
./mysql_config.sh normal
nohup ./runsb.sh run &> traced_sb_bp_${1}.txt &
sleep 100
sudo ./pt-pmp &> pmp.log.0
sleep 20
./mysql_config.sh $1
sudo ./pt-pmp &> pmp.log.1
sleep 1
sudo ./pt-pmp &> pmp.log.2
sleep 119
kill $(ps -ef|grep sysbench|awk '{print $2}')
}

run_test decreased
