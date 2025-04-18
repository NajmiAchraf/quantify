import cirq

import optimizers as cnc


def test_optimise_T_gate():

    circ = cirq.Circuit()
    qubit_a = cirq.NamedQubit("a")

    circ.append(cirq.ops.T.on(qubit_a))
    circ.append(cirq.ops.T.on(qubit_a))

    # print("1", circ)

    trans = cnc.TransformeNghGates()
    trans.optimize_circuit(circ)

    # print("2", circ)

    circ = cirq.drop_empty_moments(circ)

    # print("3", circ)

    for moment in circ:
        for op in moment:
            assert op.gate == cirq.S


def test_optimise_1_T_gate():

    circ = cirq.Circuit()
    qubit_a = cirq.NamedQubit("a")

    circ.append(cirq.ops.T.on(qubit_a) ** -1)
    circ.append(cirq.ops.T.on(qubit_a) ** -1)

    # print("1", circ)

    trans = cnc.TransformeNghGates()
    trans.optimize_circuit(circ)

    # print("2", circ)

    circ = cirq.drop_empty_moments(circ)

    # print("3", circ)

    for moment in circ:
        for op in moment:
            assert op.gate == cirq.S**-1


def test_optimise_S_gate():

    circ = cirq.Circuit()
    qubit_a = cirq.NamedQubit("a")

    circ.append(cirq.ops.S.on(qubit_a))
    circ.append(cirq.ops.S.on(qubit_a))

    # print("1", circ)

    trans = cnc.TransformeNghGates()
    trans.optimize_circuit(circ)

    # print("2", circ)

    circ = cirq.drop_empty_moments(circ)

    # print("3", circ)

    for moment in circ:
        for op in moment:
            assert op.gate == cirq.Z


def test_optimise_1_S_gate():
    circ = cirq.Circuit()
    qubit_a = cirq.NamedQubit("a")

    circ.append(cirq.ops.S.on(qubit_a) ** -1)
    circ.append(cirq.ops.S.on(qubit_a) ** -1)

    # print("1", circ)

    trans = cnc.TransformeNghGates()
    trans.optimize_circuit(circ)

    # print("2", circ)

    circ = cirq.drop_empty_moments(circ)

    # print("3", circ)

    for moment in circ:
        for op in moment:
            assert op.gate == cirq.Z
