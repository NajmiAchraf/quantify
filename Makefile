# Vars of Makefile
TASK=script
NAME=slurm_$(TASK).sh

# Vars of QRAM Experiments
# Qubits must be at least 2.
QUBITS=0
# T count is between 4 and 7.
T_COUNT=0
# T cancel is greater than 1.
T_CANCEL=0

# Var of mpi4py and SLURM
NP=1

# Vars of SLURM
TIME=1-12:00:00

ifeq ($(TASK), experiments)
	NP=1
	JOB_NAME="${QUBITS}Q_QD${T_COUNT}T"
	QRAM_CMD="python3 main_experiments.py --simulate --qubit_range=$(QUBITS) --t_count=$(T_COUNT) --print_circuit=p --print_simulation=d"
else ifeq ($(TASK), stress)
	NP=64
	JOB_NAME=$(QUBITS)Q_C$(T_CANCEL)T_QD$(T_COUNT)T
	QRAM_CMD="python3 main_stress.py --hpc --simulate --qubit_range=$(QUBITS) --t_count=$(T_COUNT) --t_cancel=$(T_CANCEL) --print_simulation=h"
endif

OUTPUT_FILE=output/$(TASK)-output-$(JOB_NAME).txt
ERROR_FILE=output/$(TASK)-error-$(JOB_NAME).txt

# Vars of SBATCH
MPI_CMD="mpirun -np $(NP) $(QRAM_CMD)"
SBATCH_FLAGS=--job-name=$(JOB_NAME) --nodes=$(NP) --ntasks-per-node=1 --cpus-per-task=56 --mem=70G --output=$(OUTPUT_FILE) --error=$(ERROR_FILE) --time=$(TIME)

# Default target
all:
	@echo "Please specify a variables:"
	@echo "	TASK: stress or experiments"
	@echo "	QUBITS: Must be at least 2"
	@echo "	T_COUNT: Should be between 4 and 7"
	@echo "	T_CANCEL: Must be greater than 1"
	@echo ""
	@echo "Also, specify a target:"
	@echo "	submit: To submit the job"
	@echo "	output: To show the output log"
	@echo "	error: To show the error log"
	@echo ""
	@echo "Example of usage:"
	@echo "	make TASK=experiments QUBITS=2 T_COUNT=4 submit"
	@echo "	make TASK=stress QUBITS=2 T_COUNT=4 T_CANCEL=2 submit"
	@echo "	make TASK=experiments QUBITS=2 T_COUNT=4 output"
	@echo "	make TASK=stress QUBITS=2 T_COUNT=4 T_CANCEL=2 error"

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
ifeq ($(TASK), experiments)
	@sbatch $(SBATCH_FLAGS) $(NAME)
else ifeq ($(TASK), stress)
	@sbatch $(SBATCH_FLAGS) $(NAME)
else
	$(MAKE) all
endif
	@$(MAKE) clean

# Target to clean up generated files
clean:
	@rm -f slurm_experiments.sh slurm_stress.sh slurm_script.sh

output:
	@cat $(OUTPUT_FILE)

error:
	@cat $(ERROR_FILE)

.PHONY: all slurm submit clean output error