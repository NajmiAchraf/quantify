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


def is_controlled_parallel_x(operation):
    """
    Returns True if the given operation is either:
      - a cirq.CNOT, or
      - a cirq.ControlledOperation whose sub_operation is a GateOperation
        with a cirq.ParallelGate(X, n) gate
    """
    if operation is None:
        return False

    # Handle the standard CNOT explicitly
    if operation.gate == cirq.CNOT:
        return True

    # Otherwise, check if this is a ControlledOperation
    if not isinstance(operation, cirq.ControlledOperation):
        return False

    sub_op = operation.sub_operation
    if not isinstance(sub_op, cirq.GateOperation):
        return False

    # Check that the sub gate is a ParallelGate with X
    gate = sub_op.gate
    if isinstance(gate, cirq.ParallelGate) and gate.sub_gate == cirq.X:
        return True

    return True


def has_control_qubit(operation, qubit):
    if operation.gate == cirq.ops.CNOT:
        return operation.qubits[0] == qubit
    elif is_controlled_parallel_x(operation):
        return qubit in operation.controls
