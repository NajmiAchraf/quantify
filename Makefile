# Vars of Makefile
TARGET=script
NAME=slurm_$(TARGET).sh

# Vars of QRAM Experiments
QUBITS=3
T_CANCEL=1
T_COUNT=5

# Var of mpi4py and SLURM
NP=1

# Vars of SLURM
CPUS_PER_TASK=56
MEMORY=70G
TIME=1-12:00:00

ifeq ($(TARGET), experiments)
	NP=1
	JOB_NAME="${QUBITS}Q-QD${T_COUNT}T"
	QRAM_CMD="python3 main_experiments.py --simulate --qubit_range=$(QUBITS) --t_count=$(T_COUNT) --print_circuit=p --print_simulation=d"
else ifeq ($(TARGET), stress)
	NP=64
	JOB_NAME=$(QUBITS)Q-C$(T_CANCEL)T-QD$(T_COUNT)T
	QRAM_CMD="python3 main_stress.py --hpc --simulate --qubit_range=$(QUBITS) --t_count=$(T_COUNT) --t_cancel=$(T_CANCEL) --print_simulation=h"
endif

OUTPUT_FILE=$(TARGET)_output_$(JOB_NAME).txt
ERROR_FILE=$(TARGET)_error_$(JOB_NAME).txt

# Vars of SBATCH
MPI_CMD="mpirun -np $(NP) $(QRAM_CMD)"
SBATCH_FLAGS=--job-name=$(JOB_NAME) --nodes=$(NP) --ntasks-per-node=1 --cpus-per-task=$(CPUS_PER_TASK) --mem=$(MEMORY) --output=$(OUTPUT_FILE) --error=$(ERROR_FILE) --time=$(TIME)

# Default target
all: $(TARGET)

# Target to generate the slurm file
slurm:
	@echo "#!/bin/bash" > $(NAME)
	@echo "cd /home/achraf.najmi/quantify-lab" >> $(NAME)
	@echo "module load OpenMPI/4.0.5-GCC-10.2.0" >> $(NAME)
	@echo "module load Python/3.8.6-GCCcore-10.2.0" >> $(NAME)
	@echo "source .venv/bin/activate" >> $(NAME)

# Target to submit the slurm job
submit: slurm
	@echo $(MPI_CMD) >> $(NAME)
	@sbatch $(SBATCH_FLAGS) $(NAME)
	@$(MAKE) clean

# Exception of script target
script:
	@echo "Please specify a target: stress or experiments"
	@echo "Also, specify the dependencies: submit, output or error"
	@echo "How to use:"
	@echo "	make TARGET={stress, experiments} {submit, output, error}"

# Target to clean up generated files
clean:
	@rm -f slurm_experiments.sh slurm_stress.sh

output:
	@cat $(OUTPUT_FILE)

error:
	@cat $(ERROR_FILE)

.PHONY: all slurm submit clean output error