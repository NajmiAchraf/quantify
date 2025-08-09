from typing import List, Optional, Callable

import cirq

import inspect
from qram.bucket_brigade.base import BucketBrigadeBase
from qram.bucket_brigade.decomp_type import BucketBrigadeDecompType


class BucketBrigadeWrite(BucketBrigadeBase):
    """
    Implements the write phase of bucket brigade QRAM.

    This class constructs the memory write operations.
    """

    def __init__(
        self, qram_bits: int, decomp_scenario: BucketBrigadeDecompType
    ) -> None:
        """Initialize the write phase of bucket brigade QRAM."""
        super().__init__(qram_bits, decomp_scenario)

        self.construct_circuit()

    def wiring_write_memory(self) -> List[cirq.Moment]:
        """
        Write to the memory cells using the ancilla qubits.

        Returns:
            List of circuit moments for memory write operations
        """

        for caller_frame in inspect.stack():
            if "bucket_brigade/main.py" in caller_frame.filename:
                return self._create_memory_operations(
                    all_ancillas=sorted(self.all_ancillas),
                    operation_type="write",
                    control1_getter=lambda i: sorted(self.all_ancillas)[i],
                    target_getter=lambda i: self.memory[i],
                    add_rw_x=True,
                )
            elif (
                "bucket_brigade/hierarchical_network.py"
                in caller_frame.filename
            ) or ("bucket_brigade/hierarchical.py" in caller_frame.filename):
                return self._create_memory_hierarchical_operations(
                    all_ancillas=sorted(self.all_ancillas),
                    operation_type="write",
                    control1_getter=lambda i: sorted(self.all_ancillas)[i],
                    target_getter=lambda i: self.memory[i],
                    add_rw_x=True,
                )

    def construct_circuit(self) -> cirq.Circuit:
        """
        Construct the write circuit memory write.

        Returns:
            Complete write circuit
        """
        self.logger.info(
            f"Constructing write circuit with {self.qram_bits} address bits"
        )

        # Wire up the write memory
        write_memory_moments = self.wiring_write_memory()

        # Decompose the Toffoli gates in the write memory moments
        memory_write_decomposed = self.decompose_parallelize_toffoli(
            write_memory_moments,
            self.decomp_scenario.dec_mem_write,
            [0, 1, 2],
        )

        # Combine into a single circuit
        circuit = cirq.Circuit()
        circuit.append(memory_write_decomposed)

        if self.decomp_scenario.parallel_toffolis:
            circuit = self.stratify(circuit)

        # Construct the qubit order for visualization
        self.construct_qubit_order(circuit)

        self.logger.info(
            f"Write circuit construction complete. "
            f"Total qubits: {len(circuit.all_qubits())}, "
            f"Circuit depth: {len(circuit)}"
        )

        self.circuit = circuit
