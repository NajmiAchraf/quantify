import cirq
import cirq.optimizers

import optimizers as cnc

def test_optimise_hadamards():

    circ = cirq.Circuit()
    qubit_a = cirq.NamedQubit("a")

    circ.append(cirq.ops.H.on(qubit_a))
    circ.append(cirq.ops.H.on(qubit_a))
    circ.append(cirq.ops.H.on(qubit_a))

    # print("1", circ)

    cncl = cnc.CancelNghGates()
    cncl.optimize_circuit(circ)

    # print("2", circ)

    dropempty = cirq.optimizers.DropEmptyMoments()
    dropempty.optimize_circuit(circ)

    # print("3", circ)

    assert(len(circ) == 1)

def test_optimise_T_gate():

    circ = cirq.Circuit()
    qubit_a = cirq.NamedQubit("a")

    circ.append(cirq.ops.T.on(qubit_a))
    circ.append(cirq.ops.T.on(qubit_a)**-1)
    circ.append(cirq.ops.T.on(qubit_a))

    # print("1", circ)

    cncl = cnc.CancelNghGates()
    cncl.optimize_circuit(circ)

    # print("2", circ)

    dropempty = cirq.optimizers.DropEmptyMoments()
    dropempty.optimize_circuit(circ)

    # print("3", circ)

    assert(len(circ) == 1)

def test_optimise_S_gate():

    circ = cirq.Circuit()
    qubit_a = cirq.NamedQubit("a")

    circ.append(cirq.ops.S.on(qubit_a))
    circ.append(cirq.ops.S.on(qubit_a)**-1)
    circ.append(cirq.ops.S.on(qubit_a))

    # print("1", circ)

    cncl = cnc.CancelNghGates()
    cncl.optimize_circuit(circ)

    # print("2", circ)

    dropempty = cirq.optimizers.DropEmptyMoments()
    dropempty.optimize_circuit(circ)

    # print("3", circ)

    assert(len(circ) == 1)

def test_optimise_Z_gate():

    circ = cirq.Circuit()
    qubit_a = cirq.NamedQubit("a")

    circ.append(cirq.ops.Z.on(qubit_a))
    circ.append(cirq.ops.Z.on(qubit_a))
    circ.append(cirq.ops.Z.on(qubit_a))

    # print("1", circ)

    cncl = cnc.CancelNghGates()
    cncl.optimize_circuit(circ)

    # print("2", circ)

    dropempty = cirq.optimizers.DropEmptyMoments()
    dropempty.optimize_circuit(circ)

    # print("3", circ)

    assert(len(circ) == 1)