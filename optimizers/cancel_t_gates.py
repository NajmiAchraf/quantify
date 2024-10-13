import cirq
from typing import Dict, List, Tuple

class CancelTGate:
    """
    Cancel T gates in a circuit.
    """

    circuit: cirq.Circuit
    T_Gate: Dict[int, List] = {}

    def __init__(self, circuit: cirq.Circuit, qubit_order: List):
        self.circuit = circuit
        self.qubit_order = qubit_order

        count = 0
        for mi, moment in enumerate(self.circuit):
            for op in moment.operations:
                if op.gate == cirq.T or op.gate == cirq.T**-1:
                    count += 1
                    self[count] = [op.qubits, mi]

    def __len__(self):
        return len(self.T_Gate)

    def __getitem__(self, index: int):
        return self.T_Gate[index]

    def __setitem__(self, index: int, value: List):
        self.T_Gate[index] = value

    def __delitem__(self, index: int):
        if index in self.T_Gate:
            self.circuit.clear_operations_touching(
                self.T_Gate[index][0],
                [self.T_Gate[index][1]]
            )
            del self.T_Gate[index]

    def __call__(self):
        return self.T_Gate

    def __str__(self):
        return '\n'.join(f"{key}: {value}" for key, value in self.T_Gate.items())

    def optimize_circuit(self, indices: Tuple[int, ...]):
        for index in indices:
            del self[index]
        return self.circuit