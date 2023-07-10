#!/bin/bash
#SBATCH --partition=ondemand-c6i
#SBATCH --time=23:15:00
#SBATCH --ntasks=128

while getopts 'r:' flag
do
    case "${flag}" in
        r) root_dir=${OPTARG};;
    esac
done
echo "root directory: $root_dir";

cd $root_dir
mpirun ./trspt.out
