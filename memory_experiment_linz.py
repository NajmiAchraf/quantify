import cirq
from qramcircuits.toffoli_decomposition import ToffoliDecompType

import qramcircuits.bucket_brigade as bb

import optimizers as qopt

import time

import os
import psutil
import sys


def spent_time(start: int) -> str:
    elapsed_time = time.time() - start
    formatted_time = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
    milliseconds = (elapsed_time - int(elapsed_time)) * 1000
    final_output = f"{formatted_time}:{int(milliseconds)}"
    return final_output


class MemoryExperiment:
    def __init__(self):
        if len(sys.argv) == 5:
            self.decomp = "decomp" if sys.argv[1].lower() in ["y", "yes", "decomp"] else "no_decomp"
            self.print_circuit = True if sys.argv[2].lower() in ["y", "yes"] else False
            self.start_range_qubits = int(sys.argv[3])
            self.end_range_qubits = int(sys.argv[4])
        else:
            self.decomp = input("Decomposition? (y/n): ")
            self.decomp = "decomp" if self.decomp.lower() in ["y", "yes", "decomp"] else "no_decomp"

            self.print_circuit = input("Print circuit? (y/n): ")
            self.print_circuit = True if self.print_circuit.lower() in ["y", "yes"] else False

            self.start_range_qubits = int(input("Start range of qubits: "))
            while self.start_range_qubits < 2:
                self.start_range_qubits = int(input("Start range of qubits: "))

            self.end_range_qubits = int(input("End range of qubits: "))
            while self.end_range_qubits < self.start_range_qubits:
                self.end_range_qubits = int(input("End range of qubits: "))

        self.forked_pid:int = None
        self.decomp_scenario: bb.BucketBrigadeDecompType = None
        self.decomp_scenario_modded: bb.BucketBrigadeDecompType = None
        self.bbcircuit: bb.BucketBrigade = None

        self.main()
        self.run()


    def main(self):
        print("Hello QRAM circuit experiments!")
        print("Decomposition: {}, Print the Circuit: {}, Start Range of Qubits: {}, End Range of Qubits: {}".format(
            self.decomp, "yes" if self.print_circuit else "no", self.start_range_qubits, self.end_range_qubits))

        if self.decomp == "decomp":
            """
                Bucket brigade - DECOMP
            """
            #! self.decomp_scenario = bb.BucketBrigadeDecompType(
            #!     [
            #!         ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4_COMPUTE,    # fan_in_decomp
            #!         ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,            # mem_decomp
            #!         ToffoliDecompType.ZERO_ANCILLA_TDEPTH_0_UNCOMPUTE,  # fan_out_decomp
            #!     ],
            #!     False
            #! )

            self.group_test_one()

        else:
            """
                Bucket brigade - NO DECOMP
            """
            self.decomp_scenario = self.bb_decompose(ToffoliDecompType.NO_DECOMP)


    def bb_decompose(self, toffoli_decomp_type:bb.BucketBrigadeDecompType):
        return bb.BucketBrigadeDecompType(
            [
                toffoli_decomp_type,    # fan_in_decomp
                toffoli_decomp_type,    # mem_decomp
                toffoli_decomp_type     # fan_out_decomp
            ],
            False
        )


    def group_test_one(self):
        # ================DECOMP================ZERO_ANCILLA_TDEPTH 4 and 2================

        self.decomp_scenario = self.bb_decompose(ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4_COMPUTE)
        
        #? self.decomp_scenario = self.bb_decompose(ToffoliDecompType.ZERO_ANCILLA_TDEPTH_2_COMPUTE)

        # ================MODDED================ZERO_ANCILLA_TDEPTH 4 to 2================

        self.decomp_scenario_modded = self.bb_decompose(ToffoliDecompType.ZERO_ANCILLA_TDEPTH_2_COMPUTE_V2)


    def run(self):
        for i in range(self.start_range_qubits, self.end_range_qubits + 1):
            self.start_range_qubits = i
            self.forked_pid = os.fork()
            if self.forked_pid == 0:
                if self.decomp == "decomp":
                    self.core(self.decomp_scenario_modded)
                sys.exit(0)
            else:
                os.waitpid(self.forked_pid, 0)
                self.core(self.decomp_scenario)


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


    def results(self, stop: int):
        process = psutil.Process(os.getpid())
        # print("\npid", os.getpid())

        """
        rss: aka “Resident Set Size”, this is the non-swapped physical memory a
        process has used. On UNIX it matches “top“‘s RES column).
        vms: aka “Virtual Memory Size”, this is the total amount of virtual
        memory used by the process. On UNIX it matches “top“‘s VIRT column.
        """
        
        print(f"{'='*150}\n\n")

        print("--> mem bucket brigade: {:<8} | qbits: {:<1} | time: {:<12} | rss: {:<10} | vms: {:<10}\n".format(
            self.decomp, self.start_range_qubits, stop, process.memory_info().rss, process.memory_info().vms), flush=True)

        if self.decomp == "decomp":
            print("--> decomp scenario:")
            if self.forked_pid == 0:
                decomp_scenario = self.decomp_scenario_modded
            else:
                decomp_scenario = self.decomp_scenario

            print("fan_in_decomp:\t\t{}\nmem_decomp:\t\t{}\nfan_out_decomp:\t\t{}\n".format(
            decomp_scenario.dec_fan_in, decomp_scenario.dec_mem, decomp_scenario.dec_fan_out))

            self.check_depth_of_circuit()

        if self.print_circuit:
            # Print the circuit
            start = time.time()

            print("\n", self.bbcircuit.circuit.to_text_diagram(use_unicode_characters=False,
                                                qubit_order=self.bbcircuit.qubit_order))

            stop = spent_time(start)
            print("Time of printing the circuit: ", stop)

        # simulate the circuit
        start = time.time()

        print("\nSimulating the circuit...")
        sim = cirq.Simulator()
        result = sim.simulate(self.bbcircuit.circuit)
        print(result)

        stop = spent_time(start)
        print("Simulation time: ", stop)

        print(f"\n\n{'='*150}")


    def check_depth_of_circuit(self):
        print("Checking depth of the circuit decomposition...")

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


if __name__ == "__main__":
    MemoryExperiment()
