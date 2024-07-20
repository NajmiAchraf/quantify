import cirq

from .transfer_flag_optimizer import TransferFlagOptimizer

class CancelNghTs(TransferFlagOptimizer):
    # Cancel T gates in the target qubit
    circuit: cirq.Circuit
    target_ops: list = []
    Z_inserted: bool = False

    def __init__(self, circuit: cirq.Circuit):
        self.circuit = circuit

        # looping on gates of each qubit to get target
        for qubit in circuit.all_qubits():
            for op in circuit.all_operations():
                if op.gate == cirq.T and op.qubits[0] == qubit and qubit.name == "target":
                    self.target_ops.append(op)

    def __str__(self):
        pr = "qubit target:"
        for t in self.target_ops:
            pr.join(" " + t)
        pr.join("\n")
        return pr

    def __del__(self):
        self.target_ops.clear()

    def core(self):
        for mi, moment in enumerate(self.circuit):
            for op in moment:
                if op == self.target_ops[0]:
                    index = self.circuit.moments.index(moment)
                    self.circuit.clear_operations_touching(op.qubits, [index])
                    if not self.Z_inserted and len(self.target_ops) == 4:
                        self.circuit.insert(index, cirq.Z(op.qubits[0]))
                        self.Z_inserted = True

    def optimize_circuit(self):
        # replace the T gate with a single Z gate if length of self.target_ops is 4
        if len(self.target_ops) == 4:
            self.core()

        # remove the T gates if length of self.target_ops is 8 or more and is a multiple of 8
        elif len(self.target_ops) >= 8 and len(self.target_ops) % 8 == 0:
            self.core()
