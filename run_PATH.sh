#!/bin/bash
MPI_comp='mpif90'
FCOMP='gfortran'

#Name your folder
root_dir='test'
input_file='creat_input.py'
thread_count=10
if_bgonly=0
if_skipbg=0
CME_dir='path_output'
trspt_dir='transport'

while getopts rd:i:td:np:bgonly:skipbg: flag
do
    case "${flag}" in
        rd) root_dir=${OPTARG};;
        i) input_file=${OPTARG};;
        td) trspt_dir=${OPTARG};;
        np) thread_count=${OPTARG};;
        bgonly) if_bgonly=1;;
        skipbg) if_skipbg=1;;

    esac
done
echo "root directory: $root_dir";
echo "input file: $input_file";
#echo "bgonly skipbg: $if_bgonly, $if_skipbg ";



# note the python here is python3
python3 $input_file

#-----------------------------------------------
# Background solar wind setup:

if [ $if_skipbg -ne 1 ]; then
mkdir $root_dir       
cp -r ./Acceleration/zeus3.6/* $root_dir
cp input.json $root_dir

cat > temp.txt << EOF
$root_dir
1
EOF

python3 prepare_PATH.py
rm temp.txt

cd $root_dir
csh -v ./iPATH_zeus.s
./xdzeus36
cd ..

fi

if [ $if_bgonly -ne 1 ]; then
#-----------------------------------------------
# CME setup and acceleration:
cat > temp.txt << EOF
$root_dir
0
EOF
python3 prepare_PATH.py
rm temp.txt

cd $root_dir
csh -v ./iPATH_zeus.s
./xdzeus36 <input
cd ..


#-----------------------------------------------
# Transport:
cat > temp.txt << EOF
$root_dir
2
EOF
python3 prepare_PATH.py
rm temp.txt

$MPI_comp -O3 ./Transport/parallel_wrapper.f ./Transport/transport_2.05.f -o trspt.out
$FCOMP ./Transport/combine.f -o combine.out

mkdir $root_dir/$CME_dir/$trspt_dir
mv ./trspt.out $root_dir/$CME_dir/$trspt_dir
mv ./combine.out $root_dir/$CME_dir/$trspt_dir
cp ./Transport/trspt_input $root_dir/$CME_dir/$trspt_dir
cp ./plotting/plot_iPATH.py $root_dir/$CME_dir/$trspt_dir
cp $input_file $root_dir/$CME_dir/$trspt_dir

cd $root_dir/$CME_dir/$trspt_dir
mpirun -np $thread_count trspt.out
./combine.out
rm RawData*

# Plot result:
python3 plot_iPATH.py
fi