#!/bin/bash

cwd=$(dirname "$(realpath "$0")")

# redirect output to both stdout and mailx
$cwd/FindSimulationProblems.sh -f yesterday -t today -p no \
|& tee >(mailx -s "iPATH rt-hpc-prod summary" -r m_ipath corti@hawaii.edu)
