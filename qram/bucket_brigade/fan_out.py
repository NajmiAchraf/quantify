from typing import List

import cirq

from qram.bucket_brigade.base import BucketBrigadeBase
from qram.bucket_brigade.decomp_type import BucketBrigadeDecompType


class BucketBrigadeFanOut(BucketBrigadeBase):
    """
    Implements the fan-out phase of bucket brigade QRAM.

    This class constructs the fan-out routing structure.
    """

    def __init__(
        self, qram_bits: int, decomp_scenario: BucketBrigadeDecompType
    ) -> None:
        """Initialize the write phase of bucket brigade QRAM."""
        super().__init__(qram_bits, decomp_scenario)

        self.construct_circuit()

    def construct_fan_out_structure(self) -> cirq.Circuit:
        """
        Construct the fan-out routing structure of the bucket brigade QRAM.

        This creates the binary tree structure that routes the address to the
        appropriate memory cell.

        Returns:
            Circuit containing the fan-out structure
        """
        # Get the pre-created ancilla qubits for the first level
        anc_created = self.all_ancillas[:2]  # First two ancillas (b_0, b_1)

        # Initialize compute fan-out moments with initial CNOT operations
        compute_fan_out_moments = [
            cirq.Moment([cirq.ops.X(anc_created[0])]),
            cirq.Moment([cirq.ops.CNOT(self.address[0], anc_created[1])]),
            cirq.Moment([cirq.ops.CNOT(anc_created[1], anc_created[0])]),
        ]

        # We will need these ancillae for the next level
        anc_previous = anc_created

        # Index to track which ancillas we've used so far
        current_idx = 2

        # Iterate through address bits to create the tree structure
        for i in range(1, self.size_adr_n):
            # Get pre-created ancillas for this level
            anc_created = self.all_ancillas[current_idx : current_idx + 2**i]
            current_idx += 2**i

            # Create Toffoli and CNOT operations for this level
            compute_fan_out_moments.extend(
                self.create_toffoli_and_cnot_moments(
                    anc_previous, anc_created, i
                )
            )

            # Prepare ancillas for the next iteration by combining
            anc_previous = self.combine_ancilla_levels(
                anc_created, anc_previous
            )

        # Final verification
        if len(anc_previous) != 2**self.size_adr_n:
            raise ValueError(
                f"Expected {2**self.size_adr_n} ancilla qubits, but got {len(anc_previous)}"
            )

        return cirq.Circuit(compute_fan_out_moments)

    def create_toffoli_and_cnot_moments(
        self,
        anc_previous: List[cirq.NamedQubit],
        anc_created: List[cirq.NamedQubit],
        i: int,
    ) -> List[cirq.Moment]:
        """
        Create the Toffoli and CNOT operations for a level in the bucket brigade.

        Args:
            anc_previous: Ancilla qubits from the previous level
            anc_created: Newly created ancilla qubits for this level
            i: The current level in the tree (address bit index)

        Returns:
            List of circuit moments containing Toffoli and CNOT gates
        """
        toffoli_moments = []
        cnot_moment_ops = []

        for j in range(2**i):
            # Define the qubits involved in this operation
            ccx_first_control = self.address[i]
            ccx_second_control = anc_previous[j]
            ccx_target = anc_created[j]

            # Add Toffoli gate (CCNOT)
            toffoli_moments.append(
                cirq.Moment(
                    [
                        cirq.TOFFOLI(
                            ccx_first_control, ccx_second_control, ccx_target
                        )
                    ]
                )
            )

            # Prepare CNOT operation to copy the result
            cnot_control = ccx_target
            cnot_target = ccx_second_control
            cnot_moment_ops.append(cirq.ops.CNOT(cnot_control, cnot_target))

        # Add all CNOT operations as a single moment for parallelism
        toffoli_moments.append(cirq.Moment(cnot_moment_ops))

        return toffoli_moments

    @staticmethod
    def combine_ancilla_levels(
        anc_created: List[cirq.NamedQubit], anc_previous: List[cirq.NamedQubit]
    ) -> List[cirq.NamedQubit]:
        """
        Combine two lists of ancilla qubits for the next level of the tree.

        Args:
            anc_created: Newly created ancilla qubits
            anc_previous: Ancilla qubits from the previous level

        Returns:
            List of Combined ancilla qubits
        """
        if len(anc_created) != len(anc_previous):
            raise ValueError(
                f"Cannot Combine lists of different lengths: "
                f"{len(anc_created)} and {len(anc_previous)}"
            )

        Combined_ancillas = []
        for i in range(len(anc_created)):
            Combined_ancillas.append(anc_previous[i])
        for i in range(len(anc_created)):
            Combined_ancillas.append(anc_created[i])
        return Combined_ancillas

    def construct_circuit(self) -> cirq.Circuit:
        """
        Construct the write circuit fan-out.

        Returns:
            Complete write circuit
        """
        self.logger.info(
            f"Constructing write circuit with {self.size_adr_n} address bits"
        )

        # Construct the fan-out structure
        compute_fan_out_moments = self.construct_fan_out_structure()

        # Decompose the Toffoli gates in the fan-out moments
        comp_fan_out = self.decompose_parallelize_toffoli(
            compute_fan_out_moments,
            self.decomp_scenario.dec_fan_out,
            [0, 1, 2],
        )

        # Combine into a single circuit
        circuit = cirq.Circuit()
        circuit.append(comp_fan_out)

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
