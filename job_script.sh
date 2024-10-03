#!/bin/bash
#SBATCH --job-name=3Q6TR1T
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mem=50G

# Load Python environment
module load Python/3.8.6-GCCcore-10.2.0
source /home/achraf.najmi/quantify-lab/.venv/bin/activate

# Run the Python script using srun across nodes
srun python3 /home/achraf.najmi/quantify-lab/main_stress.py y h h 3 3