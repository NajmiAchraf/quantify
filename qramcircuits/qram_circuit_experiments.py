import os
import psutil

import qramcircuits.bucket_brigade as bb

from qramcircuits.qram_circuit_core import QRAMCircuitCore
from qramcircuits.qram_circuit_simulator import QRAMCircuitSimulator
from qramcircuits.toffoli_decomposition import ToffoliDecompType

from utils.counting_utils import *
from utils.print_utils import *


#######################################
# QRAM Circuit Experiments
#######################################

class QRAMCircuitExperiments(QRAMCircuitCore):
    """
    A class used to represent the QRAM circuit experiments.

    Methods:
        __run(): Runs the experiment for a range of qubits.
        __core(): Core function of the experiment.
        __results(): Prints the results of the experiment.
        __essential_checks(): Performs essential checks on the experiment.
        __verify_circuit_depth_count(): Verifies the depth and count of the circuit.
        __simulate_circuit(): Simulates the circuit.
    """

    #######################################
    # core functions
    #######################################

    def _core(self, nr_qubits: int) -> None:
        """
        Core function of the experiment.
        """

        super()._core(nr_qubits=nr_qubits)

        print(f"{'='*150}\n\n")

        self._results()

        print(f"{'='*150}\n\n")

    def _results(self) -> None:
        """
        Prints the results of the experiment.
        """

        self._Simulator = QRAMCircuitSimulator(
            self._bbcircuit,
            self._bbcircuit_modded,
            self._specific_simulation,
            self._start_range_qubits,
            self._print_circuit,
            self._print_sim
        )

        if not self._simulate:
            self.__essential_checks()
        elif self._simulate:
            self._simulate_circuit()

    #######################################
    # essential checks methods
    #######################################

    def __essential_checks(self) -> None:
        """
        Performs essential checks on the experiment.
        """

        process = psutil.Process(os.getpid())

        """
        rss: aka “Resident Set Size”, this is the non-swapped physical memory a process has used. On UNIX it matches “top“‘s RES column).
        vms: aka “Virtual Memory Size”, this is the total amount of virtual memory used by the process. On UNIX it matches “top“‘s VIRT column.
        """

        colpr(
            "c",
            "Bucket Brigade circuit creation:\n"
            "\t• {:<1} Qbits\n"
            "\t• Time elapsed on creation: {:<12}\n"
            "\t• RSS (Memory Usage): {:<10}\n"
            "\t• VMS (Memory Usage): {:<10}".format(
                self._start_range_qubits,
                self._stop_time,
                format_bytes(process.memory_info().rss),
                format_bytes(process.memory_info().vms)),
            end="\n\n")

        name = "bucket brigade" if self._decomp_scenario.get_decomp_types()[0] == ToffoliDecompType.NO_DECOMP else "reference"
        for decirc in [
            [self._decomp_scenario, self._bbcircuit, name], 
            [self._decomp_scenario_modded, self._bbcircuit_modded, "modded"]
        ]:
            colpr("y", f"Decomposition scenario of {decirc[2]} circuit:", end="\n\n")
            print(
                "\t• fan_in_decomp: \t{}\n"
                "\t• mem_decomp:    \t{}\n"
                "\t• fan_out_decomp:\t{}\n\n".format(
                    decirc[0].dec_fan_in,
                    decirc[0].dec_mem,
                    decirc[0].dec_fan_out
                ))

            colpr("y", f"Optimization methods of {decirc[2]} circuit:", end="\n\n")
            print(
                "\t• parallel_toffolis:\t{}\n"
                "\t• mirror_method:    \t{}\n\n".format(
                    "YES !!" if decirc[0].parallel_toffolis else "NO !!",
                    decirc[0].mirror_method
                ))

            for decomposition_type in self._Simulator._fan_in_mem_out(decirc[0]):
                if decomposition_type == ToffoliDecompType.NO_DECOMP:
                    continue
                circuit, qubits = self._Simulator._create_decomposition_circuit(decomposition_type)
                printCircuit(self._print_circuit, circuit, qubits, f"decomposition {str(decomposition_type)}")

            self.__verify_circuit_depth_count(decirc[0], decirc[1], decirc[2])
            printCircuit(self._print_circuit, decirc[1].circuit, decirc[1].qubit_order, decirc[2])

    def __verify_circuit_depth_count(
            self, 
            decomp_scenario: bb.BucketBrigadeDecompType,
            bbcircuit: bb.BucketBrigade, 
            name: str
    ) -> None:
        """
        Verifies the depth and count of the circuit.

        Args:
            decomp_scenario (bb.BucketBrigadeDecompType): The decomposition scenario for the bucket brigade.
            bbcircuit (bb.BucketBrigade): Bucket brigade circuit.
            name (str): The name of the circuit.

        Returns:
            None
        """

        # Collect data for multiple qubit configurations
        data = []

        colpr("y", f"Verifying the depth and count of the {name} circuit:", end="\n\n")

        num_qubits = len(bbcircuit.circuit.all_qubits())
        circuit_depth = len(bbcircuit.circuit)

        if decomp_scenario.get_decomp_types()[0] == ToffoliDecompType.NO_DECOMP:
            data.append([self._start_range_qubits, num_qubits, circuit_depth, '-', '-', '-'])
        else:
            t_depth = count_t_depth_of_circuit(bbcircuit.circuit)
            t_count = count_t_of_circuit(bbcircuit.circuit)
            hadamard_count = count_h_of_circuit(bbcircuit.circuit)
            data.append([self._start_range_qubits, num_qubits, circuit_depth, t_depth, t_count, hadamard_count])

        # Create the Markdown table
        table = "| Qubits Range     | Number of Qubits | Depth of the Circuit | T Depth          | T Count          | Hadamard Count    |\n"
        table += "|------------------|------------------|----------------------|------------------|------------------|-------------------|\n"

        for row in data:
            table += f"| {row[0]:<16} | {row[1]:<16} | {row[2]:<20} | {row[3]:<16} | {row[4]:<16} | {row[5]:<17} |\n"

        print(table)

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

        self._Simulator._run_simulation()
