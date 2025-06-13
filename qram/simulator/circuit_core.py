import multiprocessing
import time
from functools import partial

import cirq

import qram.bucket_brigade.main as bb
from qram.simulator.base import QRAMSimulatorBase
from qramcircuits.toffoli_decomposition import ToffoliDecompType
from utils.print_utils import colpr, message, printCircuit, printRange

#######################################
# QRAM Simulator Circuit Core
#######################################


class QRAMSimulatorCircuitCore(QRAMSimulatorBase):
    """
    The QRAMSimulatorCircuitCore class to simulate the bucket brigade circuit.

    Methods:
        _parallel_execution(sim_range, step): Simulates the circuit using multiprocessing.
        _sequential_execution(sim_range, step): Simulates the circuit sequentially.
        _message(message): Prints the simulation message.
        _circuit_configuration(): Unified simulation function for all qubit types.
        _add_measurements(bbcircuit): Adds measurements to the circuit and returns the initial state.
        _simulation_manager(): Manages the simulation.
        _hpc_simulation(): Runs the simulation on high-performance computing.
        _parallel_simulation(sim_range, step): Simulates the circuit using multiprocessing.
        _sequential_simulation(sim_range, step): Simulates the circuit sequentially.
    """

    def __init__(self, is_stress: bool = False, *args, **kwargs) -> None:
        """
        Constructor of the QRAMCircuitSimulator class.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            None
        """

        super().__init__(*args, **kwargs)

        self._is_stress = is_stress

    #######################################
    # Execution methods
    #######################################

    def _parallel_execution(
        self, sim_range: "list[int]", step: int
    ) -> "list[tuple[int, int, int]]":
        """
        Simulates the circuit using multiprocessing.

        Args:
            range ('list[int]'): The range of the simulation.
            step (int): The step index.
        """

        # Use multiprocessing to parallelize the simulation ###################################

        results: "list[tuple[int, int, int]]" = []

        with multiprocessing.Pool() as pool:
            results = pool.map(
                partial(
                    self._worker,
                    step=step,
                    circuit=self._bbcircuit.circuit,
                    circuit_modded=self._bbcircuit_modded.circuit,
                    qubit_order=self._bbcircuit.qubit_order,
                    qubit_order_modded=self._bbcircuit_modded.qubit_order,
                ),
                sim_range,
            )

        return results

    def _sequential_execution(
        self, sim_range: "list[int]", step: int
    ) -> "list[tuple[int, int, int]]":
        """
        Simulates the circuit sequentially.

        Args:
            range ('list[int]'): The range of the simulation.
            step (int): The step index.
        """

        # simulation is not parallelized ######################################################

        results: "list[tuple[int, int, int]]" = []

        for i in sim_range:
            results.append(
                self._worker(
                    i=i,
                    step=step,
                    circuit=self._bbcircuit.circuit,
                    circuit_modded=self._bbcircuit_modded.circuit,
                    qubit_order=self._bbcircuit.qubit_order,
                    qubit_order_modded=self._bbcircuit_modded.qubit_order,
                )
            )

        return results

    #######################################
    # Configuration methods
    #######################################

    def _circuit_configuration(self) -> "tuple[list[int], int, str]":
        """
        Unified simulation function for all qubit types.
        """

        self._simulation_kind = "bb"

        extra_qubits = 1
        if any(
            component in ["write", "read"] for component in self._circuit_type
        ):
            extra_qubits = 2

        simulation_configs = {
            "full": {
                "step": 1,
                "step_multiplier": 1,
                "stop_multiplier": 2
                ** (2 * (2**self._qram_bits) + self._qram_bits + extra_qubits),
                "message": message(
                    "Simulating the circuit ... Checking all qubits"
                ),
            },
            "qram": {
                "step": 2 ** (2 * (2**self._qram_bits) + extra_qubits),
                "step_multiplier": 2
                ** (2 * (2**self._qram_bits) + extra_qubits),
                "stop_multiplier": 2**self._qram_bits,
                "message": message(
                    "Simulating the circuit ... Checking the QRAM logic and measure all qubits"
                ),
            },
        }

        config = simulation_configs.get(self._specific_simulation)
        if not config:
            raise ValueError(
                f"Unknown simulation type: {self._specific_simulation}"
            )

        start = 0
        step = config["step"]
        stop = (config.get("step_multiplier", 1)) * (
            config.get("stop_multiplier", 1)
        )
        sim_range = list(range(start, stop, step))

        return sim_range, step, config["message"]

    def _add_measurements(self, bbcircuit: bb.BucketBrigade) -> None:
        """
        Adds measurements to the circuit.

        Args:
            bbcircuit (bb.BucketBrigade): The bucket brigade circuit.
        """

        measurements = []
        for qubit in bbcircuit.qubit_order:
            measurements.append(cirq.measure(qubit))

        bbcircuit.circuit.append(measurements)
        bbcircuit.circuit = cirq.synchronize_terminal_measurements(
            bbcircuit.circuit
        )

    def _begin_configurations(self) -> None:
        """
        Simulates the circuit.

        Args:
            sim_range ('list[int]'): The range of the simulation.
            step (int): The step index.
            message (str): The message to print.
        """

        self._start_time = time.time()

        # add measurements to circuits ########################################################

        self._add_measurements(self._bbcircuit)

        self._add_measurements(self._bbcircuit_modded)

    def _prints(self, sim_range: "list[int]", step: int, message: str) -> None:
        """
        Prints the simulation configuration and circuit details.

        Args:
            sim_range (list[int]): The range of the simulation.
            step (int): The step index.
            message (str): The message to print.
        """

        if not self._is_stress and not self._hpc:

            name = (
                "bucket brigade"
                if self._decomp_scenario.get_decomp_types()[0]
                == ToffoliDecompType.NO_DECOMP
                else "reference"
            )

            colpr("y", "\n", message, end="\n\n")

            printCircuit(
                self._print_circuit,
                self._bbcircuit.circuit,
                self._bbcircuit.qubit_order,
                name,
            )

            printCircuit(
                self._print_circuit,
                self._bbcircuit_modded.circuit,
                self._bbcircuit_modded.qubit_order,
                "modded",
            )

            printRange(sim_range[0], sim_range[-1], step)

            colpr(
                "c",
                f"Simulating both the modded and {name} circuits and comparing their output vector and measurements ...",
                end="\n\n",
            )
