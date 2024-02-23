#!/bin/bash

nDays=${1:-30}
StagingDir=/data/iPATH/nowcast_module_v1/staging

date -u +'%F %T'
echo "Moving files older than $nDays days from staging to archive area:"

find $StagingDir -type f -mtime +$nDays \
| sort -V \
| while read path; do
   echo $path
   cp -p $path ${path/staging/archive} && rm $path
done

