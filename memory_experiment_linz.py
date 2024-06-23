import cirq
from qramcircuits.toffoli_decomposition import ToffoliDecompType

import qramcircuits.bucket_brigade as bb

import optimizers as qopt

import time

import os
import psutil
import sys


from typing import Iterator


def results(
    decomp: str,
    nr_qubits: int,
    stop: int,
    bbcircuit: bb.BucketBrigade,
    decomp_scenario: bb.BucketBrigadeDecompType
):
    print("\n")
    process = psutil.Process(os.getpid())
    # print("\npid", os.getpid())

    """
    rss: aka “Resident Set Size”, this is the non-swapped physical memory a
    process has used. On UNIX it matches “top“‘s RES column).
    vms: aka “Virtual Memory Size”, this is the total amount of virtual
    memory used by the process. On UNIX it matches “top“‘s VIRT column.
    """
    print("--> mem bucket brigade: {:<8} | qbits: {:<1} | time: {:<20} | rss: {:<10} | vms: {:<10}".format(
        decomp, nr_qubits, stop, process.memory_info().rss, process.memory_info().vms), flush=True)
    if decomp == "decomp":
        check_depth_of_circuit(bbcircuit, decomp_scenario)

def check_depth_of_circuit(
    bbcircuit: bb.BucketBrigade,
    decomp_scenario: bb.BucketBrigadeDecompType
):
    print("Checking depth of the circuit decomposition...")

    # print("Number of qubits: ", end="")
    bbcircuit.verify_number_qubits()

    print("Depth of the circuit: ", end="")
    bbcircuit.verify_depth(
        Alexandru_scenario=decomp_scenario.parallel_toffolis)

    # print("T count: ", end="")
    bbcircuit.verify_T_count()

    print("T depth: ", end="")
    bbcircuit.verify_T_depth(
        Alexandru_scenario=decomp_scenario.parallel_toffolis)

    # bbcircuit.verify_hadamard_count(Alexandru_scenario=decomp_scenario.parallel_toffolis)
    # bbcircuit.verify_cnot_count(Alexandru_scenario=decomp_scenario.parallel_toffolis)


def main(decomp, nr, times=1):

    print("Hello QRAM circuit experiments!")
    print("Decomposition: {}, Qubits: {}, Times: {}".format(decomp, nr, times))

    if decomp == "decomp":
        """
            Bucket brigade - DECOMP
        """
        decomp_scenario = bb.BucketBrigadeDecompType(
            [
                ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4_COMPUTE,    # fan_in_decomp
                ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,            # mem_decomp
                ToffoliDecompType.ZERO_ANCILLA_TDEPTH_0_UNCOMPUTE,  # fan_out_decomp
            ],
            False
        )
        decomp_scenario_modded = bb.BucketBrigadeDecompType(
            [
                ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4_COMPUTE_T_GATE,     # fan_in_decomp
                ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,                    # mem_decomp
                ToffoliDecompType.ZERO_ANCILLA_TDEPTH_0_UNCOMPUTE,          # fan_out_decomp
            ],
            False
        )
    else:
        """
            Bucket brigade - NO DECOMP
        """
        decomp_scenario = bb.BucketBrigadeDecompType(
            [
                ToffoliDecompType.NO_DECOMP,  # fan_in_decomp
                ToffoliDecompType.NO_DECOMP,  # mem_decomp
                ToffoliDecompType.NO_DECOMP,  # fan_out_decomp
            ],
            False
        )

    # process = psutil.Process(os.getpid())
    qubits: list[cirq.NamedQubit] = []
    for _ in range(times):
        forked_pid = os.fork()
        if forked_pid == 0:
            for i in range(nr, nr + 1):

                nr_qubits = i
                qubits.clear()
                for i in range(nr_qubits):
                    qubits.append(cirq.NamedQubit("a" + str(i)))

                start = time.time()
                bbcircuit = bb.BucketBrigade(
                    qubits, decomp_scenario=decomp_scenario_modded)
                # print(bbcircuit.circuit.to_text_diagram(use_unicode_characters=False,
                #                                         qubit_order=bbcircuit.qubit_order))
                stop = time.time() - start
                
                results(decomp, nr_qubits, stop, bbcircuit, decomp_scenario)

                # simulate the circuit
                # print("Simulating the circuit...")
                # sim = cirq.Simulator()
                # result = sim.simulate(bbcircuit.circuit)
                # print("Result: ", result)

                # print("--> mem bucket brigade, ", argv_param, ",", nr_qubits,
                #     ",", stop,
                #     ",", process.memory_info().rss,
                #     ",", process.memory_info().vms, flush=True)
            break
        else:
            os.waitpid(forked_pid, 0)
            for i in range(nr, nr + 1):

                nr_qubits = i
                qubits.clear()
                for i in range(nr_qubits):
                    qubits.append(cirq.NamedQubit("a" + str(i)))

                start = time.time()
                bbcircuit = bb.BucketBrigade(
                    qubits, decomp_scenario=decomp_scenario)
                
                print(bbcircuit.circuit.to_text_diagram(use_unicode_characters=False,
                                                        qubit_order=bbcircuit.qubit_order))
                stop = time.time() - start

                results(decomp, nr_qubits, stop, bbcircuit, decomp_scenario)


def run():
    decomp = sys.argv[1] if len(sys.argv) >= 2 else input(
        "Decomposition? (y/n): ")
    decomp = "decomp" if decomp.lower(
    ) in ["y", "yes", "decomp"] else "no_decomp"
    qubits = int(sys.argv[2]) if len(
        sys.argv) >= 3 else int(input("Number of qubits: "))
    times = int(sys.argv[3]) if len(
        sys.argv) == 4 else int(input("Number of times: "))
    main(decomp, qubits, times)


if __name__ == "__main__":

    # If param is decomp - decomposition
    # Otherwise no_decomp
    # if len(sys.argv) == 1:
    #     print("If param is decomp runs experiment with decomposition. "
    #           "Any other string no decomposition.")
    # else:
    #     main(sys.argv[1], int(sys.argv[2]))

    run()
