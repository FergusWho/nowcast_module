#!/bin/bash

# redirect output to both stdout and mailx
./FindSimulationProblems.sh -f yesterday -t today -p no \
|& tee >(mailx -s "iPATH rt-hpc-prod summary" -r m_ipath corti@hawaii.edu)
