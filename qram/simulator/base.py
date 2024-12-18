import cirq
import cirq.optimizers
import math
import numpy as np
from typing import Union

from functools import partial
import multiprocessing
from multiprocessing.managers import DictProxy

import qramcircuits.bucket_brigade as bb

from qramcircuits.toffoli_decomposition import ToffoliDecompType

from utils.print_utils import colpr, elapsed_time
from utils.types import type_specific_simulation, type_print_circuit, type_print_sim, type_simulation_kind


#######################################
# QRAM Simulator Base
#######################################

class QRAMSimulatorBase:
    """
    The QRAMCircuitSimulator class to simulate the bucket brigade circuit.

    Attributes:
        _specific_simulation (str): The specific simulation.
        _qubits_number (int): The number of qubits.
        _print_circuit (Literal["Print", "Display", "Hide"]): The print circuit flag.
        _print_sim (Literal["Dot", "Full", "Loading", "Hide"]): Flag indicating whether to print the full simulation result.
        _simulation_kind (Literal["bb", "dec"]): The simulation kind.
        _is_stress (bool): The stress flag.
        _hpc (bool): Flag indicating if high-performance computing is used.
        _shots (int): The number of shots.

        _lock (multiprocessing.Lock): The multiprocessing lock.

        _simulation_results (Union[DictProxy, dict]): The simulation results.
        _simulation_bilan (list[str]): The simulation bilan.

        _bbcircuit (bb.BucketBrigade): The bucket brigade circuit.
        _bbcircuit_modded (bb.BucketBrigade): The modded circuit.
        _decomp_scenario (bb.BucketBrigadeDecompType): The decomposition scenario.
        _decomp_scenario_modded (bb.BucketBrigadeDecompType): The modded decomposition scenario.
        _simulator (cirq.Simulator): The Cirq simulator.

    Methods:
        get_simulation_bilan(): Returns the simulation bilan.
        __init__(bbcircuit, bbcircuit_modded, specific_simulation, qubits_number, print_circuit, print_sim, hpc):
            Constructor of the CircuitSimulator class.

        _worker(i, step, circuit, circuit_modded, qubit_order, qubit_order_modded, initial_state, initial_state_modded):
            Worker function for multiprocessing.
        _simulate_and_compare(i, j, circuit, circuit_modded, qubit_order, qubit_order_modded, initial_state, initial_state_modded):
            Simulate and compares the results of the simulation.
        _simulate_one_shot(i, j, circuit, circuit_modded, qubit_order, qubit_order_modded, initial_state, initial_state_modded):
            Simulate and compares the results of the simulation.
        _run(x, index, circuit, qubit_order, initial_state): Runs the simulation.
        _simulate_multiple_shots(i, j, circuit, circuit_modded, qubit_order, qubit_order_modded, initial_state, initial_state_modded):
            Simulate and compares the results of the simulation.
        _log_results(i, result, result_modded, color): Logs the results of the simulation.
        _compare_results(i, result, result_modded, measurements, measurements_modded, final_state, final_state_modded):
            Compares the results of the simulation.
        _print_simulation_results(results, start, stop, step): Prints the simulation results.
    """

    _specific_simulation: type_specific_simulation
    _qubits_number: int
    _print_circuit: type_print_circuit
    _print_sim: type_print_sim
    _simulation_kind: type_simulation_kind = "dec"
    _is_stress: bool = False
    _hpc: bool
    _shots: int

    _lock = multiprocessing.Lock()

    _simulation_results: Union[DictProxy, dict]
    _simulation_bilan: 'list[str]' = []

    _bbcircuit: bb.BucketBrigade
    _bbcircuit_modded: bb.BucketBrigade
    _decomp_scenario: bb.BucketBrigadeDecompType
    _decomp_scenario_modded: bb.BucketBrigadeDecompType

    _simulator: cirq.Simulator = cirq.Simulator()

    _start_time: float
    _stop_time: str

    def get_simulation_bilan(self) -> 'list[str]':
        """
        Returns the simulation bilan.

        Args:
            None

        Returns:
            'list[str]': The simulation bilan.
        """

        return self._simulation_bilan

    def __init__(
            self,
            bbcircuit: bb.BucketBrigade,
            bbcircuit_modded: bb.BucketBrigade,
            specific_simulation: type_specific_simulation,
            qubits_number: int,
            print_circuit: type_print_circuit,
            print_sim: type_print_sim,
            hpc: bool,
            shots: int
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

        self._bbcircuit = bbcircuit
        self._bbcircuit_modded = bbcircuit_modded
        self._decomp_scenario = bbcircuit.decomp_scenario
        self._decomp_scenario_modded = bbcircuit_modded.decomp_scenario
        self._specific_simulation = specific_simulation
        self._qubits_number = qubits_number
        self._print_circuit = print_circuit
        self._print_sim = print_sim
        self._hpc = hpc
        self._shots = shots

    #######################################
    # Worker methods
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
        if self._simulation_kind == 'dec':
            j = math.floor(i/step) # Calculate the index for the decomposed circuit by reversing the binary representation of the index

        f, sm, sv = self._simulate_and_compare(
            i,
            j,
            circuit,
            circuit_modded,
            qubit_order,
            qubit_order_modded
        )

        return f, sm, sv

    def _simulate_and_compare(
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

        # Multiple shots simulation used only for the bucket brigade circuit and not for the decomposed circuit
        if self._specific_simulation != "full" and self._simulation_kind == "bb":
            return self._simulate_multiple_shots(
                i,
                j,
                circuit,
                circuit_modded,
                qubit_order,
                qubit_order_modded
            )

        return self._simulate_one_shot(
            i,
            j,
            circuit,
            circuit_modded,
            qubit_order,
            qubit_order_modded
        )

    def _simulate_one_shot(
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

        initial_state: int = j
        initial_state_modded: int = i

        result = self._simulator.simulate(
            circuit,
            qubit_order=qubit_order,
            initial_state=initial_state
        )

        result_modded = self._simulator.simulate(
            circuit_modded,
            qubit_order=qubit_order_modded,
            initial_state=initial_state_modded
        )

        return self._compare_results(
            i,
            result,
            result_modded,
            result.measurements,
            result_modded.measurements,
            result.final_state[j],
            result_modded.final_state[i]
        )

    def _run(self, x, index, circuit, qubit_order, initial_state) -> 'tuple[np.ndarray, dict[str, np.ndarray]]':
        result = self._simulator.simulate(
            circuit,
            qubit_order=qubit_order,
            initial_state=initial_state
        )
        return result.final_state[index], result.measurements

    def _simulate_multiple_shots(
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

        initial_state: int = j
        initial_state_modded: int = i

        measurements: 'dict[str, list]' = {}
        measurements_modded: 'dict[str, list]' = {}

        final_state: 'list[np.ndarray]' = []
        final_state_modded: 'list[np.ndarray]' = []

        with multiprocessing.Pool() as pool:
            results = pool.map(
                partial(
                    self._run,
                    index=j,
                    circuit=circuit,
                    qubit_order=qubit_order,
                    initial_state=initial_state),
                range(self._shots)
            )

        for result in results:
            final_state.append(result[0])
            for key, val in result[1].items():
                measurements.setdefault(key, []).append(val)

        with multiprocessing.Pool() as pool:
            results_modded = pool.map(
                partial(
                    self._run,
                    index=i,
                    circuit=circuit_modded,
                    qubit_order=qubit_order_modded,
                    initial_state=initial_state_modded),
                range(self._shots)
            )

        for result_modded in results_modded:
            final_state_modded.append(result_modded[0])
            for key, val in result_modded[1].items():
                measurements_modded.setdefault(key, []).append(val)

        return self._compare_results(
            i,
            result,
            result_modded,
            measurements,
            measurements_modded,
            final_state,
            final_state_modded
        )

    #######################################
    # Results methods
    #######################################

    def _log_results(self, i: int, result, result_modded, color: str) -> None:
        with self._lock:
            if self._print_sim in ["Full", "Dot"]:
                colpr(color, "•", end="")
            if self._print_sim == "Full":
                self._simulation_results[i] = [color, str(result), str(result_modded)]

    def _compare_results(
            self,
            i: int,
            result,
            result_modded,
            measurements: Union['dict[str, np.ndarray]', 'dict[str, list]'],
            measurements_modded: Union['dict[str, np.ndarray]', 'dict[str, list]'],
            final_state: 'list[np.ndarray]',
            final_state_modded: 'list[np.ndarray]',
        ) -> 'tuple[int, int, int]':
        """
        Compares the results of the simulation.

        Args:
            i (int): The index of the simulation.
            result: The result of the circuit.
            result_modded: The result of the modded circuit.
            measurements (Union['dict[str, np.ndarray]', 'dict[str, list]']): The measurements of the circuit.
            measurements_modded (Union['dict[str, np.ndarray]', 'dict[str, list]']): The measurements of the modded circuit.
            final_state (np.ndarray): The final state of the circuit.
            final_state_modded (np.ndarray): The final state of the modded circuit.
        
        Returns:
            int: The number of failed tests.
            int: The number of measurements tests success.
            int: The number of full tests success.
        """

        fail: int = 0
        success_measurements: int = 0
        success_vector: int = 0

        try:
            if self._qubits_number <= 3  or self._simulation_kind == 'dec':
                if self._specific_simulation == "full":
                    # Compare rounded final state which is the output vector
                    assert np.array_equal(
                        np.array(np.around(final_state)),
                        np.array(np.around(final_state_modded))
                    )
                else:
                    # Compare final state which is the output vector
                    assert np.array_equal(
                        np.array(final_state),
                        np.array(final_state_modded)
                    )
            else:
                raise AssertionError
        except AssertionError:
            try:
                # Compare specific measurements for the specific qubits
                for o_qubit in self._bbcircuit.qubit_order:
                    qubit_str = str(o_qubit)
                    if qubit_str in measurements:
                        assert np.array_equal(
                            measurements[qubit_str],
                            measurements_modded.get(qubit_str, np.array([]))
                        )
            except AssertionError:
                fail += 1
                self._log_results(i, result, result_modded, "r")
            else:
                success_measurements += 1
                self._log_results(i, result, result_modded, "b")
        else:
            success_vector += 1
            self._log_results(i, result, result_modded, "g")

        return fail, success_measurements, success_vector

    def _print_simulation_results(self, results: 'list[tuple[int, int, int]]', sim_range: 'list[int]', step: int) -> None:
        """
        Prints the simulation results.

        Args:
            results (list[tuple[int, int, int]]): The results of the simulation.
            sim_range (list[int]): The range of the simulation.
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

        self._stop_time = elapsed_time(self._start_time)

        f = format(((fail * 100)/total_tests), ',.2f')
        sm = format(((success_measurements * 100)/total_tests), ',.2f')
        sv = format(((success_vector * 100)/total_tests), ',.2f')
        ts = format((((success_measurements + success_vector) * 100)/total_tests), ',.2f')

        self._simulation_bilan = [f, ts, sm, sv]

        if not self._is_stress:
            print("\n\nResults of the simulation:\n")
            colpr("r", f"\t• Failed: {fail} ({f} %)")
            if success_measurements == 0:
                colpr("g", f"\t• Succeed: {success_measurements + success_vector} ({ts} %)", end="\n\n")
            else:
                colpr("y", f"\t• Succeed: {success_measurements + success_vector} ({ts} %)", end="\t( ")
                colpr("b", f"Measurements: {success_measurements} ({sm} %)", end=" • ")
                colpr("g", f"Output vector: {success_vector} ({sv} %)", end=" )\n\n")

            colpr("w", "Time elapsed on simulation and comparison:", end=" ")
            colpr("r", self._stop_time, end="\n\n")

        if self._print_sim != "Full":
            return

        if self._simulation_kind == 'dec':
            name = "Toffoli"
            name_modded = "Decomposed Toffoli"
        else:
            name = "Bucket brigade" if self._decomp_scenario.get_decomp_types()[0] == ToffoliDecompType.NO_DECOMP else "Reference"
            name_modded = "Modded circuit"

        colpr("c", "Printing the simulation results ...", end="\n\n")

        for i in sim_range:
            j = i
            if self._simulation_kind == 'dec':
                j = math.floor(i/step)
            color, result, result_modded = self._simulation_results[i]
            colpr("c", f"Index of array {j} {i}", end="\n")
            colpr("w", f"{name} circuit result: ")
            colpr("w", str(result))
            colpr("c", "Comparing the output vector and measurements of both circuits ...", end="\n")
            colpr(color, f"{name_modded} circuit result: ")
            colpr(color, str(result_modded), end="\n\n")
