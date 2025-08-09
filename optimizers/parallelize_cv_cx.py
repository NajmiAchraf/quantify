from typing import List

import cirq

import utils.clifford_t_utils as ctu
import utils.counting_utils as count
from qramcircuits.toffoli_decomposition import (
    ToffoliDecomposition,
    ToffoliDecompType,
)

from .parallelize_controlled_gates_base import ParallelizeControlledGatesBase


class ParallelizeCVCXToCSCX(ParallelizeControlledGatesBase):

    def __init__(
        self,
        decomposition_type: ToffoliDecompType,
        transfer_flag: bool = False,
    ):
        # Call the super constructor with S gate types
        super().__init__(
            decomposition_type=decomposition_type,
            gate_types={cirq.S, cirq.S**-1},
            transfer_flag=transfer_flag,
        )

    def is_target_gate(self, operation) -> bool:
        """Check if operation is a plain S gate, controlled S gate, or controlled parallel S gate."""
        return ctu.is_plain_s_gate(operation) or ctu.is_controlled_parallel_s(
            operation
        )

    def needs_conversion_to_controlled(self, operation) -> bool:
        """Check if S gate needs conversion to controlled parallel S."""
        # Plain S/S^-1 gates need conversion to controlled operations
        if ctu.is_plain_s_gate(operation):
            return True
        # Controlled S operations that come from change_cnot_to_cs are already in the right format
        # We only need conversion if they have ParallelGate structure that needs flattening
        if isinstance(operation, cirq.ControlledOperation):
            sub_op = operation.sub_operation
            if isinstance(sub_op, cirq.GateOperation):
                # If it's a single S/S^-1 gate on a single qubit, it's already in the right format
                if (
                    sub_op.gate in [cirq.ops.S, cirq.ops.S**-1]
                    and len(sub_op.qubits) == 1
                ):
                    return False
                # Only convert if it's a ParallelGate that needs restructuring
                return isinstance(sub_op.gate, cirq.ParallelGate)
        return False

    @staticmethod
    def parallelize_toffoli_decompositions_CV_CX_QC5(
        circuit: cirq.Circuit, decomposition_type: ToffoliDecompType
    ) -> List[cirq.Moment]:
        """
        Parallelize the Toffoli decompositions using CV_CX_QC5 decomposition type.
        We have 5 moments with Toffoli gates, and we want to parallelize them.
        First moment for each decomposed toffoli contain cnot or cnot ^ 0.5 will neighbor to the first moment of each decomposed toffoli and so on.

        Args:
            circuit: The quantum circuit containing the decomposed Toffoli gates.
            decomposition_type: The CV_CX_QC5 decomposition type to use.
        Returns:
            List of moments with parallelized Toffoli decompositions.
        """
        # Validate decomposition type
        cv_cx_qc5_types = [
            ToffoliDecompType.CV_CX_QC5_0,
            ToffoliDecompType.CV_CX_QC5_1,
            ToffoliDecompType.CV_CX_QC5_2,
            ToffoliDecompType.CV_CX_QC5_3,
            ToffoliDecompType.CV_CX_QC5_4,
            ToffoliDecompType.CV_CX_QC5_5,
            ToffoliDecompType.CV_CX_QC5_6,
            ToffoliDecompType.CV_CX_QC5_7,
        ]

        if decomposition_type not in cv_cx_qc5_types:
            raise ValueError(
                f"Decomposition type {decomposition_type} is not a CV_CX_QC5 type"
            )

        # Get the reference decomposition pattern
        reference_decomp = ToffoliDecomposition(
            decomposition_type=decomposition_type
        ).decomposition()

        if len(reference_decomp) != 5:
            raise ValueError(
                f"Expected 5 stages in CV_CX_QC5 decomposition, got {len(reference_decomp)}"
            )

        # Find all decomposed Toffoli sequences in the circuit
        circuit_moments = list(circuit)
        decomposed_sequences = []

        # Look for sequences that match the 5-stage pattern
        i = 0
        while i <= len(circuit_moments) - 5:
            # Check if the next 5 moments match the reference pattern
            sequence_matches = True
            current_sequence = []

            for stage in range(5):
                circuit_moment = circuit_moments[i + stage]
                reference_moment = reference_decomp[stage]

                # Check if the moment has operations that match the gate type pattern
                stage_ops = []
                ref_gate_type = (
                    reference_moment.operations[0].gate
                    if reference_moment.operations
                    else None
                )

                for op in circuit_moment.operations:
                    if ref_gate_type and op.gate == ref_gate_type:
                        stage_ops.append(op)

                if stage_ops:
                    current_sequence.append(stage_ops)
                else:
                    sequence_matches = False
                    break

            if sequence_matches and len(current_sequence) == 5:
                decomposed_sequences.append(current_sequence)
                i += 5  # Skip the processed sequence
            else:
                i += 1

        # If no decomposed sequences found, return original circuit
        if not decomposed_sequences:
            return list(circuit)

        # Group operations by stage across all sequences
        parallelized_moments = []

        for stage in range(5):
            # Collect all operations for this stage from all sequences
            stage_operations = []
            for sequence in decomposed_sequences:
                if stage < len(sequence):
                    stage_operations.extend(sequence[stage])

            # Use greedy packing similar to ParallelizeCNOTSToLeft
            remaining_ops = stage_operations[:]

            while remaining_ops:
                current_moment_ops = []
                used_qubits = set()
                ops_to_remove = []

                # Try to pack as many compatible operations as possible
                for idx, op in enumerate(remaining_ops):
                    op_qubits = set(op.qubits)

                    # Check if this operation can be added (no qubit conflicts)
                    if not (op_qubits & used_qubits):
                        current_moment_ops.append(op)
                        used_qubits.update(op_qubits)
                        ops_to_remove.append(idx)

                # Remove operations we've added (in reverse order to maintain indices)
                for idx in reversed(ops_to_remove):
                    remaining_ops.pop(idx)

                # Create and add the moment
                if current_moment_ops:
                    parallelized_moments.append(
                        cirq.Moment(current_moment_ops)
                    )

                # Safety check to prevent infinite loops
                if not ops_to_remove and remaining_ops:
                    # If no operations could be packed, add them individually
                    for op in remaining_ops:
                        parallelized_moments.append(cirq.Moment([op]))
                    break

        # Add any remaining moments that weren't part of decomposed sequences
        processed_indices = set()
        for i, sequence in enumerate(decomposed_sequences):
            start_idx = i * 5
            for j in range(5):
                processed_indices.add(start_idx + j)

        for i, moment in enumerate(circuit_moments):
            if i not in processed_indices and moment.operations:
                parallelized_moments.append(moment)

        return parallelized_moments

    def change_cnot_to_cs(self, circuit: cirq.Circuit) -> cirq.Circuit:
        """
        Change (CNOT)^0.5 to Controlled S and (CNOT)^-0.5 to Controlled S^-1 in the circuit.
        """
        new_circuit = cirq.Circuit()

        for moment in circuit:
            new_operations = []
            for op in moment.operations:
                if (
                    op.gate == cirq.ops.CNOT**0.5
                    or op.gate == cirq.ops.CX**0.5
                ):
                    # Replace CNOT^0.5 with Controlled S gate
                    # CNOT^0.5 has control and target qubits, we create CS with same structure
                    control_qubit = op.qubits[0]
                    target_qubit = op.qubits[1]
                    s_gate = cirq.GateOperation(cirq.ops.S, [target_qubit])
                    controlled_s = cirq.ControlledOperation(
                        [control_qubit], s_gate
                    )
                    new_operations.append(controlled_s)
                elif (
                    op.gate == cirq.ops.CNOT**-0.5
                    or op.gate == cirq.ops.CX**-0.5
                ):
                    # Replace CNOT^-0.5 with Controlled S^-1 gate
                    control_qubit = op.qubits[0]
                    target_qubit = op.qubits[1]
                    s_inv_gate = cirq.GateOperation(
                        cirq.ops.S**-1, [target_qubit]
                    )
                    controlled_s_inv = cirq.ControlledOperation(
                        [control_qubit], s_inv_gate
                    )
                    new_operations.append(controlled_s_inv)
                else:
                    # Keep the original operation
                    new_operations.append(op)

            if new_operations:
                new_circuit.append(cirq.Moment(new_operations))

        return new_circuit

    @staticmethod
    def swap_cs_control_gate(circuit: cirq.Circuit) -> cirq.Circuit:
        """
        Swap the control and target qubits of Controlled S gates in the circuit.
        This is useful for certain decomposition scenarios.
        """
        new_circuit = cirq.Circuit()

        for moment in circuit:
            new_operations = []
            for op in moment.operations:
                # Check if this is a ControlledOperation with S or S^-1
                if (
                    isinstance(op, cirq.ControlledOperation)
                    and hasattr(op.sub_operation, "gate")
                    and (
                        op.sub_operation.gate == cirq.ops.S
                        or op.sub_operation.gate == cirq.ops.S**-1
                    )
                ):
                    # Swap control and target qubits
                    old_control = op.controls[0]
                    old_target = op.sub_operation.qubits[0]

                    # Create new operation with swapped qubits
                    new_target_gate = cirq.GateOperation(
                        op.sub_operation.gate, [old_control]
                    )
                    new_controlled_op = cirq.ControlledOperation(
                        [old_target], new_target_gate
                    )
                    new_operations.append(new_controlled_op)
                else:
                    # Keep the original operation
                    new_operations.append(op)

            if new_operations:
                new_circuit.append(cirq.Moment(new_operations))

        return new_circuit

    def optimize_circuit(self, circuit: cirq.Circuit) -> cirq.Circuit:
        """
        Optimize the circuit by parallelizing CV_CX_QC5 Toffoli decompositions.
        This will replace CNOT^0.5 and CNOT^-0.5 with Controlled S and Controlled S^-1 gates.
        """
        # Store the value before optimization starts
        self.const_val = self.invariant_function(circuit)

        # Parallelize the Toffoli decompositions
        circuit = cirq.Circuit(
            self.parallelize_toffoli_decompositions_CV_CX_QC5(
                circuit, self.decomposition_type
            )
        )

        # Change CNOT^0.5 to Controlled S and CNOT^-0.5 to Controlled S^-1
        circuit = self.change_cnot_to_cs(circuit)

        # Swap control and target qubits of Controlled S gates if needed
        circuit = self.swap_cs_control_gate(circuit)

        # Insert Hadamard gates in the first moment and the last moment in target qubit
        if circuit:
            for qubit in circuit.all_qubits():
                if hasattr(qubit, "name") and qubit.name == "target":
                    circuit.insert(0, cirq.H(qubit))
                    circuit.insert(len(circuit), cirq.H(qubit))

        super().optimize_circuit(circuit)
        return circuit
