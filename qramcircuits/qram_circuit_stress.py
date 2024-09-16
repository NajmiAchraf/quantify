import cirq
import copy
import itertools
import os
import time

from functools import partial
import multiprocessing
import threading

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
        _stress_bilan (dict): The stress bilan.
        __nbr_combinations (int): The number of combinations.

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

    # _stress_bilan: 'dict[str, list]' = {}
    _stress_bilan: multiprocessing.Manager().dict() = multiprocessing.Manager().dict()

    _combinations: 'itertools.combinations[tuple[int, ...]]'

    __circuit_save: cirq.Circuit
    __circuit_modded_save: cirq.Circuit

    __length_combinations: int = 0
    __nbr_combinations: int = 1
    __t_count: int = 4

    def __init__(self, nbr_combinations: int = 1) -> None:
        super().__init__()

        self.__nbr_combinations = nbr_combinations
    
    def __del__(self) -> None:
        pass

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

        # use thread to load the stress experiments ###########################################

        if self._print_sim == "Hide":
            stop_event = threading.Event()
            loading_thread = threading.Thread(target=loading_animation, args=(stop_event, 'stress experiments',))
            loading_thread.start()

        # Use multiprocessing to parallelize the stress experiments ###########################

        try:
            with multiprocessing.Pool() as pool:
                results = pool.map(
                    partial(
                        self._stress_experiment
                    ),
                    combinations
                )
        finally:
            if self._print_sim == "Hide":
                stop_event.set()
                loading_thread.join()

        self.__length_combinations = len(results)

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

    def _stress_experiment(self, indices: 'tuple[int, ...]') -> None:
        """
        Stress experiment for the bucket brigade circuit.

        Args:
            indices (tuple[int, ...]): The indices.
        """

        colpr("y", f"\nStress experiment for T gate indices: {' '.join(map(str, indices))}", end="\n\n")

        self._bbcircuit.circuit = copy.deepcopy(self.__circuit_save)
        self._bbcircuit_modded.circuit = copy.deepcopy(self.__circuit_modded_save)

        self._bbcircuit_modded.circuit = self.__cancel_t_gates(self._bbcircuit_modded.circuit, self._bbcircuit_modded.qubit_order, indices)

        self._simulated = False
        self._results()

        if self._simulate:
            self._stress_bilan[",".join(map(str, indices))] = self._Simulator.get_simulation_bilan()

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
        time_stamp = time.strftime("%Y%m%d-%H%M%S")
        # export in file
        with open(
            f"{directory}/stress"
            f"_{self._start_range_qubits}qubits"
            f"_{self.__t_count}T"
            f"_{self.__nbr_combinations}comb"
            f"_{self.__length_combinations}tests"
            f"-{self._specific_simulation}"
            f"_{time_elapsed}"
            f"_{time_stamp}.csv", "w") as file:
            file.write(csv)

    #######################################
    # simulate circuit method
    #######################################

    def _simulate_circuit(self) -> None:
        """
        Simulates the circuit.
        """

        if self._simulated:
            return
        self._simulated = True

        self._Simulator._simulate_circuit(is_stress=True)
