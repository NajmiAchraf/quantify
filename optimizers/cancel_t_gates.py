import cirq

class CancelTGate():
    """
    Cancel T gates in a circuit.
    """

    circuit: cirq.Circuit
    T_operations: 'dict[int, list]' = {}   

    def __init__(self, circuit: cirq.Circuit, qubit_order: list):
        self.circuit = circuit
        self.qubit_order = qubit_order

        count = 0
        for mi, moment in enumerate(self.circuit):
            # Sort operations in the moment based on their qubits using self.qubit_order
            # sorted_ops = sorted(moment.operations, key=lambda op: qubit_order.index(op.qubits[0]))
            for op in moment.operations:
                if op.gate == cirq.T or op.gate == cirq.T**-1:
                    count += 1
                    self.T_operations[count] = [op.qubits, mi]


    def __str__(self):
        for key, value in self.T_operations.items():
            print(key, value)

    def __del__(self):
        pass

    def optimize_circuit(self, *indices: int):
        for index in indices:
            self.circuit.clear_operations_touching(
                self.T_operations[index][0],
                [self.T_operations[index][1]]
            )
        return self.circuit
