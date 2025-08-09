import cirq


def is_t_or_s_gate(cirq_op):
    # simplistic verification of T or S gate. These are not Hermitian.
    # based on the fact that the circuit generators use cirq.T,S
    # whenever a T,S gate is required
    return isinstance(cirq_op, cirq.GateOperation) and cirq_op.gate in [
        cirq.T,
        cirq.T**-1,
        cirq.S,
        cirq.S**-1,
    ]


def reverse_moments(list_of_moments):
    n_moments = []
    for moment in reversed(list_of_moments):
        n_moment = cirq.Moment()
        for op in moment:
            if is_t_or_s_gate(op):
                n_moment = n_moment.with_operation(op**-1)
            else:
                # everything else is Clifford
                # and I assume CNOT, H
                n_moment = n_moment.with_operation(op)

        n_moments.append(n_moment)
    return n_moments


def is_controlled_parallel_gate(operation, gate_types):
    """
    Generalized function to check if operation is a controlled gate of specified types.
    Returns True if the given operation is either:
      - a basic gate from gate_types (like CNOT for X), or
      - a cirq.ControlledOperation whose sub_operation is a GateOperation
        with a cirq.ParallelGate or single gate from gate_types
    """
    if operation is None:
        return False

    # Handle basic gates explicitly (like CNOT for X)
    if hasattr(operation, "gate"):
        if operation.gate == cirq.CNOT and cirq.ops.X in gate_types:
            return True

    # Otherwise, check if this is a ControlledOperation
    if not isinstance(operation, cirq.ControlledOperation):
        return False

    sub_op = operation.sub_operation
    if not isinstance(sub_op, cirq.GateOperation):
        return False

    # Check that the sub gate is a ParallelGate with one of our gate types
    gate = sub_op.gate
    if isinstance(gate, cirq.ParallelGate):
        return gate.sub_gate in gate_types

    # Also check for single gates of the specified types
    return gate in gate_types


def is_controlled_parallel_x(operation):
    """
    Returns True if the given operation is either:
      - a cirq.CNOT, or
      - a cirq.ControlledOperation whose sub_operation is a GateOperation
        with a cirq.ParallelGate(X, n) gate
    """
    return is_controlled_parallel_gate(operation, {cirq.ops.X})


def is_controlled_parallel_s(operation):
    """
    Returns True if the given operation is a cirq.ControlledOperation whose sub_operation is a GateOperation
        with a cirq.ParallelGate(S, n) gate or a single S/S^-1 gate
    """
    return is_controlled_parallel_gate(operation, {cirq.ops.S, cirq.ops.S**-1})


def has_control_qubit(operation, qubit):
    if operation.gate == cirq.ops.CNOT:
        return operation.qubits[0] == qubit
    elif is_controlled_parallel_x(operation):
        return qubit in operation.controls


def is_plain_s_gate(operation):
    """
    Returns True if the operation is a plain S or S^-1 gate (not controlled).
    """
    if operation is None:
        return False
    return isinstance(operation, cirq.GateOperation) and (
        operation.gate == cirq.ops.S or operation.gate == cirq.ops.S**-1
    )


def get_gate_type(operation):
    """
    Extract the base gate type from an operation, handling ParallelGate cases.
    Works for X, S, S^-1, T, T^-1 gates.
    Returns None if not a supported gate type.
    """
    if operation is None:
        return None

    # Handle plain gates (single-qubit operations)
    if isinstance(operation, cirq.GateOperation):
        if operation.gate in [
            cirq.ops.X,
            cirq.ops.S,
            cirq.ops.S**-1,
            cirq.ops.T,
            cirq.ops.T**-1,
        ]:
            return operation.gate

    # Handle controlled operations
    elif isinstance(operation, cirq.ControlledOperation):
        sub_op = operation.sub_operation
        if isinstance(sub_op, cirq.GateOperation):
            gate = sub_op.gate
            if isinstance(gate, cirq.ParallelGate):
                # For parallel gates, return the sub_gate type
                return gate.sub_gate
            else:
                # For single gates, return the gate itself
                return gate

    return None


def are_compatible_s_operations(op1, op2):
    """
    Check if two S-type operations have compatible gate types (both S or both S^-1).
    """
    gate1 = get_gate_type(op1)
    gate2 = get_gate_type(op2)
    return gate1 is not None and gate2 is not None and gate1 == gate2


def are_compatible_operations(op1, op2):
    """
    Check if two operations have compatible gate types (same base gate).
    Works for any gate type supported by get_gate_type.
    """
    gate1 = get_gate_type(op1)
    gate2 = get_gate_type(op2)
    return gate1 is not None and gate2 is not None and gate1 == gate2


def is_plain_gate(operation, gate_type):
    """
    Check if operation is a plain (non-controlled) gate of the specified type.
    """
    if operation is None:
        return False
    return (
        isinstance(operation, cirq.GateOperation)
        and operation.gate == gate_type
    )


def shares_control_qubit(op1, op2):
    """
    Check if two operations share a control qubit.
    Only applies to controlled operations (2+ qubit operations).
    Single-qubit operations (like plain S, T gates) don't have control qubits.
    """

    # Helper function to get control qubits from an operation
    def get_control_qubits(op):
        if isinstance(op, cirq.ControlledOperation):
            return set(op.controls)
        elif hasattr(op, "gate") and op.gate == cirq.ops.CNOT:
            # CNOT has control qubit at index 0
            return {op.qubits[0]}
        else:
            # Single-qubit operations don't have control qubits
            return set()

    controls1 = get_control_qubits(op1)
    controls2 = get_control_qubits(op2)

    # Check if there's any overlap in control qubits
    return bool(controls1 & controls2)
