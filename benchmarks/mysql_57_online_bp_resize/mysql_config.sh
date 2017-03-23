#!/bin/bash
GB=$((1024 * 1024 * 1024))
innodb_buffer_pool_size_normal=$((4 * GB))
innodb_buffer_pool_size_decreased=$((2 * GB))
innodb_buffer_pool_size_increased=$((8 * GB))

usage()
{
    echo "usage: $0 <normal|increased|decreased>">&2
}

[ $# -eq 0 ] && usage && exit 1 

[ "$1" != "normal" ] && [ "$1" != "decreased" ] && [ "$1" != "increased" ] && usage && exit 1 

bp=$(eval "echo \$innodb_buffer_pool_size_$1")

mysql -e "set @@global.innodb_buffer_pool_size=$bp"

