import cirq

import utils.misc_utils as mu

from .transfer_flag_optimizer import TransferFlagOptimizer


class CancelNghGates(TransferFlagOptimizer):
    """
    This optimizer cancels (H and H) or (T and T^-1) or (S and S^-1) or (Z and Z) gates that are neighbor horizontally on series qubits.

    Cases:
        q0: ───H───H─── =>  q0: ───

        q0: ───T^-1───T─── =>  q0: ───

        q0: ───T───T^-1─── =>  q0: ───

        q0: ───S^-1───S─── =>  q0: ───

        q0: ───S───S^-1─── =>  q0: ───

        q0: ───Z───Z─── =>  q0: ───

    """

    def optimization_at(self, circuit, index, op):

        gates = {
            "H": [cirq.H, cirq.H],
            "T": [cirq.T, cirq.T**-1],
            "S": [cirq.S, cirq.S**-1],
            "Z": [cirq.Z, cirq.Z],
        }

        for gate in gates:

            if not isinstance(op, cirq.GateOperation):
                return None

            if not (op.gate == gates[gate][0] or op.gate == gates[gate][1]):
                continue

            if self.transfer_flag and (not mu.has_flag(op)):
                # Optimize only flagged operations
                return None

            n_idx = circuit.next_moment_operating_on(op.qubits, index + 1)
            if n_idx is None:
                return None

            next_op = circuit.operation_at(op.qubits[0], n_idx)

            if (next_op.gate == gates[gate][0] and op.gate == gates[gate][1]) or (next_op.gate == gates[gate][1] and op.gate == gates[gate][0]):

                if self.transfer_flag and (not mu.has_flag(next_op)):
                    # Optimize only flagged operations
                    return None

                if self.transfer_flag:
                    mu.transfer_flags(circuit, op.qubits[0], index, n_idx)

                return cirq.PointOptimizationSummary(clear_span= n_idx - index + 1,
                                                clear_qubits=op.qubits,
                                                new_operations=[])

        return None
