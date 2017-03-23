#!/bin/bash

run_test()
{
echo "increase needed test"
sudo ./restore_datadir.sh 
./mysql_config.sh decreased
nohup ./runsb.sh run &> sb_bp_increase_needed.txt &
sleep 120
./mysql_config.sh increased
sleep 120
kill $(ps -ef|grep sysbench|awk '{print $2}')
}

run_test

