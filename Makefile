###############################################################################
# Quantify Lab Makefile
#
# A comprehensive Makefile for QRAM experiments on both local and HPC environments
###############################################################################

#==============================================================================
# CONFIGURATION VARIABLES
#==============================================================================

# Job type selection
#	SLURM Options: assessment, experiments, stress
SLURM = file
#	LOCAL Options: assessment, experiments, stress
LOCAL = local
NAME = slurm_$(SLURM).sh

# QRAM experiment parameters
#	Must be at least 2 (or a range like 2-7)
QUBITS = 0
#	Should be between 4 and 7
T_COUNT = 0
#	Must be greater than 0 (for stress tests)
T_CANCEL = 0
SPECIFIC = "qram"

# MPI and SLURM variables
#	MEMORY Options: 170G, 1.5TB
MEMORY = 170G
#	NP Options: 1, 6, 32, 64
NP = 1
#	CPUS Options: 56, 112
CPUS = 56
#	QOS Options: default-cpu, long-cpu, himem-cpu or himem-gpu
QOS = default-cpu
# Optional reservation name
RESERVATION ?=
#	SLURM Job Types: assessment, experiments, stress
SBATCH_FLAGS = --ntasks-per-node=1

# Add reservation if specified
ifneq ($(RESERVATION),)
	SBATCH_FLAGS += --reservation=$(RESERVATION)
endif

#==============================================================================
# DERIVED VARIABLES
#==============================================================================

# SLURM time configuration
ifeq ($(QOS), default-cpu)
	TIME = 1-12:00:00
	SBATCH_FLAGS += --time=$(TIME)
	NP = 64
else ifeq ($(QOS), long-cpu)
	SBATCH_FLAGS += --time=$(TIME)
	NP = 32
else ifeq ($(QOS), himem-cpu)
	CPUS = 112
	MEMORY = 1500GB
	SBATCH_FLAGS += --partition=himem
else ifeq ($(QOS), himem-gpu)
	MEMORY = 1500GB
endif

# SLURM job configuration
ifeq ($(SLURM), assessment)
	NP = 1
	JOB_NAME = "${QUBITS}Q_QD${T_COUNT}T"
	QRAM_CMD = "python3 main_assessment.py --qubit-range=$(QUBITS) --t-count=$(T_COUNT)"
	HPC_CMD = "srun $(QRAM_CMD)"
else ifeq ($(SLURM), experiments)
	JOB_NAME = "${QUBITS}Q_QD${T_COUNT}T"
#	QRAM_CMD = "python3 main_experiments.py --hpc --simulate --qubit-range=$(QUBITS) --min-qram-size=1 --t-count=$(T_COUNT) --print-circuit=h --print-simulation=h --specific=$(SPECIFIC)"
#	HPC_CMD = "mpirun -np $(NP) $(QRAM_CMD)"
	
	QRAM_CMD = "python3 main_experiments.py --hpc --simulate --qubit-range=$(QUBITS) --min-qram-size=1 --t-count=$(T_COUNT) --print-circuit=p --print-simulation=d --circuit-type=5 --specific=$(SPECIFIC)"
	HPC_CMD = "srun --mpi=pmix $(QRAM_CMD)"
else ifeq ($(SLURM), stress)
	JOB_NAME = $(QUBITS)Q_C$(T_CANCEL)T_QD$(T_COUNT)T
	QRAM_CMD = "python3 main_stress.py --hpc --simulate --qubit-range=$(QUBITS) --t-count=$(T_COUNT) --t-cancel=$(T_CANCEL) --print-simulation=h --specific=$(SPECIFIC)"
	HPC_CMD = "mpirun -np $(NP) $(QRAM_CMD)"
endif

# Output and error files
OUTPUT_FILE = output/$(SLURM)-output-$(JOB_NAME).txt
ERROR_FILE = error/$(SLURM)-error-$(JOB_NAME).txt

# SBATCH flags
# SBATCH_FLAGS += --qos=$(QOS) --job-name=$(JOB_NAME) --nodes=$(NP) --cpus-per-task=$(CPUS) --mem=$(MEMORY) --output=$(OUTPUT_FILE) --error=$(ERROR_FILE)

SBATCH_FLAGS += --qos=$(QOS) --job-name=$(JOB_NAME) --ntasks=$(NP) --cpus-per-task=$(CPUS) --mem=$(MEMORY) --output=$(OUTPUT_FILE) --error=$(ERROR_FILE)


#==============================================================================
# MAIN TARGETS
#==============================================================================

# Default target - show help
.PHONY: help
help:
	@echo "Quantify Lab Makefile Help"
	@echo "=========================="
	@echo
	@echo "HPC EXECUTION:"
	@echo "  make SLURM=<type> QUBITS=<num> T_COUNT=<num> [T_CANCEL=<num>] [QOS=<qos>] [RESERVATION=<name>] <action>"
	@echo
	@echo "  SLURM Types:"
	@echo "    assessment   - For assessment jobs"
	@echo "    experiments  - For experimental jobs"
	@echo "    stress       - For stress testing jobs (requires T_CANCEL parameter)"
	@echo
	@echo "  Parameters:"
	@echo "    QUBITS     - Number of qubits (at least 2, can be a range like 2-7)"
	@echo "    T_COUNT    - T gate count (between 4 and 7)"
	@echo "    T_CANCEL   - T cancellation count (for stress tests, >0)"
	@echo "    QOS        - Quality of service (default-cpu, long-cpu, himem-cpu, or himem-gpu)"
	@echo "    RESERVATION- Optional SLURM reservation name"
	@echo
	@echo "  Actions:"
	@echo "    submit     - Submit the job to SLURM"
	@echo "    output     - Show the output log"
	@echo "    error      - Show the error log"
	@echo "    status     - Check status of submitted jobs"
	@echo "    interactive- Start an interactive SLURM session with current settings"
	@echo
	@echo "  Examples:"
	@echo "    make SLURM=assessment QUBITS=2-7 T_COUNT=4 submit"
	@echo "    make SLURM=experiments QUBITS=2 T_COUNT=4 submit"
	@echo "    make SLURM=stress QUBITS=2 T_COUNT=4 T_CANCEL=2 QOS=long-cpu submit"
	@echo "    make SLURM=experiments QUBITS=2 T_COUNT=4 RESERVATION=myreservation submit"
	@echo "    make SLURM=experiments QUBITS=2 T_COUNT=4 interactive"
	@echo
	@echo "LOCAL EXECUTION:"
	@echo "  make LOCAL=<type> QUBITS=<num> T_COUNT=<num> [T_CANCEL=<num>] run"
	@echo
	@echo "  Examples:"
	@echo "    make LOCAL=assessment QUBITS=2-7 T_COUNT=4 run"
	@echo "    make LOCAL=experiments QUBITS=2 T_COUNT=4 run"
	@echo "    make LOCAL=stress QUBITS=2 T_COUNT=4 T_CANCEL=2 run"
	@echo
	@echo "ENVIRONMENT SETUP:"
	@echo "  make setup        - Create and setup Python environment"
	@echo "  make clean-env    - Remove Python environment"
	@echo "  make re-setup     - Rebuild Python environment from scratch"
	@echo "  make env-status   - Display current environment status"
	@echo
	@echo "DOCKER TARGETS:"
	@echo "  make build-docker  - Build the Docker image"
	@echo "  make up-docker     - Build and run the Docker container"
	@echo "  make run-docker    - Run the Docker container"
	@echo "  make down-docker   - Stop the Docker container"
	@echo "  make clean-docker  - Remove the Docker container"
	@echo "  make ps            - Show Docker processes"
	@echo "  make prune         - Remove all Docker resources"
	@echo "  make re-docker     - Rebuild and restart Docker container"

# Alias for help
all: help

#==============================================================================
# SLURM JOB TARGETS
#==============================================================================

# Generate the SLURM script file
.PHONY: script
script:
	@mkdir -p output error
	@echo "Generating SLURM script $(NAME)..."
	@echo "#!/bin/bash" > $(NAME)
	@echo "cd /home/achraf.najmi/quantify-lab" >> $(NAME)
	@echo "module purge" >> $(NAME)
	@echo "module load GCCcore/11.3.0" >> $(NAME)
	@echo "module load OpenMPI/4.1.4-GCC-11.3.0" >> $(NAME)
	@echo "module load Python/3.10.4-GCCcore-11.3.0" >> $(NAME)
	@echo "module load CMake/3.23.1-GCCcore-11.3.0" >> $(NAME)
	@echo "source .venv/bin/activate" >> $(NAME)
	@echo $(HPC_CMD) >> $(NAME)
	@chmod +x $(NAME)
	@echo "Generated $(NAME)"

# Submit the QRAM job to SLURM
.PHONY: submit
submit: script validate-params
	@if [ "$(SLURM)" = "file" ]; then \
		echo "Error: Please specify a valid SLURM job type"; \
		$(MAKE) --no-print-directory help; \
		exit 1; \
	fi
	@echo "Submitting job to SLURM..."
	@echo "Job parameters:"
	@echo "  - Type: $(SLURM)"
	@echo "  - Qubits: $(QUBITS)"
	@echo "  - T Count: $(T_COUNT)"
	@if [ "$(SLURM)" = "stress" ]; then \
		echo "  - T Cancel: $(T_CANCEL)"; \
	fi
	@echo "  - QoS: $(QOS)"
	@if [ -n "$(RESERVATION)" ]; then \
		echo "  - Reservation: $(RESERVATION)"; \
	fi
	@echo "Submitting with sbatch $(SBATCH_FLAGS)"
	@echo "Running command: $(HPC_CMD)"
	@sbatch $(SBATCH_FLAGS) $(NAME)
	@rm -f $(NAME)
	@echo "Job submitted. Output will be in: $(OUTPUT_FILE)"
	@echo "Error log will be in: $(ERROR_FILE)"

# Start an interactive SLURM session
.PHONY: interactive
interactive: validate-params
	@if [ "$(SLURM)" = "file" ]; then \
		echo "Error: Please specify a valid SLURM job type"; \
		$(MAKE) --no-print-directory help; \
		exit 1; \
	fi
	@echo "Starting interactive SLURM session..."
	@echo "Session parameters:"
	@echo "  - QoS: $(QOS)"
	@echo "  - Memory: $(MEMORY)"
	@echo "  - Time: $(TIME)"
	@if [ -n "$(RESERVATION)" ]; then \
		echo "  - Reservation: $(RESERVATION)"; \
	fi
	@srun --qos=$(QOS) --time=$(TIME) --mem=$(MEMORY) --pty bash

# Check status of submitted jobs
.PHONY: status
status:
	@echo "Checking SLURM job status..."
	@squeue -u $(shell whoami)

# Validate parameter values
.PHONY: validate-params
validate-params:
	@if [ $(QUBITS) = "0" ]; then \
		echo "Error: QUBITS parameter must be set (at least 2)"; \
		$(MAKE) --no-print-directory help; \
		exit 1; \
	fi
	@if [ $(T_COUNT) = "0" ]; then \
		echo "Error: T_COUNT parameter must be set (between 4 and 7)"; \
		$(MAKE) --no-print-directory help; \
		exit 1; \
	fi
	@if [ "$(SLURM)" = "stress" ] && [ $(T_CANCEL) = "0" ]; then \
		echo "Error: For stress tests, T_CANCEL parameter must be greater than 0"; \
		$(MAKE) --no-print-directory help; \
		exit 1; \
	fi

# Show the output log
.PHONY: output
output:
	@if [ -f "$(OUTPUT_FILE)" ]; then \
		cat $(OUTPUT_FILE); \
	else \
		echo "Output file $(OUTPUT_FILE) does not exist yet."; \
	fi

# Show the error log
.PHONY: error
error:
	@if [ -f "$(ERROR_FILE)" ]; then \
		cat $(ERROR_FILE); \
	else \
		echo "Error file $(ERROR_FILE) does not exist yet."; \
	fi

# Clean up generated files
.PHONY: clean
clean:
	@rm -f $(NAME)
	@echo "Temporary files cleaned"

#==============================================================================
# LOCAL RUN TARGETS
#==============================================================================

# Run the QRAM locally
.PHONY: run
run: validate-params
	@if [ "$(LOCAL)" = "local" ]; then \
		echo "Error: Please specify a valid LOCAL job type"; \
		$(MAKE) --no-print-directory help; \
		exit 1; \
	fi
	@echo "Running locally: $(LOCAL)"
	@if [ "$(LOCAL)" = "assessment" ]; then \
		python3 main_assessment.py --qubit-range=$(QUBITS) --t-count=$(T_COUNT); \
	elif [ "$(LOCAL)" = "experiments" ]; then \
		python3 main_experiments.py --simulate --qubit-range=$(QUBITS) --t-count=$(T_COUNT) --print-circuit=p --print-simulation=d --specific=$(SPECIFIC); \
	elif [ "$(LOCAL)" = "stress" ]; then \
		python3 main_stress.py --simulate --qubit-range=$(QUBITS) --t-count=$(T_COUNT) --t-cancel=$(T_CANCEL) --print-simulation=h --specific=$(SPECIFIC); \
	fi

#==============================================================================
# ENVIRONMENT SETUP TARGETS
#==============================================================================

# Create build_env.sh script if it doesn't exist
build_env.sh:
	@echo "Creating build_env.sh script..."
	@echo '#!/bin/bash' > build_env.sh
	@echo '# Script to setup Python environment for Quantify Lab' >> build_env.sh
	@echo '' >> build_env.sh
	@echo '# Exit on error' >> build_env.sh
	@echo 'set -e' >> build_env.sh
	@echo '' >> build_env.sh
	@echo '# Check for required dependencies' >> build_env.sh
	@echo 'for cmd in python3 pip3; do' >> build_env.sh
	@echo '	if ! command -v $$cmd &> /dev/null; then' >> build_env.sh
	@echo '		echo "Error: $$cmd is required but not installed."' >> build_env.sh
	@echo '		exit 1' >> build_env.sh
	@echo '	fi' >> build_env.sh
	@echo 'done' >> build_env.sh
	@echo '' >> build_env.sh
	@echo '# Check Python version (3.10+ recommended)' >> build_env.sh
	@echo 'python_version=$$(python3 -c "import sys; print(sys.version_info.major, sys.version_info.minor)" | tr " " ".")' >> build_env.sh
	@echo 'python_major=$$(echo $$python_version | cut -d. -f1)' >> build_env.sh
	@echo 'python_minor=$$(echo $$python_version | cut -d. -f2)' >> build_env.sh
	@echo 'if [ $$python_major -lt 3 ] || [ $$python_major -eq 3 -a $$python_minor -lt 10 ]; then' >> build_env.sh
	@echo '	echo "Warning: Python 3.10+ is recommended. Current version: $$(python3 --version)"' >> build_env.sh
	@echo '	echo "Do you want to continue anyway? [y/N]"' >> build_env.sh
	@echo '	read -r response' >> build_env.sh
	@echo '	if [[ ! "$$response" =~ ^[Yy]$$ ]]; then' >> build_env.sh
	@echo '		echo "Setup aborted."' >> build_env.sh
	@echo '		exit 1' >> build_env.sh
	@echo '	fi' >> build_env.sh
	@echo 'fi' >> build_env.sh
	@echo '' >> build_env.sh

	@echo 'PYTHON=python$$python_major.$$python_minor' >> build_env.sh
	@echo 'echo "Using Python interpreter: $$PYTHON"' >> build_env.sh

	@echo 'echo "Setting up Python environment..."' >> build_env.sh
	@echo '' >> build_env.sh
	@echo '# Create virtual environment if it doesn'\''t exist' >> build_env.sh
	@echo 'if [ ! -d ".venv" ]; then' >> build_env.sh
	@echo '	echo "Creating virtual environment..."' >> build_env.sh
	@echo '	$$PYTHON -m venv .venv --clear' >> build_env.sh
	@echo 'else' >> build_env.sh
	@echo '	echo "Virtual environment already exists."' >> build_env.sh
	@echo 'fi' >> build_env.sh
	@echo '' >> build_env.sh
	@echo '# Activate virtual environment' >> build_env.sh
	@echo 'echo "Activating virtual environment..."' >> build_env.sh
	@echo 'source .venv/bin/activate' >> build_env.sh
	@echo '' >> build_env.sh
	@echo '# Upgrade core packages and install dependencies' >> build_env.sh
	@echo 'echo "Installing dependencies..."' >> build_env.sh
	@echo '$$PYTHON -m pip install --no-cache-dir --upgrade pip setuptools wheel' >> build_env.sh
	@echo 'if [ -f "requirements.txt" ]; then' >> build_env.sh
	@echo '	$$PYTHON -m pip install --no-cache-dir -r requirements.txt' >> build_env.sh
	@echo '	env MPICC=mpicc pip install --no-cache-dir mpi4py' >> build_env.sh
	@echo 'else' >> build_env.sh
	@echo '	echo "Warning: requirements.txt not found. No packages installed."' >> build_env.sh
	@echo 'fi' >> build_env.sh
	@echo '' >> build_env.sh
	@echo '# Run setup script' >> build_env.sh
	@echo 'if [ -f "insert_missed_code.py" ]; then' >> build_env.sh
	@echo '	echo "Configuring the environment..."' >> build_env.sh
	@echo '	$$PYTHON insert_missed_code.py local' >> build_env.sh
	@echo 'else' >> build_env.sh
	@echo '	echo "Warning: insert_missed_code.py not found. Skipping configuration."' >> build_env.sh
	@echo 'fi' >> build_env.sh
	@echo '' >> build_env.sh
	@echo 'echo "Environment setup complete."' >> build_env.sh
	@chmod +x build_env.sh
	@echo "Created build_env.sh"

# Setup the Python environment using the external script
.PHONY: setup
setup: build_env.sh
	@echo "Setting up Python environment..."
	@bash build_env.sh
	@rm -f build_env.sh
	@echo "Python environment setup complete."	

# Clean the Python environment
.PHONY: clean-env
clean-env:
	@echo "Removing Python virtual environment..."
	@rm -rf .venv
	@echo "Python environment removed."

# Re-create the Python environment
.PHONY: re-setup
re-setup: clean-env setup

# Display current environment status
.PHONY: env-status
env-status:
	@echo "Checking environment status..."
	@echo "Python version:"
	@if command -v python3 &> /dev/null; then \
		python3 --version; \
	else \
		echo "Python3 not found"; \
	fi
	@echo
	@echo "Virtual environment:"
	@if [ -d ".venv" ]; then \
		echo "Virtual environment exists at .venv"; \
		if [ -f ".venv/bin/python" ]; then \
			echo "Python: $$(readlink -f .venv/bin/python)"; \
		fi; \
		echo "Installed packages:"; \
		if [ -f ".venv/bin/pip" ]; then \
			.venv/bin/pip list; \
		else \
			echo "Pip not found in virtual environment"; \
		fi; \
	else \
		echo "Virtual environment not found"; \
	fi

#==============================================================================
# DOCKER TARGETS
#==============================================================================

# Build the Docker image
.PHONY: build-docker
build-docker:
	@echo "Building Docker image..."
	@docker build -t quantify-env:latest .
	@echo "Docker image built."

# Run the Docker container
.PHONY: up-docker
up-docker: build-docker
	@$(MAKE) --no-print-directory run-docker

# Run the Docker container without rebuilding
.PHONY: run-docker
run-docker:
	@echo "Running Docker container..."
	@docker run -it --rm -v $(shell pwd):/app --name quantify-env quantify-env:latest /bin/bash

# Down the Docker container
.PHONY: down-docker
down-docker:
	@echo "Stopping Docker container..."
	-@docker stop quantify-env
	@echo "Docker container stopped."

# Clean the Docker container
.PHONY: clean-docker
clean-docker: down-docker
	@echo "Removing Docker container..."
	-@docker rm quantify-env
	@echo "Docker container removed."

# Show the Docker processes
.PHONY: ps
ps:
	@echo "Docker processes:"
	@docker ps -a

# Rebuild the Docker container from scratch
.PHONY: re-docker
re-docker: prune up-docker

# Prune the Docker system
.PHONY: prune
prune: clean-docker
	@echo "Pruning Docker system..."
	@docker system prune --all --force
	@echo "Docker system pruned."