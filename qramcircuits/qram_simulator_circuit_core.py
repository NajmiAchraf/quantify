import cirq
import time

import qramcircuits.bucket_brigade as bb

from qramcircuits.qram_simulator_base import QRAMSimulatorBase
from qramcircuits.toffoli_decomposition import ToffoliDecompType

from utils.print_utils import colpr, printRange, printCircuit


def generate_qram_patterns(qubits_number: int) -> 'list[int]':
    """2
    00 1000 0001 0 -> 258 : start
    01 0100 0010 0 -> 644
    10 0010 0100 0 -> 1096
    11 0001 1000 0 -> 1584
    """

    """3
    000 10000000 00000001 0 -> 65538 : start
    001 01000000 00000010 0 -> 163844
    010 00100000 00000100 0 -> 278536
    011 00010000 00001000 0 -> 401424
    100 00001000 00010000 0 -> 528416
    101 00000100 00100000 0 -> 657472
    110 00000010 01000000 0 -> 787584
    111 00000001 10000000 0 -> 918272
    """

    lines = []
    num_ids = 2 ** qubits_number
    control_length = 2 ** qubits_number
    # Generate active lines
    for i in range(num_ids):
        address = format(i, f'0{qubits_number}b')
        bytes = format(1 << (control_length - 1 - i), f'0{control_length}b')
        memory = format(1 << i, f'0{control_length}b')
        target = '0'
        decimal_value = int(f"{address}{bytes}{memory}{target}", 2)
        lines.append(decimal_value)
    return lines


#######################################
# QRAM Simulator Circuit Core
#######################################

class QRAMSimulatorCircuitCore(QRAMSimulatorBase):
    """
    The QRAMSimulatorCircuitCore class to simulate the bucket brigade circuit.

    Methods:
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

    def _circuit_configuration(self) -> 'tuple[list[int], int, str]':
        """
        Unified simulation function for all qubit types.
        """

        self._simulation_kind = "bb"

        simulation_configs = {
            "a": {
                "step": 2 ** (2 * (2 ** self._qubits_number) + 1),
                "stop_multiplier": 2 ** self._qubits_number,
                "message": "<==================== Simulating the circuit ... Checking the addressing of the a qubits =====================>\n"
            },
            "b": {
                "step": 2 ** (2 ** self._qubits_number + 1),
                "stop_multiplier": 2 ** (2 ** self._qubits_number),
                "message": "<==================== Simulating the circuit ... Checking the uncomputation of FANOUT ... were the b qubits are returned to their initial state =====================>\n"
            },
            "m": {
                "step": 2,
                "stop_multiplier": 2 ** (2 ** self._qubits_number),
                "message": "<==================== Simulating the circuit ... Checking the computation of MEM ... were the m qubits are getting the result of the computation =====================>\n"
            },
            "ab": {
                "step": 2 ** (2 ** self._qubits_number + 1),
                "stop_multiplier": 2 ** self._qubits_number,
                "message": "<==================== Simulating the circuit ... Checking the addressing and uncomputation of the a and b qubits =====================>\n"
            },
            "bm": {
                "step": 2,
                "stop_multiplier": 2 ** (2 ** self._qubits_number),
                "message": "<==================== Simulating the circuit ... Checking the addressing and uncomputation of the b and m qubits =====================>\n"
            },
            "abm": {
                "step": 2,
                "stop_multiplier": 2 ** (2 ** self._qubits_number),
                "message": "<==================== Simulating the circuit ... Checking the addressing and uncomputation of the a, b, and m qubits =====================>\n"
            },
            "t": {
                "step": 2,
                "stop_multiplier": 2 ** (2 ** self._qubits_number),
                "message": "<==================== Simulating the circuit ... Checking the addressing and uncomputation of the a, b, and m qubits and measure only the target qubit =====================>\n"
            },
            "full": {
                "step": 1,
                "stop_multiplier": 2 ** (2 * (2 ** self._qubits_number) + self._qubits_number + 1),
                "message": "<==================== Simulating the circuit ... Checking all qubits =====================>\n"
            },
            "qram": {
                "step": 1,
                "stop_multiplier": None,
                "message": "Simulating the circuit ... Checking the QRAM logic and measure only the target qubit ..."
            }
        }

        config = simulation_configs.get(self._specific_simulation)
        if not config:
            raise ValueError(f"Unknown simulation type: {self._specific_simulation}")

        start = 0
        step = config["step"]
        if self._specific_simulation != "qram":
            stop = step * config.get("stop_multiplier", 1)
            sim_range = list(range(start, stop, step))
        else:
            sim_range = generate_qram_patterns(self._qubits_number)

        return sim_range, step, config["message"]

    def _add_measurements(self, bbcircuit: bb.BucketBrigade) -> None:
        """
        Adds measurements to the circuit.

        Args:
            bbcircuit (bb.BucketBrigade): The bucket brigade circuit.
        """

        measurements = []
        for qubit in bbcircuit.qubit_order:
            if self._specific_simulation in ["full", "qram"]:
                measurements.append(cirq.measure(qubit))
            else:
                for _name in self._specific_simulation:
                    if qubit.name.startswith(_name):
                        measurements.append(cirq.measure(qubit))

        bbcircuit.circuit.append(measurements)
        cirq.optimizers.SynchronizeTerminalMeasurements().optimize_circuit(bbcircuit.circuit)

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

    def _prints(self, sim_range: 'list[int]', step: int, message: str) -> None:
        """
        Prints the simulation configuration and circuit details.

        Args:
            sim_range (list[int]): The range of the simulation.
            step (int): The step index.
            message (str): The message to print.
        """

        if not self._is_stress and not self._hpc:

            name = "bucket brigade" if self._decomp_scenario.get_decomp_types()[0] == ToffoliDecompType.NO_DECOMP else "reference"

            colpr("y", '\n', message, end="\n\n")

            printCircuit(self._print_circuit, self._bbcircuit.circuit, self._bbcircuit.qubit_order, name)

            printCircuit(self._print_circuit, self._bbcircuit_modded.circuit, self._bbcircuit_modded.qubit_order, "modded")

            printRange(sim_range[0], sim_range[-1], step)

            colpr("c", f"Simulating both the modded and {name} circuits and comparing their output vector and measurements ...", end="\n\n")
