import cirq
import cirq.optimizers
import itertools
import math
import numpy as np
import qsimcirq
import sys
import time
from typing import Union

from functools import partial
import multiprocessing
from multiprocessing.managers import DictProxy
import threading

import qramcircuits.bucket_brigade as bb

from qramcircuits.toffoli_decomposition import ToffoliDecompType, ToffoliDecomposition

from utils.counting_utils import *
from utils.print_utils import *
from utils.types import *


#######################################
# QRAM Circuit Simulator
#######################################

class QRAMCircuitSimulator:
    """
    The QRAMCircuitSimulator class to simulate the bucket brigade circuit.

    Attributes:
        __specific_simulation (str): The specific simulation.
        __qubits_number (int): The number of qubits.
        __print_circuit (Literal["Print", "Display", "Hide"]): The print circuit flag.
        __print_sim (Literal["Dot", "Full", "Loading", "Hide"]): Flag indicating whether to print the full simulation result.
        __simulation_kind (Literal["bb", "dec"]): The simulation kind.
        __is_stress (bool): The stress flag.
        __hpc (bool): Flag indicating if high-performance computing is used.

        __lock (multiprocessing.Lock): The multiprocessing lock.

        __simulation_results (Union[DictProxy, dict]): The simulation results.
        __simulation_bilan (list[str]): The simulation bilan.

        __bbcircuit (bb.BucketBrigade): The bucket brigade circuit.
        __bbcircuit_modded (bb.BucketBrigade): The modded circuit.
        __decomp_scenario (bb.BucketBrigadeDecompType): The decomposition scenario.
        __decomp_scenario_modded (bb.BucketBrigadeDecompType): The modded decomposition scenario.
        __simulator (cirq.Simulator): The Cirq simulator.

    Methods:
        get_simulation_bilan(): Returns the simulation bilan.
        __init__(bbcircuit, bbcircuit_modded, specific_simulation, qubits_number, print_circuit, print_sim, hpc):
            Constructor of the CircuitSimulator class.
        _run_simulation(is_stress): Runs the simulation.

        _fan_in_mem_out(decomp_scenario): Returns the fan-in, memory, and fan-out decomposition types.
        _create_decomposition_circuit(decomposition_type): Creates a Toffoli decomposition circuit.
        __decomposed_circuit(decomposition_type): Creates a Toffoli decomposition with measurements circuit.
        __simulate_decompositions(): Simulates the Toffoli decompositions.
        __simulate_decomposition(decomposition_type): Simulates a Toffoli decomposition.

        __simulate_circuit(): Simulates the circuit.
        _simulation_a_qubits(): Simulates the circuit and measure addressing of the a qubits.
        _simulation_b_qubits(): Simulates the circuit and measure uncomputation of FANOUT.
        _simulation_m_qubits(): Simulates the circuit and measure computation of MEM.
        _simulation_ab_qubits(): Simulates the circuit and measure addressing and uncomputation of the a and b qubits.
        _simulation_bm_qubits(): Simulates the circuit and measure computation and uncomputation of the b and m qubits.
        _simulation_abm_qubits(): Simulates the circuit and measure addressing and uncomputation and computation of the a, b, and m qubits.
        _simulation_t_qubits(): Simulates the addressing and uncomputation and computation of the a, b, and m qubits and measure only the target qubit.
        _simulation_full_qubits(): Simulates the circuit and measure all qubits.
        __add_measurements(bbcircuit): Adds measurements to the circuit and returns the initial state.
        __simulation(start, stop, step, message): Simulates the circuit.

        _worker(i, step, circuit, circuit_modded, qubit_order, qubit_order_modded, initial_state, initial_state_modded):
            Worker function for multiprocessing.
        __simulate_and_compare(i, j, circuit, circuit_modded, qubit_order, qubit_order_modded, initial_state, initial_state_modded):
            Simulate and compares the results of the simulation.
        __print_simulation_results(results, start, stop, step): Prints the simulation results.
    """

    __specific_simulation: type_specific_simulation
    __qubits_number: int
    __print_circuit: type_print_circuit
    __print_sim: type_print_sim
    __simulation_kind: type_simulation_kind = "dec"
    __is_stress: bool = False
    __hpc: bool

    __lock = multiprocessing.Lock()

    __simulation_results: Union[DictProxy, dict]
    __simulation_bilan: 'list[str]' = []

    __bbcircuit: bb.BucketBrigade
    __bbcircuit_modded: bb.BucketBrigade
    __decomp_scenario: bb.BucketBrigadeDecompType
    __decomp_scenario_modded: bb.BucketBrigadeDecompType

    def get_simulation_bilan(self) -> 'list[str]':
        """
        Returns the simulation bilan.

        Args:
            None

        Returns:
            'list[str]': The simulation bilan.
        """

        return self.__simulation_bilan

    def __init__(
            self,
            bbcircuit: bb.BucketBrigade,
            bbcircuit_modded: bb.BucketBrigade,
            specific_simulation: str,
            qubits_number: int,
            print_circuit: str,
            print_sim: str,
            hpc: bool
        ) -> None:
        """
        Constructor of the CircuitSimulator class.

        Args:
            bbcircuit (BBCircuit): The bucket brigade circuit.
            bbcircuit_modded (BBCircuit): The modded circuit.
            specific_simulation (str): The specific simulation.
            qubits_number (int): The number of qubits.
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
        self.__qubits_number = qubits_number
        self.__print_circuit = print_circuit
        self.__print_sim = print_sim
        self.__hpc = hpc

    def _run_simulation(self, is_stress: bool = False) -> None:
        """
        Runs the simulation.
        """

        self.__is_stress = is_stress

        if is_stress:
            self.__print_sim = "Hide"
        elif not is_stress and not self.__hpc:
            self.__simulate_decompositions()

        self.__simulate_circuit()

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

        return circuit, qubits

    def __simulate_decompositions(self) -> None:
        """
        Simulates the Toffoli decompositions.
        """

        message =  "<" + "="*20 + " Simulating the circuit ... Comparing the results of the decompositions to the Toffoli gate " + "="*20 + ">\n"
        colpr("y", f"\n{message}", end="\n\n")

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

        circuit, qubits= self.__decomposed_circuit(ToffoliDecompType.NO_DECOMP)
        circuit_modded, qubits_modded = self.__decomposed_circuit(decomposition_type)

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
        printRange(start, stop, step)

        colpr("c", "Simulating the decomposition ... ", str(decomposition_type),  end="\n\n")

        # reset the simulation results ########################################################
        self.__simulation_results = multiprocessing.Manager().dict()

        # use thread to load the simulation ###################################################
        if self.__print_sim == "Loading":
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
                        qubit_order_modded=qubits_modded),
                    range(start, stop, step))
        finally:
            if self.__print_sim == "Loading":
                stop_event.set()
                loading_thread.join()

        self.__print_simulation_results(results, start, stop, step)

    #######################################
    # simulate circuit methods
    #######################################

    def __simulate_circuit(self) -> None:
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
        step = 2 ** ( 2 * ( 2 ** self.__qubits_number ) + 1 )
        stop = step * ( 2 ** self.__qubits_number )
        message =  "<" + "="*20 + " Simulating the circuit ... Checking the addressing of the a qubits " + "="*20 + ">\n"
        self.__simulation(start, stop, step, message)

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
        step = 2 ** ( 2 ** self.__qubits_number + 1 )
        stop = step * ( 2 ** ( 2 ** self.__qubits_number ) )
        message =  "<" + "="*20 + " Simulating the circuit ... Checking the uncomputation of FANOUT ... were the b qubits are returned to their initial state " + "="*20 + ">\n"
        self.__simulation(start, stop, step, message)

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
        stop = step * ( 2 ** ( 2 ** self.__qubits_number ) )
        message =  "<" + "="*20 + " Simulating the circuit ... Checking the computation of MEM ... were the m qubits are getting the result of the computation " + "="*20 + ">\n"
        self.__simulation(start, stop, step, message)

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
        step_b = 2 ** ( 2 ** self.__qubits_number + 1 )

        step_a = 2 ** ( 2 * ( 2 ** self.__qubits_number ) + 1 )
        stop = step_a * ( 2 ** self.__qubits_number )
        message =  "<" + "="*20 + " Simulating the circuit ... Checking the addressing and uncomputation of the a and b qubits " + "="*20 + ">\n"
        self.__simulation(start, stop, step_b, message)

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

        step_b = 2 ** ( 2 ** self.__qubits_number + 1 )
        stop = step_b * ( 2 ** ( 2 ** self.__qubits_number ) )
        message =  "<" + "="*20 + " Simulating the circuit ... Checking the addressing and uncomputation of the b and m qubits " + "="*20 + ">\n"
        self.__simulation(start, stop, step_m, message)

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
        step_a = 2 ** ( 2 * ( 2 ** self.__qubits_number ) + 1 )
        stop = step_a * ( 2 ** self.__qubits_number )
        message =  "<" + "="*20 + " Simulating the circuit ... Checking the addressing and uncomputation of the a, b, and m qubits " + "="*20 + ">\n"
        self.__simulation(start, stop, step_m, message)

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
        step_a = 2 ** ( 2 * ( 2 ** self.__qubits_number ) + 1 )
        stop = step_a * ( 2 ** self.__qubits_number )
        message =  "<" + "="*20 + " Simulating the circuit ... Checking the addressing and uncomputation of the a, b, and m qubits and measure only the target qubit " + "="*20 + ">\n"
        self.__simulation(start, stop, step_m, message)

    def _simulation_at_qubits(self) -> None:
        """
        Simulates the addressing and uncomputation and computation of the a, b, and m qubits and measure only the target qubit.
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
        step = 2 ** ( 2 * ( 2 ** self.__qubits_number ) + 1 )
        stop = step * ( 2 ** self.__qubits_number )
        message =  "<" + "="*20 + " Simulating the circuit ... Checking the addressing of the a qubits and measure only the target qubit " + "="*20 + ">\n"
        self.__simulation(start, stop, step, message)

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
        stop = 2 ** ( 2 * ( 2 ** self.__qubits_number ) + self.__qubits_number + 1 )
        message =  "<" + "="*20 + " Simulating the circuit ... Checking the all qubits " + "="*20 + ">\n"
        self.__simulation(start, stop, 1, message)

    def __add_measurements(self, bbcircuit: bb.BucketBrigade) -> None:
        """
        Adds measurements to the circuit and returns the initial state.

        Args:
            bbcircuit (bb.BucketBrigade): The bucket brigade circuit.
        """

        measurements = []
        for qubit in bbcircuit.qubit_order:
            if self.__specific_simulation == "full":
                measurements.append(cirq.measure(qubit))
            elif self.__specific_simulation == "at":
                if qubit.name.startswith("t"):
                    measurements.append(cirq.measure(qubit))
            else:
                for _name in self.__specific_simulation:
                    if qubit.name.startswith(_name):
                        measurements.append(cirq.measure(qubit))

        bbcircuit.circuit.append(measurements)
        cirq.optimizers.SynchronizeTerminalMeasurements().optimize_circuit(bbcircuit.circuit)

    def __simulation(self, start:int, stop:int, step:int, message:str) -> None:
        """
        Simulates the circuit.

        Args:
            start (int): The start index.
            stop (int): The stop index.
            step (int): The step index.
        """

        self.__start_time = time.time()

        # add measurements to circuits ########################################################

        self.__add_measurements(self.__bbcircuit)

        self.__add_measurements(self.__bbcircuit_modded)

        # prints ##############################################################################

        if not self.__is_stress and not self.__hpc:

            name = "bucket brigade" if self.__decomp_scenario.get_decomp_types()[0] == ToffoliDecompType.NO_DECOMP else "reference"

            colpr("y", '\n', message, end="\n\n")

            printCircuit(self.__print_circuit, self.__bbcircuit.circuit, self.__bbcircuit.qubit_order, name)

            printCircuit(self.__print_circuit, self.__bbcircuit_modded.circuit, self.__bbcircuit_modded.qubit_order, "modded")

            printRange(start, stop, step)

            print(f"Allocated memory for 'stop': {sys.getsizeof(stop)} bytes")
            print(f"Allocated memory for 'step': {sys.getsizeof(step)} bytes")

            colpr("c", f"Simulating both the modded and {name} circuits and comparing their output vector and measurements ...", end="\n\n")

        if self.__hpc and not self.__is_stress:

            self.__hpc_multiprocessing_simulation(start, stop, step)

        elif self.__qubits_number == 2 and not self.__hpc and self.__is_stress:

            self.__non_multiprocessing_simulation(start, stop, step)

        else:

            self.__multiprocessing_simulation(start, stop, step)

    def __hpc_multiprocessing_simulation(self, start:int, stop:int, step:int) -> None:
        """
        Simulates the circuit using multiprocessing and MPI.

        Args:
            start (int): The start index.
            stop (int): The stop index.
            step (int): The step index.
        """

        from mpi4py import MPI

        # Initialize MPI ######################################################################

        comm = MPI.COMM_WORLD
        rank = comm.Get_rank()
        size = comm.Get_size()

        # Prints ##############################################################################

        if rank == 0:
            print(f"{'='*150}\n\n")
    
            name = "bucket brigade" if self.__decomp_scenario.get_decomp_types()[0] == ToffoliDecompType.NO_DECOMP else "reference"

            printRange(start, stop, step)

            colpr("c", f"Simulating both the modded and {name} circuits and comparing their output vector and measurements ...", end="\n\n")

        # Split the total work into chunks based on the number of ranks #######################

        chunk_size_per_rank = stop // size
        if rank < size - 1:
            local_work_range = range(rank * chunk_size_per_rank, (rank + 1) * chunk_size_per_rank, step)
        else:
            local_work_range = range(rank * chunk_size_per_rank, stop, step)

        # wait for all MPI processes to reach this point ######################################

        comm.Barrier()

        # reset the simulation results ########################################################

        self.__simulation_results = {}

        # Use multiprocessing to parallelize the simulation ###################################

        results: 'list[tuple[int, int, int]]' = []
        with multiprocessing.Pool() as pool:
            results = pool.map(
                partial(
                    self._worker,
                    step=step,
                    circuit=self.__bbcircuit.circuit,
                    circuit_modded=self.__bbcircuit_modded.circuit,
                    qubit_order=self.__bbcircuit.qubit_order,
                    qubit_order_modded=self.__bbcircuit_modded.qubit_order),
                local_work_range)

        # Ensure results are serializable #####################################################

        serializable_result = [list(item) for item in results]

        # Gather the results from all MPI processes ###########################################

        all_results = comm.gather(serializable_result, root=0)

        # Combine the results from all MPI processes ##########################################

        if rank == 0:
            root_results = list(itertools.chain(*all_results))

            self.__print_simulation_results(root_results, start, stop, step)

            print(f"{'='*150}\n\n")

    def __multiprocessing_simulation(self, start:int, stop:int, step:int) -> None:
        """
        Simulates the circuit using multiprocessing.

        Args:
            start (int): The start index.
            stop (int): The stop index.
            step (int): The step index.
        """

        # reset the simulation results ########################################################

        self.__simulation_results = multiprocessing.Manager().dict()
        if self.__hpc:
            self.__simulation_results = {}

        # use thread to load the simulation ###################################################

        if self.__print_sim == "Loading":
            stop_event = threading.Event()
            loading_thread = threading.Thread(target=loading_animation, args=(stop_event, 'simulation',))
            loading_thread.start()

        # Use multiprocessing to parallelize the simulation ###################################

        results: 'list[tuple[int, int, int]]' = []

        try:
            with multiprocessing.Pool() as pool:
                results = pool.map(
                    partial(
                        self._worker,
                        step=step,
                        circuit=self.__bbcircuit.circuit,
                        circuit_modded=self.__bbcircuit_modded.circuit,
                        qubit_order=self.__bbcircuit.qubit_order,
                        qubit_order_modded=self.__bbcircuit_modded.qubit_order),
                    range(start, stop, step))
        finally:
            if self.__print_sim == "Loading":
                stop_event.set()
                loading_thread.join()

        self.__print_simulation_results(results, start, stop, step)

    def __non_multiprocessing_simulation(self, start:int, stop:int, step:int) -> None:
        """
        Simulates the circuit without using multiprocessing.

        Args:
            start (int): The start index.
            stop (int): The stop index.
            step (int): The step index.
        """

        # reset the simulation results ########################################################

        self.__simulation_results = {}

        # simulation is not parallelized ######################################################

        results: 'list[tuple[int, int, int]]' = []

        for i in range(start, stop, step):
            results.append(self._worker(
                    i=i,
                    step=step,
                    circuit=self.__bbcircuit.circuit,
                    circuit_modded=self.__bbcircuit_modded.circuit,
                    qubit_order=self.__bbcircuit.qubit_order,
                    qubit_order_modded=self.__bbcircuit_modded.qubit_order))

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

        Returns:
            tuple[int, int, int]: The number of failed tests and the number of measurements and full tests success.
        """

        j = i
        if self.__simulation_kind == 'dec':
            j = math.floor(i/step) # reverse the 2 ** nbr_anc binary number


        f, sm, sv = self.__simulate_and_compare(
            i,
            j,
            circuit,
            circuit_modded,
            qubit_order,
            qubit_order_modded
        )

        return f, sm, sv

    def __simulate_and_compare(
            self,
            i: int,
            j: int,
            circuit: cirq.Circuit,
            circuit_modded: cirq.Circuit,
            qubit_order: 'list[cirq.NamedQubit]',
            qubit_order_modded: 'list[cirq.NamedQubit]',
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

        Returns:
            int: The number of failed tests.
            int: The number of measurements tests success.
            int: The number of full tests success.
        """

        fail: int = 0
        success_measurements: int = 0
        success_vector: int = 0

        initial_state: int = j
        initial_state_modded: int = i

        if self.__qubits_number <= 3 or self.__simulation_kind == 'dec':
            simulator: cirq.Simulator = cirq.Simulator()
        else:
            simulator: qsimcirq.QSimSimulator = qsimcirq.QSimSimulator()

        try:
            result = simulator.simulate(
                circuit,
                qubit_order=qubit_order,
                initial_state=initial_state
            )

            result_modded = simulator.simulate(
                circuit_modded,
                qubit_order=qubit_order_modded,
                initial_state=initial_state_modded
            )
        except ValueError:
            print(
            """
    An error occurred during the simulation.
    Only on 4 qubits or less, the QSimSimulator can be used.
    Please ensure that the following code is added to the qsim_circuit.py file:

    def _cirq_gate_kind(gate):
        ...
        ...
        ...

        if isinstance(gate, cirq.ops.ControlledGate):
            # Handle ControlledGate by returning the kind of the sub-gate
            sub_gate_kind = _cirq_gate_kind(gate.sub_gate)
            if sub_gate_kind is not None:
                return sub_gate_kind
            raise ValueError(f'Unrecognized controlled gate: {gate}')
        ...
        ...
    """
            )
            return fail, success_measurements, success_vector

        # Extract specific measurements
        measurements = result.measurements
        measurements_modded = result_modded.measurements

        try:
            if self.__qubits_number <= 3  or self.__simulation_kind == 'dec':
                # Compare final state which is the output vector, only for all qubits
                assert np.array_equal(
                    np.array(np.around(result.final_state[j])),
                    np.array(np.around(result_modded.final_state[i]))
                )
            else:
                raise AssertionError
        except AssertionError:
            try:
                # Compare specific measurements for the specific qubits
                for o_qubit in self.__bbcircuit.qubit_order:
                    qubit_str = str(o_qubit)
                    if qubit_str in measurements:
                        assert np.array_equal(
                            measurements[qubit_str],
                            measurements_modded.get(qubit_str, np.array([]))
                        )
            except AssertionError:
                fail += 1
                with self.__lock:
                    if self.__print_sim in ["Full", "Dot"]:
                        colpr("r", "•", end="")
                    if self.__print_sim == "Full":
                        self.__simulation_results[i] = ['r', result, result_modded]
            else:
                success_measurements += 1
                with self.__lock:
                    if self.__print_sim in ["Full", "Dot"]:
                        colpr("b", "•", end="")
                    if self.__print_sim == "Full":
                        self.__simulation_results[i] = ['b', result, result_modded]
        else:
            success_vector += 1
            with self.__lock:
                if self.__print_sim in ["Full", "Dot"]:
                    colpr("g", "•", end="")
                if self.__print_sim == "Full":
                    self.__simulation_results[i] = ['g', result, result_modded]

        return fail, success_measurements, success_vector

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

        fail: int = 0
        success_measurements: int = 0
        success_vector: int = 0
        total_tests: int = 0

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

        self.__simulation_bilan = [f, ts, sm, sv]

        if not self.__is_stress:
            print("\n\nResults of the simulation:\n")
            colpr("r", f"\t• Failed: {fail} ({f} %)")
            if success_measurements == 0:
                colpr("g", f"\t• Succeed: {success_measurements + success_vector} ({ts} %)", end="\n\n")
            else:
                colpr("y", f"\t• Succeed: {success_measurements + success_vector} ({ts} %)", end="\t( ")
                colpr("b", f"Measurements: {success_measurements} ({sm} %)", end=" • ")
                colpr("g", f"Output vector: {success_vector} ({sv} %)", end=" )\n\n")

            colpr("w", "Time elapsed on simulation and comparison:", end=" ")
            colpr("r", self.__stop_time, end="\n\n")

        if self.__print_sim != "Full":
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
            color, result, result_modded = self.__simulation_results[i]
            colpr("c", f"Index of array {j} {i}", end="\n")
            colpr("w", f"{name} circuit result: ")
            colpr("w", str(result))
            colpr("c", "Comparing the output vector and measurements of both circuits ...", end="\n")
            colpr(color, f"{name_modded} circuit result: ")
            colpr(color, str(result_modded), end="\n\n")
