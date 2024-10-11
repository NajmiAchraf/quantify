# Define variables
QUBITS=3
T_CANCEL=1
T_COUNT=5

CPUS_PER_TASK=56
MEMORY=70G
TIME=1-12:00:00

ifeq ($(TARGET), experiments)
	NAME=job_experiments.sh
	NP=1
	JOB_NAME="${QUBITS}Q-QD${T_COUNT}T"
	OUTPUT_FILE=experiments_output_$(QUBITS)_Qubits_Query_Decomposition_$(T_COUNT)_T.txt
	ERROR_FILE=experiments_error_$(QUBITS)_Qubits_Query_Decomposition_$(T_COUNT)_T.txt
else ifeq ($(TARGET), stress)
	NAME=job_stress.sh
	NP=64
	JOB_NAME=$(QUBITS)Q-C$(T_CANCEL)T-QD$(T_COUNT)T
	OUTPUT_FILE=stress_output_$(QUBITS)_Qubits_Query_Decomposition_$(T_COUNT)_T.txt
	ERROR_FILE=stress_error_$(QUBITS)_Qubits_Query_Decomposition_$(T_COUNT)_T.txt
endif

# Default target
all: $(TARGET)

# Target to generate the job file
job:
	@echo "#!/bin/bash" > $(NAME)
	@echo "#SBATCH --job-name=$(JOB_NAME)" >> $(NAME)
	@echo "#SBATCH --nodes=$(NP)" >> $(NAME)
	@echo "#SBATCH --ntasks-per-node=1" >> $(NAME)
	@echo "#SBATCH --cpus-per-task=$(CPUS_PER_TASK)" >> $(NAME)
	@echo "#SBATCH --mem=$(MEMORY)" >> $(NAME)
	@echo "#SBATCH --output=$(OUTPUT_FILE)" >> $(NAME)
	@echo "#SBATCH --error=$(ERROR_FILE)" >> $(NAME)
	@echo "#SBATCH --time=$(TIME)" >> $(NAME)

	@echo "" >> $(NAME)

	@echo "cd /home/achraf.najmi/quantify-lab" >> $(NAME)

	@echo "" >> $(NAME)

	@echo "# Load OpenMPI" >> $(NAME)
	@echo "module load OpenMPI/4.0.5-GCC-10.2.0" >> $(NAME)

	@echo "" >> $(NAME)

	@echo "# Load Python environment" >> $(NAME)
	@echo "module load Python/3.8.6-GCCcore-10.2.0" >> $(NAME)
	@echo "source .venv/bin/activate" >> $(NAME)
	@echo "" >> $(NAME)

# Target to submit the job stress
stress: job
	@echo "mpirun -np $(NP) python3 main_stress.py --hpc --simulate --start=$(QUBITS) --t_count=$(T_COUNT) --t_cancel=$(T_CANCEL) --print_simulation=h" >> $(NAME)
	@sbatch $(NAME)
	@$(MAKE) clean

# Target to submit the job experiments
experiments: job
	@echo "mpirun -np $(NP) python3 main_experiments.py --simulate --start=$(QUBITS) --t_count=$(T_COUNT) --print_circuit=p --print_simulation=d" >> $(NAME)
	@sbatch $(NAME)
	@$(MAKE) clean

# Target to clean up generated files
clean:
	@rm -f job_experiments.sh job_stress.sh

output:
	@cat $(OUTPUT_FILE)

error:
	@cat $(ERROR_FILE)

.PHONY: all job stress experiments clean output error