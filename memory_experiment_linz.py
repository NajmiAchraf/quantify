import cirq
from qramcircuits.toffoli_decomposition import ToffoliDecompType, ToffoliDecomposition

import qramcircuits.bucket_brigade as bb

import optimizers as qopt

import time
from typing import Union

import copy
import os
import psutil
import sys

import numpy as np


class MemoryExperiment:
    decomp: str = "no_decomp"
    dec_sim: bool = False
    compare: bool = False
    print_circuit: bool = False
    start_range_qubits: int
    end_range_qubits: int

    start: float = 0
    stop: str = ""

    forked_pid: int
    decomp_scenario: bb.BucketBrigadeDecompType
    decomp_scenario_modded: bb.BucketBrigadeDecompType
    bbcircuit: bb.BucketBrigade

    def __init__(self):
        self.get_input()
        self.main()

    def get_input(self):
        flag = True
        msg0 = "Start range of qubits must be greater than 1"
        msg1 = "End range of qubits must be greater than"\
            " start range of qubits or equal to it"

        len_argv = 7

        if len(sys.argv) == len_argv:
            if sys.argv[1].lower() in ["y", "yes"]:
                self.decomp = "decomp"

            if sys.argv[2].lower() in ["y", "yes"]:
                self.dec_sim = True

            if sys.argv[3].lower() in ["y", "yes"] and self.decomp == "decomp":
                self.compare = True

            if sys.argv[4].lower() in ["y", "yes"]:
                self.print_circuit = True

            self.start_range_qubits = int(sys.argv[5])
            if self.start_range_qubits < 2:
                print(msg0)
                flag = False

            self.end_range_qubits = int(sys.argv[6])
            if self.end_range_qubits < self.start_range_qubits:
                print(msg1)
                flag = False

        if len(sys.argv) != len_argv or not flag:
            if input("Decomposition? (y/n): ").lower() in ["y", "yes"]:
                self.decomp = "decomp"

            if input("Decomposition simulation? (y/n): ").lower() in ["y", "yes"]:
                self.dec_sim = True

            if self.decomp == "decomp":
                if input("Compare? (y/n): ").lower() in ["y", "yes"]:
                    self.compare = True

            if input("Print circuit? (y/n): ").lower() in ["y", "yes"]:
                self.print_circuit = True

            self.start_range_qubits = int(input("Start range of qubits: "))
            while self.start_range_qubits < 2:
                print(msg0)
                self.start_range_qubits = int(input("Start range of qubits: "))

            self.end_range_qubits = int(input("End range of qubits: "))
            while self.end_range_qubits < self.start_range_qubits:
                print(msg1)
                self.end_range_qubits = int(input("End range of qubits: "))

    def main(self):
        print("Hello QRAM circuit experiments!")
        print("Decomposition: {}, Compare: {}, Print the Circuit: {}, Start Range of Qubits: {}, End Range of Qubits: {}".format(
            self.decomp,
            "yes" if self.compare else "no",
            "yes" if self.print_circuit else "no",
            self.start_range_qubits,
            self.end_range_qubits
        ))

        if self.decomp == "decomp":
            """
                Bucket brigade - DECOMP
            """
            # self.bb_decompose_test(
            #     ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
            #     ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4_TEST,
            #     True
            # )

            # self.bb_decompose_test(
            #     ToffoliDecompType.ZERO_ANCILLA_TDEPTH_3,
            #     ToffoliDecompType.ZERO_ANCILLA_TDEPTH_3_TEST,
            #     False
            # )

            # for ptstatus in [True, False]:
            #     self.bb_decompose_test(
            #         [
            #             ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4_COMPUTE,
            #             ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
            #             ToffoliDecompType.ZERO_ANCILLA_TDEPTH_0_UNCOMPUTE],
            #         [
            #             ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4_COMPUTE,
            #             ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
            #             ToffoliDecompType.ZERO_ANCILLA_TDEPTH_0_UNCOMPUTE],
            #         ptstatus
            #     )

            self.bb_decompose_test(
                [
                    ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4_COMPUTE,
                    ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
                    ToffoliDecompType.ZERO_ANCILLA_TDEPTH_0_UNCOMPUTE],
                [
                    ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4_COMPUTE_TEST,
                    ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4_TEST,
                    ToffoliDecompType.ZERO_ANCILLA_TDEPTH_0_UNCOMPUTE_TEST],
                True
            )

        else:
            """
                Bucket brigade - NO DECOMP
            """
            self.decomp_scenario = self.bb_decompose(
                ToffoliDecompType.NO_DECOMP,
                False
            )
            self.run()

    def bb_decompose(
        self,
        toffoli_decomp_type: Union[list[ToffoliDecompType], ToffoliDecompType],
        parallel_toffolis: bool
    ):
        if isinstance(toffoli_decomp_type, list):
            return bb.BucketBrigadeDecompType(
                toffoli_decomp_types=[
                    toffoli_decomp_type[0],    # fan_in_decomp
                    toffoli_decomp_type[1],    # mem_decomp
                    toffoli_decomp_type[2]     # fan_out_decomp
                ],
                parallel_toffolis=parallel_toffolis
            )
        else:
            return bb.BucketBrigadeDecompType(
                toffoli_decomp_types=[
                    toffoli_decomp_type,    # fan_in_decomp
                    toffoli_decomp_type,    # mem_decomp
                    toffoli_decomp_type     # fan_out_decomp
                ],
                parallel_toffolis=parallel_toffolis
            )

    def bb_decompose_test(
            self,
            dec: Union[list[ToffoliDecompType], ToffoliDecompType],
            dec_mod: Union[list[ToffoliDecompType], ToffoliDecompType],
            parallel_toffolis: bool
    ):
        # ================DECOMP================

        self.decomp_scenario = self.bb_decompose(dec, parallel_toffolis)

        # ================MODDED================

        self.decomp_scenario_modded = self.bb_decompose(
            dec_mod, parallel_toffolis)

        self.run()

    def printCircuit(self, circuit: cirq.Circuit, qubits: list[cirq.NamedQubit]):
        # Print the circuit
        start = time.time()

        print(
            circuit.to_text_diagram(
                use_unicode_characters=False,
                qubit_order=qubits
            ),
            end="\n\n"
        )

        stop = self.spent_time(start)
        print("Time of printing the circuit: ", stop, "\n")

    def run(self):
        for i in range(self.start_range_qubits, self.end_range_qubits + 1):
            self.start_range_qubits = i
            self.forked_pid = os.fork()
            if self.forked_pid == 0:
                if self.compare or self.decomp == "no_decomp":
                    self.core(self.decomp_scenario)
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

            self.start = time.time()
            self.bbcircuit = bb.BucketBrigade(
                qubits, decomp_scenario=decomp_scenario)
            self.stop = self.spent_time(self.start)

            self.results()

    def results(self):
        print(f"{'='*150}\n\n")

        self.simulate_circuit()

        if self.dec_sim:
            self.simulate_decompositions()

        print(f"\n\n{'='*150}")

    def simulate_circuit(self):
        process = psutil.Process(os.getpid())
        # print("\npid", os.getpid())

        """
        rss: aka “Resident Set Size”, this is the non-swapped physical memory a
        process has used. On UNIX it matches “top“‘s RES column).
        vms: aka “Virtual Memory Size”, this is the total amount of virtual
        memory used by the process. On UNIX it matches “top“‘s VIRT column.
        """

        print(
            "--> mem bucket brigade: {:<8} | Qbits: {:<1} "
            "| Time: {:<12} | rss: {:<10} | vms: {:<10}\n".format(
                self.decomp,
                self.start_range_qubits,
                self.stop, process.memory_info().rss,
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
                "fan_out_decomp:\t\t{}\n"
                "parallel_toffolis:\t{}\n".format(
                    decomp_scenario.dec_fan_in,
                    decomp_scenario.dec_mem,
                    decomp_scenario.dec_fan_out,
                    "YES !!" if decomp_scenario.parallel_toffolis else "NO !!"
                ))

            self.check_depth_of_circuit()

        if self.print_circuit:
            self.printCircuit(self.bbcircuit.circuit,
                              self.bbcircuit.qubit_order)

        self.simulation()

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

    def simulation(self):
        flag = True
        self.start = time.time()

        print("\nSimulating the circuit...")

        measurements = [cirq.measure(self.bbcircuit.qubit_order[i])
                        for i in range(len(self.bbcircuit.qubit_order))]

        self.bbcircuit.circuit.append(measurements)

        simulator = cirq.Simulator()

        if self.print_circuit:
            self.printCircuit(self.bbcircuit.circuit,
                              self.bbcircuit.qubit_order)

        ls = [0 for _ in range(2**len(self.bbcircuit.qubit_order))]
        initial_state = np.array(ls, dtype=np.complex64)

        """ 2
the range of b qubits
0000 -> 0
0001 -> 32
0010 -> 64
0011 -> 96
...
1111 -> 480
10000 -> 512
        """
        """ 3
the range of b qubits
00000000 -> 0
00000001 -> 512
00000010 -> 1024
00000011 -> 1536
...
11111111 -> 65536
100000000 -> 131072
        """

        step = 2**(2**self.start_range_qubits+1)
        max_value = (step * (2**(2**self.start_range_qubits)))
        print("step", step)
        print("max_value", max_value)

        for i in range(0, max_value, step):
            initial_state[i] = 1
            result = simulator.simulate(
                self.bbcircuit.circuit,
                qubit_order=self.bbcircuit.qubit_order,
                initial_state=initial_state
            )
            # temp is supposed to have the expected result of a toffoli
            temp = copy.deepcopy(initial_state)

            try:
                assert (np.array_equal(
                    np.array(np.around(result.final_state)), temp))
            except Exception:
                flag = False
                self.rgp("r", str(result))
            else:
                self.rgp("g", str(result))
            print("")
            initial_state[i] = 0

        self.stop = self.spent_time(self.start)
        if flag:
            self.rgp("g", "Decomposition simulation passed, Time:", self.stop)
        else:
            self.rgp("r", "Decomposition simulation failed, Time:", self.stop)

    def fan_in_mem_out(self, decomp_scenario):
        return [
            decomp_scenario.dec_fan_in,
            decomp_scenario.dec_mem,
            decomp_scenario.dec_fan_out
        ]

    def simulate_decompositions(self):
        if self.forked_pid == 0:
            decomp_scenario = list(
                set(self.fan_in_mem_out(self.decomp_scenario)))
        else:
            decomp_scenario = list(
                set(self.fan_in_mem_out(self.decomp_scenario_modded)))

        for dec in decomp_scenario:
            flag = True
            self.start = time.time()
            print("\nSimulating the decomposition ...", dec,  end="\n\n")

            circuit = cirq.Circuit()

            qubits = [cirq.NamedQubit("q" + str(i)) for i in range(3)]

            moments = ToffoliDecomposition(
                decomposition_type=dec,
                qubits=qubits).decomposition()
            circuit.append(moments)

            measurements = [cirq.measure(qubits[i])
                            for i in range(len(qubits))]
            circuit.append(measurements)

            if self.print_circuit:
                self.printCircuit(circuit, qubits)

            simulator = cirq.Simulator()

            ls = [0 for i in range(2**len(qubits))]
            initial_state = np.array(ls, dtype=np.complex64)
            print(initial_state)
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

                try:
                    assert (np.array_equal(
                        np.array(np.around(result.final_state)), temp))
                except Exception:
                    flag = False
                    self.rgp("r", str(result))
                else:
                    self.rgp("g", str(result))
                print("")

                initial_state[i] = 0

            self.stop = self.spent_time(self.start)
            if flag:
                self.rgp("g", "Decomposition simulation passed, Time:", self.stop)
            else:
                self.rgp("r", "Decomposition simulation failed, Time:", self.stop)

    ########################
    # static methods
    ########################

    @ staticmethod
    def rgp(color: str, *args) -> None:
        if color == "r":
            print("\033[91m" + " ".join(args) + "\033[0m")
        elif color == "g":
            print("\033[92m" + " ".join(args) + "\033[0m")

    @ staticmethod
    def spent_time(start: float) -> str:
        elapsed_time = time.time() - start
        formatted_time = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
        milliseconds = (elapsed_time - int(elapsed_time)) * 1000
        final_output = f"{formatted_time}:{int(milliseconds)}"
        return final_output


if __name__ == "__main__":
    MemoryExperiment()
