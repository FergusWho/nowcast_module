#!/bin/bash
iPATH_dir='/data/iPATH/iPATH2.0'
root_dir='/data/iPATH/nowcast_module'
python_bin='/data/spack/opt/spack/linux-centos7-skylake_avx512/gcc-10.2.0/python-3.8.9-dtvwd3qomfzkcimvlwvw5ilvr4eb5dvg/bin/python3'

module load gcc-4.8.5
module load python-3.8.9-gcc-10.2.0-dtvwd3q

MPI_comp='mpif90'
FCOMP='gfortran'

run_time=$(date +'%Y-%m-%d_%H:%M' -u)

# testing for specific event:
#run_time='2022-01-20_08:30'



CME_dir=$run_time

trspt_dir='transport'
thread_count=72

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
	cd $root_dir
        /opt/slurm/bin/sbatch -W run_zeus2.sh -r $root_dir/$bgsw_folder_name
	wait
	cd $root_dir

	$python_bin $iPATH_dir/prepare_PATH.py --root_dir $root_dir/$bgsw_folder_name --path_dir $iPATH_dir --run_mode 2 --ranks $thread_count --input $root_dir/$bgsw_folder_name/${CME_dir}_input.json
	
	$MPI_comp -O3 $iPATH_dir/Transport/parallel_wrapper.f $iPATH_dir/Transport/transport_2.05.f -o trspt.out
	$FCOMP $iPATH_dir/Transport/combine.f -o combine.out

	mkdir $root_dir/$bgsw_folder_name/path_output/$trspt_dir
	mv ./trspt.out $root_dir/$bgsw_folder_name/path_output/$trspt_dir
	mv ./combine.out $root_dir/$bgsw_folder_name/path_output/$trspt_dir
	cp $iPATH_dir/Transport/trspt_input $root_dir/$bgsw_folder_name/path_output/$trspt_dir
	cp $iPATH_dir/plotting/plot_iPATH.py $root_dir/$bgsw_folder_name/path_output/$trspt_dir
	cp $root_dir/$bgsw_folder_name/${CME_dir}_input.json $root_dir/$bgsw_folder_name/path_output/$trspt_dir

	/opt/slurm/bin/sbatch -W run_transport.sh -r $root_dir/$bgsw_folder_name/path_output/$trspt_dir	
	wait
	cd $root_dir/$bgsw_folder_name/path_output/$trspt_dir
	./combine.out
	rm RawData*
	
	# Plot result:
	$python_bin $root_dir/$bgsw_folder_name/path_output/$trspt_dir/plot_iPATH.py
fi

