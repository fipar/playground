#!/bin/bash

# graph titles
sb_bp_decreased="BP size decreased"
sb_bp_increased="BP size increased"
sb_bp_rollback_decrease="BP size decreased with rollback of change"
sb_bp_increase_needed="BP size increase 2 to 8"
sb_bp_nochange="BP size unchanged"
sb_small_bp_decreased="BP size decreased small dataset"

for f in sb_*txt; do
    echo "ts,tps" > $f.csv; grep thds $f|awk '{print $2 ","$7}'|tr -d s >> $f.csv
done

for f in *csv; do
    title=$(echo $f|awk -F. '{print $1}')
    title=$(eval "echo \$$title")
    env _INPUT_FILE=$f _OUTPUT_FILE=$f.png _OUTPUT_RATIO=2 _X_AXIS=ts _X_AXIS_LABEL='time (secs)' _Y_AXIS=tps _Y_AXIS_LABEL=tps _AXIS_HAVE_0=no _GRAPH_TITLE="$title" csv_to_png.sh
done

