import cirq

import utils.clifford_t_utils as ctu
from qram.bucket_brigade.base import BucketBrigadeBase
from qram.bucket_brigade.decomp_type import BucketBrigadeDecompType
from qram.bucket_brigade.fan_out import BucketBrigadeFanOut


class BucketBrigadeFanIn(BucketBrigadeFanOut):
    """
    Implements the reset phase of bucket brigade QRAM.

    This class constructs the uncomputation circuit by reversing the fan-out structure
    from the fan-out phase, effectively cleaning up all ancilla qubits.
    """

    def __init__(
        self, qram_bits: int, decomp_scenario: BucketBrigadeDecompType
    ) -> None:
        """
        Initialize the reset phase of bucket brigade QRAM.

        Args:
            qram_bits: Number of address bits for the QRAM
            decomp_scenario: Decomposition scenario for Toffoli gates
        """
        BucketBrigadeBase.__init__(self, qram_bits, decomp_scenario)

        self.construct_circuit()

    def construct_circuit(self) -> None:
        """
        Construct the reset circuit by reversing the fan-out structure
        with name of fan-in.

        The reset phase uncomputes all ancilla qubits by applying the inverse
        of the fan-out operations from the write phase in reverse order.

        Returns:
            Complete reset circuit
        """
        self.logger.info(
            f"Constructing reset circuit with {self.qram_bits} address bits"
        )

        # Construct the fan-out structure
        compute_fan_out_moments = self.construct_fan_out_structure()

        # Construct the fan-out (uncompute) structure by reversing the fan-in moments
        uncompute_fan_out_moments = ctu.reverse_moments(
            compute_fan_out_moments
        )

        # Decompose the circuits with appropriate decomposition types
        uncomp_fan_out = self.decompose_parallelize_toffoli(
            uncompute_fan_out_moments,
            self.decomp_scenario.dec_fan_in,
            [1, 0, 2],
        )

        # Create the final circuit
        circuit = cirq.Circuit()
        circuit.append(uncomp_fan_out)

        if self.decomp_scenario.parallel_toffolis:
            circuit = self.stratify(circuit)

        # Construct the qubit order for visualization
        self.construct_qubit_order(circuit)

        self.logger.info(
            f"Reset circuit construction complete. "
            f"Total qubits: {len(circuit.all_qubits())}, "
            f"Circuit depth: {len(circuit)}"
        )

        self.circuit = circuit
