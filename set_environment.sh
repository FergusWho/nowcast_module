which spack &>/dev/null || {
   echo "==> Setting up Spack ..."
   source /etc/profile.d/spack.sh
}

which sbatch &>/dev/null || {
   echo "==> Setting up Slurm ..."
   source /etc/profile.d/slurm.sh
}

echo "==> Loading Spack packages ..."

( gcc --version |& grep -q 12.2.0 ) || spack load gcc@12.2.0
( mpirun --version |& grep -q 4.1.4 ) || spack load openmpi@4.1.4
( python3 --version |& grep -q 3.10.8 ) || spack load python@3.10.8
which convert &>/dev/null || spack load imagemagick

spack load --list

echo -n "==> Setting up Python3 virtual environment: "
source ~/.venv/ipath/bin/activate
echo $VIRTUAL_ENV
