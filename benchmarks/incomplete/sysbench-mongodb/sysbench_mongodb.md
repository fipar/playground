---

title: "Percona Server for MongoDB: Storage Engine comparison"
author: "Percona Lab"
generated on:April 19, 2016
output:
  md_document:
    variant: markdown_github

---


# Percona Server for MongoDB 3.0.10-1.5 and 3.2.0-1.0 - data set that fits in RAM 

## Setup

* Client (sysbench) and server are on the same machine
* CPU: 48 logical CPU threads servers Intel(R) Xeon(R) CPU E5-2680 v3 @ 2.50GHz
* 128GB RAM (64GB storage engine cache)
* sysbench with mongodb support, 16 collections x 2M documents (~6GB compressed), uniform and pareto distributions. 
* For WiredTiger, MongoDB 3.0.11 and 3.2.4 were also tested. 

## Throughput per threads and workload

![plot of chunk global](figure/global-1.png)![plot of chunk global](figure/global-2.png)![plot of chunk global](figure/global-3.png)![plot of chunk global](figure/global-4.png)

## Throughput per threads and workload, summary for each version and engine

Versions marked with an 'M' correspond to upstream MongoDB, and with a 'P' to Percona Server for MongoDB


```
## Error: Faceting variables must have at least one value
```

```
## Error: Faceting variables must have at least one value
```

![plot of chunk engines](figure/engines-1.png)

## Throughput per threads and workload, details. 
## Throughput per threads and workload, PerconaFT


```
## Error: Faceting variables must have at least one value
```

![plot of chunk ft](figure/ft-1.png)

## Throughput per threads and workload, WiredTiger


```
## Error: Faceting variables must have at least one value
```

![plot of chunk wt](figure/wt-1.png)

## Throughput per threads and workload, RocksDB

![plot of chunk rocks](figure/rocks-1.png)![plot of chunk rocks](figure/rocks-2.png)![plot of chunk rocks](figure/rocks-3.png)![plot of chunk rocks](figure/rocks-4.png)![plot of chunk rocks](figure/rocks-5.png)![plot of chunk rocks](figure/rocks-6.png)![plot of chunk rocks](figure/rocks-7.png)![plot of chunk rocks](figure/rocks-8.png)![plot of chunk rocks](figure/rocks-9.png)![plot of chunk rocks](figure/rocks-10.png)![plot of chunk rocks](figure/rocks-11.png)![plot of chunk rocks](figure/rocks-12.png)![plot of chunk rocks](figure/rocks-13.png)
