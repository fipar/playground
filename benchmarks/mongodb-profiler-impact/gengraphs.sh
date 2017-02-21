#!/bin/bash

ba=~/src/benchmark_automation

# we first generate a header line, then we iterate over each file based on threads and profiler level, and concat the data to the csv file
echo "$(env _ONLYHEADER=1 $ba/data_preparation_scripts/csv_from_sysbench.sh sysbench-oltp-8-profiler-0.txt mongoprofiler 8),profiler_level" > data.csv
for t in 8 16 32; do
	for p in 0 2; do
		env _NOHEADER=1 $ba/data_preparation_scripts/csv_from_sysbench.sh sysbench-oltp-$t-profiler-$p.txt mongoprofiler $t| while read l; do
																		echo "$l,$p">>data.csv
																	done	
	done
done

# finally we generate a graph

cat <<EOF>label_custom.R

remove(label_custom)

label_custom <- function(variable, value) {
	if (variable=="profiler_level") { 
		if (value=="0") { 
			return ("no profiler")
		} else {
			return ("profile all queries")
		}
	} else if (variable=="threads") {
		return (paste (variable,":",value))
	} else {
		return (value)
	}
}

EOF

env _INPUT_FILE=data.csv \
	_OUTPUT_FILE=mongodb_profiler_impact.png \
	_X_AXIS=ts \
	_X_AXIS_LABEL="Time (secs)" \
	_Y_AXIS=tps \
	_Y_AXIS_LABEL="Throughput (tps)" \
	_FACET_X=threads \
	_FACET_Y=profiler_level \
	_AXIS_HAVE_0=no \
	_GRAPH_TITLE="MongoDB: Profiler impact on throughput" $ba/data_presentation_scripts/csv_to_png.sh

#	_R_EXP="$(cat label_custom.R)" \
