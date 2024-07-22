import cirq

from .transfer_flag_optimizer import TransferFlagOptimizer

class CancelNghTs(TransferFlagOptimizer):
    # cancel T gates series in every qubit
    circuit: cirq.Circuit
    qubits_ops: dict = {}
    ops_to_cancel: list = []

    def __init__(self, circuit: cirq.Circuit):
        self.circuit = circuit
        self.qubits_ops = {str(qubit): [] for qubit in circuit.all_qubits()}

        # Collect operations for each qubit in the right order
        for moment in circuit:
            for op in moment:
                for qubit in op.qubits:
                    self.qubits_ops[str(qubit)].append(op)

    def __str__(self):
        for qubit in self.qubits_ops:
            pr = "qubit " + qubit + ":"
            for t in self.qubits_ops[qubit]:
                pr.join(" " + t)
            pr.join("\n")
        return pr

    def __del__(self):
        self.qubits_ops.clear()
        self.ops_to_cancel.clear()

    def coreZ(self, insert_Z=False):
        Z_inserted = False
        for mi, moment in enumerate(self.circuit):
            for op in moment:
                if len(self.ops_to_cancel) == 0:
                    return
                if op == self.ops_to_cancel[0]:
                    self.ops_to_cancel.remove(op)
                    index = self.circuit.moments.index(moment)
                    self.circuit.clear_operations_touching(op.qubits, [index])
                    if insert_Z and not Z_inserted:
                        self.circuit.insert(index, cirq.Z(op.qubits[0]))
                        Z_inserted = True

    def optimize_circuit(self):
        def check_and_optimize(gate, count_needed, insert_Z=False):
            count = 0
            for qubit in self.qubits_ops:
                for op in self.qubits_ops[qubit]:
                    if op.gate == gate:
                        self.ops_to_cancel.append(op)
                        count += 1
                    else:
                        self.ops_to_cancel.clear()
                        count = 0
                    if count == count_needed:
                        self.coreZ(insert_Z)
                        count = 0

        # Check for 4 T gates in series and replace with a single Z gate
        check_and_optimize(cirq.T, 4, insert_Z=True)

        # Check for 4 T**-1 gates in series and replace with a single Z gate
        check_and_optimize(cirq.T**-1, 4, insert_Z=True)

        # Check for 2 Z gates in series and remove them
        check_and_optimize(cirq.Z, 2)
