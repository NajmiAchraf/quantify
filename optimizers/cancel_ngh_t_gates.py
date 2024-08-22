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
        self.core(cirq.T, 5, self.qubit_order_inv)
        self.core(cirq.T**-1, 5, self.qubit_order_inv)
        return self.circuit


class CancelNghTs(TransferFlagOptimizer):
    """ TEST NOT OFFICIAL METHOD
    Example:
        b_*0

    """
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

    def core(self):
        for mi, moment in enumerate(self.circuit):
            for op in moment:
                if len(self.ops_to_cancel) == 0:
                    return
                if op == self.ops_to_cancel[0]:
                    self.ops_to_cancel.remove(op)
                    self.circuit.clear_operations_touching(op.qubits, [mi])

    def optimize_circuit(self):
        def check_and_optimize(gate):
            def check_qubit_name_is_zeros(qubit_name: str):
                if qubit_name[0] != "b":
                    return False
                qubit_name = qubit_name[2:-1]

                for qubit in qubit_name:
                    if qubit != "0":
                        return False
                return True

            for qubit in self.qubits_ops:
                if not check_qubit_name_is_zeros(str(qubit)):
                    continue
                for op in self.qubits_ops[qubit]:
                    if op.gate == gate:
                        self.ops_to_cancel.append(op)
                self.core()

        check_and_optimize(cirq.T)

        # check_and_optimize(cirq.T**-1)


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