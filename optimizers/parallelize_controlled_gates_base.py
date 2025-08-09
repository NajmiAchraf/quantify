from typing import List, Set

import cirq

import utils.clifford_t_utils as ctu
import utils.counting_utils as count
import utils.misc_utils as miscutils
from qramcircuits.toffoli_decomposition import (
    ToffoliDecomposition,
    ToffoliDecompType,
)

from .invariant_check_optimizer import InvariantCheckOptimizer


class ParallelizeControlledGatesBase(InvariantCheckOptimizer):

    def __init__(
        self,
        decomposition_type: ToffoliDecompType = None,
        gate_types: Set = None,
        transfer_flag: bool = False,
    ):
        """
        Initialize the optimizer.

        Args:
            decomposition_type: Type of Toffoli decomposition to use (optional)
            gate_types: Set of gate types to operate on (e.g., {cirq.S, cirq.S**-1, cirq.X})
            transfer_flag: Whether to only operate on flagged operations
        """
        super().__init__(count.count_t_of_circuit)
        self.decomposition_type = decomposition_type
        self.gate_types = gate_types or set()
        self.transfer_flag = transfer_flag

    def should_process_operation(self, operation) -> bool:
        """
        Determine if an operation should be processed.
        If transfer_flag is True, only process flagged operations.
        Otherwise, process operations that match our criteria.
        """
        if self.transfer_flag and not miscutils.has_flag(operation):
            return False
        return self.is_target_gate(operation)

    def apply_until_nothing_changes(self, circuit, criteria_to_int):
        """Apply optimization repeatedly until no more changes occur."""
        count2 = -1
        n_count2 = -2
        while count2 != n_count2:
            count2 = n_count2
            super().optimize_circuit(circuit)
            n_count2 = criteria_to_int(circuit)

    def optimize_circuit(self, circuit: cirq.Circuit) -> cirq.Circuit:
        """Main optimization method."""
        # Flag target operations if gate types are specified
        if self.gate_types and not self.transfer_flag:
            miscutils.flag_operations(circuit, self.gate_types)

        # Apply optimization until nothing changes
        self.apply_until_nothing_changes(circuit, count.count_t_of_circuit)

        # Clean all optimization flags
        miscutils.remove_all_flags(circuit)

        return circuit

    def is_target_gate(self, operation) -> bool:
        """Check if operation should be processed. Override in subclasses."""
        if self.gate_types:
            return ctu.is_controlled_parallel_gate(operation, self.gate_types)
        # Default behavior - check for controlled parallel gates
        return ctu.is_controlled_parallel_x(
            operation
        ) or ctu.is_controlled_parallel_s(operation)

    def optimization_at(self, circuit, index, op):
        """Core optimization logic for a single operation."""

        # Check if this operation should be processed
        if not self.should_process_operation(op):
            return None

        # Convert plain gate to controlled operation if needed
        if self.needs_conversion_to_controlled(op):
            op = self.controlled_gate_to_controlled_parallel_gate(
                circuit, index, op
            )

        p_idx_control = index
        prev_op = op
        can_still_search_left = True

        while can_still_search_left:
            # The control wire
            tmp_idx_1 = circuit.prev_moment_operating_on(
                [prev_op.qubits[0]], p_idx_control
            )

            # The target wires
            tmp_idx_2 = -1
            for qub_idx, qub in enumerate(op.qubits[1:], 1):
                tmp_tmp = circuit.prev_moment_operating_on(
                    [qub], p_idx_control
                )
                if tmp_tmp is None:
                    tmp_tmp = -1
                tmp_idx_2 = max(tmp_tmp, tmp_idx_2)

            if tmp_idx_1 is None:
                tmp_idx_1 = -1
            if tmp_idx_2 is None:
                tmp_idx_2 = -1

            can_still_search_left = tmp_idx_2 < tmp_idx_1

            if not can_still_search_left:
                break

            potential_prev_op = circuit.operation_at(
                prev_op.qubits[0], tmp_idx_1
            )

            # Is this an operation we are searching for?
            can_still_search_left = (
                can_still_search_left
                and self.is_target_gate(potential_prev_op)
            )

            # Does it share a control wire?
            if can_still_search_left:
                can_still_search_left = ctu.shares_control_qubit(
                    potential_prev_op, op
                )

            # Check gate type compatibility
            if can_still_search_left:
                can_still_search_left = ctu.are_compatible_operations(
                    op, potential_prev_op
                )

            if can_still_search_left:
                prev_op = potential_prev_op
                p_idx_control = tmp_idx_1

        # If nothing was found...do nothing
        if op == prev_op:
            return None

        current_controlled_op = prev_op
        if self.needs_conversion_to_controlled(prev_op):
            current_controlled_op = (
                self.controlled_gate_to_controlled_parallel_gate(
                    circuit, p_idx_control, prev_op
                )
            )

        # Additional safety check before merging
        if not ctu.are_compatible_operations(op, current_controlled_op):
            print(
                f"WARNING: Trying to merge incompatible operations: {op} and {current_controlled_op}"
            )
            return None

        # Merge the operations
        merged_op = self.merge_controlled_parallel_gate(
            op, current_controlled_op
        )

        # Update the circuit
        self.update_operation(circuit, p_idx_control, prev_op, merged_op)

        # Remove the old operation
        circuit.clear_operations_touching(op.qubits, [index])

        self.check_invariant(circuit)

        # Clean up the circuit
        circuit = cirq.drop_negligible_operations(circuit)
        circuit = cirq.drop_empty_moments(circuit)
        circuit = cirq.Circuit(circuit.all_operations())

    def needs_conversion_to_controlled(self, operation) -> bool:
        """Check if operation needs conversion to controlled form. Override in subclasses."""
        # Enhanced check: only convert gates that match our gate types
        if self.gate_types:
            for gate_type in self.gate_types:
                if ctu.is_plain_gate(operation, gate_type):
                    return True
        return False

    def update_operation(self, circuit, index, old_operation, new_operation):
        circuit.clear_operations_touching(old_operation.qubits, [index])
        circuit.insert(index, new_operation)

    def merge_controlled_parallel_gate(
        self, op1: cirq.ControlledOperation, op2: cirq.ControlledOperation
    ) -> cirq.ControlledOperation:
        """
        Merge two Controlled gate operations into a single Controlled Parallel gate operation.
        Args:
            op1: First Controlled gate operation.
            op2: Second Controlled gate operation.
        Returns:
            A new ControlledOperation with a ParallelGate representing the merged operation.
        """

        # Ensure both operations have the same control qubits
        if (
            (len(op1.controls) != len(op2.controls))
            and (len(op1.controls) != 1)
            and op1.controls[0] != op2.controls[0]
        ):
            raise ValueError(
                "Control qubits must be the same for both operations"
            )

        # Get gate types using utility function
        op1_gate_type = ctu.get_gate_type(op1)
        op2_gate_type = ctu.get_gate_type(op2)

        # Check if both operations are the same type
        if op1_gate_type != op2_gate_type:
            raise ValueError(
                f"Cannot merge Controlled {op1_gate_type} and Controlled {op2_gate_type} operations"
            )

        # Define a recursive function to completely flatten nested qubit structures
        def fully_flatten_qubits(qubits_structure):
            flattened = []
            if isinstance(qubits_structure, (list, tuple)):
                for item in qubits_structure:
                    flattened.extend(fully_flatten_qubits(item))
            else:
                flattened.append(qubits_structure)
            return flattened

        # Extract and fully flatten qubits from both operations
        op1_qubits = fully_flatten_qubits(op1.sub_operation.qubits)
        op2_qubits = fully_flatten_qubits(op2.sub_operation.qubits)

        # Combine the flattened lists
        merged_qubits = op1_qubits + op2_qubits

        # Ensure no duplicates in merged_qubits (optional, if needed)
        merged_qubits = list(dict.fromkeys(merged_qubits))

        # Create a parallel operation by applying the gate to each qubit individually
        parallel_gate = cirq.parallel_gate_op(op1_gate_type, *merged_qubits)

        # Create a ControlledOperation with the ParallelGate
        controlled_parallel_op = cirq.ControlledOperation(
            op1.controls, parallel_gate
        )

        return controlled_parallel_op

    def controlled_gate_to_controlled_parallel_gate(
        self, circuit, index, operation
    ):
        """Convert a plain gate to controlled parallel gate."""
        # Enhanced safety check: Only process gates that match our gate types
        if self.gate_types:
            operation_gate_matches = operation.gate in self.gate_types
            if not operation_gate_matches:
                return operation  # Return unchanged if gate doesn't match our types

        # Additional safety check: Don't process CNOT gates in CV_CX optimizer
        if (
            (operation.gate == cirq.ops.CNOT or operation.gate == cirq.ops.CX)
            and hasattr(self, "gate_types")
            and cirq.X not in self.gate_types
        ):
            return operation  # Return unchanged if this is a CNOT in a non-CNOT optimizer

        if len(operation.qubits) < 2:
            raise ValueError(
                f"Operation {operation} must have at least 2 qubits for conversion"
            )

        p_op = cirq.GateOperation(operation.gate, [operation.qubits[1]])
        current_controlled_op = cirq.ControlledOperation(
            [operation.qubits[0]], p_op
        )

        circuit.clear_operations_touching(operation.qubits, [index])
        circuit.insert(
            index + 1,
            current_controlled_op,
            strategy=cirq.InsertStrategy.INLINE,
        )

        return current_controlled_op
