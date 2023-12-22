#!/bin/bash
#SBATCH --partition=ondemand-m5n
#SBATCH --time=23:15:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1

while getopts 'r:' flag
do
    case "${flag}" in
        r) root_dir=${OPTARG};;
    esac
done
echo "root directory: $root_dir";

cd $root_dir
./xdzeus36 <input

