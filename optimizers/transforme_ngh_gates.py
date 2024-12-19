from collections import defaultdict
from typing import Dict, Tuple, cast

import cirq
from cirq import ops
from cirq.circuits.circuit import Circuit
from cirq.ops import Qid

import utils.misc_utils as mu

from .transfer_flag_optimizer import TransferFlagOptimizer


class TransformeNghGates(TransferFlagOptimizer):
    """
    This optimizer transforms (T and T) or (T^-1 and T^-1) or (S and S) or (S^-1 and S^-1) gates that are neighbor horizontally on series qubits.

    Cases:
        q0: ───T───T───  =>  q0: ───S───

        q0: ───T^-1───T^-1───  =>  q0: ───S^-1───

        q0: ───S───S───  =>  q0: ───Z───

        q0: ───S^-1───S^-1───  =>  q0: ───Z───

    """

    def optimization_at(self, circuit, index, op):

        gates = {
            "T": cirq.T,
            "T^-1": cirq.T**-1,
            "S": cirq.S,
            "S^-1": cirq.S**-1,
        }

        for gate in gates:

            if not isinstance(op, cirq.GateOperation):
                return None

            if op.gate != gates[gate]:
                continue

            if self.transfer_flag and (not mu.has_flag(op)):
                # Optimize only flagged operations
                return None

            n_idx = circuit.next_moment_operating_on(op.qubits, index + 1)
            if n_idx is None:
                return None

            next_op = circuit.operation_at(op.qubits[0], n_idx)

            if next_op.gate == gates[gate] and op.gate == gates[gate]:

                if self.transfer_flag and (not mu.has_flag(next_op)):
                    # Optimize only flagged operations
                    return None

                if self.transfer_flag:
                    mu.transfer_flags(circuit, op.qubits[0], index, n_idx)

                return cirq.PointOptimizationSummary(
                    clear_span=n_idx - index + 1,
                    clear_qubits=op.qubits,
                    new_operations=[],
                )

        return None

    def optimize_circuit(self, circuit: Circuit):
        frontier: Dict["Qid", int] = defaultdict(lambda: 0)
        i = 0
        while i < len(circuit):  # Note: circuit may mutate as we go.
            for op in circuit[i].operations:
                # Don't touch stuff inserted by previous optimizations.
                if any(frontier[q] > i for q in op.qubits):
                    continue

                # Skip if an optimization removed the circuit underneath us.
                if i >= len(circuit):
                    continue
                # Skip if an optimization removed the op we're considering.
                if op not in circuit[i].operations:
                    continue

                sog = op.gate  # Save original gate

                opt = self.optimization_at(circuit, i, op)
                # Skip if the optimization did nothing.
                if opt is None:
                    continue

                # Clear target area, and insert new operations.
                circuit.clear_operations_touching(
                    opt.clear_qubits, [e for e in range(i, i + opt.clear_span)]
                )

                if sog == cirq.T:
                    circuit.insert(i, cirq.S(op.qubits[0]))
                if sog == cirq.T**-1:
                    circuit.insert(i, cirq.S(op.qubits[0]) ** -1)
                if sog == cirq.S or sog == cirq.S**-1:
                    circuit.insert(i, cirq.Z(op.qubits[0]))

                new_operations = self.post_clean_up(
                    cast(Tuple[ops.Operation], opt.new_operations)
                )
                circuit.insert_at_frontier(new_operations, i, frontier)

            i += 1
