# QUANTIFY [![arXiv](https://img.shields.io/badge/arXiv-2007.10893-b31b1b.svg)](https://arxiv.org/abs/2007.10893)

QUANTIFY is a collection of tools used for the analysis and optimisation of quantum circuits. QUANTIFY is based on Google Cirq. QUANTIFY includes:
* a library of arithmetic circuits
    - Shor's algorithm as formulated in [arXiv:1611.07995](https://arxiv.org/abs/1611.07995)
    - The T-count optimized integer multiplier from [arXiv:1706.05113](https://arxiv.org/pdf/1706.05113.pdf)
    - The quantum addition circuits from [arXiv:0910.2530](https://arxiv.org/abs/0910.2530)
* a library of Toffoli decompositions which probably covers all known Toffoli gate decompositions
* novel optimisation strategies compatible with surface code layouts
* circuit structure analysis tools
* bucket brigade QRAM circuits as used in [![arXiv](https://img.shields.io/badge/arXiv-2002.09340-b31b1b.svg)](https://arxiv.org/abs/2002.09340)
* an analysis of the scheduling of distillation procedures in surface code layouts [![arXiv](https://img.shields.io/badge/arXiv-1906.06400-b31b1b.svg)](https://arxiv.org/abs/1906.06400)

[ISVLSI QCW Presentation of QUANTIFY](https://docs.google.com/presentation/d/1zcHJ25BphWS48wtRnaEK8xZZjGzoP6Q6LfkSKXuvHuY/edit?usp=sharing)

Documentation, code, and examples are WIP.

Examples are in the `examples` and `tests` folder.

## Constructing the Environment on System

### Prerequisites on Ubuntu 22.04

Install the required packages:

```bash
sudo apt-get install -y python3.7 python3.7-dev python3.7-venv python3-pip cmake make build-essential libssl-dev libffi-dev
```

### Building the Environment for Python3.7

Set up the Python virtual environment and install dependencies:

```bash
make build
```

### Running the Experiments

Run the experiments using the Makefile:

```bash
make
```

## Constructing the Environment on Docker

### Prerequisites

Ensure you have [Docker](https://docs.docker.com/engine/install/ubuntu/) installed on Ubuntu.

#### Install the required packages

```bash
sudo apt-get install -y make
```

### First Time Setup

Build the Docker image and set up the environment:

```bash
make up-docker
```

### Subsequent Runs

Run the Docker container without rebuilding the image:

```bash
make run-docker
```

### Running the Experiments Inside the Docker Container

Once inside the Docker container, you can run the experiments:

```bash
make
```
## Citation

To cite, please use:
```
@INPROCEEDINGS{quantify2020,
  author={O. {Oumarou} and A. {Paler} and R. {Basmadjian}},
  booktitle={2020 IEEE Computer Society Annual Symposium on VLSI (ISVLSI)}, 
  title={QUANTIFY: A Framework for Resource Analysis and Design Verification of Quantum Circuits}, 
  year={2020},
  pages={126-131},}

@INPROCEEDINGS{quantify2024,
  author={A. {Najmi} and A. {Paler} and R. {Basmadjian}},
  booktitle={2024 IEEE Computer Society Annual Symposium on VLSI (ISVLSI)}, 
  title={QUANTIFY: A Framework for Resource Analysis and Design Verification of Quantum Circuits}, 
  year={2024},
  pages={TBD},}
```