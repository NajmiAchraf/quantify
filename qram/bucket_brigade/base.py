from __future__ import annotations

import logging
from typing import Callable, List, Optional

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
        self.qram_bits: int = qram_bits
        self.decomp_scenario: BucketBrigadeDecompType = decomp_scenario
        self.target: Optional[cirq.NamedQubit] = None
        self.read_write: Optional[cirq.NamedQubit] = None
        self.circuit: Optional[cirq.Circuit] = None

        # Logger initialization
        self.logger = logging.getLogger(__name__)

        # construct the qubits needed for the circuit
        self.construct_qubits()

    @property
    def qubit_order(self) -> List[cirq.NamedQubit]:
        """
        Returns the order of qubits for visualization or simulation.

        Returns:
            List of qubits in a specific order.
        """
        return self._qubit_order.copy()

    def construct_qubits(self) -> None:
        """
        Create all the qubits needed for the circuit: address register,
        memory cells, target qubit, read_write qubit, and ancilla qubits.
        """
        # Create address qubits
        self.address = [
            cirq.NamedQubit(f"a{i}") for i in range(self.qram_bits)
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
        for level in range(1, self.qram_bits):
            level_ancillas = [
                cirq.NamedQubit(self.get_b_ancilla_name(j))
                for j in range(2**level, 2 ** (level + 1))
            ]
            self.all_ancillas.extend(level_ancillas)

        # Create memory qubits - one for each possible address
        self.memory = [
            cirq.NamedQubit(f"m{miscutils.my_bin(i, self.qram_bits)}")
            for i in range(2**self.qram_bits)
        ]

        # Create target qubit
        self.target = cirq.NamedQubit("target")

        # Create read_write qubit only if needed based on the class name
        if any(name in self.__class__.__name__ for name in ["Write", "Read"]):
            self.read_write = cirq.NamedQubit("read_write")
        else:
            self.read_write = None

    def construct_qubit_order(self, circuit: cirq.Circuit) -> None:
        """
        Construct the order of qubits for circuit visualization or execution.

        Args:
            circuit: The complete circuit
        """
        # Clear any previous ordering
        self._qubit_order = []

        # Get only qubits that are actually used in the circuit
        circuit_qubits = circuit.all_qubits()

        # Add address qubits in reverse order (LSB to MSB)
        for qubit in reversed(self.address):
            if qubit in circuit_qubits:
                self._qubit_order.append(qubit)

        # Add ancilla qubits in sorted order (only those used in circuit)
        ancilla_qubits = [
            q for q in sorted(self.all_ancillas) if q in circuit_qubits
        ]
        self._qubit_order.extend(ancilla_qubits)

        # Add memory qubits in reverse order (only those used in circuit)
        memory_qubits = [
            q for q in reversed(self.memory) if q in circuit_qubits
        ]
        self._qubit_order.extend(memory_qubits)

        # Add any Toffoli decomposition ancillas that are present in the circuit
        try:
            toffoli_ancillas = ToffoliDecomposition(None, None).ancilla
            for qubit in toffoli_ancillas:
                if qubit in circuit_qubits and qubit not in self._qubit_order:
                    self._qubit_order.append(qubit)
        except Exception as e:
            # If ToffoliDecomposition fails, just log and continue
            self.logger.debug(f"Could not get Toffoli ancillas: {e}")

        # Add target qubit if used in circuit
        if (
            self.target is not None
            and self.target in circuit_qubits
            and self.target not in self._qubit_order
        ):
            self._qubit_order.append(self.target)

        # Add read_write qubit last, if it exists and is used in circuit
        if (
            self.read_write is not None
            and self.read_write in circuit_qubits
            and self.read_write not in self._qubit_order
        ):
            self._qubit_order.append(self.read_write)

        # Ensure we don't have duplicate qubits
        seen = set()
        unique_order = []
        for qubit in self._qubit_order:
            if qubit not in seen:
                seen.add(qubit)
                unique_order.append(qubit)
        self._qubit_order = unique_order

        self.logger.debug(
            f"Constructed qubit order with {len(self._qubit_order)} qubits"
        )

    def get_b_ancilla_name(self, i: int) -> str:
        """
        Generate a standardized name for bucket brigade ancilla qubits.

        Args:
            i: Ancilla qubit index.

        Returns:
            String representing the ancilla qubit name.
        """
        return f"b_{miscutils.my_bin(i, self.qram_bits)}"

    def _create_memory_operations(
        self,
        all_ancillas: List[cirq.NamedQubit],
        operation_type: str,
        control1_getter: Callable[[int], cirq.NamedQubit],
        control2_getter: Optional[Callable[[int], cirq.NamedQubit]] = None,
        target_getter: Callable[
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

        # Add X gate on read_write qubit if needed and available
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
                # Fall back to using the first address qubit if read_write is not available
                control2 = self.address[0]

            target = target_getter(i)

            # Create and add the Toffoli gate
            mem_toff = cirq.TOFFOLI.on(control1, control2, target)
            memory_operations.append(cirq.Moment([mem_toff]))

        return memory_operations

    def _create_memory_hierarchical_operations(
        self,
        all_ancillas: List[cirq.NamedQubit],
        operation_type: str,
        control1_getter: Callable[[int], cirq.NamedQubit],
        target_getter: Callable[
            [int], cirq.NamedQubit
        ] = lambda i: cirq.NamedQubit(f"m{i}"),
        add_rw_x: bool = False,
    ) -> cirq.CircuitOperation:
        """
        Helper method to create memory operations (write, read, query) with hierarchical control.
        """
        memory_operations = []

        # Sort ancillas to ensure deterministic order
        sorted_ancillas = sorted(all_ancillas)

        # Create CNOT gates for each memory cell
        for i in range(len(self.memory)):
            # Check if we have enough ancilla qubits
            if i >= len(sorted_ancillas):
                raise IndexError(
                    f"Insufficient ancilla qubits for {operation_type} operation: "
                    f"need at least {i+1}, have {len(sorted_ancillas)}"
                )

            # Get control and target qubits
            control1 = control1_getter(i)
            target = target_getter(i)

            # Create and add the CNOT gate
            mem_cnot = cirq.CNOT.on(control1, target)
            memory_operations.append(cirq.Moment([mem_cnot]))

        # Create frozen circuit from the memory operations
        frozen_circuit = cirq.FrozenCircuit(memory_operations)

        circuit_op = cirq.CircuitOperation(
            frozen_circuit, use_repetition_ids=True
        )
        circuit_op = circuit_op.controlled_by(
            self.read_write, control_values=[1]
        )

        # Insert X gate if required outside the frozen circuit operation
        if add_rw_x:
            circuit_op = cirq.Circuit(
                [
                    cirq.Moment([cirq.X.on(self.read_write)]),
                    circuit_op,
                ]
            )

        return cirq.Circuit(circuit_op)

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

        self.optimize_clifford_t_cnot_gates(circuit)

        # Parallelize Toffoli gates if requested
        if self.decomp_scenario.parallel_toffolis:
            circuit = self.parallelize_toffolis(
                cirq.Circuit(circuit.all_operations())
            )
            self.optimize_clifford_t_cnot_gates(circuit)

        return circuit

    def parallelize_toffolis(self, circuit: cirq.Circuit) -> cirq.Circuit:
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

        CV_CX_QC5_N = [
            eval(f"ToffoliDecompType.CV_CX_QC5_{x}") for x in range(0, 8)
        ]

        if self.__class__.__name__ == "BucketBrigadeQuery" and any(
            scenario in {self.decomp_scenario.dec_mem_query}
            for scenario in CV_CX_QC5_N
        ):
            # Special case for CV_CX_QC5 decomposition only on query component
            # Use the specialized CVCX to CSCX optimizer
            # This will handle CVCX gates and parallelize them to the left
            # while converting them to CSCX gates
            circuit: cirq.Circuit = qopt.ParallelizeCVCXToCSCX(
                decomposition_type=self.decomp_scenario.dec_mem_query,
                transfer_flag=False,
            ).optimize_circuit(circuit)
        else:
            # Use our generalized CNOT optimizer on any component
            # This will handle all CNOT and CX gates
            # and parallelize them to the left
            circuit: cirq.Circuit = qopt.ParallelizeCNOTSToLeft(
                transfer_flag=False
            ).optimize_circuit(circuit)

        return BucketBrigadeBase.stratified_circuit(circuit)

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
                    cirq.ops.CNOT,
                    cirq.ops.CNOT**0.5,
                    cirq.ops.CNOT ** (-0.5),
                    cirq.ops.CX,
                    cirq.ops.CX**0.5,
                    cirq.ops.CX ** (-0.5),
                    cirq.ops.CZ,
                ],
            )
            previous_circuit_state = circuit.copy()

            # Cancel adjacent gates that multiply to identity
            qopt.CancelNghGates(transfer_flag=True).optimize_circuit(circuit)

            # Cancel adjacent gates that multiply to identity
            qopt.CancelNghCNOTs(transfer_flag=True).optimize_circuit(circuit)

            # Transform adjacent gates using circuit identities
            qopt.TransformNghGates(transfer_flag=True).optimize_circuit(
                circuit
            )

            # If no changes were made, we've reached a fixed point
            if previous_circuit_state == circuit:
                break

        # Drop the negligible operations and empty moments
        circuit = cirq.drop_negligible_operations(circuit)
        circuit = cirq.drop_empty_moments(circuit)

        # Clean all optimization flags
        miscutils.remove_all_flags(circuit)

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
