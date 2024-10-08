import cirq
import copy
import itertools
import os
import time
import numpy as np

from functools import partial
import multiprocessing
from multiprocessing.managers import DictProxy
from concurrent.futures import ThreadPoolExecutor

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

    Methods:
        _run(): Runs the experiment for a range of qubits.
        _core(): Core function of the experiment.
        _stress(): Stress experiment for the bucket brigade circuit.
        __cancel_t_gates(): Cancel T gates in modded bucket brigade circuit.
        __stress_experiment(): Stress experiment for the bucket brigade circuit.
        __print_bilan(): Print the bilan of the stress experiment.
        __export_bilan(): Export the bilan of the stress experiment.
        _simulate_circuit(): Simulates the circuit.
    """

    _stress_bilan: 'DictProxy[str, list[str]]' = multiprocessing.Manager().dict()

    _combinations: 'itertools.combinations[tuple[int, ...]]'

    __circuit_save: cirq.Circuit
    __circuit_modded_save: cirq.Circuit

    __length_combinations: int = 0
    __nbr_combinations: int = 1
    __t_count: int = 2

    __lock = multiprocessing.Lock()

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

        tmp = self._simulate
        self._simulate = False

        super()._core(nr_qubits=nr_qubits)

        self._simulate = tmp

        if nr_qubits > 4:
            self._simulate = False

        self._stress()

    def _stress(self) -> None:
        """
        Stress experiment for the bucket brigade circuit.
        """

        self.__circuit_save = copy.deepcopy(self._bbcircuit.circuit)
        self.__circuit_modded_save = copy.deepcopy(self._bbcircuit_modded.circuit)

        self.__t_count = count_t_of_circuit(self.__circuit_modded_save)

        self._start_time = time.time()

        combinations = itertools.combinations(range(1, self.__t_count + 1), self.__nbr_combinations)

        self._combinations = copy.deepcopy(combinations)

        if self._simulate and not self._hpc:
            if self._start_range_qubits == 2:
                # Use multiprocessing to parallelize the stress testing #######################
                with multiprocessing.Pool() as pool:
                    results = pool.map(
                        partial(
                            self._stress_experiment
                        ),
                        combinations
                    )
                self.__length_combinations = len(results)

            elif self._start_range_qubits == 3:
                # Use concurrent futures to parallelize the stress testing #######################
                for indices in combinations:
                    self._stress_experiment(indices)
                    self.__length_combinations += 1

            self.__extract_results()

        elif self._simulate and self._hpc:

            from mpi4py import MPI
            # Initialize MPI
            comm = MPI.COMM_WORLD
            rank = comm.Get_rank()
            size = comm.Get_size()
            
            # Determine the range of work for this MPI process
            # print("rank, size : ", rank, size)
            total_work = list(copy.deepcopy(combinations))
            
            # Split the total work into chunks based on the number of ranks
            work_chunks = np.array_split(total_work, size)
            local_work = work_chunks[rank] if rank < len(work_chunks) else []
            
            # print("rank, local_work : ", rank, local_work)

            result = []
            for indices in combinations:
                self.__length_combinations += 1
                if indices in local_work:
                    result.append(self._stress_experiment(indices))

            # for item in result:
            #     for map_name, value in item.items():
            #         print(f"rank, map_name, value : {rank}, {map_name}, {value}")

            # Ensure results are serializable
            serializable_result = {map_name: value for item in result for map_name, value in item.items()}
            # print(f"rank, serializable_result : {rank}, {serializable_result}")

            # Gather results from all MPI processes
            results = comm.gather(serializable_result, root=0)

            if rank == 0:
                for item in results:
                    for map_name, value in item.items():
                        # print(f"map_name, value : {map_name}, {value}")
                        if len(value) != 0:
                            self._stress_bilan[map_name] = value

                self.__extract_results()

        elif not self._simulate:
            for indices in combinations:
                time.sleep(0.5)
                self._stress_experiment(indices)
                self.__length_combinations += 1

            self.__extract_results()

    def __extract_results(self) -> None:
        """
        Extract the results.
        """

        self._stop_time = elapsed_time(self._start_time)

        if self._simulate:
            self.__print_bilan()
            self.__export_bilan()

        print(f"Time elapsed for stress testing {self.__length_combinations} unique combinations: {self._stop_time}", end="\n\n")

    def __cancel_t_gates(self, circuit: cirq.Circuit, qubit_order: 'list[cirq.Qid]', indices: 'tuple[int, ...]') -> cirq.Circuit:
        """
        Cancel T gates in modded bucket brigade circuit.

        Args:
            circuit (cirq.Circuit): The circuit.
            qubit_order (list[cirq.Qid]): The qubit order.
            indices (tuple[int, ...]): The indices.

        Returns:
            cirq.Circuit: The optimized circuit.
        """

        return qopt.CancelTGate(circuit, qubit_order).optimize_circuit(indices)

    def _stress_experiment(self, indices: 'tuple[int, ...]') -> 'DictProxy[str, list[str]]':
        """
        Stress experiment for the bucket brigade circuit.

        Args:
            indices (tuple[int, ...]): The indices.
        """

        start = time.time()
        with self.__lock:
            colpr("w", "\nLoading stress experiment with T gate indices:", end=" ")
            colpr("r", ' '.join(map(str, indices)), end="\n\n")

        self._bbcircuit.circuit = copy.deepcopy(self.__circuit_save)
        self._bbcircuit_modded.circuit = copy.deepcopy(self.__circuit_modded_save)

        self._bbcircuit_modded.circuit = self.__cancel_t_gates(self._bbcircuit_modded.circuit, self._bbcircuit_modded.qubit_order, indices)

        self._simulated = False
        self._results()

        if self._simulate:
            self._stress_bilan[",".join(map(str, indices))] = self._Simulator.get_simulation_bilan()

        elapsed = elapsed_time(start)
        with self.__lock:
            colpr("g", f"\nCompleted stress experiment with T gate indices:", end=" ")
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
            f"_{self.__nbr_combinations}comb"
            f"_{self.__length_combinations}tests"
            f"-{self._specific_simulation}"
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
