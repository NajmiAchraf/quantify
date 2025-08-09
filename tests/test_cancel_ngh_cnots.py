import cirq

import optimizers.cancel_ngh_cnots as cnc


def test_optimise_cnots():

    circ = cirq.Circuit()
    qubit_a = cirq.NamedQubit("a")
    qubit_b = cirq.NamedQubit("b")

    circ.append(cirq.ops.CNOT.on(qubit_a, qubit_b))
    circ.append(cirq.ops.CNOT.on(qubit_a, qubit_b))
    circ.append(cirq.ops.CNOT.on(qubit_a, qubit_b))

    # print("1", circ)

    cncl = cnc.CancelNghCNOTs()
    cncl.optimize_circuit(circ)

    # print("2", circ)

    circ = cirq.drop_empty_moments(circ)

    # print("3", circ)

    assert len(circ) == 1


def test_optimise_cx():

    circ = cirq.Circuit()
    qubit_a = cirq.NamedQubit("a")
    qubit_b = cirq.NamedQubit("b")

    circ.append(cirq.ops.CX.on(qubit_a, qubit_b))
    circ.append(cirq.ops.CX.on(qubit_a, qubit_b))
    circ.append(cirq.ops.CX.on(qubit_a, qubit_b))

    # print("1", circ)

    cncl = cnc.CancelNghCNOTs()
    cncl.optimize_circuit(circ)

    # print("2", circ)

    circ = cirq.drop_empty_moments(circ)

    # print("3", circ)

    assert len(circ) == 1


def test_optimise_cz():
    circ = cirq.Circuit()
    qubit_a = cirq.NamedQubit("a")
    qubit_b = cirq.NamedQubit("b")

    circ.append(cirq.ops.CZ.on(qubit_a, qubit_b))
    circ.append(cirq.ops.CZ.on(qubit_a, qubit_b))
    circ.append(cirq.ops.CZ.on(qubit_a, qubit_b))

    # print("1", circ)

    cncl = cnc.CancelNghCNOTs()
    cncl.optimize_circuit(circ)

    # print("2", circ)

    circ = cirq.drop_empty_moments(circ)

    # print("3", circ)

    assert len(circ) == 1


def test_optimise_cnot_half():
    circ = cirq.Circuit()
    qubit_a = cirq.NamedQubit("a")
    qubit_b = cirq.NamedQubit("b")

    circ.append(cirq.ops.CNOT.on(qubit_a, qubit_b) ** (-0.5))
    circ.append(cirq.ops.CNOT.on(qubit_a, qubit_b) ** 0.5)
    circ.append(cirq.ops.CNOT.on(qubit_a, qubit_b) ** 0.5)

    # print("1", circ)

    cncl = cnc.CancelNghCNOTs()
    cncl.optimize_circuit(circ)

    # print("2", circ)

    circ = cirq.drop_empty_moments(circ)

    # print("3", circ)

    assert len(circ) == 1


def test_optimise_cx_half():
    circ = cirq.Circuit()
    qubit_a = cirq.NamedQubit("a")
    qubit_b = cirq.NamedQubit("b")

    circ.append(cirq.ops.CX.on(qubit_a, qubit_b) ** (-0.5))
    circ.append(cirq.ops.CX.on(qubit_a, qubit_b) ** (-0.5))
    circ.append(cirq.ops.CX.on(qubit_a, qubit_b) ** 0.5)

    # print("1", circ)

    cncl = cnc.CancelNghCNOTs()
    cncl.optimize_circuit(circ)

    # print("2", circ)

    circ = cirq.drop_empty_moments(circ)

    # print("3", circ)

    assert len(circ) == 1
