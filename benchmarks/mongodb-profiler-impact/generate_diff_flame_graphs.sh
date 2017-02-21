#!/bin/bash

fg=~/src/FlameGraph/

for t in 8 16 32; do
    for p in 0 2; do	
	$fg/stackcollapse-perf.pl out.oltp-$t-profiler-$p. > t${t}p${p}.folded
    done
    $fg/difffolded.pl -n t${t}p0.folded t${t}p2.folded | $fg/flamegraph.pl --negate > t${t}p0vsp2.svg
done
