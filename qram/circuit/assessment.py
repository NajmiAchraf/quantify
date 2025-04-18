import os

import psutil

from qram.circuit.core import QRAMCircuitCore
from qramcircuits.toffoli_decomposition import ToffoliDecompType
from utils.counting_utils import *
from utils.print_utils import *

#######################################
# QRAM Circuit Assessment
#######################################


class QRAMCircuitAssessment(QRAMCircuitCore):
    """
    A class used to represent the QRAM circuit assessment.

    Attributes:
        _data (dict): Stores the assessment data for the reference circuit.
        _data_modded (dict): Stores the assessment data for the modded circuit.

    Methods:
        _run(): Runs the assessment for a range of qubits.
        _core(nr_qubits: int): Core function of the experiment.
        __assessment(nr_qubits: int): Collects the assessment of the experiment.
        __print_assessment(): Prints the assessment of the experiment.
    """

    _data: dict = {}
    _data_modded: dict = {}

    #######################################
    # core functions
    #######################################

    def _run(self) -> None:
        """
        Run the assessment for a range of qubits.
        """

        # Reset data for multiple tests on series
        self._data.clear()
        self._data_modded.clear()

        super()._run("assessment")

        self.__print_assessment()

    def _core(self, nr_qubits: int) -> None:
        """
        Core function of the experiment.
        """

        super()._core(nr_qubits=nr_qubits)

        self.__assessment(nr_qubits=nr_qubits)

    #######################################
    # assessment functions
    #######################################

    def __assessment(self, nr_qubits: int) -> None:
        """
        Collect the assessment of the experiment
        """

        process = psutil.Process(os.getpid())

        if self._decomp_scenario.dec_fan_in != ToffoliDecompType.NO_DECOMP:

            num_qubits = len(self._bbcircuit.circuit.all_qubits())
            circuit_depth = len(self._bbcircuit.circuit)

            t_depth = count_t_depth_of_circuit(self._bbcircuit.circuit)
            t_count = count_t_of_circuit(self._bbcircuit.circuit)
            hadamard_count = count_h_of_circuit(self._bbcircuit.circuit)

            self._data[nr_qubits] = [
                nr_qubits,
                num_qubits,
                circuit_depth,
                t_depth,
                t_count,
                hadamard_count,
            ]

        num_qubits = len(self._bbcircuit_modded.circuit.all_qubits())
        circuit_depth = len(self._bbcircuit_modded.circuit)

        t_depth = count_t_depth_of_circuit(self._bbcircuit_modded.circuit)
        t_count = count_t_of_circuit(self._bbcircuit_modded.circuit)
        hadamard_count = count_h_of_circuit(self._bbcircuit_modded.circuit)

        rss = format_bytes(process.memory_info().rss)
        vms = format_bytes(process.memory_info().vms)

        self._data_modded[nr_qubits] = [
            nr_qubits,
            num_qubits,
            circuit_depth,
            t_depth,
            t_count,
            hadamard_count,
            self._stop_time,
            rss,
            vms,
        ]

    def __print_assessment(self) -> None:
        """
        Prints the assessment of the experiment.
        """

        colpr("y", "\n\nAssessment of the experiment:", end="\n\n")

        # Assessment of essential checks
        colpr("b", "Creation of the Bucket Brigade Circuits:", end="\n\n")
        table = "| Qubits Range     | Elapsed Time               | RSS (Memory Usage)     | VMS (Memory Usage)     |\n"
        table += "|------------------|----------------------------|------------------------|------------------------|\n"

        for x in range(self._start_range_qubits, self._end_range_qubits + 1):
            table += f"| {self._data_modded[x][0]:<16} | {self._data_modded[x][6]:<26} | {self._data_modded[x][7]:<22} | {self._data_modded[x][8]:<22} |\n"

        print(table, end="\n\n")

        # Assessment of the reference circuit
        if self._decomp_scenario.dec_fan_in != ToffoliDecompType.NO_DECOMP:
            colpr("b", "Reference circuit assessment:", end="\n\n")

            table = "| Qubits Range     | Number of Qubits | Depth of the Circuit | T Depth          | T Count          | Hadamard Count    |\n"
            table += "|------------------|------------------|----------------------|------------------|------------------|-------------------|\n"

            for x in range(self._start_range_qubits, self._end_range_qubits + 1):
                table += f"| {self._data[x][0]:<16} | {self._data[x][1]:<16} | {self._data[x][2]:<20} | {self._data[x][3]:<16} | {self._data[x][4]:<16} | {self._data[x][5]:<17} |\n"

            print(table, end="\n\n")

        # Assessment of the modded circuit
        colpr("b", "Modded circuit assessment:", end="\n\n")
        table = "| Qubits Range     | Number of Qubits | Depth of the Circuit | T Depth          | T Count          | Hadamard Count    |\n"
        table += "|------------------|------------------|----------------------|------------------|------------------|-------------------|\n"

        for x in range(self._start_range_qubits, self._end_range_qubits + 1):
            table += f"| {self._data_modded[x][0]:<16} | {self._data_modded[x][1]:<16} | {self._data_modded[x][2]:<20} | {self._data_modded[x][3]:<16} | {self._data_modded[x][4]:<16} | {self._data_modded[x][5]:<17} |\n"

        print(table, end="\n\n")

        # Comparing assessments
        if self._decomp_scenario.dec_fan_in != ToffoliDecompType.NO_DECOMP:

            def calculate(i: int, j: int) -> "tuple[str, str]":
                modded_percent = (self._data_modded[i][j] / self._data[i][j]) * 100
                modded_percent_str = format(modded_percent, ",.2f")
                modded = str(self._data_modded[i][j]) + f"  ( {modded_percent_str} )"

                cancelled_percent = 100.0 - modded_percent
                cancelled_percent_str = format(cancelled_percent, ",.2f")
                cancelled = (
                    str(self._data[i][j] - self._data_modded[i][j])
                    + f"  ( {cancelled_percent_str} )"
                )

                return modded, cancelled

            colpr("y", "Comparing assessments", end="\n\n")

            colpr("b", "T count comparison:", end="\n\n")
            table = "| Qubits Range     | T Count Reference  | T Count Modded (%) | T Count Cancelled (%)  |\n"
            table += "|------------------|--------------------|--------------------|------------------------|\n"

            for i in range(self._start_range_qubits, self._end_range_qubits + 1):
                modded, cancelled = calculate(i, 4)
                table += f"| {self._data[i][0]:<16} | {self._data[i][4]:<18} | {modded :<18} | {cancelled:<22} |\n"

            print(table, end="\n\n")

            colpr("b", "T depth comparison:", end="\n\n")
            table = "| Qubits Range     | T Depth Reference  | T Depth Modded (%) | T Depth Cancelled (%)  |\n"
            table += "|------------------|--------------------|--------------------|------------------------|\n"

            for i in range(self._start_range_qubits, self._end_range_qubits + 1):
                modded, cancelled = calculate(i, 3)
                table += f"| {self._data[i][0]:<16} | {self._data[i][3]:<18} | {modded :<18} | {cancelled:<22} |\n"

            print(table, end="\n\n")

            colpr("b", "Depth of the circuit comparison:", end="\n\n")
            table = "| Qubits Range     | Depth Reference    | Depth Modded (%)   | Depth Cancelled (%)    |\n"
            table += "|------------------|--------------------|--------------------|------------------------|\n"

            for i in range(self._start_range_qubits, self._end_range_qubits + 1):
                modded, cancelled = calculate(i, 2)
                table += f"| {self._data[i][0]:<16} | {self._data[i][2]:<18} | {modded :<18} | {cancelled:<22} |\n"

            print(table, end="\n\n")
