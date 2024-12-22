import multiprocessing
import threading
import time
from functools import partial

import cirq
import cirq.optimizers

import qramcircuits.bucket_brigade as bb
from qram.simulator.base import QRAMSimulatorBase
from qramcircuits.toffoli_decomposition import ToffoliDecomposition, ToffoliDecompType
from utils.print_utils import (
    colpr,
    loading_animation,
    message,
    printCircuit,
    printRange,
)


def fan_in_mem_out(
    decomp_scenario: bb.BucketBrigadeDecompType,
) -> "list[ToffoliDecompType]":
    """
    Returns the fan-in, memory, and fan-out decomposition types.

    Args:
        decomp_scenario (bb.BucketBrigadeDecompType): The decomposition scenario for the bucket brigade.

    Returns:
        'list[ToffoliDecompType]': The fan-in, memory, and fan-out decomposition types.
    """

    return list(set(decomp_scenario.get_decomp_types()))


def create_decomposition_circuit(
    decomposition_type: ToffoliDecompType,
) -> "tuple[cirq.Circuit, list[cirq.NamedQubit]]":
    """
    Creates a Toffoli decomposition circuit.

    Args:
        decomposition_type (ToffoliDecompType): The type of Toffoli decomposition.

    Returns:
        'tuple[cirq.Circuit, list[cirq.NamedQubit]]': The Toffoli decomposition circuit and qubits.
    """

    circuit = cirq.Circuit()

    qubits = [cirq.NamedQubit("q" + str(i)) for i in range(3)]

    decomp = ToffoliDecomposition(decomposition_type=decomposition_type, qubits=qubits)

    if decomp.number_of_ancilla() > 0:
        qubits += [decomp.ancilla[i] for i in range(int(decomp.number_of_ancilla()))]

    circuit.append(decomp.decomposition())

    return circuit, qubits


#######################################
# QRAM Simulator Decompositions
#######################################


class QRAMSimulatorDecompositions(QRAMSimulatorBase):
    """
    The QRAMDecompositionsSimulator class to simulate the Toffoli decompositions.

    Methods:
        _decomposed_circuit(decomposition_type): Creates a Toffoli decomposition with measurements circuit.
        _simulate_decompositions(): Simulates the Toffoli decompositions.
        _simulate_decomposition(decomposition_type): Simulates a Toffoli decomposition.
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Constructor of the QRAMDecompositionsSimulator class.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            None
        """

        super().__init__(*args, **kwargs)

        self._simulate_decompositions()

    #######################################
    # core functions
    #######################################

    def _decomposed_circuit(
        self, decomposition_type: ToffoliDecompType
    ) -> "tuple[cirq.Circuit, list[cirq.NamedQubit]]":
        """
        Creates a Toffoli decomposition with measurements circuit.

        Args:
            decomposition_type (ToffoliDecompType): The type of Toffoli decomposition.

        Returns:
            'tuple[cirq.Circuit, list[cirq.NamedQubit]]': The Toffoli decomposition circuit and qubits.
        """

        circuit, qubits = create_decomposition_circuit(decomposition_type)

        measurements = []
        for qubit in qubits:
            if qubit.name[0] == "q":
                measurements.append(cirq.measure(qubit))

        circuit.append(measurements)
        cirq.optimizers.SynchronizeTerminalMeasurements().optimize_circuit(circuit)

        if decomposition_type != ToffoliDecompType.NO_DECOMP:
            printCircuit(
                self._print_circuit,
                circuit,
                qubits,
                f"decomposition {str(decomposition_type)}",
            )

        return circuit, qubits

    def _simulate_decompositions(self) -> None:
        """
        Simulates the Toffoli decompositions.
        """

        self._simulation_kind = "dec"

        msg = message(
            "Simulating the circuit ... Comparing the results of the decompositions to the Toffoli gate"
        )
        colpr("y", f"\n{msg}", end="\n\n")

        for decomp_scenario in [self._decomp_scenario, self._decomp_scenario_modded]:
            for decomposition_type in fan_in_mem_out(decomp_scenario):
                if decomposition_type == ToffoliDecompType.NO_DECOMP:
                    continue
                self._simulate_decomposition(decomposition_type)

    def _simulate_decomposition(self, decomposition_type: ToffoliDecompType) -> None:
        """
        Simulates a Toffoli decomposition.

        Args:
            decomposition_type (ToffoliDecompType): The type of Toffoli decomposition.

        Returns:
            None
        """

        self._start_time = time.time()

        circuit, qubits = self._decomposed_circuit(ToffoliDecompType.NO_DECOMP)
        circuit_modded, qubits_modded = self._decomposed_circuit(decomposition_type)

        nbr_anc = ToffoliDecomposition.numbers_of_ancilla(decomposition_type)

        """ 0 ancilla
            0 0 0 0 -> 0 : start
            0 0 0 0 -> 1 : step
            ...
            0 1 1 1 -> 7
            1 0 0 0 -> 8 : stop
        """
        """ 2 ancilla
            0 0 0 0 0 0 -> 0 : start
            0 0 0 1 0 0 -> 4 : step
            0 0 1 0 0 0 -> 8
            ...
            0 1 1 1 0 0 -> 28
            1 0 0 0 0 0 -> 32 : stop
        """
        start = 0
        step = 2**nbr_anc
        stop = 8 * step

        # prints ##############################################################################
        printRange(start, stop, step)

        colpr(
            "c",
            "Simulating the decomposition ... ",
            str(decomposition_type),
            end="\n\n",
        )

        # reset the simulation results ########################################################
        self._simulation_results = multiprocessing.Manager().dict()

        # use thread to load the simulation ###################################################
        if self._print_sim == "Loading":
            stop_event = threading.Event()
            loading_thread = threading.Thread(
                target=loading_animation,
                args=(
                    stop_event,
                    "simulation",
                ),
            )
            loading_thread.start()

        # Use multiprocessing to parallelize the simulation ###################################
        try:
            with multiprocessing.Pool() as pool:
                results = pool.map(
                    partial(
                        self._worker,
                        step=step,
                        circuit=circuit,
                        circuit_modded=circuit_modded,
                        qubit_order=qubits,
                        qubit_order_modded=qubits_modded,
                    ),
                    range(start, stop, step),
                )
        finally:
            if self._print_sim == "Loading":
                stop_event.set()
                loading_thread.join()

        self._print_simulation_results(results, list(range(start, stop, step)), step)
