import cirq
import cirq.optimizers
import copy
import itertools
import math
import numpy as np
import os
import psutil
import sys
import time
from datetime import timedelta

from functools import partial
import multiprocessing
import threading

from IPython.display import display
from cirq.contrib.svg import SVGCircuit, circuit_to_svg
from typing import Union

import optimizers as qopt
import qramcircuits.bucket_brigade as bb
from qramcircuits.bucket_brigade import MirrorMethod
from qramcircuits.toffoli_decomposition import ToffoliDecompType, ToffoliDecomposition
from utils.counting_utils import *


help: str = """
How to run the QRAMCircuitExperiments.py file:

Run the following command in the terminal:

    python3 QRAMCircuitExperiments.py

or by adding arguments:

    python3 QRAMCircuitExperiments.py y y n 2 2

Arguments:
- arg 1: Simulate Toffoli decompositions and circuit (y/n).
- arg 2: (P) print or (D) display or (H) hide circuits.
- arg 3: (F) full simulation or (D) just dots or (H) hide the simulation.
- arg 4: Start range of qubits, starting from 2.
- arg 5: End range of qubits, should be equal to or greater than the start range.
- additional arg 6: Specific simulation (a, b, m, ab, bm, abm, abmt, t).
    leave it empty to simulate the full circuit.
    only for full circuit we compare the output vector.
"""


#######################################
# static methods
#######################################

def colpr(color: str, *args: str, end: str="\n") -> None:
    """
    Prints colored text.

    Args:
        color (str): The color of the text [r, g, v, b, y, c, w, m, k, d, u].
        args (str): The text to be printed.
        end (str): The end character.

    Returns:
        None
    """

    colors = {
        "r": "\033[91m",
        "g": "\033[92m",
        "v": "\033[95m",
        "b": "\033[94m",
        "y": "\033[93m",
        "c": "\033[96m",
        "w": "\033[97m",
        "m": "\033[95m",
        "k": "\033[90m",
        "d": "\033[2m",
        "u": "\033[4m"
    }
    print(colors[color] + "".join(args) + "\033[0m", flush=True, end=end)


def elapsed_time(start: float) -> str:
    """
    Format the elapsed time from the start time to the current time.

    Args:
        start (float): The start time in seconds.

    Returns:
        str: The formatted elapsed time.
    """

    elapsed_time = time.time() - start
    delta = timedelta(seconds=elapsed_time)
    
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = delta.microseconds // 1000

    if hours > 0:
        return f"{hours}h {minutes}min {seconds}s {milliseconds}ms"
    elif minutes > 0:
        return f"{minutes}min {seconds}s {milliseconds}ms"
    elif seconds > 0:
        return f"{seconds}s {milliseconds}ms"
    else:
        return f"{milliseconds}ms"


def loading_animation(stop_event: threading.Event, title: str) -> None:
    animation = "|/-\\"
    idx = 0
    while not stop_event.is_set():
        print(f"\rLoading {title} {animation[idx % len(animation)]}", end="")
        idx += 1
        time.sleep(0.1)
    print("\r" + " " * (10 + len(title)) + "\r", end="")


def format_bytes(num_bytes):
    """
    Convert bytes to a human-readable format using SI units.

    Args:
        num_bytes (int): The number of bytes.

    Returns:
        str: The human-readable format.
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num_bytes < 1024:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024


def printCircuit(
        print_circuit: str,
        circuit: cirq.Circuit,
        qubits: 'list[cirq.NamedQubit]',
        name: str = "bucket brigade"
) -> None:
    """
    Prints the circuit.

    Args:
        circuit (cirq.Circuit): The circuit to be printed.
        qubits ('list[cirq.NamedQubit]'): The qubits of the circuit.
        name (str): The name of the circuit.

    Returns:
        None
    """
    if print_circuit == "Print":
        # Print the circuit
        start = time.time()

        colpr("c", f"Print {name} circuit:" , end="\n\n")
        print(
            circuit.to_text_diagram(
                # use_unicode_characters=False,
                qubit_order=qubits
            ),
            end="\n\n"
        )

        stop = elapsed_time(start)
        colpr("w", "Time of printing the circuit: ", stop, end="\n\n")

    elif print_circuit == "Display":
        # Display the circuit
        start = time.time()

        colpr("c", f"Display {name} circuit:" , end="\n\n")

        display(SVGCircuit(circuit))

        stop = elapsed_time(start)
        colpr("w", "Time of displaying the circuit: ", stop, end="\n\n")

    # # Save the circuit as an SVG file
    # with open(f"images/{self.__start_range_qubits}_{name}_circuit.svg", "w") as f:
    #     f.write(sv.circuit_to_svg(circuit))


#######################################
# QRAM Circuit Simulator
#######################################

class QRAMCircuitSimulator:
    """
    The QRAMCircuitSimulator class to simulate the bucket brigade circuit.

    Attributes:
        __specific_simulation (str): The specific simulation.
        __start_range_qubits (int): The start range of the qubits.
        __print_circuit (str): The print circuit flag.
        __print_sim (str): Flag indicating whether to print the full simulation result.

        __simulation_results (multiprocessing.managers.DictProxy): The simulation results.

        __bbcircuit (bb.BucketBrigade): The bucket brigade circuit.
        __bbcircuit_modded (bb.BucketBrigade): The modded circuit.
        __decomp_scenario (bb.BucketBrigadeDecompType): The decomposition scenario.
        __simulator (cirq.Simulator): The Cirq simulator.

    Methods:
        get_simulation_bilan(): Returns the simulation bilan.
        __init__(self, bbcircuit, bbcircuit_modded, specific_simulation, start_range_qubits, print_circuit, print_sim):
            Constructor of the CircuitSimulator class.

        __fan_in_mem_out(): Returns the fan-in, memory, and fan-out decomposition types.
        __create_decomposition_circuit(): Creates a Toffoli decomposition circuit.
        __decomposed_circuit(): Creates a Toffoli decomposition with measurements circuit.
        __simulate_decompositions(): Simulates the Toffoli decompositions.
        __simulate_decomposition(): Simulates a Toffoli decomposition.

        __simulate_circuit(): Simulates the circuit.
        _simulation_a_qubits(): Simulates the circuit and measure addressing of the a qubits.
        _simulation_b_qubits(): Simulates the circuit and measure uncomputation of FANOUT.
        _simulation_m_qubits(): Simulates the circuit and measure computation of MEM.
        _simulation_ab_qubits(): Simulates the circuit and measure addressing and uncomputation of the a and b qubits.
        _simulation_bm_qubits(): Simulates the circuit and measure computation and uncomputation of the b and m qubits.
        _simulation_abm_qubits(): Simulates the circuit and measure addressing and uncomputation and computation of the a, b, and m qubits.
        _simulation_t_qubits(): Simulates the addressing and uncomputation and computation of the a, b, and m qubits and measure only the target qubit.
        _simulation_full_qubits(): Simulates the circuit and measure all full circuit.
        __simulation(): Simulates the circuit.

        _worker(): Worker function for multiprocessing.
        __simulate_and_compare(): Simulate and compares the results of the simulation and measurement.
        __print_simulation_results(): Prints the simulation results.
    """

    __specific_simulation: str
    __start_range_qubits: int
    __print_circuit: str
    __print_sim: str
    __simulation_kind: str = "dec"

    __simulation_results: multiprocessing.managers.DictProxy = multiprocessing.Manager().dict()
    __simulation_bilan: list = []

    __bbcircuit: bb.BucketBrigade
    __bbcircuit_modded: bb.BucketBrigade
    __decomp_scenario: bb.BucketBrigadeDecompType
    __decomp_scenario_modded: bb.BucketBrigadeDecompType
    __simulator: cirq.Simulator = cirq.Simulator()

    def get_simulation_bilan(self) -> list:
        """
        Returns the simulation bilan.

        Args:
            None

        Returns:
            list: The simulation bilan.
        """

        return self.__simulation_bilan

    def __init__(
            self,
            bbcircuit: bb.BucketBrigade,
            bbcircuit_modded: bb.BucketBrigade,
            specific_simulation: str,
            start_range_qubits: int,
            print_circuit: str,
            print_sim: str
        ) -> None:
        """
        Constructor of the CircuitSimulator class.

        Args:
            bbcircuit (BBCircuit): The bucket brigade circuit.
            bbcircuit_modded (BBCircuit): The modded circuit.
            decomp_scenario (DecompScenario): The decomposition scenario.
            specific_simulation (str): The specific simulation.
            start_range_qubits (int): The start range of the qubits.
            simulate (bool): The simulation flag.
            print_circuit (str): The print circuit flag.
            print_sim (str): The print simulation flag.

        Returns:
            None
        """

        self.__bbcircuit = bbcircuit
        self.__bbcircuit_modded = bbcircuit_modded
        self.__decomp_scenario = bbcircuit.decomp_scenario
        self.__decomp_scenario_modded = bbcircuit_modded.decomp_scenario
        self.__specific_simulation = specific_simulation
        self.__start_range_qubits = start_range_qubits
        self.__print_circuit = print_circuit
        self.__print_sim = print_sim
    
    def _run_simulation(self) -> None:
        """
        Runs the simulation.
        """

        self.__simulate_decompositions()

        self._simulate_circuit()

    #######################################
    # simulate decompositions methods
    #######################################

    def _fan_in_mem_out(
            self, 
            decomp_scenario: bb.BucketBrigadeDecompType
    ) -> 'list[ToffoliDecompType]':
        """
        Returns the fan-in, memory, and fan-out decomposition types.

        Args:
            decomp_scenario (bb.BucketBrigadeDecompType): The decomposition scenario for the bucket brigade.

        Returns:
            'list[ToffoliDecompType]': The fan-in, memory, and fan-out decomposition types.
        """

        return list(set(decomp_scenario.get_decomp_types()))

    def _create_decomposition_circuit(
            self, 
            decomposition_type: ToffoliDecompType
    ) -> 'tuple[cirq.Circuit, list[cirq.NamedQubit]]':
        """
        Creates a Toffoli decomposition circuit.

        Args:
            decomposition_type (ToffoliDecompType): The type of Toffoli decomposition.

        Returns:
            'tuple[cirq.Circuit, list[cirq.NamedQubit]]': The Toffoli decomposition circuit and qubits.
        """
        
        circuit = cirq.Circuit()

        qubits = [cirq.NamedQubit("q" + str(i)) for i in range(3)]

        decomp = ToffoliDecomposition(
            decomposition_type=decomposition_type,
            qubits=qubits)

        if decomp.number_of_ancilla() > 0:
            qubits += [decomp.ancilla[i] for i in range(int(decomp.number_of_ancilla()))]

        circuit.append(decomp.decomposition())

        return circuit, qubits

    def __decomposed_circuit(
            self, 
            decomposition_type: ToffoliDecompType
    ) -> 'tuple[cirq.Circuit, list[cirq.NamedQubit], np.array]':
        """
        Creates a Toffoli decomposition with measurements circuit.

        Args:
            decomposition_type (ToffoliDecompType): The type of Toffoli decomposition.

        Returns:
            'tuple[cirq.Circuit, list[cirq.NamedQubit], np.array]': The Toffoli decomposition circuit, qubits, and initial state.
        """

        circuit, qubits = self._create_decomposition_circuit(decomposition_type)

        measurements = []
        for qubit in qubits:
            if qubit.name[0] == "q":
                measurements.append(cirq.measure(qubit))

        circuit.append(measurements)
        cirq.optimizers.SynchronizeTerminalMeasurements().optimize_circuit(circuit)

        if decomposition_type != ToffoliDecompType.NO_DECOMP:
            printCircuit(self.__print_circuit, circuit, qubits, f"decomposition {str(decomposition_type)}")

        ls = [0 for _ in range(2**len(qubits))]
        initial_state = np.array(ls, dtype=np.complex64)
    
        return circuit, qubits, initial_state

    def __simulate_decompositions(self) -> None:
        """
        Simulates the Toffoli decompositions.
        """

        colpr("y", "\nSimulating the decompositions ... comparing the results of the decompositions to the Toffoli gate.", end="\n\n")

        for decomp_scenario in [self.__decomp_scenario, self.__decomp_scenario_modded]:
            for decomposition_type in self._fan_in_mem_out(decomp_scenario):
                if decomposition_type == ToffoliDecompType.NO_DECOMP:
                    continue
                self.__simulate_decomposition(decomposition_type)

    def __simulate_decomposition(self, decomposition_type: ToffoliDecompType) -> None:
        """
        Simulates a Toffoli decomposition.

        Args:
            decomposition_type (ToffoliDecompType): The type of Toffoli decomposition.

        Returns:
            None
        """

        self.__start_time = time.time()

        circuit, qubits, initial_state = self.__decomposed_circuit(ToffoliDecompType.NO_DECOMP)
        circuit_modded, qubits_modded, initial_state_modded = self.__decomposed_circuit(decomposition_type)

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
        step = 2 ** nbr_anc
        stop = 8 * step

        # prints ##############################################################################
        print("start =", start,"\tstop =", stop,"\tstep =", step, end="\n\n")

        colpr("c", "Simulating the decomposition ... ", str(decomposition_type),  end="\n\n")

        # reset the simulation results ########################################################
        self.__simulation_results = multiprocessing.Manager().dict()

        # use thread to load the simulation ################################################
        if self.__print_sim == "Hide":
            stop_event = threading.Event()
            loading_thread = threading.Thread(target=loading_animation, args=(stop_event, 'simulation',))
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
                        initial_state=initial_state,
                        initial_state_modded=initial_state_modded),
                    range(start, stop, step))
        finally:
            if self.__print_sim == "Hide":
                stop_event.set()
                loading_thread.join()

        self.__print_simulation_results(results, start, stop, step)

    #######################################
    # simulate circuit methods
    #######################################

    def _simulate_circuit(self) -> None:
        """
        Simulates the circuit.
        """

        self.__simulation_kind = "bb"

        # Construct the method name
        method_name = f"_simulation_{self.__specific_simulation}_qubits"

        # Get the method from the class instance
        method = getattr(self, method_name, None)

        # Check if the method exists and call it
        if callable(method):
            method()
        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{method_name}'")

    def _simulation_a_qubits(self) -> None:
        """
        Simulates the circuit and measure addressing of the a qubits.
        """

        """ 2
        the range of a qubits
        0 00 0000 0000 0 -> 0 : start
        0 01 0000 0000 0 -> 512 : step
        0 10 0000 0000 0 -> 1024
        0 11 0000 0000 0 -> 1536
        1 00 0000 0000 0 -> 2048 : stop 
        """
        """ 3
        the range of a qubits
        0 000 00000000 00000000 0 -> 0 : start
        0 001 00000000 00000000 0 -> 131072 : step
        0 010 00000000 00000000 0 -> 262144
        0 011 00000000 00000000 0 -> 393216
        0 100 00000000 00000000 0 -> 524288
        0 101 00000000 00000000 0 -> 655360
        0 110 00000000 00000000 0 -> 786432
        0 111 00000000 00000000 0 -> 917504
        1 000 00000000 00000000 0 -> 1048576 : stop
        """

        start = 0
        # step = 2**(2**self.start_range_qubits+1) * (2**(2**self.start_range_qubits))
        step = 2 ** ( 2 * ( 2 ** self.__start_range_qubits ) + 1 )
        stop = step * ( 2 ** self.__start_range_qubits )
        colpr("y", "\nSimulating the circuit ... checking the addressing of the a qubits.", end="\n\n")
        self.__simulation(start, stop, step)

    def _simulation_b_qubits(self) -> None:
        """
        Simulates the circuit and measure uncomputation of FANOUT.
        """

        """ 2
        the range of b qubits
        0 00 0000 0000 0 -> 0 : start
        0 00 0001 0000 0 -> 32 : step
        0 00 0010 0000 0 -> 64
        0 00 0011 0000 0 -> 96
        ...
        0 00 1111 0000 0 -> 480
        0 01 0000 0000 0 -> 512 : stop
        """
        """ 3
        the range of b qubits
        0 000 00000000 00000000 0 -> 0 : start
        0 000 00000001 00000000 0 -> 512 : step
        0 000 00000010 00000000 0 -> 1024
        0 000 00000011 00000000 0 -> 1536
        ...
        0 000 11111111 00000000 0 -> 65536
        0 001 00000000 00000000 0 -> 131072 : stop
        """

        start = 0
        step = 2 ** ( 2 ** self.__start_range_qubits + 1 )
        stop = step * ( 2 ** ( 2 ** self.__start_range_qubits ) )
        colpr("y", "\nSimulating the circuit ... checking the uncomputation of FANOUT ... were the b qubits are returned to their initial state.", end="\n\n")
        self.__simulation(start, stop, step)

    def _simulation_m_qubits(self) -> None:
        """
        Simulates the circuit and measure computation of MEM.
        """

        """ 2
        the range of m qubits
        0 00 0000 0000 0 -> 0 : start
        0 00 0000 0001 0 -> 2 : step
        0 00 0000 0010 0 -> 4
        0 00 0000 0011 0 -> 6
        ...
        0 00 0000 1111 0 -> 30
        0 00 0001 0000 0 -> 32 : stop
        """
        """ 3
        the range of m qubits
        0 000 00000000 00000000 0 -> 0 : start
        0 000 00000000 00000001 0 -> 2 : step
        0 000 00000000 00000010 0 -> 4
        0 000 00000000 00000011 0 -> 6
        ...
        0 000 00000000 00001111 0 -> 30
        0 000 00000000 00010000 0 -> 32
        ...
        0 000 00000000 11111111 0 -> 510
        0 000 00000001 00000000 0 -> 512 : stop
        """

        start = 0
        step = 2
        stop = step * ( 2 ** ( 2 ** self.__start_range_qubits ) )
        colpr("y", "\nSimulating the circuit ... checking the computation of MEM ... were the m qubits are getting the result of the computation.", end="\n\n")
        self.__simulation(start, stop, step)

    def _simulation_ab_qubits(self) -> None:
        """
        Simulates the circuit and measure addressing and uncomputation of the a and b qubits.
        """

        """ 2
        the range of a and b qubits
        0 00 0000 0000 0 -> 0 : start
        0 00 0001 0000 0 -> 32 : step
        0 00 0010 0000 0 -> 64
        0 00 0011 0000 0 -> 96
        ...
        0 00 1111 0000 0 -> 480
        0 01 0000 0000 0 -> 512
        ...
        0 11 1111 0000 0 -> 2016
        1 00 0000 0000 0 -> 2048 : stop
        """
        """ 3
        the range of a and b qubits
        0 000 00000000 00000000 0 -> 0 : start
        0 000 00000001 00000000 0 -> 512 : step
        ...
        0 000 11111111 00000000 0 -> 65536
        0 001 00000000 00000000 0 -> 131072
        ...
        0 100 11111111 00000000 0 -> 589824
        ...
        1 000 00000000 00000000 0 -> 1048576 : stop
        """

        start = 0
        step_b = 2 ** ( 2 ** self.__start_range_qubits + 1 )

        step_a = 2 ** ( 2 * ( 2 ** self.__start_range_qubits ) + 1 )
        stop = step_a * ( 2 ** self.__start_range_qubits )
        colpr("y", "\nSimulating the circuit ... checking the addressing and uncomputation of the a and b qubits.", end="\n\n")
        self.__simulation(start, stop, step_b)

    def _simulation_bm_qubits(self) -> None:
        """
        Simulates the circuit and measure computation and uncomputation of the b and m qubits.
        """

        """ 2
        the range of b and m qubits
        0 00 0000 0000 0 -> 0 : start
        0 00 0000 0001 0 -> 2 : step
        0 00 0000 0010 0 -> 4
        0 00 0000 0011 0 -> 6
        ...
        0 00 0000 1111 0 -> 30
        0 00 0001 0000 0 -> 32
        ...
        0 00 1111 0000 0 -> 480
        0 01 0000 0000 0 -> 512 : stop
        """
        """ 3
        the range of b and m qubits
        0 000 00000000 00000000 0 -> 0 : start
        0 000 00000000 00000001 0 -> 2 : step
        0 000 00000000 00000010 0 -> 4
        0 000 00000000 00000011 0 -> 6
        ...
        0 000 00000000 00001111 0 -> 30
        0 000 00000000 00010000 0 -> 32
        ...
        0 000 00000000 11111111 0 -> 510
        0 000 00000001 00000000 0 -> 512
        ...
        0 000 11111111 00000000 0 -> 65536
        0 001 00000000 00000000 0 -> 131072 : stop
        """

        start = 0
        step_m = 2

        step_b = 2 ** ( 2 ** self.__start_range_qubits + 1 )
        stop = step_b * ( 2 ** ( 2 ** self.__start_range_qubits ) )
        colpr("y", "\nSimulating the circuit ... checking the addressing and uncomputation of the b and m qubits.", end="\n\n")
        self.__simulation(start, stop, step_m)

    def _simulation_abm_qubits(self) -> None:
        """
        Simulates the circuit and measure addressing and uncomputation and computation of the a, b, and m qubits.
        """

        """ 2
        the range of a, b, and m qubits
        0 00 0000 0000 0 -> 0 : start
        0 00 0000 0001 0 -> 2 : step
        0 00 0000 0010 0 -> 4
        0 00 0000 0011 0 -> 6
        ...
        0 00 0000 1111 0 -> 30
        0 00 0001 0000 0 -> 32
        ...
        0 00 1111 0000 0 -> 480
        0 01 0000 0000 0 -> 512
        ...
        0 11 1111 0000 0 -> 2016
        1 00 0000 0000 0 -> 2048 : stop
        """
        """ 3
        the range of a, b, and m qubits
        0 000 00000000 00000000 0 -> 0 : start
        0 000 00000000 00000001 0 -> 2 : step
        0 000 00000000 00000010 0 -> 4
        0 000 00000000 00000011 0 -> 6
        ...
        0 000 00000000 00001111 0 -> 30
        0 000 00000000 00010000 0 -> 32
        ...
        0 000 00000000 11111111 0 -> 510
        0 000 00000001 00000000 0 -> 512
        ...
        0 000 11111111 00000000 0 -> 65536
        0 001 00000000 00000000 0 -> 131072
        ...
        0 100 11111111 00000000 0 -> 589824
        ...
        1 000 00000000 00000000 0 -> 1048576 : stop
        """

        start = 0
        step_m = 2
        step_a = 2 ** ( 2 * ( 2 ** self.__start_range_qubits ) + 1 )
        stop = step_a * ( 2 ** self.__start_range_qubits )
        colpr("y", "\nSimulating the circuit ... checking the addressing and uncomputation of the a, b, and m qubits.", end="\n\n")
        self.__simulation(start, stop, step_m)

    def _simulation_t_qubits(self) -> None:
        """
        Simulates the addressing and uncomputation and computation of the a, b, and m qubits and measure only the target qubit.
        """

        """ 2
        the range of a, b, and m qubits
        0 00 0000 0000 0 -> 0 : start
        0 00 0000 0001 0 -> 2 : step
        0 00 0000 0010 0 -> 4
        0 00 0000 0011 0 -> 6
        ...
        0 00 0000 1111 0 -> 30
        0 00 0001 0000 0 -> 32
        ...
        0 00 1111 0000 0 -> 480
        0 01 0000 0000 0 -> 512
        ...
        0 11 1111 0000 0 -> 2016
        1 00 0000 0000 0 -> 2048 : stop
        """
        """ 3
        the range of a, b, and m qubits
        0 000 00000000 00000000 0 -> 0 : start
        0 000 00000000 00000001 0 -> 2 : step
        0 000 00000000 00000010 0 -> 4
        0 000 00000000 00000011 0 -> 6
        ...
        0 000 00000000 00001111 0 -> 30
        0 000 00000000 00010000 0 -> 32
        ...
        0 000 00000000 11111111 0 -> 510
        0 000 00000001 00000000 0 -> 512
        ...
        0 000 11111111 00000000 0 -> 65536
        0 001 00000000 00000000 0 -> 131072
        ...
        0 100 11111111 00000000 0 -> 589824
        ...
        1 000 00000000 00000000 0 -> 1048576 : stop
        """

        start = 0
        step_m = 2
        step_a = 2 ** ( 2 * ( 2 ** self.__start_range_qubits ) + 1 )
        stop = step_a * ( 2 ** self.__start_range_qubits )
        print("\nSimulating the circuit ... checking the addressing and uncomputation of the a, b, and m qubits and measure only the target qubit.", end="\n\n")
        self.__simulation(start, stop, step_m)

    def _simulation_full_qubits(self) -> None:
        """
        Simulates the circuit and measure all qubits.
        """

        """ 2
        the range of all qubits
        0 00 0000 0000 0 -> 0 : start
        0 00 0000 0000 1 -> 1 : step
        ...
        1 00 0000 0000 0 -> 2048 : stop 
        """
        """ 3
        the range of all qubits
        0 000 00000000 00000000 0 -> 0 : start
        0 000 00000000 00000000 1 -> 0 : 1
        ...
        1 000 00000000 00000000 0 -> 1048576 : stop
        """

        start = 0
        # stop = 2**(2**self.start_range_qubits+1) * (2**(2**self.start_range_qubits)) * (2**self.start_range_qubits)
        stop = 2 ** ( 2 * ( 2 ** self.__start_range_qubits ) + self.__start_range_qubits + 1 )
        print("\nSimulating the circuit ... checking the all qubits.", end="\n\n")
        self.__simulation(start, stop, 1)

    def __simulation(self, start:int, stop:int, step:int) -> None:
        """
        Simulates the circuit.

        Args:
            start (int): The start index.
            stop (int): The stop index.
            step (int): The step index.

        Returns:
            None
        """

        self.__start_time = time.time()

        # add measurements to the reference circuit ############################################
        measurements = []
        for qubit in self.__bbcircuit.qubit_order:
            if self.__specific_simulation == "full":
                measurements.append(cirq.measure(qubit))
            else:
                for _name in self.__specific_simulation:
                    if qubit.name.startswith(_name):
                        measurements.append(cirq.measure(qubit))

        self.__bbcircuit.circuit.append(measurements)
        cirq.optimizers.SynchronizeTerminalMeasurements().optimize_circuit(self.__bbcircuit.circuit)

        name = "bucket brigade" if self.__decomp_scenario.get_decomp_types()[0] == ToffoliDecompType.NO_DECOMP else "reference"
        printCircuit(self.__print_circuit, self.__bbcircuit.circuit, self.__bbcircuit.qubit_order, name)

        ls = [0 for _ in range(2**len(self.__bbcircuit.qubit_order))]
        initial_state = np.array(ls, dtype=np.complex64)

        # add measurements to the modded circuit ##############################################
        measurements_modded = []
        for qubit in self.__bbcircuit_modded.qubit_order:
            if self.__specific_simulation == "full":
                measurements_modded.append(cirq.measure(qubit))
            else:
                for _name in self.__specific_simulation:
                    if qubit.name.startswith(_name):
                        measurements_modded.append(cirq.measure(qubit))

        self.__bbcircuit_modded.circuit.append(measurements_modded)
        cirq.optimizers.SynchronizeTerminalMeasurements().optimize_circuit(self.__bbcircuit_modded.circuit)

        printCircuit(self.__print_circuit, self.__bbcircuit_modded.circuit, self.__bbcircuit_modded.qubit_order, "modded")

        ls_modded = [0 for _ in range(2**len(self.__bbcircuit_modded.qubit_order))]
        initial_state_modded = np.array(ls_modded, dtype=np.complex64)

        # prints ##############################################################################
        print("start =", start,"\tstop =", stop,"\tstep =", step, end="\n\n")

        colpr("c", f"Simulating both the modded and {name} circuits and comparing their output vector and measurements ...", end="\n\n")

        # reset the simulation results ########################################################
        self.__simulation_results = multiprocessing.Manager().dict()

        # use thread to load the simulation ################################################
        if self.__print_sim == "Hide":
            stop_event = threading.Event()
            loading_thread = threading.Thread(target=loading_animation, args=(stop_event, 'simulation',))
            loading_thread.start()

        # Use multiprocessing to parallelize the simulation ###################################
        try:
            with multiprocessing.Pool() as pool:
                results = pool.map(
                    partial(
                        self._worker,
                        step=step,
                        circuit=self.__bbcircuit.circuit,
                        circuit_modded=self.__bbcircuit_modded.circuit,
                        qubit_order=self.__bbcircuit.qubit_order,
                        qubit_order_modded=self.__bbcircuit_modded.qubit_order,
                        initial_state=initial_state,
                        initial_state_modded=initial_state_modded),
                    range(start, stop, step))            
        finally:
            if self.__print_sim == "Hide":
                stop_event.set()
                loading_thread.join()

        self.__print_simulation_results(results, start, stop, step)

    #######################################
    # Core methods
    #######################################

    def _worker(
            self,
            i: int,
            step: int,
            circuit: cirq.Circuit,
            circuit_modded: cirq.Circuit,
            qubit_order: 'list[cirq.NamedQubit]',
            qubit_order_modded: 'list[cirq.NamedQubit]',
            initial_state: np.ndarray,
            initial_state_modded: np.ndarray
        ) -> 'tuple[int, int, int]':
        """
        Worker function for multiprocessing.

        Args:
            i (int): The index of the simulation.
            step (int): The step index.
            circuit (cirq.Circuit): The circuit.
            circuit_modded (cirq.Circuit): The modded circuit.
            qubit_order (list[cirq.NamedQubit]): The qubit order of the circuit.
            qubit_order_modded (list[cirq.NamedQubit]): The qubit order of the modded circuit.
            initial_state (np.ndarray): The initial state of the circuit.
            initial_state_modded (np.ndarray): The initial state of the modded circuit.

        Returns:
            tuple[int, int, int]: The number of failed tests and the number of measurements and full tests success.
        """

        j = i
        if self.__simulation_kind == 'dec':
            j = math.floor(i/step) # reverse the 2 ** nbr_anc binary number

        initial_state[j] = 1
        initial_state_modded[i] = 1

        f, sm, sv = self.__simulate_and_compare(
            i,
            j,
            circuit,
            circuit_modded,
            qubit_order,
            qubit_order_modded,
            initial_state,
            initial_state_modded
        )

        initial_state[j] = 0
        initial_state_modded[i] = 0
        return f, sm, sv

    def __simulate_and_compare(
            self,
            i: int,
            j: int,
            circuit: cirq.Circuit,
            circuit_modded: cirq.Circuit,
            qubit_order: 'list[cirq.NamedQubit]',
            qubit_order_modded: 'list[cirq.NamedQubit]',
            initial_state: np.ndarray,
            initial_state_modded: np.ndarray
        ) -> 'tuple[int, int, int]':
        """
        Simulate and compares the results of the simulation.

        Args:
            i (int): The index of the simulation.
            j (int): The index of the reversed binary number.
            circuit (cirq.Circuit): The circuit.
            circuit_modded (cirq.Circuit): The modded circuit.
            qubit_order (list[cirq.NamedQubit]): The qubit order of the circuit.
            qubit_order_modded (list[cirq.NamedQubit]): The qubit order of the modded circuit.
            initial_state (np.ndarray): The initial state of the circuit.
            initial_state_modded (np.ndarray): The initial state of the modded circuit.

        Returns:
            int: The number of failed tests.
            int: The number of measurements tests success.
            int: The number of full tests success.
        """

        fail:int = 0
        success_measurements:int = 0
        success_vector:int = 0

        result = self.__simulator.simulate(
            circuit,
            qubit_order=qubit_order,
            initial_state=initial_state
        )

        result_modded = self.__simulator.simulate(
            circuit_modded,
            qubit_order=qubit_order_modded,
            initial_state=initial_state_modded
        )

        # Extract specific measurements
        measurements = result.measurements
        measurements_modded = result_modded.measurements

        try:
            # Compare final state which is the output vector, only for all qubits
            assert np.array_equal(
                np.array(np.around(result.final_state[j])),
                np.array(np.around(result_modded.final_state[i]))
            )
        except Exception:
            try:
                # Compare specific measurements for the specific qubits
                for o_qubit in self.__bbcircuit.qubit_order:
                    for qubit in measurements.keys():
                        if str(o_qubit) == str(qubit):
                            assert np.array_equal(
                                measurements.get(qubit, np.array([])),
                                measurements_modded.get(qubit, np.array([]))
                            )
            except Exception:
                fail += 1
                if self.__print_sim == "Full" or self.__print_sim == "Dot":
                    colpr("r", "•", end="")
                if self.__print_sim == "Full":
                    self.__simulation_results[i] = ['r', result, result_modded]
            else:
                success_measurements += 1
                if self.__print_sim == "Full" or self.__print_sim == "Dot":
                    colpr("b", "•", end="")
                if self.__print_sim == "Full":
                    self.__simulation_results[i] = ['b', result, result_modded]
        else:
            success_vector += 1
            if self.__print_sim == "Full" or self.__print_sim == "Dot":
                colpr("g", "•", end="")
            if self.__print_sim == "Full":
                self.__simulation_results[i] = ['g', result, result_modded]

        return (fail, success_measurements, success_vector)

    def __print_simulation_results(self, results: 'list[tuple[int, int, int]]', start:int, stop:int, step:int) -> None:
        """
        Prints the simulation results.

        Args:
            results (list[tuple[int, int, int]]): The results of the simulation.
            start (int): The start index.
            stop (int): The stop index.
            step (int): The step index.

        Returns:
            None
        """

        fail:int = 0
        success_measurements:int = 0
        success_vector:int = 0
        total_tests:int = 0

        # Aggregate results
        for f, sm, sv in results:
            fail += f
            success_measurements += sm
            success_vector += sv
            total_tests += 1

        self.__stop_time = elapsed_time(self.__start_time)

        f = format(((fail * 100)/total_tests), ',.2f')
        sm = format(((success_measurements * 100)/total_tests), ',.2f')
        sv = format(((success_vector * 100)/total_tests), ',.2f')
        ts = format((((success_measurements + success_vector) * 100)/total_tests), ',.2f')

        print("\n\nResults of the simulation:\n")
        colpr("r", "\t• Failed: ", str(f), "%")
        if success_measurements == 0:
            colpr("g", "\t• Succeed: ", str(ts), "%", end="\n\n")
        else:
            colpr("y", "\t• Succeed: ", str(ts), "%", end="\t( ")
            colpr("b", "Measurements: ", str(sm), "%", end=" • ")
            colpr("g", "Output vector: ", str(sv), "%", end=" )\n\n")

        self.__simulation_bilan = [f, ts, sm, sv, success_measurements]

        colpr("w", "Time elapsed on simulate the decomposition: ", self.__stop_time, end="\n\n")

        if self.__print_sim == "Hide" or self.__print_sim == "Dot":
            return

        if self.__simulation_kind == 'dec':
            name = "Toffoli"
            name_modded = "Decomposed Toffoli"
        else:
            name = "Bucket brigade" if self.__decomp_scenario.get_decomp_types()[0] == ToffoliDecompType.NO_DECOMP else "Reference"
            name_modded = "Modded circuit"

        colpr("c", "Printing the simulation results ...", end="\n\n")

        for i in range(start, stop, step):
            j = i
            if self.__simulation_kind == 'dec':
                j = math.floor(i/step)
            (color, result, result_modded) = self.__simulation_results[i]
            colpr("c", f"Index of array {j} {i}", end="\n")
            colpr("w", f"{name} circuit result: ")
            colpr("w", str(result))
            colpr("c", "Comparing the output vector and measurements of both circuits ...", end="\n")
            colpr(color, f"{name_modded} circuit result: ")
            colpr(color, str(result_modded), end="\n\n")


#######################################
# QRAM Circuit Experiments
#######################################

class QRAMCircuitExperiments:
    """
    A class used to represent the QRAM circuit experiments.

    Attributes:
        __simulate (bool): Flag indicating whether to simulate Toffoli decompositions and circuit.
        __print_circuit (bool): Flag indicating whether to print the circuits.
        __print_sim (str): Flag indicating whether to print the full simulation result.
        __start_range_qubits (int): Start range of qubits.
        __end_range_qubits (int): End range of qubits.
        __start_time (float): Start time of the experiment.
        __stop_time (str): Stop time of the experiment.
        __decomp_scenario (bb.BucketBrigadeDecompType): Decomposition scenario for the bucket brigade.
        __decomp_scenario_modded (bb.BucketBrigadeDecompType): Modified decomposition scenario for the bucket brigade.
        __bbcircuit (bb.BucketBrigade): Bucket brigade circuit.
        __bbcircuit_modded (bb.BucketBrigade): Modified bucket brigade circuit.
        __simulator (cirq.Simulator): Cirq simulator.
        __specific_simulation (str): Specific simulation for specific qubit wire.
        __simulated (bool): Flag indicating whether the circuit has been simulated.

    Methods:
        __init__(): Initializes the QRAMCircuitExperiments class.
        __del__(): Destructs the QRAMCircuitExperiments class.
        __get_input(): Gets user input for the experiment.
        __bb_decompose(): Decomposes the Toffoli gates in the bucket brigade circuit.
        bb_decompose_test(): Tests the bucket brigade circuit with different decomposition scenarios.
        __run(): Runs the experiment for a range of qubits.
        __core(): Core function of the experiment.
        __results(): Prints the results of the experiment.
        __essential_checks(): Performs essential checks on the experiment.
        __verify_circuit_depth_count(): Verifies the depth and count of the circuit.
        __bilan(): Collect the bilan of the experiment.
        __print_bilan(): Prints the bilan of the experiment.
        __simulate_circuit(): Simulates the circuit.
    """

    _simulate: bool = False
    _print_circuit: str = "Hide"
    _print_sim: str = "Hide"
    _start_range_qubits: int
    _end_range_qubits: int
    _specific_simulation: str = "full"
    _simulated: bool = False

    _start_time: float = 0
    _stop_time: str = ""

    _data: multiprocessing.managers.DictProxy = multiprocessing.Manager().dict()
    _data_modded: multiprocessing.managers.DictProxy = multiprocessing.Manager().dict()
    _simulation_bilan: list = []
    _decomp_scenario: bb.BucketBrigadeDecompType
    _decomp_scenario_modded: bb.BucketBrigadeDecompType
    _bbcircuit: bb.BucketBrigade
    _bbcircuit_modded: bb.BucketBrigade
    _Simulator: QRAMCircuitSimulator


    def __init__(self):
        """
        Constructor the QRAMCircuitExperiments class.
        """

        self.__get_input()

        colpr("y", "Hello QRAM circuit experiments!", end="\n\n")

        colpr("c", f"Simulate Toffoli decompositions and circuit: {'yes' if self._simulate else 'no'}")
        colpr("c", f"{self._print_circuit} circuits")
        colpr("c", f"Print the full simulation result: {'yes' if self._print_sim else 'no'}")
        colpr("c", f"Start Range of Qubits: {self._start_range_qubits}")
        colpr("c", f"End Range of Qubits: {self._end_range_qubits}")

        if self._simulate:
            if self._specific_simulation == "full":
                colpr("c", f"Simulate full circuit")
            else:
                colpr("c", f"Simulate Specific Measurement: {self._specific_simulation}")
        print("\n")

    # def __del__(self):
    #     """
    #     Destructor of the QRAMCircuitExperiments class.
    #     """

    #     colpr("y", "Goodbye QRAM circuit experiments!")

    def __get_input(self) -> None:
        """
        Gets user input for the experiment.
        """

        flag = True
        msg0 = "Start range of qubits must be greater than 1"
        msg1 = "End range of qubits must be greater than start range of qubits or equal to it"
        msg2 = "Specific simulation must be (a, b, m, ab, bm, abm, t), by default it is full circuit"
        len_argv = 6
        
        try:
            if len(sys.argv) == len_argv or len(sys.argv) == len_argv + 1:
                if sys.argv[1].lower() in ["y", "yes"]:
                    self._simulate = True

                if sys.argv[2].lower() == "p":
                    self._print_circuit = "Print"
                elif sys.argv[2].lower() == "d":
                    self._print_circuit = "Display"

                if sys.argv[3].lower() == "d":
                    self._print_sim = "Dot"
                elif sys.argv[3].lower() == "f":
                    self._print_sim = "Full"

                self._start_range_qubits = int(sys.argv[4])
                if self._start_range_qubits < 2:
                    colpr("r", msg0, end="\n\n")
                    raise Exception

                self._end_range_qubits = int(sys.argv[5])
                if self._end_range_qubits < self._start_range_qubits:
                    self._end_range_qubits = self._start_range_qubits

                if len(sys.argv) == len_argv + 1 and self._simulate:
                    if str(sys.argv[6]) not in ['a', 'b', 'm', "ab", "bm", "abm", "t"]:
                        colpr("r", msg2, end="\n\n")
                        raise Exception
                    self._specific_simulation = str(sys.argv[6])
        except Exception:
            flag = False
            colpr("y", help, end="\n\n")

        if not flag or len(sys.argv) < len_argv or len_argv + 1 < len(sys.argv) :
            while True:
                user_input = input("Simulate Toffoli decompositions and circuit? (y/n): ").lower()
                if user_input in ["y", "yes"]:
                    self._simulate = True
                    break
                elif user_input in ["n", "no"]:
                    self._simulate = False
                    break
                else:
                    print("Invalid input. Please enter 'y' or 'n'.")

            while True:
                var = input("(p) print or (d) display or (h) hide circuits: ").lower()
                if var == "p":
                    self._print_circuit = "Print"
                    break
                elif var == "d":
                    self._print_circuit = "Display"
                    break
                elif var == "h":
                    self._print_circuit = "Hide"
                    break
                else:
                    print("Invalid input. Please enter 'p', 'd', or 'h'.")

            if self._simulate:
                while True:
                    user_input = input("Print the full simulation result (f) or just the dot (d) or hide (h)? ").lower()
                    if user_input == "f":
                        self._print_sim = "Full"
                        break
                    elif user_input == "d":
                        self._print_sim = "Dot"
                        break
                    elif user_input == "h":
                        self._print_sim = "Hide"
                        break
                    else:
                        print("Invalid input. Please enter 'f', 'd', or 'h'.")

            self._start_range_qubits = int(input("Start range of qubits: "))
            while self._start_range_qubits < 2:
                colpr("r", msg0, end="\n\n")
                self._start_range_qubits = int(input("Start range of qubits: "))

            self._end_range_qubits = int(input("End range of qubits: "))
            while self._end_range_qubits < self._start_range_qubits:
                colpr("r", msg1, end="\n\n")
                self._end_range_qubits = int(input("End range of qubits: "))

            if self._simulate:            
                while True:
                    user_input = input("Simulate specific measurement for specific qubits wires? (y/n): ").lower()
                    if user_input in ["y", "yes"]:
                        while self._specific_simulation not in ['a', 'b', 'm', "ab", "bm", "abm", "t"]:
                            self._specific_simulation = input("Choose specific qubits wires (a, b, m, ab, bm, abm, abmt, t): ").lower()
                        break
                    elif user_input in ["n", "no"]:
                        break
                    else:
                        print("Invalid input. Please enter 'y' or 'n'.")

    #######################################
    # decomposition methods
    #######################################

    def __bb_decompose(
            self,
            toffoli_decomp_type: Union['list[ToffoliDecompType]', ToffoliDecompType],
            parallel_toffolis: bool,
            mirror_method: MirrorMethod = MirrorMethod.NO_MIRROR
    ) -> bb.BucketBrigadeDecompType:
        """
        Decomposes the Toffoli gates in the bucket brigade circuit.

        Args:
            toffoli_decomp_type (Union['list[ToffoliDecompType]', ToffoliDecompType]): The type of Toffoli decomposition.
            parallel_toffolis (bool): Flag indicating whether to use parallel toffolis.
            mirror_method (bool): Flag indicating whether to mirror the input to the output.

        Returns:
            bb.BucketBrigadeDecompType: The decomposition scenario for the bucket brigade.
        """

        if isinstance(toffoli_decomp_type, list):
            return bb.BucketBrigadeDecompType(
                toffoli_decomp_types=[
                    toffoli_decomp_type[0],    # fan_in_decomp
                    toffoli_decomp_type[1],    # mem_decomp
                    toffoli_decomp_type[2]     # fan_out_decomp
                ],
                parallel_toffolis=parallel_toffolis,
                mirror_method=mirror_method
            )
        else:
            return bb.BucketBrigadeDecompType(
                toffoli_decomp_types=[
                    toffoli_decomp_type,    # fan_in_decomp
                    toffoli_decomp_type,    # mem_decomp
                    toffoli_decomp_type     # fan_out_decomp
                ],
                parallel_toffolis=parallel_toffolis,
                mirror_method=mirror_method
            )

    def bb_decompose_test(
            self,
            dec: Union['list[ToffoliDecompType]', ToffoliDecompType],
            parallel_toffolis: bool,

            dec_mod: Union['list[ToffoliDecompType]', ToffoliDecompType],
            parallel_toffolis_mod: bool,
            mirror_method: MirrorMethod = MirrorMethod.NO_MIRROR
    ) -> None:
        """
        Tests the bucket brigade circuit with different decomposition scenarios.

        Args:
            dec (Union['list[ToffoliDecompType]', ToffoliDecompType]): The decomposition scenario for the bucket brigade.
            parallel_toffolis (bool): Flag indicating whether to use parallel toffolis for the bucket brigade.
            dec_mod (Union['list[ToffoliDecompType]', ToffoliDecompType]): The modified decomposition scenario for the bucket brigade.
            parallel_toffolis_mod (bool): Flag indicating whether to use parallel toffolis for the modified bucket brigade.
            mirror_method (bool): Flag indicating whether to mirror the input to the output.

        Returns:
            None
        """

        # ===============REFERENCE==============

        self._decomp_scenario = self.__bb_decompose(
            dec, 
            parallel_toffolis, 
            mirror_method
        )

        # ================MODDED================

        self._decomp_scenario_modded = self.__bb_decompose(
            dec_mod, 
            parallel_toffolis_mod,
            mirror_method
        )

        self._run()

    #######################################
    # core functions
    #######################################

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
            self._core(i, "results")

        # This is for final bilan from 2 qubits to 8 qubits
        self._start_range_qubits = 2
        self._end_range_qubits = 7

        # Reset data for multiple tests on series
        self._data = multiprocessing.Manager().dict()
        self._data_modded = multiprocessing.Manager().dict()

        stop_event = threading.Event()
        loading_thread = threading.Thread(target=loading_animation, args=(stop_event, 'bilan',))
        loading_thread.start()

        try:
            for i in range(self._start_range_qubits, self._end_range_qubits + 1):
                self._core(i, state="bilan")
        finally:
            stop_event.set()
            loading_thread.join()

        self.__print_bilan()

    def _core(self, nr_qubits: int, state: str) -> None:
        """
        Core function of the experiment.
        """

        qubits: 'list[cirq.NamedQubit]' = []

        qubits.clear()
        for i in range(nr_qubits):
            qubits.append(cirq.NamedQubit("a" + str(i)))

        # prevent from simulate the circuit if the number of qubits is greater than 4
        if nr_qubits > 4:
            self._simulate = False

        self._start_time = time.time()

        # Use multiprocessing.Pool to parallelize the construction
        with multiprocessing.Pool(processes=2) as pool:
            results = pool.starmap(bb.BucketBrigade, [
                (qubits, self._decomp_scenario),
                (qubits, self._decomp_scenario_modded)
            ])

        # Retrieve the results
        self._bbcircuit, self._bbcircuit_modded = results

        self._stop_time = elapsed_time(self._start_time)

        if state == "bilan":
            self.__bilan(nr_qubits=nr_qubits)
        elif state == "results":
            self._results()
        else:
            return

    def _results(self) -> None:
        """
        Prints the results of the experiment.
        """

        print(f"{'='*150}\n\n")

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

        print(f"\n\n{'='*150}")

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

    def __bilan(self, nr_qubits: int) -> None:
        """
        Collect the bilan of the experiment
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
                hadamard_count
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
            vms
        ]

    def __print_bilan(self) -> None:
        """
        Prints the bilan of the experiment.
        """

        colpr("y", "\n\nBilan of the experiment:", end="\n\n")

        # Bilan of essential checks
        colpr("b", "Creation of the Bucket Brigade Circuits:", end="\n\n")
        table = "| Qubits Range     | Elapsed Time               | RSS (Memory Usage)     | VMS (Memory Usage)     |\n"
        table += "|------------------|----------------------------|------------------------|------------------------|\n"

        for x in range(self._start_range_qubits, self._end_range_qubits + 1):
            table += f"| {self._data_modded[x][0]:<16} | {self._data_modded[x][6]:<26} | {self._data_modded[x][7]:<22} | {self._data_modded[x][8]:<22} |\n"

        print(table, end="\n\n")

        # Bilan of simulation circuit
        if self._simulate:
            colpr('b', "Simulation circuit result: ", end="\n\n")

            colpr("r", "\t• Failed: ", str(self._simulation_bilan[0]), "%")
            if str(self._simulation_bilan[4]) == 0:
                colpr("g", "\t• Succeed: ", str(self._simulation_bilan[1]), "%", end="\n\n")
            else:
                colpr("y", "\t• Succeed: ", str(self._simulation_bilan[1]), "%", end="\t( ")
                colpr("b", "Measurements: ", str(self._simulation_bilan[2]), "%", end=" • ")
                colpr("g", "Output vector: ", str(self._simulation_bilan[3]), "%", end=" )\n\n")

        # Bilan of the reference circuit
        if self._decomp_scenario.dec_fan_in != ToffoliDecompType.NO_DECOMP:
            colpr("b", "Reference circuit bilan:", end="\n\n")

            table = "| Qubits Range     | Number of Qubits | Depth of the Circuit | T Depth          | T Count          | Hadamard Count    |\n"
            table += "|------------------|------------------|----------------------|------------------|------------------|-------------------|\n"

            for x in range(self._start_range_qubits, self._end_range_qubits + 1):
                table += f"| {self._data[x][0]:<16} | {self._data[x][1]:<16} | {self._data[x][2]:<20} | {self._data[x][3]:<16} | {self._data[x][4]:<16} | {self._data[x][5]:<17} |\n"

            print(table, end="\n\n")

        # Bilan of the modded circuit
        colpr("b", "Modded circuit bilan:", end="\n\n")
        table = "| Qubits Range     | Number of Qubits | Depth of the Circuit | T Depth          | T Count          | Hadamard Count    |\n"
        table += "|------------------|------------------|----------------------|------------------|------------------|-------------------|\n"

        for x in range(self._start_range_qubits, self._end_range_qubits + 1):
            table += f"| {self._data_modded[x][0]:<16} | {self._data_modded[x][1]:<16} | {self._data_modded[x][2]:<20} | {self._data_modded[x][3]:<16} | {self._data_modded[x][4]:<16} | {self._data_modded[x][5]:<17} |\n"

        print(table, end="\n\n")

        # Comparing bilans
        if self._decomp_scenario.dec_fan_in != ToffoliDecompType.NO_DECOMP:

            def calculate(i: int, j: int) -> 'tuple[str, str]':
                modded_percent = format(((self._data_modded[i][j] / self._data[i][j]) * 100), ',.2f')
                modded = str(self._data_modded[i][j]) + f"  ( {modded_percent} )"
                cancelled_percent = format((100 - eval(modded_percent)), ',.2f')
                cancelled = str(self._data[i][j] - self._data_modded[i][j]) + f"  ( {cancelled_percent} )"

                return modded, cancelled

            colpr("y", "Comparing bilans", end="\n\n")

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

        self._simulation_bilan = self._Simulator.get_simulation_bilan()


#######################################
# QRAM Circuit Stress
#######################################

class QRAMCircuitStress(QRAMCircuitExperiments):

    _stress_bilan: 'dict[str, list]' = {}

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

        # self._stress(1)
        self._stress(2)

    def _stress(self, num_loops: int) -> None:
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
            self._stress_bilan[" | ".join(map(str, indices))] = self._simulation_bilan

        bbcircuit_save = copy.deepcopy(self._bbcircuit)
        bbcircuit_modded_save = copy.deepcopy(self._bbcircuit_modded)

        t_count = count_t_of_circuit(bbcircuit_modded_save.circuit)
        # t_count = 2

        for indices in itertools.product(range(1, t_count + 1), repeat=num_loops):
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

        # export in file
        len_bilan = len(self._stress_bilan)
        time_stamp = time.strftime("%Y%m%d-%H%M%S")
        with open(f"stress_bilan_{len_bilan}_{time_stamp}.txt", "w") as file:
            file.write(table)

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


#######################################
# main function
#######################################

def main():
    """
    Main function of the experiments.
    """

    # QRAMCircuitExperiments().bb_decompose_test(
    #     dec=ToffoliDecompType.NO_DECOMP,
    #     parallel_toffolis=False,

    #     dec_mod=[
    #         ToffoliDecompType.RELATIVE_PHASE_TD_4_CX_3,
    #         ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
    #         ToffoliDecompType.RELATIVE_PHASE_TD_4_CX_3,
    #     ],
    #     parallel_toffolis_mod=True,
    #     mirror_method=MirrorMethod.OUT_TO_IN
    # )

    QRAMCircuitExperiments().bb_decompose_test(
        dec=[
            ToffoliDecompType.RELATIVE_PHASE_TD_4_CX_3,
            ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
            ToffoliDecompType.RELATIVE_PHASE_TD_4_CX_3,
        ],
        parallel_toffolis=True,

        dec_mod=[
            ToffoliDecompType.RELATIVE_PHASE_TD_4_CX_3,
            ToffoliDecompType.ANCILLA_0_TD4_MOD,
            ToffoliDecompType.RELATIVE_PHASE_TD_4_CX_3,
        ],

        parallel_toffolis_mod=True,
        mirror_method=MirrorMethod.OUT_TO_IN
    )

    # QRAMCircuitStress().bb_decompose_test(
    #     dec=ToffoliDecompType.NO_DECOMP,
    #     parallel_toffolis=False,

    #     dec_mod=[
    #         ToffoliDecompType.RELATIVE_PHASE_TD_4_CX_3,
    #         ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
    #         ToffoliDecompType.RELATIVE_PHASE_TD_4_CX_3,
    #     ],

    #     parallel_toffolis_mod=True,
    #     mirror_method=MirrorMethod.OUT_TO_IN
    # )

    # QRAMCircuitStress().bb_decompose_test(
    #     dec=ToffoliDecompType.NO_DECOMP,
    #     parallel_toffolis=False,

    #     dec_mod=[
    #         ToffoliDecompType.RELATIVE_PHASE_TD_4_CX_3,
    #         ToffoliDecompType.ANCILLA_0_TD4_MOD,
    #         ToffoliDecompType.RELATIVE_PHASE_TD_4_CX_3,
    #     ],

    #     parallel_toffolis_mod=True,
    #     mirror_method=MirrorMethod.OUT_TO_IN
    # )

if __name__ == "__main__":
    main()
