import math
import multiprocessing
from functools import partial
from multiprocessing.managers import DictProxy
from typing import List, Literal, Union

import cirq
import numpy as np

import qram.bucket_brigade.main as bb
from qramcircuits.toffoli_decomposition import ToffoliDecompType
from utils.print_utils import colpr, elapsed_time
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
    _bbcircuit_modded: bb.BucketBrigade
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
    ) -> "tuple[int, int, int]":
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
        if self._simulation_kind == "dec":
            # Calculate the index for the decomposed circuit by reversing the binary representation of the index
            j = math.floor(i / step)

        f, sm, sv = self._simulate_and_compare(
            i, j, circuit, circuit_modded, qubit_order, qubit_order_modded
        )

        return f, sm, sv

    def _simulate_and_compare(
        self,
        i: int,
        j: int,
        circuit: cirq.Circuit,
        circuit_modded: cirq.Circuit,
        qubit_order: "list[cirq.NamedQubit]",
        qubit_order_modded: "list[cirq.NamedQubit]",
    ) -> "tuple[int, int, int]":
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
    ) -> "tuple[int, int, int]":
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
            circuit, qubit_order=qubit_order, initial_state=initial_state
        )

        result_modded = self._simulator.simulate(
            circuit_modded,
            qubit_order=qubit_order_modded,
            initial_state=initial_state_modded,
        )

        return self._compare_results(
            i,
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
    ) -> "tuple[int, int, int]":
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
                colpr(color, "•", end="")
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
        result,
        result_modded,
        measurements: Union["dict[str, np.ndarray]", "dict[str, list]"],
        measurements_modded: Union["dict[str, np.ndarray]", "dict[str, list]"],
        final_state_vector: "list[np.ndarray]",
        final_state_vector_modded: "list[np.ndarray]",
    ) -> "tuple[int, int, int]":
        """
        Compares the results of the simulation.

        Args:
            i (int): The index of the simulation.
            result: The result of the circuit.
            result_modded: The result of the modded circuit.
            measurements (Union['dict[str, np.ndarray]', 'dict[str, list]']): The measurements of the circuit.
            measurements_modded (Union['dict[str, np.ndarray]', 'dict[str, list]']): The measurements of the modded circuit.
            final_state_vector (np.ndarray): The final state of the circuit.
            final_state_vector_modded (np.ndarray): The final state of the modded circuit.

        Returns:
            int: The number of failed tests.
            int: The number of measurements tests success.
            int: The number of full tests success.
        """

        fail: int = 0
        success_measurements: int = 0
        success_vector: int = 0

        try:
            if self._qram_bits <= 3 or self._simulation_kind == "dec":
                # Compare rounded final state which is the output vector
                assert np.array_equal(
                    np.array(np.around(final_state_vector)),
                    np.array(np.around(final_state_vector_modded)),
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
                            measurements_modded.get(qubit_str, np.array([])),
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

    def _print_simulation_results(
        self,
        results: "list[tuple[int, int, int]]",
        sim_range: "list[int]",
        step: int,
    ) -> None:
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

        f = format(((fail * 100) / total_tests), ",.2f")
        sm = format(((success_measurements * 100) / total_tests), ",.2f")
        sv = format(((success_vector * 100) / total_tests), ",.2f")
        ts = format(
            (((success_measurements + success_vector) * 100) / total_tests),
            ",.2f",
        )

        self._simulation_assessment = [f, ts, sm, sv]

        if not self._is_stress:
            print("\n\nResults of the simulation:\n")
            colpr("r", f"\t• Failed: {fail} ({f} %)")
            if success_measurements == 0:
                colpr(
                    "g",
                    f"\t• Succeed: {success_measurements + success_vector} ({ts} %)",
                    end="\n\n",
                )
            else:
                colpr(
                    "y",
                    f"\t• Succeed: {success_measurements + success_vector} ({ts} %)",
                    end="\t( ",
                )
                colpr(
                    "b",
                    f"Measurements: {success_measurements} ({sm} %)",
                    end=" • ",
                )
                colpr(
                    "g",
                    f"Output vector: {success_vector} ({sv} %)",
                    end=" )\n\n",
                )

            colpr("w", "Time elapsed on simulation and comparison:", end=" ")
            colpr("r", self._stop_time, end="\n\n")

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

        colpr("c", "Printing the simulation results ...", end="\n\n")

        for i in sim_range:
            j = i
            if self._simulation_kind == "dec":
                j = math.floor(i / step)
            color, result, result_modded = self._simulation_results[i]
            colpr("c", f"Index of array {j} {i}", end="\n")
            colpr("w", f"{name} circuit result: ")
            colpr("w", result)
            colpr(
                "c",
                "Comparing the output vector and measurements of both circuits ...",
                end="\n",
            )
            colpr(color, f"{name_modded} circuit result: ")
            colpr(color, result_modded, end="\n\n")
