#!/bin/bash
#SBATCH --job-name=3Q-R1T-C5T
#SBATCH --nodes=56
#SBATCH --ntasks-per-node=1
#SBATCH --mem=70G
#SBATCH --output=mpi_test_output5.txt
#SBATCH --error=mpi_test_error5.txt

cd /home/achraf.najmi/quantify-lab

# Load OpenMPI
module load OpenMPI/4.0.5-GCC-10.2.0

# Load Python environment
module load Python/3.8.6-GCCcore-10.2.0
source .venv/bin/activate

# Run the Python script using srun across nodes
# srun python3 main_stress.py --simulate --start=3 --t_count=7 --t_cancel=1 --print_simulation=h
# python3 main_experiments.py --simulate --start=3 --t_count=7 --print_circuit=p --print_simulation=d

# Run the Python script using mpirun across nodes
mpirun -np 56 python3 main_stress.py --hpc --simulate --start=3 --t_count=5 --t_cancel=1 --print_simulation=h
# mpirun -np 56 python3 main_experiments.py --hpc --simulate --start=2 --t_count=7 --print_circuit=h --print_simulation=d