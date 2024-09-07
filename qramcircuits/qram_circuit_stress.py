import cirq
import copy
import itertools
import time

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
        __print_bilan(): Print the bilan of the stress experiment.
        __export_bilan(): Export the bilan of the stress experiment.
        _simulate_circuit(): Simulates the circuit.
    """

    _stress_bilan: 'dict[str, list]' = {}
    __length_combinations: int = 0
    __nbr_combinations: int = 1
    __t_count: int = 5

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
        self._stress()

    def _stress(self) -> None:
        """
        Stress experiment for the bucket brigade circuit.
        """

        def cancel_t_gates(circuit: cirq.Circuit, qubit_order: 'list[cirq.Qid]', indices: 'tuple[int, ...]') -> cirq.Circuit:
            # Cancel T gates in modded bucket brigade circuit.
            return qopt.CancelTGate(circuit, qubit_order).optimize_circuit(indices)

        def stress_experiment(indices: 'tuple[int, ...]') -> None:
            colpr("y", f"\nStress experiment for T gate indices: {' '.join(map(str, indices))}", end="\n\n")

            self._bbcircuit = copy.deepcopy(bbcircuit_save)
            self._bbcircuit_modded = copy.deepcopy(bbcircuit_modded_save)

            self._bbcircuit_modded.circuit = cancel_t_gates(self._bbcircuit_modded.circuit, self._bbcircuit_modded.qubit_order, indices)
            self._simulated = False
            self._results()
            if self._simulate:
                self._stress_bilan[",".join(map(str, indices))] = self._Simulator.get_simulation_bilan()

        bbcircuit_save = copy.deepcopy(self._bbcircuit)
        bbcircuit_modded_save = copy.deepcopy(self._bbcircuit_modded)

        self.__t_count = count_t_of_circuit(bbcircuit_modded_save.circuit)

        start = time.time()

        combinations = itertools.combinations(range(1, self.__t_count + 1), self.__nbr_combinations)

        for indices in combinations:
            # print(indices)
            stress_experiment(indices)
            self.__length_combinations += 1

        end = elapsed_time(start)

        if self._simulate:
            self.__print_bilan()
            self.__export_bilan()

        print(f"Time elapsed for stress testing {self.__length_combinations} unique combinations: {end}", end="\n\n")

    def __print_bilan(self) -> None:
        """
        Print the bilan of the stress experiment.
        """

        colpr("y", "\n\nBilan of the stress experiment:", end="\n\n")

        # Bilan of the stress experiment
        colpr("b", "Stress experiment bilan:", end="\n\n")

        table = "| T Gate Index     | Failed (%)        | Succeed (%)       | Measurements (%)  | Output Vector (%) |\n"
        table += "|------------------|-------------------|-------------------|-------------------|-------------------|\n"

        # sort depend in the high success rate
        for bil in self._stress_bilan:
        # for bil in sorted(self._stress_bilan, key=lambda x: float(self._stress_bilan[x][0]), reverse=False):
            table += f"| {bil:<16} | {self._stress_bilan[bil][0]:<17} | {self._stress_bilan[bil][1]:<17} | {self._stress_bilan[bil][2]:<17} | {self._stress_bilan[bil][3]:<17} |\n"

        print(table, end="\n\n")

    def __export_bilan(self) -> None:
        """
        Export the bilan of the stress experiment.
        """

        csv = "T Gate Index 0"
        ref: str
        for bil in self._stress_bilan:
            ref = bil
            break
        num_indices = len(ref.split(","))
        for i in range(num_indices - 1):
            csv += f",T Gate Index {i + 1}"

        csv += ",Failed (%),Succeed (%),Measurements (%),Output Vector (%)\n"
        for bil in self._stress_bilan:
            csv += f"{bil},{self._stress_bilan[bil][0]},{self._stress_bilan[bil][1]},{self._stress_bilan[bil][2]},{self._stress_bilan[bil][3]}\n"

        # export in file
        time_stamp = time.strftime("%Y%m%d-%H%M%S")
        with open(
            f"bilans/stress_bilan"
            f"_{self._start_range_qubits}qubits"
            f"_{self.__t_count}T"
            f"_{self.__nbr_combinations}comb"
            f"_{self.__length_combinations}tests"
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

        self._Simulator._simulate_circuit()
