#!/bin/bash
iPATH_dir='/data/iPATH/iPATH2.0'
root_dir='/data/iPATH/nowcast_module'
python_bin='/data/spack/opt/spack/linux-centos7-skylake_avx512/gcc-10.2.0/python-3.8.9-dtvwd3qomfzkcimvlwvw5ilvr4eb5dvg/bin/python3'
# default for CCMC AWS

MPI_comp='mpif90'
FCOMP='gfortran'

run_time=$(date +'%Y-%m-%d_%H:%M' -u)
if_local=0

# testing for specific event:
# example: bash CME.sh -t '2022-01-20_08:30'
while getopts 't:L' flag
do
    case "${flag}" in
        t) run_time=${OPTARG};;
        L) if_local=1;;
    esac
done

if [ $if_local -eq 1 ]
then
    # change these accordingly if you want to run locally
    iPATH_dir=$HOME'/iPATH2.0'
    root_dir=$HOME'/nowcast_module'
    python_bin='/usr/bin/python3'
    thread_count=12
else
    module load gcc-4.8.5
    module load python-3.8.9-gcc-10.2.0-dtvwd3q
    thread_count=96
fi

CME_dir=$run_time

trspt_dir='transport'


# save last line of output to bgsw_folder_name
bgsw_folder_name=`$python_bin $root_dir/check_CME.py --root_dir $root_dir --run_time $run_time | tail -n 1`

echo $bgsw_folder_name

if [ -z "$bgsw_folder_name" ]
then
	echo "There is no CME"

else
	#-----------------------------------------------
	# CME setup and acceleration:
	$python_bin $iPATH_dir/prepare_PATH.py --root_dir $root_dir/$bgsw_folder_name --path_dir $iPATH_dir --run_mode 0 --input $root_dir/$bgsw_folder_name/${CME_dir}_input.json
	cd $root_dir/$bgsw_folder_name
	csh -v ./iPATH_zeus.s
	if [ $if_local -eq 1 ]
	then
		./xdzeus36 <input
	else
		cd $root_dir
        /opt/slurm/bin/sbatch -W run_zeus2.sh -r $root_dir/$bgsw_folder_name
		wait
	fi
	cd $root_dir

	$python_bin $iPATH_dir/prepare_PATH.py --root_dir $root_dir/$bgsw_folder_name --path_dir $iPATH_dir --run_mode 2 --ranks $thread_count --input $root_dir/$bgsw_folder_name/${CME_dir}_input.json
	
	$MPI_comp -O3 $iPATH_dir/Transport/parallel_wrapper.f $iPATH_dir/Transport/transport_2.05.f -o trspt.out
	$FCOMP $iPATH_dir/Transport/combine.f -o combine.out

	mkdir $root_dir/$bgsw_folder_name/path_output/$trspt_dir
	mv ./trspt.out $root_dir/$bgsw_folder_name/path_output/$trspt_dir
	mv ./combine.out $root_dir/$bgsw_folder_name/path_output/$trspt_dir
	cp $iPATH_dir/Transport/trspt_input $root_dir/$bgsw_folder_name/path_output/$trspt_dir
	cp $root_dir/plot_iPATH_nowcast.py $root_dir/$bgsw_folder_name/path_output/$trspt_dir
	cp $root_dir/$bgsw_folder_name/${CME_dir}_input.json $root_dir/$bgsw_folder_name/path_output/$trspt_dir
	mv $root_dir/$bgsw_folder_name/${CME_dir}_output.json $root_dir/$bgsw_folder_name/path_output/$trspt_dir/output.json

	if [ $if_local -eq 1 ]
	then
		cd $root_dir/$bgsw_folder_name/path_output/$trspt_dir
		mpirun -np $thread_count trspt.out
	else
		/opt/slurm/bin/sbatch -W run_transport.sh -r $root_dir/$bgsw_folder_name/path_output/$trspt_dir	
		wait
		cd $root_dir/$bgsw_folder_name/path_output/$trspt_dir
	fi
		
	./combine.out
	rm RawData*
	
	# Plot result:
	$python_bin $root_dir/$bgsw_folder_name/path_output/$trspt_dir/plot_iPATH_nowcast.py
fi

