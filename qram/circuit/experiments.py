import os

import psutil

from qram.bucket_brigade.decomp_type import BucketBrigadeDecompType
from qram.bucket_brigade.main import BucketBrigade
from qram.circuit.core import QRAMCircuitCore
from qram.simulator.decomposition import (
    create_decomposition_circuit,
    fan_in_mem_out,
)
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
        _core(nr_qubits: int): Core function of the experiment.
        _results(): Prints the results of the experiment.
        __essential_checks(): Performs essential checks on the experiment.
        __verify_circuit_depth_count(decomp_scenario: BucketBrigadeDecompType, bbcircuit: BucketBrigade, name: str): Verifies the depth and count of the circuit.
        _simulate_circuit(is_stress: bool=False): Simulates the circuit.
    """

    #######################################
    # core functions
    #######################################

    def _core(self, nr_qubits: int) -> None:
        """
        Core function of the experiment.
        """

        super()._core(qram_bits=nr_qubits)

        self._results()

    def _results(self) -> None:
        """
        Prints the results of the experiment.
        """

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

        # Print memory usage with Rich formatting
        print_memory_usage(
            self._start_range_qubits,
            self._stop_time,
            format_bytes(process.memory_info().rss),
            format_bytes(process.memory_info().vms),
        )

        name = (
            "bucket brigade"
            if self._decomp_scenario.get_decomp_types()[0]
            == ToffoliDecompType.NO_DECOMP
            else "reference"
        )

        for decirc in [
            [self._decomp_scenario, self._bbcircuit, name],
            [self._decomp_scenario_modded, self._bbcircuit_modded, "modded"],
        ]:
            # Print decomposition scenario
            print_decomposition_scenario(
                self._circuit_type, decirc[0], decirc[2]
            )

            # Print optimization methods
            print_optimization_methods(decirc[0], decirc[2])

            # Handle decomposition circuits
            for decomposition_type in fan_in_mem_out(decirc[0]):
                if decomposition_type == ToffoliDecompType.NO_DECOMP:
                    continue
                circuit, qubits = create_decomposition_circuit(
                    decomposition_type
                )
                render_circuit(
                    self._print_circuit,
                    circuit,
                    qubits,
                    f"decomposition {str(decomposition_type)}",
                )

            self.__verify_circuit_depth_count(decirc[0], decirc[1], decirc[2])
            render_circuit(
                self._print_circuit,
                decirc[1].circuit,
                decirc[1].qubit_order,
                decirc[2],
            )

    def __verify_circuit_depth_count(
        self,
        decomp_scenario: BucketBrigadeDecompType,
        bbcircuit: BucketBrigade,
        name: str,
    ) -> None:
        """
        Verifies the depth and count of the circuit.

        Args:
            decomp_scenario (BucketBrigadeDecompType): The decomposition scenario for the bucket brigade.
            bbcircuit (BucketBrigade): Bucket brigade circuit.
            name (str): The name of the circuit.
        """

        # Include circuit type in output
        circuit_type_str = (
            self._circuit_type
            if isinstance(self._circuit_type, str)
            else ", ".join(self._circuit_type)
        )

        # Create verification header
        header_panel = Panel(
            f"[bold yellow]🔍 Verifying Circuit Metrics: {name.title()} Circuit[/bold yellow]\n"
            f"[cyan]Circuit Type: [white]{circuit_type_str}[/white][/cyan]",
            border_style="yellow",
            box=box.ROUNDED,
        )
        console.print()
        console.print(header_panel)
        console.print("", style="white", end="")  # Reset color

        num_qubits = len(bbcircuit.circuit.all_qubits())
        circuit_depth = len(bbcircuit.circuit)
        sub_circuits_depth = count_circuit_depth(bbcircuit.circuit)

        # Prepare data for table
        if (
            decomp_scenario.get_decomp_types()[0]
            == ToffoliDecompType.NO_DECOMP
        ):
            data = [
                [
                    self._start_range_qubits,
                    num_qubits,
                    circuit_depth,
                    "-",
                    "-",
                    "-",
                ]
            ]
        else:
            t_depth = count_t_depth_of_circuit(bbcircuit.circuit)
            t_count = count_t_of_circuit(bbcircuit.circuit)
            hadamard_count = count_h_of_circuit(bbcircuit.circuit)
            data = [
                [
                    self._start_range_qubits,
                    num_qubits,
                    circuit_depth,
                    t_depth,
                    t_count,
                    hadamard_count,
                ]
            ]

        headers = [
            "QRAM Bits",
            "Number of Qubits",
            "Depth of Circuit",
            "T Depth",
            "T Count",
            "Hadamard Count",
        ]

        if sub_circuits_depth != circuit_depth:
            data[0].insert(3, sub_circuits_depth)
            headers.insert(3, "Sub-Circuits Depth")

        print_assessment_table(
            headers,
            data,
            f"📊 {name.title()} Circuit Metrics",
            "bold cyan",
        )

    #######################################
    # simulate circuit method
    #######################################

    def _simulate_circuit(self, is_stress: bool = False) -> None:
        """
        Simulates the circuit.

        Args:
            is_stress (bool, optional): Whether the simulation is a stress test. Defaults to False.
        """

        if self._simulated:
            return
        self._simulated = True

        self._simulator_manager._run_simulation(is_stress=is_stress)
