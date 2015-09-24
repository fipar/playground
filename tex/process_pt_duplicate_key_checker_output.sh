#!/bin/bash
# Takes as input the output to pt-duplicate-key-checker and produces latex output to format it

input_file=$1
[ -z "$1" ] && {
   echo "Usage: $0 <input-file>">&2
   echo "Where <input-file> is the output from pt-online-duplicate-key-checker">&2
   exit 1
}

echo '\begin{verbatim}' > $input_file.tex
while read line; do
echo $line | grep ^ALTER > /dev/null && {
   echo '\end{verbatim}'
   echo '\begin{minted}{sql}'
   echo $line #| sed 's/_/\\_/g'
   echo '\end{minted}'
   echo '\begin{verbatim}'
} || echo $line 
done < $input_file >> $input_file.tex 
echo '\end{verbatim}' >> $input_file.tex
