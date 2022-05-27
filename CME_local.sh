#!/bin/bash
iPATH_dir='/home/junxiang/iPATH2.0'
root_dir='/home/junxiang/nowcast_module'

MPI_comp='mpif90'
FCOMP='gfortran'

#run_time=$(date +'%Y-%m-%d_%H:%M' -u)

# testing for specific event:
run_time='2022-05-25_17:15'



CME_dir=$run_time

trspt_dir='transport'
thread_count=20

# save last line of output to bgsw_folder_name
bgsw_folder_name=`/usr/bin/python3 $root_dir/check_CME.py --root_dir $root_dir --run_time $run_time | tail -n 1`

echo $bgsw_folder_name

if [ -z "$bgsw_folder_name" ]
then
	echo "There is no CME"

else
	#-----------------------------------------------
	# CME setup and acceleration:
	/usr/bin/python3 $iPATH_dir/prepare_PATH.py --root_dir $root_dir/$bgsw_folder_name --path_dir $iPATH_dir --run_mode 0 --input $root_dir/$bgsw_folder_name/${CME_dir}_input.json
	cd $root_dir/$bgsw_folder_name
	csh -v ./iPATH_zeus.s
	./xdzeus36 <input
	cd ..

	python3 $iPATH_dir/prepare_PATH.py --root_dir $root_dir/$bgsw_folder_name --path_dir $iPATH_dir --run_mode 2 --ranks $thread_count --input $root_dir/$bgsw_folder_name/${CME_dir}_input.json
	
	$MPI_comp -O3 $iPATH_dir/Transport/parallel_wrapper.f $iPATH_dir/Transport/transport_2.05.f -o trspt.out
	$FCOMP $iPATH_dir/Transport/combine.f -o combine.out

	mkdir $root_dir/$bgsw_folder_name/path_output/$trspt_dir
	mv ./trspt.out $root_dir/$bgsw_folder_name/path_output/$trspt_dir
	mv ./combine.out $root_dir/$bgsw_folder_name/path_output/$trspt_dir
	cp $iPATH_dir/Transport/trspt_input $root_dir/$bgsw_folder_name/path_output/$trspt_dir
	cp $root_dir/plot_iPATH_nowcast.py $root_dir/$bgsw_folder_name/path_output/$trspt_dir
	cp $root_dir/$bgsw_folder_name/${CME_dir}_input.json $root_dir/$bgsw_folder_name/path_output/$trspt_dir
	mv $root_dir/$bgsw_folder_name/${CME_dir}_output.json $root_dir/$bgsw_folder_name/path_output/$trspt_dir/output.json
	
	cd $root_dir/$bgsw_folder_name/path_output/$trspt_dir
	mpirun -np $thread_count trspt.out
	./combine.out
	rm RawData*
	
	# Plot result:
	python3 $root_dir/$bgsw_folder_name/path_output/$trspt_dir/plot_iPATH_nowcast.py
fi

