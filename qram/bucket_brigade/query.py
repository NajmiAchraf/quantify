from typing import List

import cirq

from qram.bucket_brigade.base import BucketBrigadeBase
from qram.bucket_brigade.decomp_type import BucketBrigadeDecompType


class BucketBrigadeQuery(BucketBrigadeBase):
    """
    Implements the query phase of bucket brigade QRAM.

    This class constructs the memory query operations to copy memory contents to the target qubit.
    """

    def __init__(
        self, qram_bits: int, decomp_scenario: BucketBrigadeDecompType
    ) -> None:
        """
        Initialize the query phase of bucket brigade QRAM.

        Args:
            qram_bits: Number of address bits for the QRAM
            decomp_scenario: Decomposition scenario for Toffoli gates
        """
        super().__init__(qram_bits, decomp_scenario)

        self.construct_circuit()

    def wiring_query_memory(self) -> List[cirq.Moment]:
        """
        Query the memory cells using the routing ancillas.

        Returns:
            List of circuit moments for memory query operations
        """
        return self._create_memory_operations(
            all_ancillas=sorted(self.all_ancillas),  # Use sorted ancillas
            operation_type="query",
            control1_getter=lambda i: sorted(self.all_ancillas)[i],
            control2_getter=lambda i: self.memory[i],
            target_getter=lambda i: self.target,
            add_rw_x=False,
        )

    def construct_circuit(self) -> None:
        """
        Construct the query circuit (memory query operations).

        Returns:
            Complete query circuit
        """
        self.logger.info(
            f"Constructing query circuit with {self.qram_bits} address bits"
        )

        # Wire up the query memory
        query_memory_moments = self.wiring_query_memory()

        # Decompose the circuits with appropriate decomposition types
        memory_query_decomposed = self.decompose_parallelize_toffoli(
            query_memory_moments,
            self.decomp_scenario.dec_mem_query,
            [0, 2, 1],  # Special permutation for query operations
        )

        # Combine into a single circuit
        circuit = cirq.Circuit()
        circuit.append(memory_query_decomposed)

        if self.decomp_scenario.parallel_toffolis:
            circuit = self.stratify(circuit)

        # Construct the qubit order for visualization
        self.construct_qubit_order(circuit)

        self.logger.info(
            f"Query circuit construction complete. "
            f"Total qubits: {len(circuit.all_qubits())}, "
            f"Circuit depth: {len(circuit)}"
        )

        self.circuit = circuit
