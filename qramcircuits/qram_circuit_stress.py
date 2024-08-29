import cirq
import cirq.optimizers
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

    _stress_bilan: 'dict[str, list]' = {}
    __nbr_combinations: int = 1

    def __init__(self, nbr_combinations: int = 1) -> None:
        super().__init__()

        self.__nbr_combinations = nbr_combinations

    def _run(self) -> None:
        """
        Runs the experiment for a range of qubits.
        """

        if self._decomp_scenario is None:
            colpr("r", "Decomposition scenario is None")
            return

        for i in range(self._start_range_qubits, self._end_range_qubits + 1):
            self._start_range_qubits = i
            self._simulated = False
            self._core(i, "stress")

        # self._stress()
        self._stress()

    def _stress(self) -> None:
        """
        Stress experiment for the bucket brigade circuit.
        """

        def recursive_cancel_t_gate(circuit: cirq.Circuit, qubit_order: 'list[cirq.Qid]', indices: list) -> cirq.Circuit:
            # Implement the logic to cancel T gates based on the indices
            for index in indices:
                circuit = qopt.CancelTGate(circuit, qubit_order).optimize_circuit(index)
            return circuit

        def stress_experiment(indices):
            colpr("y", f"\nStress experiment for T gate indices: {' '.join(map(str, indices))}", end="\n\n")

            self._bbcircuit = copy.deepcopy(bbcircuit_save)
            self._bbcircuit_modded = copy.deepcopy(bbcircuit_modded_save)

            self._bbcircuit_modded.circuit = recursive_cancel_t_gate(self._bbcircuit_modded.circuit, self._bbcircuit_modded.qubit_order, indices)
            self._simulated = False
            self._results()
            self._stress_bilan[",".join(map(str, indices))] = self._simulation_bilan

        bbcircuit_save = copy.deepcopy(self._bbcircuit)
        bbcircuit_modded_save = copy.deepcopy(self._bbcircuit_modded)

        t_count = count_t_of_circuit(bbcircuit_modded_save.circuit)
        t_count = 2

        for indices in itertools.product(range(1, t_count + 1), repeat=self.__nbr_combinations):
            adjusted_indices = []
            for i, index in enumerate(indices):
                adjusted_index = max(1, index - i)
                if index - i > 0:
                    adjusted_indices.append(adjusted_index)
                else:
                    adjusted_indices = []
            if len(adjusted_indices) == 0:
                continue
            # print(tuple(adjusted_indices))
            stress_experiment(tuple(adjusted_indices))

        self.__print_bilan()

    def __print_bilan(self) -> None:
        """
        Prints the bilan of the stress experiment.
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
        len_bilan = len(self._stress_bilan)
        time_stamp = time.strftime("%Y%m%d-%H%M%S")
        with open(f"stress_bilan_{len_bilan}_{time_stamp}.txt", "w") as file:
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

        self._simulation_bilan = self._Simulator.get_simulation_bilan()
