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

        super()._core(qram_bits=nr_qubits)

        self.__assessment(nr_qubits=nr_qubits)

    #######################################
    # assessment functions
    #######################################

    def __assessment(self, nr_qubits: int) -> None:
        """
        Collect the assessment of the experiment
        """

        process = psutil.Process(os.getpid())

        if self._decomp_scenario.dec_fan_out != ToffoliDecompType.NO_DECOMP:

            num_qubits = len(self._bbcircuit.circuit.all_qubits())
            circuit_depth = len(self._bbcircuit.circuit)
            sub_circuits_depth = count_circuit_depth(self._bbcircuit.circuit)

            t_depth = count_t_depth_of_circuit(self._bbcircuit.circuit)
            t_count = count_t_of_circuit(self._bbcircuit.circuit)
            hadamard_count = count_h_of_circuit(self._bbcircuit.circuit)

            # Store data with sub-circuits depth
            if sub_circuits_depth != circuit_depth:
                self._data[nr_qubits] = [
                    nr_qubits,
                    num_qubits,
                    circuit_depth,
                    sub_circuits_depth,
                    t_depth,
                    t_count,
                    hadamard_count,
                ]
            else:
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
        sub_circuits_depth = count_circuit_depth(
            self._bbcircuit_modded.circuit
        )

        t_depth = count_t_depth_of_circuit(self._bbcircuit_modded.circuit)
        t_count = count_t_of_circuit(self._bbcircuit_modded.circuit)
        hadamard_count = count_h_of_circuit(self._bbcircuit_modded.circuit)

        rss = format_bytes(process.memory_info().rss)
        vms = format_bytes(process.memory_info().vms)

        # Store data with sub-circuits depth for modded circuit
        if sub_circuits_depth != circuit_depth:
            self._data_modded[nr_qubits] = [
                nr_qubits,
                num_qubits,
                circuit_depth,
                sub_circuits_depth,
                t_depth,
                t_count,
                hadamard_count,
                self._stop_time,
                rss,
                vms,
            ]
        else:
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

        # Print main title
        print_assessment_main_title()

        # Print circuit creation assessment
        print_circuit_creation_assessment(
            self._data_modded, self._start_range_qubits, self._end_range_qubits
        )

        # Print reference circuit assessment (if applicable)
        if self._decomp_scenario.dec_fan_out != ToffoliDecompType.NO_DECOMP:
            print_reference_circuit_assessment(
                self._data, self._start_range_qubits, self._end_range_qubits
            )

        # Print modded circuit assessment
        print_modded_circuit_assessment(
            self._data_modded, self._start_range_qubits, self._end_range_qubits
        )

        # Print depth analysis (sub-circuits vs circuit depth)
        has_reference = (
            self._decomp_scenario.dec_fan_out != ToffoliDecompType.NO_DECOMP
        )
        print_depth_analysis(
            self._data_modded,
            self._data,
            self._start_range_qubits,
            self._end_range_qubits,
            has_reference,
        )

        # Print reference vs modded comparison (if applicable)
        if self._decomp_scenario.dec_fan_out != ToffoliDecompType.NO_DECOMP:
            print_reference_modded_comparison(
                self._data,
                self._data_modded,
                self._start_range_qubits,
                self._end_range_qubits,
            )

        # Print final summary
        print_assessment_summary()
