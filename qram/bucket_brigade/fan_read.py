from typing import Dict, List

import cirq

from qram.bucket_brigade.base import BucketBrigadeBase
from qram.bucket_brigade.decomp_type import BucketBrigadeDecompType


class BucketBrigadeFanRead(BucketBrigadeBase):
    """
    Implements the read phase of bucket brigade QRAM.

    This class constructs the memory read operations and fan-read structure.
    """

    def __init__(
        self, qram_bits: int, decomp_scenario: BucketBrigadeDecompType
    ) -> None:
        """
        Initialize the read phase of bucket brigade QRAM.

        Args:
            qram_bits: Number of address bits for the QRAM
            decomp_scenario: Decomposition scenario for Toffoli gates
        """
        super().__init__(qram_bits, decomp_scenario)

        self.construct_circuit()

    def construct_fan_read_structure(self) -> List[cirq.Moment]:
        """
        Construct the fan-read structure of the bucket brigade QRAM for read phase.

        This structure efficiently routes signals from memory cells back through
        the binary tree network, using parallel controlled-X operations on address
        qubits based on the binary encoding in ancilla qubit names.

        Returns:
            List of circuit moments that form the fan-read structure
        """
        fan_read_moments = []
        # Sort ancillas to ensure deterministic order
        sorted_ancillas = sorted(self.all_ancillas)

        # Dictionary to store operations with same control qubit
        parallel_ops: Dict[cirq.NamedQubit, List[cirq.ops.X]] = {}

        # Skip the first ancilla (b_00...0) as it doesn't need special handling
        for i in range(1, len(sorted_ancillas)):
            routing_ancilla = sorted_ancillas[i]

            # Extract binary pattern from ancilla name (skipping 'b_' prefix)
            # and process it in reverse order to match address qubits
            binary_pattern = routing_ancilla.name[2:][::-1]

            # Find address qubits that need X operations based on binary pattern
            target_address_qubits = [
                self.address[j]
                for j, bit in enumerate(binary_pattern)
                if bit == "1" and j < len(self.address)
            ]

            # Only add to parallel_ops if there are qubits to operate on
            if target_address_qubits:
                parallel_ops[routing_ancilla] = [
                    cirq.ops.X(qubit) for qubit in target_address_qubits
                ]

        # Create parallel controlled operations in a single pass
        for control, x_gates in parallel_ops.items():
            # Create ParallelGate with all X gates for this control
            parallel_x = cirq.ParallelGate(cirq.ops.X, len(x_gates))
            target_qubits = [op.qubits[0] for op in x_gates]

            # Create controlled operation with parallel X gates
            controlled_parallel_x = cirq.ControlledOperation(
                [control], parallel_x(*target_qubits)
            )

            fan_read_moments.append(cirq.Moment([controlled_parallel_x]))

        return cirq.Circuit(fan_read_moments)

    def construct_circuit(self) -> None:
        """
        Construct the read circuit (memory read + fan-read).

        Returns:
            Complete read circuit
        """
        self.logger.info(
            f"Constructing read circuit with {self.qram_bits} address bits"
        )

        # Construct the fan-read structure
        circuit = self.construct_fan_read_structure()

        if self.decomp_scenario.parallel_toffolis:
            circuit = self.stratify(circuit)

        # Construct the qubit order for visualization
        self.construct_qubit_order(circuit)

        self.logger.info(
            f"Read circuit construction complete. "
            f"Total qubits: {len(circuit.all_qubits())}, "
            f"Circuit depth: {len(circuit)}"
        )

        self.circuit = circuit
