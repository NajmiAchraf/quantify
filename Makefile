# Makefile for QRAM Experiments

# Variables
SLURM = file
LOCAL = local
NAME = slurm_$(SLURM).sh

# QRAM Experiment Variables
QUBITS = 0
T_COUNT = 0
T_CANCEL = 0
SPECIFIC = "qram"

# MPI and SLURM Variables
NP = 1
QOS = default-cpu

# SLURM Time Configuration
ifeq ($(QOS), default-cpu)
	TIME = 1-12:00:00
	NP = 64
else ifeq ($(QOS), long-cpu)
	TIME = 7-00:00:00
	NP = 32
endif

# SLURM Job Configuration
ifeq ($(SLURM), assessment)
	NP = 1
	JOB_NAME = "${QUBITS}Q_QD${T_COUNT}T"
	QRAM_CMD = "python3 main_bilan.py --qubit-range=$(QUBITS) --t-count=$(T_COUNT)"
	HPC_CMD = "srun $(QRAM_CMD)"
else ifeq ($(SLURM), experiments)
	JOB_NAME = "${QUBITS}Q_QD${T_COUNT}T"
	QRAM_CMD = "python3 main_experiments.py --hpc --simulate --qubit-range=$(QUBITS) --t-count=$(T_COUNT) --print-circuit=h --print-simulation=h --specific=$(SPECIFIC)"
	HPC_CMD = "mpirun -np $(NP) $(QRAM_CMD)"
else ifeq ($(SLURM), stress)
	JOB_NAME = $(QUBITS)Q_C$(T_CANCEL)T_QD$(T_COUNT)T
	QRAM_CMD = "python3 main_stress.py --hpc --simulate --qubit-range=$(QUBITS) --t-count=$(T_COUNT) --t-cancel=$(T_CANCEL) --print-simulation=h --specific=$(SPECIFIC)"
	HPC_CMD = "mpirun -np $(NP) $(QRAM_CMD)"
endif

# Output and Error Files
OUTPUT_FILE = output/$(SLURM)-output-$(JOB_NAME).txt
ERROR_FILE = error/$(SLURM)-error-$(JOB_NAME).txt

# SBATCH Flags
SBATCH_FLAGS = --qos=$(QOS) --job-name=$(JOB_NAME) --nodes=$(NP) --ntasks-per-node=1 --cpus-per-task=56 --mem=170G --output=$(OUTPUT_FILE) --error=$(ERROR_FILE) --time=$(TIME)

# Default Target
all:
	@echo "To execute the program on HPC, please use the following command:"
	@echo "	Please specify variables:"
	@echo "		SLURM: assessment, experiments or stress"
	@echo "		QUBITS: Must be at least 2"
	@echo "		T_COUNT: Should be between 4 and 7"
	@echo "		T_CANCEL: Must be greater than 1"
	@echo "		For long-cpu, please specify QOS=long-cpu"
	@echo ""
	@echo "	Also, specify a target:"
	@echo "		submit: To submit the job"
	@echo "		output: To show the output log"
	@echo "		error: To show the error log"
	@echo ""
	@echo "	Example of usage:"
	@echo "		make SLURM=assessment QUBITS=2-7 T_COUNT=4 submit"
	@echo "		make SLURM=experiments QUBITS=2 T_COUNT=4 submit"
	@echo "		make SLURM=stress QUBITS=2 T_COUNT=4 T_CANCEL=2 submit"
	@echo "		make SLURM=assessment QUBITS=2-7 T_COUNT=4 output"
	@echo "		make SLURM=experiments QUBITS=2 T_COUNT=4 output"
	@echo "		make SLURM=stress QUBITS=2 T_COUNT=4 T_CANCEL=2 error"
	@echo ""
	@echo "To run the program locally, please use the following command:"
	@echo "	Please specify variables:"
	@echo "		LOCAL: assessment, experiments or stress"
	@echo "		QUBITS: Must be at least 2"
	@echo "		T_COUNT: Should be between 4 and 7 (for assessment, it should be between 4 and 6)"
	@echo "		T_CANCEL: Must be greater than 0"
	@echo ""
	@echo "	Also, specify a target:"
	@echo "		run: To run the program"
	@echo ""
	@echo "	Example of usage:"
	@echo "		make LOCAL=assessment QUBITS=2-7 T_COUNT=4 run"
	@echo "		make LOCAL=experiments QUBITS=2 T_COUNT=4 run"
	@echo "		make LOCAL=stress QUBITS=2 T_COUNT=4 T_CANCEL=2 run"

# Generate the script file
script:
	@echo "#!/bin/bash" > $(NAME)
	@echo "cd /home/achraf.najmi/quantify-lab" >> $(NAME)
	@echo "module load OpenMPI/3.1.4-GCC-8.3.0" >> $(NAME)
	@echo "module load CMake/3.15.3-GCCcore-8.3.0" >> $(NAME)
	@echo "module load Python/3.7.4-GCCcore-8.3.0" >> $(NAME)
	@echo "source .venv/bin/activate" >> $(NAME)

# Submit the QRAM job on HPC
submit: script
	@mkdir -p output
	@echo $(HPC_CMD) >> $(NAME)
ifeq ($(SLURM), assessment)
	@sbatch $(SBATCH_FLAGS) $(NAME)
else ifeq ($(SLURM), experiments)
	@sbatch $(SBATCH_FLAGS) $(NAME)
else ifeq ($(SLURM), stress)
#	@echo sbatch $(SBATCH_FLAGS) $(NAME)
	@sbatch $(SBATCH_FLAGS) $(NAME)
else
	@$(MAKE) --no-print-directory all
endif
	@$(MAKE) --no-print-directory clean

# Clean up generated files
clean:
	@rm -f $(NAME)

# Show the output log
output:
	@cat $(OUTPUT_FILE)

# Show the error log
error:
	@cat $(ERROR_FILE)

# Run the QRAM locally
run:
ifeq ($(LOCAL), assessment)
	@python3 main_bilan.py --qubit-range=$(QUBITS) --t-count=$(T_COUNT)
else ifeq ($(LOCAL), experiments)
	@python3 main_experiments.py --simulate --qubit-range=$(QUBITS) --t-count=$(T_COUNT) --print-circuit=p --print-simulation=d --specific=$(SPECIFIC)
else ifeq ($(LOCAL), stress)
	@python3 main_stress.py --simulate --qubit-range=$(QUBITS) --t-count=$(T_COUNT) --t-cancel=$(T_CANCEL) --print-simulation=h --specific=$(SPECIFIC)
else
	@$(MAKE) --no-print-directory all
endif

# Install the Python dependencies
build:
	@python3 -m venv .venv
	@. .venv/bin/activate
	@python3 -m pip install --upgrade pip
	@python3 -m pip install -r requirements.txt
	@python3 insert_missed_code.py local

re:
	@rm -rf .venv
	@$(MAKE) --no-print-directory build

# Docker Targets ###############################################################

# Build the Docker image
build-docker:
	@docker build -t quantify-env:latest .

# Run the Docker container
up-docker: build-docker
	@$(MAKE) --no-print-directory run-docker

# Run the Docker container without rebuilding
run-docker:
	@docker run -it --rm -v $(shell pwd):/app --name quantify-env quantify-env:latest /bin/bash

# Down the Docker container
down-docker:
	-@docker stop quantify-env

# Clean the Docker container
clean-docker: down-docker
	-@docker rm quantify-env

# Show the Docker processes
ps:
	@docker ps -a

# Rebuild the Docker container from scratch
re-docker: prune up-docker

# Prune the Docker system
prune: clean-docker
	@docker system prune --all

.PHONY: all script submit clean output error run build build-docker up-docker run-docker down-docker clean-docker ps re prune