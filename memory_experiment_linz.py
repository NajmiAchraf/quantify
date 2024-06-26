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


def rgp(color: str, *args) -> None:
    if color == "r":
        print("\033[91m" + " ".join(args) + "\033[0m")
    elif color == "g":
        print("\033[92m" + " ".join(args) + "\033[0m")


def spent_time(start: float) -> str:
    elapsed_time = time.time() - start
    formatted_time = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
    milliseconds = (elapsed_time - int(elapsed_time)) * 1000
    final_output = f"{formatted_time}:{int(milliseconds)}"
    return final_output


class MemoryExperiment:
    decomp: str = "no_decomp"
    compare: bool = False
    print_circuit: bool = False
    start_range_qubits: int
    end_range_qubits: int

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

        if len(sys.argv) == 6:
            if sys.argv[1].lower() in ["y", "yes"]:
                self.decomp = "decomp"

            if sys.argv[2].lower() in ["y", "yes"] and self.decomp == "decomp":
                self.compare = True

            if sys.argv[3].lower() in ["y", "yes"]:
                self.print_circuit = True

            self.start_range_qubits = int(sys.argv[4])
            if self.start_range_qubits < 2:
                print(msg0)
                flag = False

            self.end_range_qubits = int(sys.argv[5])
            if self.end_range_qubits < self.start_range_qubits:
                print(msg1)
                flag = False

        if len(sys.argv) != 6 or not flag:
            if input("Decomposition? (y/n): ").lower() in ["y", "yes"]:
                self.decomp = "decomp"

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
        print("Decomposition: {}, Print the Circuit: {}, Start Range of Qubits: {}, End Range of Qubits: {}".format(
            self.decomp, "yes" if self.print_circuit else "no", self.start_range_qubits, self.end_range_qubits))

        if self.decomp == "decomp":
            """
                Bucket brigade - DECOMP
            """
            # self.bb_decompose_test(
            #     ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
            #     ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4_TEST
            # )
            self.bb_decompose_test(
                ToffoliDecompType.ZERO_ANCILLA_TDEPTH_0_UNCOMPUTE,
                ToffoliDecompType.ZERO_ANCILLA_TDEPTH_3_TEST
            )

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

    def bb_decompose_test(
        self,
        dec: ToffoliDecompType,
        dec_mod: ToffoliDecompType
    ):
        # ================DECOMP================

        self.decomp_scenario = self.bb_decompose(dec)

        # ================MODDED================

        self.decomp_scenario_modded = self.bb_decompose(dec_mod)

        self.run()

    def run(self):
        for i in range(self.start_range_qubits, self.end_range_qubits + 1):
            self.start_range_qubits = i
            self.forked_pid = os.fork()
            if self.forked_pid == 0:
                if self.compare:
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

            start = time.time()
            self.bbcircuit = bb.BucketBrigade(
                qubits, decomp_scenario=decomp_scenario)
            stop = spent_time(start)

            self.results(stop)

    def results(self, stop: str):
        print(f"{'='*150}\n\n")

        self.simulate_decompositions()

        self.simulate_circuit(stop)

        print(f"\n\n{'='*150}")

    def simulate_circuit(self, stop: str):
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

        if self.print_circuit:
            # Print the circuit
            start = time.time()
            print("\n", self.bbcircuit.circuit.to_text_diagram(
                use_unicode_characters=False,
                qubit_order=self.bbcircuit.qubit_order))
            print("Time of printing the circuit: ", spent_time(start))

        # TODO: Implement the simulation of the full circuit
        # self.simulation()

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

    # TODO: Implement the simulation of the full circuit
    def simulation(self):
        self.check_depth_of_circuit()

        start = time.time()

        print("\nSimulating the circuit...")

        simulator = cirq.Simulator()
        result = simulator.simulate(self.bbcircuit.circuit)
        print(result)

        stop = spent_time(start)
        print("Simulation time: ", stop)

    def fan_in_mem_out(self, decomp_scenario):
        return [decomp_scenario.dec_fan_in, decomp_scenario.dec_mem, decomp_scenario.dec_fan_out]

    def simulate_decompositions(self):
        if self.forked_pid == 0:
            decomp_scenario = list(
                set(self.fan_in_mem_out(self.decomp_scenario)))
        else:
            decomp_scenario = list(
                set(self.fan_in_mem_out(self.decomp_scenario_modded)))

        for dec in decomp_scenario:
            flag = True
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

                try:
                    assert (np.array_equal(
                        np.array(np.around(result.final_state)), temp))
                except Exception:
                    flag = False
                    rgp("r", str(result))
                else:
                    rgp("g", str(result))
                print("")

                initial_state[i] = 0

            stop = spent_time(start)
            if flag:
                rgp("g", "Decomposition simulation passed, Time:", stop)
            else:
                rgp("r", "Decomposition simulation failed, Time:", stop)


if __name__ == "__main__":
    MemoryExperiment()
