import cirq

from .transfer_flag_optimizer import TransferFlagOptimizer

class CancelNghTp(TransferFlagOptimizer):
    """ TEST NOT OFFICIAL METHOD
    This optimizer cancels T gates that are neighbor vertically on parallel qubits.
    """

    circuit: cirq.Circuit

    def __init__(self, circuit: cirq.Circuit, qubit_order: list):
        self.circuit = circuit
        self.qubit_order = qubit_order
        self.qubit_order_inv = [self.qubit_order[q] for q in range(len(self.qubit_order) - 1, -1, -1)]

    def __str__(self):
        pass

    def __del__(self):
        pass

    def core(self, gate: cirq.Gate, rhythm: int, order: list):
        for mi, moment in enumerate(self.circuit):
            count = 0
            # Sort operations in the moment based on their qubits using self.qubit_order
            sorted_ops = sorted(moment.operations, key=lambda op: order.index(op.qubits[0]))
            print("sorted_ops", sorted_ops)
            for op in sorted_ops:
                if op.gate == gate:
                    count += 1
                    if count % rhythm == 0:
                        self.circuit.clear_operations_touching(op.qubits, [mi])
                        count = 0

    def optimize_circuit(self):
        # self.core(cirq.T, 3, self.qubit_order)
        # self.core(cirq.T**-1, 3, self.qubit_order)
        self.core(cirq.T, 3, self.qubit_order_inv)
        self.core(cirq.T**-1, 3, self.qubit_order_inv)
        return self.circuit
