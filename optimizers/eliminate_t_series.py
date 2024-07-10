import cirq

import utils.clifford_t_utils as ctu


class EliminateTSeriesInTarget():

    def optimize_circuit(self, circuit: cirq.Circuit):

        # looping on gates of each qubit to get target
        target_ops = []
        for qubit in circuit.all_qubits():
            for op in circuit.all_operations():
                if op.gate == cirq.T and op.qubits[0] == qubit and qubit.name == "target":
                    target_ops.append(op)

        # print("qubit target: ", end="")
        # for t in target_ops:
        #     print(t , end=" ")
        # print("\n")

        # replace the T gate with a single Z gate if length of target_ops is 4 and Z gate is not inserted
        if len(target_ops) == 4:
            Z_inserted = False
            for op in circuit.all_operations():
                if op.gate == cirq.T and op.qubits[0] == target_ops[0].qubits[0]:
                    for mi, moment in enumerate(circuit):
                        for op in moment:
                            if op == target_ops[0]:
                                index = circuit.moments.index(moment)
                                circuit.clear_operations_touching(op.qubits, [index])
                                if not Z_inserted:
                                    circuit.insert(index, cirq.Moment([cirq.Z(op.qubits[0])]))
                                    Z_inserted = True

        # remove the T gates if length of target_ops is 8 or more and is a multiple of 8
        elif len(target_ops) >= 8 and len(target_ops) % 8 == 0:
            for op in circuit.all_operations():
                if op.gate == cirq.T and op.qubits[0] == target_ops[0].qubits[0]:
                    for mi, moment in enumerate(circuit):
                        for op in moment:
                            if op == target_ops[0]:
                                index = circuit.moments.index(moment)
                                circuit.clear_operations_touching(op.qubits, [index])

        target_ops.clear()
