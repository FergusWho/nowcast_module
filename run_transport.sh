#!/bin/bash
#SBATCH --partition=ondemand
#SBATCH --time=23:15:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=64

while getopts 'r:' flag
do
    case "${flag}" in
        r) root_dir=${OPTARG};;
    esac
done
echo "root directory: $root_dir";

cd $root_dir
/opt/amazon/openmpi/bin/mpirun -np 64 ./trspt.out
#/opt/slurm/bin/srun -n 128 ./trspt.out

