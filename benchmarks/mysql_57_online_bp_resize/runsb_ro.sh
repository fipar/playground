#!/bin/bash
sysbench_args='--report-interval=1 --num-threads=16 --max-time=240 --test=select --oltp-table-size=40000000 --db-driver=mysql --mysql-user=root --mysql-password=password'
sysbench $sysbench_args $1

