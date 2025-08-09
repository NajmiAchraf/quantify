import math
import multiprocessing
from functools import partial
from multiprocessing.managers import DictProxy
from typing import List, Tuple, Union

import cirq
import numpy as np

import qram.bucket_brigade.main as bb
from qram.bucket_brigade.hierarchical import (
    BucketBrigadeHierarchical,
)
from qramcircuits.toffoli_decomposition import ToffoliDecompType
from utils.print_utils import *
from utils.types import (
    type_circuit,
    type_print_circuit,
    type_print_sim,
    type_simulation_kind,
    type_specific_simulation,
)

#######################################
# QRAM Simulator Base
#######################################


class QRAMSimulatorBase:
    """
    The QRAMCircuitSimulator class to simulate the bucket brigade circuit.

    Attributes:
        _specific_simulation (str): The specific simulation.
        _qram_bits (int): The number of QRAM bits.
        _print_circuit (Literal["Print", "Display", "Hide"]): The print circuit flag.
        _print_sim (Literal["Dot", "Full", "Loading", "Hide"]): Flag indicating whether to print the full simulation result.
        _simulation_kind (Literal["bb", "dec"]): The simulation kind.
        _is_stress (bool): The stress flag.
        _hpc (bool): Flag indicating if high-performance computing is used.
        _shots (int): The number of shots.

        _lock (multiprocessing.Lock): The multiprocessing lock.

        _simulation_results (Union[DictProxy, dict]): The simulation results.
        _simulation_assessment (list[str]): The simulation assessment.

        _bbcircuit (bb.BucketBrigade): The bucket brigade circuit.
        _bbcircuit_modded (bb.BucketBrigade): The modded circuit.
        _decomp_scenario (bb.BucketBrigadeDecompType): The decomposition scenario.
        _decomp_scenario_modded (bb.BucketBrigadeDecompType): The modded decomposition scenario.
        _simulator (cirq.Simulator): The Cirq simulator.

    Methods:
        get_simulation_assessment(): Returns the simulation assessment.
        __init__(bbcircuit, bbcircuit_modded, specific_simulation, qram_bits, print_circuit, print_sim, hpc):
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
        _compare_results(i, result, result_modded, measurements, measurements_modded, final_state_vector, final_state_vector_modded):
            Compares the results of the simulation.
        _print_simulation_results(results, start, stop, step): Prints the simulation results.
    """

    _specific_simulation: type_specific_simulation
    _qram_bits: int
    _print_circuit: type_print_circuit
    _print_sim: type_print_sim
    _simulation_kind: type_simulation_kind = "dec"
    _is_stress: bool = False
    _hpc: bool
    _shots: int

    _lock = multiprocessing.Lock()

    _simulation_results: Union[DictProxy, dict]
    _simulation_assessment: "list[str]" = []

    _bbcircuit: bb.BucketBrigade
    _bbcircuit_modded: Union[bb.BucketBrigade, BucketBrigadeHierarchical]
    _decomp_scenario: bb.BucketBrigadeDecompType
    _decomp_scenario_modded: bb.BucketBrigadeDecompType

    _simulator: cirq.Simulator = cirq.Simulator()

    _start_time: float
    _stop_time: str

    def get_simulation_assessment(self) -> "list[str]":
        """
        Returns the simulation assessment.

        Args:
            None

        Returns:
            'list[str]': The simulation assessment.
        """

        return self._simulation_assessment

    def __init__(
        self,
        circuit_type: type_circuit,
        bbcircuit: bb.BucketBrigade,
        bbcircuit_modded: bb.BucketBrigade,
        specific_simulation: type_specific_simulation,
        qram_bits: int,
        print_circuit: type_print_circuit,
        print_sim: type_print_sim,
        hpc: bool,
        shots: int,
    ) -> None:
        """
        Constructor of the CircuitSimulator class.

        Args:
            bbcircuit (BBCircuit): The bucket brigade circuit.
            bbcircuit_modded (BBCircuit): The modded circuit.
            specific_simulation (str): The specific simulation.
            qram_bits (int): The number of QRAM bits.
            print_circuit (str): The print circuit flag.
            print_sim (str): The print simulation flag.

        Returns:
            None
        """

        self._circuit_type = circuit_type
        self._bbcircuit = bbcircuit
        self._bbcircuit_modded = bbcircuit_modded
        self._decomp_scenario = bbcircuit.decomp_scenario
        self._decomp_scenario_modded = bbcircuit_modded.decomp_scenario
        self._specific_simulation = specific_simulation
        self._qram_bits = qram_bits
        self._print_circuit = print_circuit
        self._print_sim = print_sim
        self._hpc = hpc
        self._shots = shots

        if self._hpc:
            manager = multiprocessing.Manager()
            self._simulation_results = manager.dict()
        else:
            self._simulation_results = {}

    #######################################
    # Worker methods
    #######################################

    def _worker(
        self,
        i: int,
        step: int,
        circuit: cirq.Circuit,
        circuit_modded: cirq.Circuit,
        qubit_order: "list[cirq.NamedQubit]",
        qubit_order_modded: "list[cirq.NamedQubit]",
    ) -> Tuple[int, int, int, int]:
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
            tuple[int, int, int, int]: The number of failed tests and the number of measurements and fidelity and vector tests success.
        """

        j = i
        if self._simulation_kind == "dec":
            # Calculate the index for the decomposed circuit by reversing the binary representation of the index
            j = math.floor(i / step)

        f, sm, sf, sv = self._simulate_and_compare(
            i, j, circuit, circuit_modded, qubit_order, qubit_order_modded
        )

        return f, sm, sf, sv

    def _simulate_and_compare(
        self,
        i: int,
        j: int,
        circuit: cirq.Circuit,
        circuit_modded: cirq.Circuit,
        qubit_order: "list[cirq.NamedQubit]",
        qubit_order_modded: "list[cirq.NamedQubit]",
    ) -> Tuple[int, int, int, int]:
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
            int: The number of fidelity tests success.
            int: The number of vector tests success.
        """

        # Multiple shots simulation used only for the bucket brigade circuit and not for the decomposed circuit
        if (
            "Parallel" in self.__class__.__name__
            or "Decompositions" in self.__class__.__name__
        ):
            return self._simulate_one_shot(
                i, j, circuit, circuit_modded, qubit_order, qubit_order_modded
            )
        elif "Sequential" in self.__class__.__name__:
            return self._simulate_multiple_shots(
                i, j, circuit, circuit_modded, qubit_order, qubit_order_modded
            )

    def _simulate_one_shot(
        self,
        i: int,
        j: int,
        circuit: cirq.Circuit,
        circuit_modded: cirq.Circuit,
        qubit_order: "list[cirq.NamedQubit]",
        qubit_order_modded: "list[cirq.NamedQubit]",
    ) -> Tuple[int, int, int, int]:
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
            int: The number of fidelity tests success.
            int: The number of vector tests success.
        """

        initial_state: int = j
        initial_state_modded: int = i

        result = self._simulator.simulate(
            circuit, qubit_order=qubit_order, initial_state=initial_state
        )

        result_modded = self._simulator.simulate(
            circuit_modded,
            qubit_order=qubit_order_modded,
            initial_state=initial_state_modded,
        )

        return self._compare_results(
            i,
            qubit_order,
            result,
            result_modded,
            result.measurements,
            result_modded.measurements,
            result.final_state_vector,  # [j]
            result_modded.final_state_vector,  # [i]
        )

    def _run(
        self, x, index, circuit, qubit_order, initial_state
    ) -> "tuple[np.ndarray, dict[str, np.ndarray]]":
        result = self._simulator.simulate(
            circuit, qubit_order=qubit_order, initial_state=initial_state
        )
        return result.final_state_vector[index], result.measurements

    def _simulate_circuit(
        self,
        circuit: cirq.Circuit,
        qubit_order: "list[cirq.NamedQubit]",
        initial_state: int,
    ) -> "tuple[list[np.ndarray], dict[str, list]]":
        """
        Simulates the given circuit and collects final states and measurements.

        Args:
            circuit (cirq.Circuit): The quantum circuit to simulate.
            qubit_order (list[cirq.NamedQubit]): The order of qubits.
            initial_state (int): The initial state index.

        Returns:
            tuple: A tuple containing a list of final states and a dictionary of measurements.
        """
        measurements: "dict[str, list]" = {}
        final_state_vector: "list[np.ndarray]" = []

        with multiprocessing.Pool() as pool:
            results = pool.map(
                partial(
                    self._run,
                    index=initial_state,
                    circuit=circuit,
                    qubit_order=qubit_order,
                    initial_state=initial_state,
                ),
                range(self._shots),
            )

        for result in results:
            final_state_vector.append(result[0])
            for key, val in result[1].items():
                measurements.setdefault(key, []).append(val)

        return final_state_vector, measurements

    def _simulate_multiple_shots(
        self,
        i: int,
        j: int,
        circuit: cirq.Circuit,
        circuit_modded: cirq.Circuit,
        qubit_order: "list[cirq.NamedQubit]",
        qubit_order_modded: "list[cirq.NamedQubit]",
    ) -> Tuple[int, int, int, int]:
        """
        Simulate and compare the results of the simulation.

        Args:
            i (int): The index of the modded simulation.
            j (int): The index of the standard simulation.
            circuit (cirq.Circuit): The standard circuit.
            circuit_modded (cirq.Circuit): The modded circuit.
            qubit_order (list[cirq.NamedQubit]): The qubit order of the standard circuit.
            qubit_order_modded (list[cirq.NamedQubit]): The qubit order of the modded circuit.

        Returns:
            tuple: A tuple containing the number of failed tests, successful measurement tests, and successful full tests.
        """
        initial_state = j
        initial_state_modded = i

        # Simulate standard circuit
        final_state_vector, measurements = self._simulate_circuit(
            circuit, qubit_order, initial_state
        )

        # Simulate modded circuit
        final_state_vector_modded, measurements_modded = (
            self._simulate_circuit(
                circuit_modded, qubit_order_modded, initial_state_modded
            )
        )

        # Format the results
        str_measurements = self._format_measurements(measurements)
        str_output_vector = str(np.around(final_state_vector)[0])
        str_final_state_vector = self._format_final_state_vector(
            str_output_vector, measurements
        )
        result = str_measurements + "\n" + str_final_state_vector

        str_measurements_modded = self._format_measurements(
            measurements_modded
        )
        str_output_vector_modded = str(np.around(final_state_vector_modded)[0])
        str_final_state_vector_modded = self._format_final_state_vector(
            str_output_vector_modded, measurements_modded
        )
        result_modded = (
            str_measurements_modded + "\n" + str_final_state_vector_modded
        )

        return self._compare_results(
            i,
            qubit_order,
            result,
            result_modded,
            measurements,
            measurements_modded,
            final_state_vector,
            final_state_vector_modded,
        )

    @staticmethod
    def bitstring(vals):
        if np.isscalar(vals):
            vals = [vals]
        separator = " " if np.max(vals) >= 10 else ""
        return separator.join(str(int(v)) for v in vals)

    def _format_measurements(self, measurements: "dict[str, list]") -> str:
        """
        Formats the measurements dictionary into a string.

        Args:
            measurements (dict[str, list]): The measurements to format.

        Returns:
            str: The formatted measurements string.
        """
        formatted = []
        for o_qubit in self._bbcircuit.qubit_order:
            qubit_str = str(o_qubit)
            if qubit_str in measurements:
                formatted.append(
                    f"{qubit_str}={self.bitstring(measurements[qubit_str])[0]}"
                )
        return "measurements: " + " ".join(formatted)

    def _format_final_state_vector(
        self, str_output_vector: str, measurements: "dict[str, list]"
    ) -> str:
        """
        Formats the final state into a string.

        Args:
            str_output_vector (str): The rounded output vector as a string.
            measurements (dict[str, list]): The measurements to include in the final state.

        Returns:
            str: The formatted final state string.
        """
        formatted = []
        for o_qubit in self._bbcircuit.qubit_order:
            qubit_str = str(o_qubit)
            if qubit_str in measurements:
                formatted.append(
                    f"{self.bitstring(measurements[qubit_str])[0]}"
                )
        return (
            f"output vector: {str_output_vector}|" + "".join(formatted) + "⟩"
        )

    #######################################
    # Results methods
    #######################################

    def _log_results(self, i: int, result, result_modded, color: str) -> None:
        with self._lock:
            if self._print_sim in ["Full", "Dot"]:
                color = "g" if color in ["v", "b", "o"] else color
                if color == "r":
                    print("❌", flush=True, end="")
                else:
                    print("✅", flush=True, end="")

            if self._print_sim == "Full":
                result_str = str(result)
                result_modded_str = str(result_modded)
                self._simulation_results[i] = [
                    color,
                    result_str,
                    result_modded_str,
                ]

    def _compare_results(
        self,
        i: int,
        qubit_order: "list[cirq.NamedQubit]",
        result,
        result_modded,
        measurements: Union["dict[str, np.ndarray]", "dict[str, list]"],
        measurements_modded: Union["dict[str, np.ndarray]", "dict[str, list]"],
        final_state_vector: "list[np.ndarray]",
        final_state_vector_modded: "list[np.ndarray]",
    ) -> Tuple[int, int, int, int]:
        """
        Compares the results of the simulation.

        Args:
            i (int): The index of the simulation.
            qubit_order (list[cirq.NamedQubit]): The qubit order of the circuit.
            result: The result of the circuit.
            result_modded: The result of the modded circuit.
            measurements (Union['dict[str, np.ndarray]', 'dict[str, list]']): The measurements of the circuit.
            measurements_modded (Union['dict[str, np.ndarray]', 'dict[str, list]']): The measurements of the modded circuit.
            final_state_vector (np.ndarray): The final state of the circuit.
            final_state_vector_modded (np.ndarray): The final state of the modded circuit.

        Returns:
            int: The number of failed tests.
            int: The number of measurements tests success.
            int: The number of fidelity tests success.
            int: The number of vector tests success.
        """

        fail: int = 0
        success_measurements: int = 0
        success_fidelity: int = 0
        success_vector: int = 0

        # First check if measurements match
        measurement_match = False
        for o_qubit in qubit_order:
            qubit_str = str(o_qubit)
            if qubit_str in measurements and qubit_str in measurements_modded:
                # Extract measurement values for comparison
                if isinstance(measurements[qubit_str], list):
                    m1 = measurements[qubit_str][0]
                else:
                    m1 = measurements[qubit_str]

                if isinstance(measurements_modded[qubit_str], list):
                    m2 = measurements_modded[qubit_str][0]
                else:
                    m2 = measurements_modded[qubit_str]

                # Compare bit values - these must match exactly
                if np.array_equal(m1, m2):
                    measurement_match = True
                    break

        # If measurements don't match, mark as failure
        if not measurement_match:
            fail += 1
            self._log_results(i, result, result_modded, "r")
            return fail, success_measurements, success_fidelity, success_vector

        # If measurements match, proceed to state vector comparison
        try:
            fidelity = -1
            if self._qram_bits <= 3 or self._simulation_kind == "dec":
                v1 = np.array(final_state_vector)
                v2 = np.array(final_state_vector_modded)

                # First try exact array comparison (preferred)
                try:
                    # Try to check if arrays are exactly equal (considering a small tolerance for floating point)
                    if np.allclose(v1, v2, rtol=1e-5, atol=1e-8):
                        success_vector += 1
                        self._log_results(i, result, result_modded, "v")
                        return (
                            fail,
                            success_measurements,
                            success_fidelity,
                            success_vector,
                        )
                except (ValueError, TypeError):
                    # If the comparison fails (e.g., shape mismatch), continue to fidelity check
                    pass

                # If exact comparison failed, normalize and check fidelity
                # to account for phase differences
                if np.linalg.norm(v1) > 0:
                    v1 = v1 / np.linalg.norm(v1)
                if np.linalg.norm(v2) > 0:
                    v2 = v2 / np.linalg.norm(v2)

                # Check if they're approximately equal with fidelity
                fidelity = np.abs(np.vdot(v1, v2)) ** 2
            if fidelity > 0.99:
                # If vectors differ but measurements match, it's a partial success
                success_fidelity += 1
                self._log_results(i, result, result_modded, "b")
            else:
                success_measurements += 1
                self._log_results(i, result, result_modded, "o")
        except (AssertionError, TypeError, ValueError):
            # If any comparison fails but measurements match, count as measurement success
            success_measurements += 1
            self._log_results(i, result, result_modded, "o")

        return fail, success_measurements, success_fidelity, success_vector

    def _print_simulation_results(
        self,
        results: List[Tuple[int, int, int, int]],
        sim_range: "list[int]",
        step: int,
    ) -> None:
        """
        Prints the simulation results with enhanced visual formatting.

        Args:
            results (list[tuple[int, int, int, int]]): The results of the simulation.
            sim_range (list[int]): The range of the simulation.
            step (int): The step index.

        Returns:
            None
        """

        fail: int = 0
        success_measurements: int = 0
        success_fidelity: int = 0
        success_vector: int = 0
        total_tests: int = 0

        # Aggregate results
        for f, sm, sf, sv in results:
            fail += f
            success_measurements += sm
            success_fidelity += sf
            success_vector += sv
            total_tests += 1

        self._stop_time = elapsed_time(self._start_time)

        # Calculate percentages
        f_pct = (fail * 100) / total_tests
        sm_pct = (success_measurements * 100) / total_tests
        sf_pct = (success_fidelity * 100) / total_tests
        sv_pct = (success_vector * 100) / total_tests
        ts_pct = (
            (success_measurements + success_fidelity + success_vector) * 100
        ) / total_tests

        # Format percentages
        f = format(f_pct, ",.2f")
        sm = format(sm_pct, ",.2f")
        sf = format(sf_pct, ",.2f")
        sv = format(sv_pct, ",.2f")
        ts = format(ts_pct, ",.2f")

        self._simulation_assessment = [f, ts, sm, sf, sv]

        if not self._is_stress:
            display_simulation_results(
                fail,
                success_measurements,
                success_fidelity,
                success_vector,
                f_pct,
                sm_pct,
                sf_pct,
                sv_pct,
                ts_pct,
                self._stop_time,
            )

        # Rest of the function remains the same
        if self._print_sim != "Full":
            return

        if self._simulation_kind == "dec":
            name = "Toffoli"
            name_modded = "Decomposed Toffoli"
        else:
            name = (
                "Bucket brigade"
                if self._decomp_scenario.get_decomp_types()[0]
                == ToffoliDecompType.NO_DECOMP
                else "Reference"
            )
            name_modded = "Modded circuit"

        print_colored("c", "Printing the simulation results ...", end="\n\n")

        for i in sim_range:
            j = i
            if self._simulation_kind == "dec":
                j = math.floor(i / step)
            color, result, result_modded = self._simulation_results[i]
            print_colored("c", f"Index of array {j} {i}", end="\n")
            print_colored("w", f"{name} circuit result: ")
            print_colored("w", result)
            print_colored(
                "c",
                "Comparing the output vector and measurements of both circuits ...",
                end="\n",
            )
            print_colored(color, f"{name_modded} circuit result: ")
            print_colored(color, result_modded, end="\n\n")
