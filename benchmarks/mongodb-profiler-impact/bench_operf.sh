#!/bin/bash

mongoc="mongo localhost/sbtest"
sb='/home/vagrant/src/sysbench/sysbench/sysbench'
testpath='/home/vagrant/src/sysbench/sysbench/tests/'
size=40000
tables=4
time=30
runs=1
# set the next two to '' if you don't want to run perf along with the benchmarks
perf_prefix='perf record -F 99 -a -g -- '
perf_post='perf script > '

prepare()
{
    [ -z "$1" ] && return
    $sb --test="$testpath/mongodb/$1.lua" --max-time=0 --mongo-write-concern=1 --mongo-url='mongodb://localhost' --oltp_tables_count=$tables --mongo-database-name='sbtest' --oltp_table_size=$size prepare
}

cleanup()
{
    [ -z "$1" ] && return
    $sb --test="$testpath/mongodb/$1.lua" --max-time=0 --mongo-write-concern=1 --mongo-url='mongodb://localhost' --oltp_tables_count=$tables --mongo-database-name='sbtest' --oltp_table_size=$size cleanup
}

run()
{
   [ -z "$1" -o -z "$2" ] && return
   $sb --test="$testpath/mongodb/$1.lua" --report-interval=1 --max-requests=10000000 --max-time=$time --oltp_tables_count=$tables --mongo-write-concern=1 --mongo-url='mongodb://localhost' --mongo-database-name='sbtest' --oltp_table_size=$size --num-threads=$2 run
}

profiler()
{
  [ -z "$1" ] && return 
  $mongoc --eval "db.setProfilingLevel($1)"
}


#for run in $(seq $runs); do
for run in 1; do
    for profiler in 0 2; do
	for threads in 8 16 32; do
	    profiler $profiler
	    prepare oltp
	    tag=oltp-$threads-profiler-$profiler
	    opcontrol --init
	    opcontrol --start --no-vmlinux
	    run oltp $threads 2>&1 | tee sysbench-$tag.txt
	    sleep 2
	    opcontrol --stop
	    opcontrol --dump
	    opcontrol --save=pt_collect_$tag
	    opreport --demangle=smart --symbols --merge tgid session:pt_collect_$tag > opreport.$tag
	    cleanup oltp
	done
    done
done
