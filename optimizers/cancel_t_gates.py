import cirq

class CancelTGate():
    """ TEST NOT OFFICIAL METHOD
    
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

    def core(self, index: int, order: list):
        count = 0
        for mi, moment in enumerate(self.circuit):
            # Sort operations in the moment based on their qubits using self.qubit_order
            sorted_ops = sorted(moment.operations, key=lambda op: order.index(op.qubits[0]))
            for op in sorted_ops:
                if op.gate == cirq.T or op.gate == cirq.T**-1:
                    count += 1
                    if count == index:
                        self.circuit.clear_operations_touching(op.qubits, [mi])
                        return

    def optimize_circuit(self, *indices: int):
        for index in indices:
            self.core(index, self.qubit_order)
        return self.circuit