#!/bin/bash

nDays=${1:-30}

CodeDir=$(dirname "$(realpath "$0")")

date -u +'%F %T'
$CodeDir/CleanupDisk.sh -t $(date -ud "$nDays days ago" +%F) -p no

echo
date -u +'%F %T'
