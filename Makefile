# Vars of Makefile
SLURM=file
LOCAL=local
NAME=slurm_$(SLURM).sh

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
TIME=1-13:00:00

ifeq ($(SLURM), experiments)
	NP=1
	JOB_NAME="${QUBITS}Q_QD${T_COUNT}T"
	QRAM_CMD="python3 main_experiments.py --simulate --qubit_range=$(QUBITS) --t_count=$(T_COUNT) --print_circuit=p --print_simulation=d"
	HPC_CMD="srun $(QRAM_CMD)"
else ifeq ($(SLURM), stress)
	NP=64
	JOB_NAME=$(QUBITS)Q_C$(T_CANCEL)T_QD$(T_COUNT)T
	QRAM_CMD="python3 main_stress.py --hpc --simulate --qubit_range=$(QUBITS) --t_count=$(T_COUNT) --t_cancel=$(T_CANCEL) --print_simulation=h"
	HPC_CMD="mpirun -np $(NP) $(QRAM_CMD)"
endif

OUTPUT_FILE=output/$(SLURM)-output-$(JOB_NAME).txt
ERROR_FILE=output/$(SLURM)-error-$(JOB_NAME).txt

# Vars of SBATCH
SBATCH_FLAGS=--job-name=$(JOB_NAME) --nodes=$(NP) --ntasks-per-node=1 --cpus-per-task=56 --mem=70G --output=$(OUTPUT_FILE) --error=$(ERROR_FILE) --time=$(TIME)

# Default target
all:
	@echo "To execute the program on hpc, please use the following command:"
	@echo "	Please specify a variables:"
	@echo "		SLURM: stress or experiments"
	@echo "		QUBITS: Must be at least 2"
	@echo "		T_COUNT: Should be between 4 and 7"
	@echo "		T_CANCEL: Must be greater than 1"
	@echo ""
	@echo "	Also, specify a target:"
	@echo "		submit: To submit the job"
	@echo "		output: To show the output log"
	@echo "		error: To show the error log"
	@echo ""
	@echo "	Example of usage:"
	@echo "		make SLURM=experiments QUBITS=2 T_COUNT=4 submit"
	@echo "		make SLURM=stress QUBITS=2 T_COUNT=4 T_CANCEL=2 submit"
	@echo "		make SLURM=experiments QUBITS=2 T_COUNT=4 output"
	@echo "		make SLURM=stress QUBITS=2 T_COUNT=4 T_CANCEL=2 error"
	@echo ""
	@echo "To run the program locally, please use the following command:"
	@echo "	Please specify a variable:"
	@echo "		LOCAL: bilan, experiments or stress"
	@echo "		QUBITS: Must be at least 2"
	@echo "		T_COUNT: Should be between 4 and 7"
	@echo "		T_CANCEL: Must be greater than 1"
	@echo ""
	@echo "	Also, specify a target:"
	@echo "		run: To run the program"
	@echo ""
	@echo "	Example of usage:"
	@echo "		make LOCAL=bilan QUBITS=2-7 T_COUNT=4 run"
	@echo "		make LOCAL=experiments QUBITS=2 T_COUNT=4 run"
	@echo "		make LOCAL=stress QUBITS=2 T_COUNT=4 T_CANCEL=2 run"

# Target to generate the script file
script:
	@echo "#!/bin/bash" > $(NAME)
	@echo "cd /home/achraf.najmi/quantify-lab" >> $(NAME)
	@echo "module load OpenMPI/4.0.5-GCC-10.2.0" >> $(NAME)
	@echo "module load Python/3.8.6-GCCcore-10.2.0" >> $(NAME)
	@echo "source .venv/bin/activate" >> $(NAME)

# Target to submit the QRAM job on hpc
submit: script
	@echo $(HPC_CMD) >> $(NAME)
ifeq ($(SLURM), experiments)
	@sbatch $(SBATCH_FLAGS) $(NAME)
else ifeq ($(SLURM), stress)
	@sbatch $(SBATCH_FLAGS) $(NAME)
else
	@$(MAKE) --no-print-directory all
endif
	@$(MAKE) --no-print-directory clean

# Target to clean up generated files
clean:
	@rm -f slurm_experiments.sh slurm_stress.sh slurm_script.sh

# Targets to show the output and error logs
output:
	@cat $(OUTPUT_FILE)

error:
	@cat $(ERROR_FILE)

# Target to run the QRAM locally
run:
ifeq ($(LOCAL), bilan)
	@python3 main_bilan.py --qubit_range=$(QUBITS) --t_count=$(T_COUNT)
else ifeq ($(LOCAL), experiments)
	@python3 main_experiments.py --simulate --qubit_range=$(QUBITS) --t_count=$(T_COUNT) --print_circuit=p --print_simulation=d
else ifeq ($(LOCAL), stress)
	@python3 main_stress.py --simulate --qubit_range=$(QUBITS) --t_count=$(T_COUNT) --t_cancel=$(T_CANCEL) --print_simulation=h
else
	@$(MAKE) --no-print-directory all
endif

.PHONY: all script submit clean output error