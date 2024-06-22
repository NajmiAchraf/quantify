import cirq

# Create some qubits
q0, q1 = cirq.LineQubit.range(2)

# Create a circuit
circuit = cirq.Circuit()

# Add some operations to the circuit
circuit.append([cirq.CZ(q0, q1), cirq.X(q0), cirq.Y(q1)])

# Now, let's say we want to remove the CZ operation from the first moment
# and the X operation from the second moment

# First, we need to find the moments that these operations are in
cz_moment_index = None
x_moment_index = None
for i, moment in enumerate(circuit):
    if cirq.CZ(q0, q1) in moment:
        cz_moment_index = i
    if cirq.X(q0) in moment:
        x_moment_index = i

# Now we can create the input for the batch_remove function
removals = [(cz_moment_index, cirq.CZ(q0, q1)), (x_moment_index, cirq.X(q0))]
