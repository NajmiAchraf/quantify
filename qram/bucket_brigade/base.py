from __future__ import annotations

import logging
from typing import List, Optional

import cirq

import optimizers as qopt
import utils.misc_utils as miscutils
from qram.bucket_brigade.decomp_type import BucketBrigadeDecompType
from qramcircuits.toffoli_decomposition import (
    ToffoliDecomposition,
    ToffoliDecompType,
)
from utils.counting_utils import count_cnot_of_circuit


class BucketBrigadeBase:
    """
    Base class for bucket brigade QRAM implementations providing core functionality.

    This class contains shared methods and properties used by all QRAM circuit types.

    Attributes:
        circuit (cirq.Circuit): The quantum circuit implementing the QRAM.
        address (List[cirq.NamedQubit]): The address register qubits.
        memory (List[cirq.NamedQubit]): The memory register qubits.
        target (cirq.NamedQubit): The target qubit where the memory content is copied.
        size_adr_n (int): The number of address bits.
        decomp_scenario (BucketBrigadeDecompType): The decomposition configuration.
    """

    def __init__(
        self, qram_bits: int, decomp_scenario: BucketBrigadeDecompType
    ) -> None:
        """
        Initialize a BucketBrigade QRAM circuit base class.

        Args:
            qram_bits: The number of address bits for the QRAM.
            decomp_scenario: The decomposition scenario for Toffoli gates.
        """
        self._qubit_order: List[cirq.NamedQubit] = []
        self.address: List[cirq.NamedQubit] = []
        self.all_ancillas: List[cirq.NamedQubit] = []
        self.memory: List[cirq.NamedQubit] = []
        self.size_adr_n: int = qram_bits
        self.decomp_scenario = decomp_scenario
        self.target: Optional[cirq.NamedQubit] = None
        self.read_write: Optional[cirq.NamedQubit] = None
        self.circuit: Optional[cirq.Circuit] = None

        # Logger initialization
        self.logger = logging.getLogger(__name__)

        # construct the qubits needed for the circuit
        self.construct_qubits()

    def construct_qubits(self) -> None:
        """
        Create all the qubits needed for the circuit: address register,
        memory cells, target qubit, read/write qubit, and ancilla qubits.
        """
        # Create address qubits
        self.address = [
            cirq.NamedQubit(f"a{i}") for i in range(self.size_adr_n)
        ]

        # Create all possible ancilla qubits
        # This includes all qubits needed for the bucket brigade architecture
        self.all_ancillas = []

        # First level (2 ancillas: b_0, b_1)
        first_level = [
            cirq.NamedQubit(self.get_b_ancilla_name(i)) for i in range(2)
        ]
        self.all_ancillas.extend(first_level)

        # Remaining levels in the binary tree
        for level in range(1, self.size_adr_n):
            level_ancillas = [
                cirq.NamedQubit(self.get_b_ancilla_name(j))
                for j in range(2**level, 2 ** (level + 1))
            ]
            self.all_ancillas.extend(level_ancillas)

        # Create memory qubits - one for each possible address
        self.memory = [
            cirq.NamedQubit(f"m{miscutils.my_bin(i, self.size_adr_n)}")
            for i in range(2**self.size_adr_n)
        ]

        # Create target qubit
        self.target = cirq.NamedQubit("target")

        # Create read/write qubit only if needed based on the class name
        if any(
            name in self.__class__.__name__
            for name in ["Write", "Read", "FanRead"]
        ):
            self.read_write = cirq.NamedQubit("read/write")
        else:
            self.read_write = None

    @property
    def qubit_order(self) -> List[cirq.NamedQubit]:
        """
        Returns the order of qubits for visualization or simulation.

        Returns:
            List of qubits in a specific order.
        """
        return self._qubit_order

    def get_b_ancilla_name(self, i: int) -> str:
        """
        Generate a standardized name for bucket brigade ancilla qubits.

        Args:
            i: Ancilla qubit index.

        Returns:
            String representing the ancilla qubit name.
        """
        return f"b_{miscutils.my_bin(i, self.size_adr_n)}"

    def _create_memory_operations(
        self,
        all_ancillas: List[cirq.NamedQubit],
        operation_type: str,
        control1_getter: callable[[int], cirq.NamedQubit],
        control2_getter: Optional[callable[[int], cirq.NamedQubit]] = None,
        target_getter: callable[
            [int], cirq.NamedQubit
        ] = lambda i: cirq.NamedQubit(f"m{i}"),
        add_rw_x: bool = False,
    ) -> List[cirq.Moment]:
        """
        Helper method to create memory operations (write, read, query) with Toffoli gates.
        """
        memory_operations = []

        # Sort ancillas to ensure deterministic order
        sorted_ancillas = sorted(all_ancillas)

        # Add X gate on read/write qubit if needed and available
        if add_rw_x and self.read_write is not None:
            memory_operations.append(
                cirq.Moment([cirq.ops.X(self.read_write)])
            )

        # Create Toffoli gates for each memory cell
        for i in range(len(self.memory)):
            # Check if we have enough ancilla qubits
            if i >= len(sorted_ancillas):
                raise IndexError(
                    f"Insufficient ancilla qubits for {operation_type} operation: "
                    f"need at least {i+1}, have {len(sorted_ancillas)}"
                )

            # Get control and target qubits
            control1 = control1_getter(i)
            if control2_getter:
                control2 = control2_getter(i)
            elif self.read_write is not None:
                control2 = self.read_write
            else:
                # Fall back to using the first address qubit if read/write is not available
                control2 = self.address[0]

            target = target_getter(i)

            # Create and add the Toffoli gate
            mem_toff = cirq.TOFFOLI.on(control1, control2, target)
            memory_operations.append(cirq.Moment([mem_toff]))

        return memory_operations

    def decompose_parallelize_toffoli(
        self,
        circuit: cirq.Circuit,
        decomp_scenario: ToffoliDecompType,
        permutation: List[int],
    ) -> cirq.Circuit:
        """
        Decompose Toffoli gates in the circuit and potentially parallelize them.

        Args:
            circuit: Circuit containing Toffoli gates to decompose
            decomp_scenario: The decomposition type to use
            permutation: Permutation of qubit indices for the decomposition

        Returns:
            Circuit with decomposed Toffoli gates
        """
        # If not parallelizing, use standard permutation
        if not self.decomp_scenario.parallel_toffolis:
            permutation = [0, 1, 2]

        # Decompose the Toffoli gates
        circuit = cirq.Circuit(
            ToffoliDecomposition.construct_decomposed_moments(
                circuit, decomp_scenario, permutation
            )
        )

        # Special optimization for memory decomposition with certain scenarios
        if (
            permutation == [0, 2, 1]
            and decomp_scenario == self.decomp_scenario.dec_mem_query
            and decomp_scenario
            in [
                ToffoliDecompType.FOUR_ANCILLA_TDEPTH_1_A,
                ToffoliDecompType.FOUR_ANCILLA_TDEPTH_1_B,
                ToffoliDecompType.AN0_TD4_TC7_CX6,
                ToffoliDecompType.AN0_TD4_TC7_CX6_INV,
                ToffoliDecompType.AN0_TD4_TC6_CX6,
                ToffoliDecompType.AN0_TD4_TC5_CX6,
                ToffoliDecompType.AN0_TD3_TC4_CX6,
                ToffoliDecompType.TD_4_CXD_8,
                ToffoliDecompType.TD_4_CXD_8_INV,
                ToffoliDecompType.TD_5_CXD_6,
                ToffoliDecompType.TD_5_CXD_6_INV,
            ]
        ):
            self.optimize_clifford_t_cnot_gates(circuit)

        # Parallelize Toffoli gates if requested
        if self.decomp_scenario.parallel_toffolis:
            circuit = self.parallelize_toffolis(
                cirq.Circuit(circuit.all_operations())
            )
            self.optimize_clifford_t_cnot_gates(circuit)

        return circuit

    def construct_qubit_order(self, circuit: cirq.Circuit) -> None:
        """
        Construct the order of qubits for circuit visualization or execution.

        Args:
            circuit: The complete circuit
            all_ancillas: All ancilla qubits used in the bucket brigade structure
        """
        # Clear any previous ordering
        self._qubit_order = []

        # Add address qubits in reverse order (LSB to MSB)
        self._qubit_order.extend(self.address[::-1])

        # Add ancilla qubits in sorted order
        self._qubit_order.extend(sorted(self.all_ancillas))

        # Add memory qubits in reverse order
        self._qubit_order.extend(self.memory[::-1])

        # Add any Toffoli decomposition ancillas that are present in the circuit
        all_qubits = circuit.all_qubits()
        toffoli_ancillas = ToffoliDecomposition(None, None).ancilla
        for qubit in toffoli_ancillas:
            if qubit in all_qubits:
                self._qubit_order.append(qubit)

        # Add target qubit
        if self.target is not None:
            self._qubit_order.append(self.target)

        # Add read/write qubit last, if it exists
        if self.read_write is not None:
            self._qubit_order.append(self.read_write)

    @staticmethod
    def optimize_clifford_t_cnot_gates(circuit: cirq.Circuit) -> None:
        """
        Optimize a circuit by cancelling and transforming Clifford+T and CNOT gates.

        Args:
            circuit: The circuit to optimize
        """

        while True:
            # Flag operations for optimization
            miscutils.flag_operations(
                circuit,
                [
                    cirq.ops.H,
                    cirq.ops.T,
                    cirq.ops.T**-1,
                    cirq.ops.S,
                    cirq.ops.S**-1,
                    cirq.ops.Z,
                ],
            )
            previous_circuit_state = circuit.copy()

            # Cancel adjacent gates that multiply to identity
            qopt.CancelNghGates(transfer_flag=True).optimize_circuit(circuit)

            # Transform adjacent gates using circuit identities
            qopt.TransformeNghGates(transfer_flag=True).optimize_circuit(
                circuit
            )

            # If no changes were made, we've reached a fixed point
            if previous_circuit_state == circuit:
                break

        # Optimize CNOT gates
        miscutils.flag_operations(circuit, [cirq.ops.CNOT])
        qopt.CancelNghCNOTs(transfer_flag=True).apply_until_nothing_changes(
            circuit, count_cnot_of_circuit
        )

        # Drop the negligible operations and empty moments
        circuit = cirq.drop_negligible_operations(circuit)
        circuit = cirq.drop_empty_moments(circuit)

        # Clean all optimization flags
        miscutils.remove_all_flags(circuit)

    @staticmethod
    def parallelize_toffolis(circuit: cirq.Circuit) -> cirq.Circuit:
        """
        Parallelize Toffoli gate decompositions to reduce circuit depth.

        Args:
            circuit: Circuit containing decomposed Toffoli gates

        Returns:
            Optimized circuit with parallelized gates
        """
        # The first and last moments typically contain Hadamards
        # Extract the middle part for optimization
        if len(circuit) < 3:
            return circuit  # Not enough moments to optimize

        _circuit_: cirq.Circuit = circuit[1:-1]

        while True:
            previous_circuit_state = _circuit_.copy()

            # Move T gates toward the beginning
            qopt.CommuteTGatesToStart().optimize_circuit(_circuit_)

            # Clean up the circuit
            _circuit_ = cirq.drop_negligible_operations(_circuit_)
            _circuit_ = cirq.drop_empty_moments(_circuit_)

            # Move CNOT gates to the left when possible
            qopt.ParallelizeCNOTSToLeft().optimize_circuit(_circuit_)

            # Repack circuit without stratification
            _circuit_ = cirq.Circuit(_circuit_.all_operations())

            # If no changes were made, we've reached a fixed point
            if previous_circuit_state == _circuit_:
                return BucketBrigadeBase.stratified_circuit(
                    cirq.Circuit(circuit[0] + _circuit_ + circuit[-1])
                )

    @staticmethod
    def stratify(circuit: cirq.Circuit) -> cirq.Circuit:
        """
        Stratify a circuit by gate type to improve parallelism.

        Args:
            circuit: Circuit to stratify

        Returns:
            Stratified circuit
        """
        # Define the gate categories for stratification
        categories = [
            cirq.ops.CNOT,
            cirq.ops.H,
            cirq.ops.CX,
            cirq.ops.T,
            cirq.ops.T**-1,
        ]

        # Use optimizers to stratify the circuit
        return qopt.stratified_circuit(circuit=circuit, categories=categories)

    @staticmethod
    def stratified_circuit(circuit: cirq.Circuit) -> cirq.Circuit:
        """
        Apply repeated stratification until the circuit converges.

        Args:
            circuit: Circuit to optimize and stratify

        Returns:
            Fully optimized and stratified circuit
        """
        while True:
            previous_circuit_state = circuit.copy()

            # Repack all operations without moment structure
            circuit = cirq.Circuit(circuit.all_operations())

            # Clean up the circuit
            circuit = cirq.drop_negligible_operations(circuit)
            circuit = cirq.drop_empty_moments(circuit)

            # Stratify by gate type
            circuit = BucketBrigadeBase.stratify(circuit)

            # If no changes were made, we've reached a fixed point
            if previous_circuit_state == circuit:
                return circuit
