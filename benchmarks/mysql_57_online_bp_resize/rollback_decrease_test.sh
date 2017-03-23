#!/bin/bash

run_test()
{
echo "rollback decrease test"
sudo ./restore_datadir.sh 
./mysql_config.sh normal
nohup ./runsb.sh run &> sb_bp_rollback_decrease.txt &
sleep 120
./mysql_config.sh decreased
sleep 20
./mysql_config.sh increased
sleep 100
kill $(ps -ef|grep sysbench|awk '{print $2}')
}

run_test

