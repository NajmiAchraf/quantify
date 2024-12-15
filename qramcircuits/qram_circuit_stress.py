import cirq
import copy
import itertools
import os
import time
import numpy as np
import fasteners

from functools import partial
import multiprocessing
from multiprocessing.managers import DictProxy

import optimizers as qopt

from qramcircuits.qram_circuit_experiments import QRAMCircuitExperiments

from utils.counting_utils import *
from utils.print_utils import *


#######################################
# QRAM Circuit Stress
#######################################

class QRAMCircuitStress(QRAMCircuitExperiments):
    """
    QRAM circuit stress experiment.

    Attributes:
        _stress_bilan (DictProxy): The stress bilan.
        _combinations (itertools.combinations[tuple[int, ...]]): The combinations.
        __circuit_save (cirq.Circuit): The circuit save.
        __circuit_modded_save (cirq.Circuit): The modded circuit save.
        __length_combinations (int): The length of the combinations.
        __nbr_combinations (int): The number of combinations.
        __t_count (int): The T count.
        __rank (int): The rank of the MPI process.
        __chunk (int): The chunk size for the MPI process.

    Methods:
        __init__(nbr_combinations: int = 1): Initializes the QRAM circuit stress experiment.

        _core(nr_qubits: int): Core function of the experiment.
        _stress(): Stress experiment for the bucket brigade circuit.
        __initialize_circuits(): Initializes the circuits for the stress experiment.
        __generate_combinations(): Generates combinations of T gate indices.
        __simulate_local(combinations): Simulates the stress experiment locally.
        __simulate_with_multiprocessing(combinations): Uses multiprocessing to parallelize the stress testing.
        __simulate_sequentially(combinations): Simulates the stress experiment sequentially.
        __simulate_hpc(combinations): Uses MPI to parallelize the stress testing.
        __run_non_simulation(combinations): Runs the stress experiment without simulation.
        __extract_results(): Extracts and prints the results of the stress experiment.
        _stress_experiment(indices: tuple[int, ...]): Runs a single stress experiment.
        __print_bilan(): Prints the bilan of the stress experiment.
        __export_bilan(): Exports the bilan of the stress experiment.

        _simulate_circuit(): Simulates the circuit.
    """

    _stress_bilan: 'DictProxy[str, list[str]]' = multiprocessing.Manager().dict()

    _combinations: 'itertools.combinations[tuple[int, ...]]'

    __circuit_save: cirq.Circuit
    __circuit_modded_save: cirq.Circuit

    __length_combinations: int = 0
    __nbr_combinations: int = 1
    __t_count: int = 2

    __rank: int
    __chunk: int

    def __init__(self, nbr_combinations: int = 1) -> None:
        super().__init__()

        self.__nbr_combinations = nbr_combinations

    #######################################
    # core functions
    #######################################

    def _core(self, nr_qubits: int) -> None:
        """
        Core function of the experiment.
        """

        super(QRAMCircuitExperiments, self)._core(nr_qubits=nr_qubits)

        self._stress()

    def _stress(self) -> None:
        """
        Stress experiment for the bucket brigade circuit.
        """

        self.__initialize_circuits()
        self._start_time = time.time()
        combinations = self.__generate_combinations()

        if self._simulate and not self._hpc:
            self.__simulate_local(combinations)
        elif self._simulate and self._hpc:
            self.__simulate_hpc(combinations)
        elif not self._simulate and not self._hpc:
            self.__run_non_simulation(combinations)

    def __initialize_circuits(self):
        self.__circuit_save = copy.deepcopy(self._bbcircuit.circuit)
        self.__circuit_modded_save = copy.deepcopy(self._bbcircuit_modded.circuit)
        self.__t_count = count_t_of_circuit(self.__circuit_modded_save)

    def __generate_combinations(self):
        combinations = itertools.combinations(range(1, self.__t_count + 1), self.__nbr_combinations)
        self._combinations = copy.deepcopy(combinations)
        return combinations

    def __simulate_local(self, combinations):
        self.__simulate_sequentially(combinations)
        self.__extract_results()

    def __simulate_sequentially(self, combinations):
        """
        On each combination, we use multiprocessing to parallelize the stress testing
        """

        for indices in combinations:
            self._stress_experiment(indices)
            self.__length_combinations += 1

    def __simulate_hpc(self, combinations):
        """
        Use MPI to parallelize the stress testing
        """

        from mpi4py import MPI

        # Initialize MPI
        comm = MPI.COMM_WORLD
        self.__rank = comm.Get_rank()
        size = comm.Get_size()

        # Determine the range of work for this MPI process
        # print("rank, size : ", rank, size)
        total_work = list(copy.deepcopy(combinations))

        # Split the total work into chunks based on the number of ranks
        work_chunks = np.array_split(total_work, size)
        local_work = work_chunks[self.__rank] if self.__rank < len(work_chunks) else []
        self.__chunk = len(work_chunks[self.__rank]) if self.__rank < len(work_chunks) else 0

        # print("rank, local_work : ", rank, local_work)

        result = []
        for indices in local_work:
            self.__length_combinations += 1
            result.append(self._stress_experiment(indices))

        # for item in result:
        #     for map_name, value in item.items():
        #         print(f"rank, map_name, value : {rank}, {map_name}, {value}")

        # Ensure results are serializable
        serializable_result = {map_name: value for item in result for map_name, value in item.items()}
        # print(f"rank, serializable_result : {rank}, {serializable_result}")

        # Gather results from all MPI processes
        results = comm.gather(serializable_result, root=0)

        if self.__rank == 0:
            self.__length_combinations = 0
            for _ in combinations:
                self.__length_combinations += 1

            for item in results:
                for map_name, value in item.items():
                    # print(f"map_name, value : {map_name}, {value}")
                    if len(value) != 0:
                        self._stress_bilan[map_name] = value

            self.__extract_results()

    def __run_non_simulation(self, combinations):
        for indices in combinations:
            time.sleep(0.5)
            self._stress_experiment(indices)
            self.__length_combinations += 1
        self.__extract_results()

    def __extract_results(self):
        """
        Extract the results.
        """

        self._stop_time = elapsed_time(self._start_time)
        if self._simulate:
            self.__print_bilan()
            self.__export_bilan()
        print(f"Time elapsed for stress testing {self.__length_combinations} unique combinations: {self._stop_time}", end="\n\n")

    def _stress_experiment(self, indices: 'tuple[int, ...]') -> 'DictProxy[str, list[str]]':
        """
        Stress experiment for the bucket brigade circuit.

        Args:
            indices (tuple[int, ...]): The indices.
        """

        # Ensure the lock file exists
        lock_file = 'file.lock'
        if not os.path.exists(lock_file):
            open(lock_file, 'w').close()

        start = time.time()

        with fasteners.InterProcessLock(lock_file):
            if self._hpc:
                colpr("w", "\nRank", end=": ")
                colpr("r", f"{self.__rank}")
                colpr("y", "Loading stress experiment", end=" ")
                colpr("r", f"#{self.__length_combinations}", end=" ")
                colpr("y", "of", end=" ")
                colpr("r", f"{self.__chunk}", end=" ")
                colpr("y", "with T gate indices:", end=" ")
            else:
                colpr("y", "\nLoading stress experiment with T gate indices:", end=" ")
            colpr("r", ' '.join(map(str, indices)), end="\n\n")

        self._bbcircuit.circuit = copy.deepcopy(self.__circuit_save)
        self._bbcircuit_modded.circuit = copy.deepcopy(self.__circuit_modded_save)

        self._bbcircuit_modded.circuit = qopt.CancelTGate(self._bbcircuit_modded.circuit, self._bbcircuit_modded.qubit_order).optimize_circuit(indices)

        self._simulated = False
        self._results()

        if self._simulate:
            self._stress_bilan[",".join(map(str, indices))] = self._Simulator.get_simulation_bilan()

        elapsed = elapsed_time(start)

        with fasteners.InterProcessLock(lock_file):
            if self._hpc:
                colpr("w", "\nRank", end=": ")
                colpr("r", f"{self.__rank}")
                colpr("g", "Completed stress experiment", end=" ")
                colpr("r", f"#{self.__length_combinations}", end=" ")
                colpr("g", "of", end=" ")
                colpr("r", f"{self.__chunk}", end=" ")
                colpr("g", "with T gate indices:", end=" ")
            else:
                colpr("g", "\nCompleted stress experiment with T gate indices:", end=" ")
            colpr("r", ' '.join(map(str, indices)), end="\n")
            colpr("w", "Time elapsed:", end=" ")
            colpr("r", elapsed, end="\n\n")

        return self._stress_bilan

    #######################################
    # print and export bilan methods
    #######################################

    def __print_bilan(self) -> None:
        """
        Print the bilan of the stress experiment.
        """

        colpr("y", "\n\nBilan of the stress experiment:", end="\n\n")

        # Bilan of the stress experiment
        colpr("b", "Stress experiment bilan:", end="\n\n")

        # Calculate the required width for the "T Gate Index" column
        t_gate_index_width = self.__nbr_combinations * 3 + 13

        # Create the table header with the adjusted width
        table = f"| {'T Gate Index'.ljust(t_gate_index_width)} | Failed (%)        | Succeed (%)       | Measurements (%)  | Output Vector (%) |\n"
        table += f"|-{'-' * t_gate_index_width}-|-------------------|-------------------|-------------------|-------------------|\n"

        copied_combinations = copy.deepcopy(self._combinations)

        # sort depend in the high success rate
        # for bil in sorted(self._stress_bilan, key=lambda x: float(self._stress_bilan[x][1]), reverse=False):

        for indices in copied_combinations:
            bil = ",".join(map(str, indices))
            table += f"| {bil:<{t_gate_index_width}} | {self._stress_bilan[bil][0]:<17} | {self._stress_bilan[bil][1]:<17} | {self._stress_bilan[bil][2]:<17} | {self._stress_bilan[bil][3]:<17} |\n"

        print(table, end="\n\n")

    def __export_bilan(self) -> None:
        """
        Export the bilan of the stress experiment.
        """

        csv = "T Gate Index 0"
        for i in range(self.__nbr_combinations - 1):
            csv += f",T Gate Index {i + 1}"

        csv += ",Failed (%),Succeed (%),Measurements (%),Output Vector (%)\n"
        for indices in self._combinations:
            bil = ",".join(map(str, indices))
            csv += f"{bil},{self._stress_bilan[bil][0]},{self._stress_bilan[bil][1]},{self._stress_bilan[bil][2]},{self._stress_bilan[bil][3]}\n"

        directory = f"data/{self._decomp_scenario_modded.dec_mem}"
        if not os.path.exists(directory):
            os.makedirs(directory)
        time_elapsed = self._stop_time.replace(' ', '')
        time_stamp_start = time.strftime("%Y%m%d-%H%M%S", time.localtime(self._start_time))
        time_stamp_end = time.strftime("%Y%m%d-%H%M%S")
        # export in file
        with open(
            f"{directory}/stress"
            f"_{self._start_range_qubits}qubits"
            f"_{self.__t_count}T"
            f"_{self.__nbr_combinations}-comb"
            f"_{self.__length_combinations}-{self._specific_simulation}-tests"
            f"_{time_elapsed}"
            f"_{time_stamp_start}"
            f"_{time_stamp_end}.csv", "w") as file:
            file.write(csv)

    #######################################
    # simulate circuit method
    #######################################

    def _simulate_circuit(self) -> None:
        """
        Simulates the circuit.
        """

        super()._simulate_circuit(is_stress=True)
