import cirq
import numpy as np

qubits = [cirq.NamedQubit("q" + str(1)), cirq.NamedQubit("q" + str(2))]
# qubits = [cirq.NamedQubit("q" + str(1))]

# moments = []
# for _ in range(4):
#     moments += [cirq.Moment([cirq.T(qubit)]) for qubit in qubits]


# moments = []
# moments += [cirq.Moment([cirq.Z(qubits[0])])]

moments = []
# gate anything input the gate will be zeroed
moments += [
    cirq.Moment([cirq.ResetChannel().on(qubits[1])]),
    # cirq.Moment([cirq.I(qubits[0])]),
    cirq.Moment([cirq.CNOT(qubits[0], qubits[1])])
]

circuit = cirq.Circuit(moments)

measurements = [cirq.measure(qubit) for qubit in qubits]
circuit.append(measurements)

print(circuit)

ls = [0 for _ in range(2**len(qubits))]
initial_state = np.zeros(2**len(qubits), dtype=np.complex64)
for i, l in enumerate(ls):
    initial_state[i] = 1

    simulator = cirq.Simulator()
    result = simulator.simulate(circuit, initial_state=initial_state)

    print(result)

    initial_state[i] = 0
