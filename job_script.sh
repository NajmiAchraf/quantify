#!/bin/bash
#SBATCH --job-name=3Q7T1C
#SBATCH --nodes=10
#SBATCH --ntasks=1
#SBATCH --mem=70G

cd /home/achraf.najmi/quantify-lab/

# Load Python environment
module load Python/3.8.6-GCCcore-10.2.0
source .venv/bin/activate

# Run the Python script using srun across nodes
srun python3 main_stress.py --simulate --start=3 --t_count=7 --t_cancel=1 --print_simulation=h