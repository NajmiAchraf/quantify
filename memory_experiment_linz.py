import cirq
from qramcircuits.toffoli_decomposition import ToffoliDecompType, ToffoliDecomposition

import qramcircuits.bucket_brigade as bb

import optimizers as qopt

import time

import copy
import os
import psutil
import sys

import numpy as np


def spent_time(start: float) -> str:
    elapsed_time = time.time() - start
    formatted_time = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
    milliseconds = (elapsed_time - int(elapsed_time)) * 1000
    final_output = f"{formatted_time}:{int(milliseconds)}"
    return final_output


class MemoryExperiment:

    forked_pid: int
    decomp_scenario: bb.BucketBrigadeDecompType
    decomp_scenario_modded: bb.BucketBrigadeDecompType
    bbcircuit: bb.BucketBrigade

    def __init__(self):
        if len(sys.argv) == 5:
            self.decomp = "decomp" if sys.argv[1].lower(
            ) in ["y", "yes", "decomp"] else "no_decomp"
            self.print_circuit = True if sys.argv[2].lower() in [
                "y", "yes"] else False
            self.start_range_qubits = int(sys.argv[3])
            self.end_range_qubits = int(sys.argv[4])
        else:
            self.decomp = input("Decomposition? (y/n): ")
            self.decomp = "decomp" if self.decomp.lower(
            ) in ["y", "yes", "decomp"] else "no_decomp"

            self.print_circuit = input("Print circuit? (y/n): ")
            self.print_circuit = True if self.print_circuit.lower() in [
                "y", "yes"] else False

            self.start_range_qubits = int(input("Start range of qubits: "))
            while self.start_range_qubits < 2:
                self.start_range_qubits = int(input("Start range of qubits: "))

            self.end_range_qubits = int(input("End range of qubits: "))
            while self.end_range_qubits < self.start_range_qubits:
                self.end_range_qubits = int(input("End range of qubits: "))

        self.main()

    def main(self):
        print("Hello QRAM circuit experiments!")
        print("Decomposition: {}, Print the Circuit: {}, Start Range of Qubits: {}, End Range of Qubits: {}".format(
            self.decomp, "yes" if self.print_circuit else "no", self.start_range_qubits, self.end_range_qubits))

        if self.decomp == "decomp":
            """
                Bucket brigade - DECOMP
            """
            self.group_test_TDEPTH_4()
            self.run()
            self.group_test_TDEPTH_3()
            self.run()

        else:
            """
                Bucket brigade - NO DECOMP
            """
            self.decomp_scenario = self.bb_decompose(
                ToffoliDecompType.NO_DECOMP)
            self.run()

    def bb_decompose(self, toffoli_decomp_type: ToffoliDecompType):
        return bb.BucketBrigadeDecompType(
            [
                toffoli_decomp_type,    # fan_in_decomp
                toffoli_decomp_type,    # mem_decomp
                toffoli_decomp_type     # fan_out_decomp
            ],
            False
        )

    def group_test_TDEPTH_4(self):
        # ================DECOMP================ZERO_ANCILLA_TDEPTH_4================

        self.decomp_scenario = self.bb_decompose(
            ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4)

        # ================MODDED================ZERO_ANCILLA_TDEPTH_4_TEST================

        self.decomp_scenario_modded = self.bb_decompose(
            ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4_TEST)

    def group_test_TDEPTH_3(self):
        # ================DECOMP================ZERO_ANCILLA_TDEPTH_3================

        self.decomp_scenario = self.bb_decompose(
            ToffoliDecompType.ZERO_ANCILLA_TDEPTH_3)

        # ================MODDED================ZERO_ANCILLA_TDEPTH_3_TEST================

        self.decomp_scenario_modded = self.bb_decompose(
            ToffoliDecompType.ZERO_ANCILLA_TDEPTH_3_TEST)

    def run(self):
        for i in range(self.start_range_qubits, self.end_range_qubits + 1):
            self.start_range_qubits = i
            self.forked_pid = os.fork()
            if self.forked_pid == 0:
                # self.core(self.decomp_scenario)
                sys.exit(0)
            else:
                os.waitpid(self.forked_pid, 0)
                if self.decomp == "decomp":
                    self.core(self.decomp_scenario_modded)

    def core(self, decomp_scenario):
        qubits: list[cirq.NamedQubit] = []
        for i in range(self.start_range_qubits, self.start_range_qubits + 1):
            nr_qubits = i
            qubits.clear()
            for i in range(nr_qubits):
                qubits.append(cirq.NamedQubit("a" + str(i)))

            start = time.time()
            self.bbcircuit = bb.BucketBrigade(
                qubits, decomp_scenario=decomp_scenario)
            stop = spent_time(start)

            self.results(stop)

    def results(self, stop: str):
        print(f"{'='*150}\n\n")

        self.simulate_decomposition()

        self.full_circuit(stop)

        print(f"\n\n{'='*150}")

    def full_circuit(self, stop: str):
        process = psutil.Process(os.getpid())
        # print("\npid", os.getpid())

        """
        rss: aka “Resident Set Size”, this is the non-swapped physical memory a
        process has used. On UNIX it matches “top“‘s RES column).
        vms: aka “Virtual Memory Size”, this is the total amount of virtual
        memory used by the process. On UNIX it matches “top“‘s VIRT column.
        """

        if self.print_circuit:
            # Print the circuit
            start = time.time()
            print("\n", self.bbcircuit.circuit.to_text_diagram(
                use_unicode_characters=False,
                qubit_order=self.bbcircuit.qubit_order))
            print("Time of printing the circuit: ", spent_time(start))

        print(
            "--> mem bucket brigade: {:<8} | Qbits: {:<1} "
            "| Time: {:<12} | rss: {:<10} | vms: {:<10}\n".format(
                self.decomp,
                self.start_range_qubits,
                stop, process.memory_info().rss,
                process.memory_info().vms),
            flush=True)

        if self.decomp == "decomp":
            print("--> decomp scenario:")
            if self.forked_pid == 0:
                decomp_scenario = self.decomp_scenario
            else:
                decomp_scenario = self.decomp_scenario_modded

            print(
                "fan_in_decomp:\t\t{}\n"
                "mem_decomp:\t\t{}\n"
                "fan_out_decomp:\t\t{}\n".format(
                    decomp_scenario.dec_fan_in,
                    decomp_scenario.dec_mem,
                    decomp_scenario.dec_fan_out
                ))

            self.check_depth_of_circuit()

        # self.simulate_circuit()

    def check_depth_of_circuit(self):
        print("\nChecking depth of the circuit decomposition...", end="\n\n")

        # print("Start range of qubits: ", end="")
        self.bbcircuit.verify_number_qubits()

        print("Depth of the circuit: ", end="")
        self.bbcircuit.verify_depth(
            Alexandru_scenario=self.decomp_scenario.parallel_toffolis)

        # print("T count: ", end="")
        self.bbcircuit.verify_T_count()

        print("T depth: ", end="")
        self.bbcircuit.verify_T_depth(
            Alexandru_scenario=self.decomp_scenario.parallel_toffolis)

        # self.bbcircuit.verify_hadamard_count(Alexandru_scenario=self.decomp_scenario.parallel_toffolis)
        # self.bbcircuit.verify_cnot_count(Alexandru_scenario=self.decomp_scenario.parallel_toffolis)

        print("\n")

    def simulate_circuit(self):
        start = time.time()

        print("\nSimulating the circuit...")

        simulator = cirq.Simulator()
        result = simulator.simulate(self.bbcircuit.circuit)
        print(result)

        stop = spent_time(start)
        print("Simulation time: ", stop)

    def fan_in_mem_out(self, decomp_scenario):
        return [decomp_scenario.dec_fan_in, decomp_scenario.dec_mem, decomp_scenario.dec_fan_out]

    def simulate_decomposition(self):
        if self.forked_pid == 0:
            decomp_scenario = list(
                set(self.fan_in_mem_out(self.decomp_scenario)))
        else:
            decomp_scenario = list(
                set(self.fan_in_mem_out(self.decomp_scenario_modded)))

        for dec in decomp_scenario:
            try:
                start = time.time()
                print("\nSimulating the decomposition ...", dec,  end="\n\n")

                circuit = cirq.Circuit()

                qubits = [cirq.NamedQubit("q" + str(i)) for i in range(3)]

                moments = ToffoliDecomposition(
                    decomposition_type=decomp_scenario[0],
                    qubits=qubits).decomposition()

                measurements = [cirq.measure(qubits[i])
                                for i in range(len(qubits))]

                circuit.append(moments)
                circuit.append(measurements)

                if self.print_circuit:
                    # Print the circuit
                    start = time.time()

                    print(
                        circuit.to_text_diagram(
                            use_unicode_characters=False,
                            qubit_order=qubits
                        ),
                        end="\n\n"
                    )

                    stop = spent_time(start)
                    print("Time of printing the circuit: ", stop, "\n")

                simulator = cirq.Simulator()

                ls = [0 for i in range(2**len(qubits))]
                initial_state = np.array(ls, dtype=np.complex64)
                for i in range(8):
                    initial_state[i] = 1
                    result = simulator.simulate(
                        circuit,
                        qubit_order=qubits,
                        initial_state=initial_state
                    )
                    # temp is supposed to have the expected result of a toffoli
                    temp = copy.deepcopy(initial_state)
                    if i in [6, 7]:
                        temp[6] = (1 - temp[6])
                        temp[-1] = (1 - temp[-1])
                    assert (np.array_equal(
                        np.array(np.around(result.final_state)), temp))

                    initial_state[i] = 0

                    print(result, end="\n\n")

                stop = spent_time(start)

                print("Decomposition simulation passed, Time: ", stop)
            except Exception:
                print("Decomposition simulation failed")


if __name__ == "__main__":
    MemoryExperiment()
