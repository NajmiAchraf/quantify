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
    dec_sim: bool = False
    print_circuit: bool = False
    print_sim: bool = False
    start_range_qubits: int
    end_range_qubits: int

    start: float = 0
    stop: str = ""

    decomp_scenario: bb.BucketBrigadeDecompType
    decomp_scenario_modded: bb.BucketBrigadeDecompType
    bbcircuit: bb.BucketBrigade
    bbcircuit_modded: bb.BucketBrigade

    simulator: cirq.Simulator = cirq.Simulator()

    def __init__(self):
        self.get_input()
        self.main()

    def get_input(self):
        flag = True
        msg0 = "Start range of qubits must be greater than 1"
        msg1 = "End range of qubits must be greater than"\
            " start range of qubits or equal to it"

        len_argv = 6

        if len(sys.argv) == len_argv:
            if sys.argv[1].lower() in ["y", "yes"]:
                self.dec_sim = True

            if sys.argv[2].lower() in ["y", "yes"]:
                self.print_circuit = True

            if sys.argv[3].lower() in ["y", "yes"]:
                self.print_sim = True

            self.start_range_qubits = int(sys.argv[4])
            if self.start_range_qubits < 2:
                print(msg0)
                flag = False

            self.end_range_qubits = int(sys.argv[5])
            if self.end_range_qubits < self.start_range_qubits:
                print(msg1)
                flag = False

        if len(sys.argv) != len_argv or not flag:
            if input("Simulate Toffoli decompositions? (y/n): ").lower() in ["y", "yes"]:
                self.dec_sim = True

            if input("Print circuits? (y/n): ").lower() in ["y", "yes"]:
                self.print_circuit = True

            if input("Print full simulation result? (y/n): ").lower() in ["y", "yes"]:
                self.print_sim = True

            self.start_range_qubits = int(input("Start range of qubits: "))
            while self.start_range_qubits < 2:
                print(msg0)
                self.start_range_qubits = int(input("Start range of qubits: "))

            self.end_range_qubits = int(input("End range of qubits: "))
            while self.end_range_qubits < self.start_range_qubits:
                print(msg1)
                self.end_range_qubits = int(input("End range of qubits: "))

    #######################################
    # main function
    #######################################

    def main(self):
        print("Hello QRAM circuit experiments!")
        print("Print the Circuit: {}, Start Range of Qubits: {}, End Range of Qubits: {}".format(
            "yes" if self.print_circuit else "no",
            self.start_range_qubits,
            self.end_range_qubits
        ))

        """
            Bucket brigade
        """
        self.bb_decompose_test(
            ToffoliDecompType.NO_DECOMP,
            False,
            [
                ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4_COMPUTE,
                ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
                ToffoliDecompType.ZERO_ANCILLA_TDEPTH_0_UNCOMPUTE],
            True
        )

        self.bb_decompose_test(
            ToffoliDecompType.NO_DECOMP,
            False,
            ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
            True
        )

        # self.bb_decompose_test(
        #     ToffoliDecompType.NO_DECOMP,
        #     False,
        #     [
        #         ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4_TEST,
        #         ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4_TEST,
        #         ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4_TEST],
        #     True
        # )

    #######################################
    # decomposition methods
    #######################################

    def bb_decompose(
        self,
        toffoli_decomp_type: Union['list[ToffoliDecompType]', ToffoliDecompType],
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
            dec: Union['list[ToffoliDecompType]', ToffoliDecompType],
            parallel_toffolis: bool,

            dec_mod: Union['list[ToffoliDecompType]', ToffoliDecompType],
            parallel_toffolis_mod: bool
    ):
        # ================ORIGIN================

        self.decomp_scenario = self.bb_decompose(dec, parallel_toffolis)

        # ================MODDED================

        self.decomp_scenario_modded = self.bb_decompose(
            dec_mod, parallel_toffolis_mod)

        self.run()

    #######################################
    # core functions
    #######################################

    def run(self):
        if self.decomp_scenario is None:
            self.rgp("r", "Decomposition scenario is None")
            return
        for i in range(self.start_range_qubits, self.end_range_qubits + 1):
            self.start_range_qubits = i
            self.core()

    def core(self):
        qubits: 'list[cirq.NamedQubit]' = []
        for i in range(self.start_range_qubits, self.start_range_qubits + 1):
            nr_qubits = i
            qubits.clear()
            for i in range(nr_qubits):
                qubits.append(cirq.NamedQubit("a" + str(i)))

            self.start = time.time()

            self.bbcircuit = bb.BucketBrigade(
                qubits, decomp_scenario=self.decomp_scenario)
            
            self.bbcircuit_modded = bb.BucketBrigade(
                qubits, decomp_scenario=self.decomp_scenario_modded)

            self.stop = self.spent_time(self.start)

            self.results()

    def results(self):
        print(f"{'='*150}\n\n")

        self.essential_checks()

        self.simulate_circuit()

        self.simulate_decompositions()

        print(f"\n\n{'='*150}")

    #######################################
    # essential checks methods
    #######################################

    def essential_checks(self):
        process = psutil.Process(os.getpid())
        # print("\npid", os.getpid())

        """
        rss: aka “Resident Set Size”, this is the non-swapped physical memory a
        process has used. On UNIX it matches “top“‘s RES column).
        vms: aka “Virtual Memory Size”, this is the total amount of virtual
        memory used by the process. On UNIX it matches “top“‘s VIRT column.
        """

        print(
            "--> mem bucket brigade -> Qbits: {:<1} "
            "| Time: {:<12} | rss: {:<10} | vms: {:<10}\n".format(
                self.start_range_qubits,
                self.stop, process.memory_info().rss,
                process.memory_info().vms),
            flush=True)

        for decomp_scenario in [self.decomp_scenario, self.decomp_scenario_modded]:
            print(
                "--> decomp scenario:\n"
                "fan_in_decomp:\t\t{}\n"
                "mem_decomp:\t\t{}\n"
                "fan_out_decomp:\t\t{}\n"
                "parallel_toffolis:\t{}\n".format(
                    decomp_scenario.dec_fan_in,
                    decomp_scenario.dec_mem,
                    decomp_scenario.dec_fan_out,
                    "YES !!" if decomp_scenario.parallel_toffolis else "NO !!"
                ))

            self.check_depth_of_circuit(decomp_scenario)
            
            if decomp_scenario == self.decomp_scenario:
                self.printCircuit(self.bbcircuit.circuit, self.bbcircuit.qubit_order)
            elif decomp_scenario == self.decomp_scenario_modded:
                self.printCircuit(self.bbcircuit_modded.circuit, self.bbcircuit_modded.qubit_order)

    def check_depth_of_circuit(self, decomp_scenario: bb.BucketBrigadeDecompType):
        if decomp_scenario.get_decomp_types()[0] != ToffoliDecompType.NO_DECOMP:
            print("\nChecking depth of the circuit decomposition...", end="\n\n")

            print("Number of qubits: ", end="")
            try:
                assert (self.bbcircuit.verify_number_qubits() == True)
            except Exception:
                self.rgp("r", "Number of qubits failed\n")
            else:
                self.rgp("g", "Number of qubits passed\n")

            print("Depth of the circuit: ", end="")
            try:
                assert (self.bbcircuit.verify_depth(
                    Alexandru_scenario=self.decomp_scenario.parallel_toffolis) == True)
            except Exception:
                self.rgp("r", "Depth of the circuit failed\n")
            else:
                self.rgp("g", "Depth of the circuit passed\n")

            print("T count: ", end="")
            try:
                assert (self.bbcircuit.verify_T_count() == True)
            except Exception:
                self.rgp("r", "T count failed\n")
            else:
                self.rgp("g", "T count passed\n")

            print("T depth: ", end="")
            try:
                assert (self.bbcircuit.verify_T_depth(
                    Alexandru_scenario=self.decomp_scenario.parallel_toffolis) == True)
            except Exception:
                self.rgp("r", "T depth failed\n")
            else:
                self.rgp("g", "T depth passed\n")

            # assert (self.bbcircuit.verify_hadamard_count(Alexandru_scenario=self.decomp_scenario.parallel_toffolis) == True)
            # assert (self.bbcircuit.verify_cnot_count(Alexandru_scenario=self.decomp_scenario.parallel_toffolis) == True)

            print("\n")

    #######################################
    # simulate circuit methods
    #######################################

    def simulate_circuit(self):
        self.simulation_full()

        # self.simulation_addressing()

        # self.simulation_b_qubits()

        # self.simulation_m_qubits()

    def simulation_full(self):
        """ 2
        the range of all qubits
        0 00 0000 0000 0 -> 0 : start
        0 00 0000 0000 1 -> 1 : step
        ...
        1 00 0000 0000 0 -> 2048 : stop 
        """
        """ 3
        the range of all qubits
        0 000 00000000 00000000 0 -> 0 : start
        0 000 00000000 00000000 1 -> 0 : 1
        ...
        1 000 00000000 00000000 0 -> 1048576 : stop
        """

        start = 0
        # stop = 2**(2**self.start_range_qubits+1) * (2**(2**self.start_range_qubits)) * (2**self.start_range_qubits)
        stop = 2 ** ( 2 * ( 2 ** self.start_range_qubits ) + self.start_range_qubits + 1 )
        print("\nSimulating the circuit...checking the full range of qubits.", end="\n\n")
        self._simulation(start, stop, 1)
    
    def simulation_addressing(self):
        """ 2
        the range of a qubits
        0 00 0000 0000 0 -> 0 : start
        0 01 0000 0000 0 -> 512 : step
        0 10 0000 0000 0 -> 1024
        0 11 0000 0000 0 -> 1536
        1 00 0000 0000 0 -> 2048 : stop 
        """
        """ 3
        the range of a qubits
        0 000 00000000 00000000 0 -> 0 : start
        0 001 00000000 00000000 0 -> 131072 : step
        0 010 00000000 00000000 0 -> 262144
        0 011 00000000 00000000 0 -> 393216
        0 100 00000000 00000000 0 -> 524288
        0 101 00000000 00000000 0 -> 655360
        0 110 00000000 00000000 0 -> 786432
        0 111 00000000 00000000 0 -> 917504
        1 000 00000000 00000000 0 -> 1048576 : stop
        """

        start = 0
        # step = 2**(2**self.start_range_qubits+1) * (2**(2**self.start_range_qubits))
        step = 2 ** ( 2 * ( 2 ** self.start_range_qubits ) + 1 )
        stop = step * ( 2 ** self.start_range_qubits )
        print("\nSimulating the circuit...checking the addressing of the a qubits.", end="\n\n")
        self._simulation(start, stop, step)

    def simulation_b_qubits(self):
        """ 2
        the range of b qubits
        0 00 0000 0000 0 -> 0 : start
        0 00 0001 0000 0 -> 32 : step
        0 00 0010 0000 0 -> 64
        0 00 0011 0000 0 -> 96
        ...
        0 00 1111 0000 0 -> 480
        0 01 0000 0000 0 -> 512 : stop
        """
        """ 3
        the range of b qubits
        0 000 00000000 00000000 0 -> 0 : start
        0 000 00000001 00000000 0 -> 512 : step
        0 000 00000010 00000000 0 -> 1024
        0 000 00000011 00000000 0 -> 1536
        ...
        0 000 11111111 00000000 0 -> 65536
        0 001 00000000 00000000 0 -> 131072 : stop
        """

        start = 0
        step = 2 ** ( 2 ** self.start_range_qubits + 1 )
        stop = step * ( 2 ** ( 2 ** self.start_range_qubits ) )
        print("\nSimulating the circuit...checking the uncomputation of FANOUT...were the b qubits are returned to their initial state.", end="\n\n")
        self._simulation(start, stop, step)

    def simulation_m_qubits(self):
        """ 2
        the range of m qubits
        0 00 0000 0000 0 -> 0 : start
        0 00 0000 0001 0 -> 2 : step
        0 00 0000 0010 0 -> 4
        0 00 0000 0011 0 -> 6
        ...
        0 00 0000 1111 0 -> 30
        0 00 0001 0000 0 -> 32 : stop
        """
        """ 3
        the range of m qubits
        0 000 00000000 00000000 0 -> 0 : start
        0 000 00000000 00000001 0 -> 2 : step
        0 000 00000000 00000010 0 -> 4
        0 000 00000000 00000011 0 -> 6
        ...
        0 000 00000000 00001111 0 -> 30
        0 000 00000000 00010000 0 -> 32
        ...
        0 000 00000000 11111111 0 -> 510
        0 001 00000000 00000000 0 -> 512 : stop
        """

        start = 0
        step = 2
        stop = step * ( 2 ** ( 2 ** self.start_range_qubits ) )
        print("\nSimulating the circuit...checking the uncomputation of MEM...were the m qubits are returned to their initial state.", end="\n\n")
        self._simulation(start, stop, step)

    def _simulation(self, start, stop, step):
        fail:int = 0
        success:int = 0
        total_tests:int = 0

        self.start = time.time()

        # add measurements to the original circuit ############################################
        measurements = [cirq.measure(self.bbcircuit.qubit_order[i])
                        for i in range(len(self.bbcircuit.qubit_order))]

        self.bbcircuit.circuit.append(measurements)

        self.printCircuit(self.bbcircuit.circuit, self.bbcircuit.qubit_order)

        ls = [0 for _ in range(2**len(self.bbcircuit.qubit_order))]
        initial_state = np.array(ls, dtype=np.complex64)

        # add measurements to the modded circuit ##############################################
        measurements_modded = [cirq.measure(self.bbcircuit_modded.qubit_order[i])
                        for i in range(len(self.bbcircuit_modded.qubit_order))]

        self.bbcircuit_modded.circuit.append(measurements_modded)

        self.printCircuit(self.bbcircuit_modded.circuit, self.bbcircuit_modded.qubit_order)

        ls_modded = [0 for _ in range(2**len(self.bbcircuit_modded.qubit_order))]
        initial_state_modded = np.array(ls_modded, dtype=np.complex64)

        print("start =", start,"\tstop =", stop,"\tstep =", step, end="\n\n")

        for i in range(start, stop, step):
            initial_state[i] = 1
            initial_state_modded[i] = 1

            result = self.simulator.simulate(
                self.bbcircuit.circuit,
                qubit_order=self.bbcircuit.qubit_order,
                initial_state=initial_state
            )

            result_modded = self.simulator.simulate(
                self.bbcircuit_modded.circuit,
                qubit_order=self.bbcircuit_modded.qubit_order,
                initial_state=initial_state_modded
            )

            if self.print_sim:
                print("index =", str(i))
                print("Original circuit: ")
                print(str(result))

            try:
                assert (np.array_equal(
                    np.array(np.around(result.final_state)), 
                    np.array(np.around(result_modded.final_state))))
            except Exception:
                fail += 1
                if self.print_sim:
                    self.rgp("r","Modded circuit: ")
                    self.rgp("r", str(result_modded), end="\n\n")
                else:
                    self.rgp("r", "•", end="")
            else:
                success += 1
                if self.print_sim:
                    self.rgp("g","Modded circuit: ")
                    self.rgp("g", str(result_modded), end="\n\n")
                else:
                    self.rgp("g", "•", end="")

            initial_state[i] = 0
            initial_state_modded[i] = 0
            total_tests += 1

        self.stop = self.spent_time(self.start)
        print("\n\nTime: ", self.stop, end="\n\n", flush=True)

        f = format(((fail * 100)/total_tests), ',.2f')
        s = format(((success * 100)/total_tests), ',.2f')

        self.rgp("r", "Failed: ", str(f), "%")
        self.rgp("g", "Succeed: ", str(s), "%")

    #######################################
    # simulate decompositions methods
    #######################################

    def fan_in_mem_out(self, decomp_scenario: bb.BucketBrigadeDecompType) -> 'list[ToffoliDecompType]':
        return list(set(decomp_scenario.get_decomp_types()))

    def simulate_decompositions(self):
        if not self.dec_sim:
            return

        for decomp_scenario in [self.decomp_scenario, self.decomp_scenario_modded]:
            for decomposition_type in self.fan_in_mem_out(decomp_scenario):
                self._simulate_decomposition(decomposition_type)

    def _simulate_decomposition(self, decomposition_type: ToffoliDecompType):
        fail:int = 0
        success:int = 0
        total_tests:int = 0

        self.start = time.time()
        print("\nSimulating the decomposition ...", decomposition_type,  end="\n\n")

        circuit = cirq.Circuit()

        qubits = [cirq.NamedQubit("q" + str(i)) for i in range(3)]

        moments = ToffoliDecomposition(
            decomposition_type=decomposition_type,
            qubits=qubits).decomposition()
        circuit.append(moments)

        measurements = [cirq.measure(qubits[i])
                        for i in range(len(qubits))]
        circuit.append(measurements)

        self.printCircuit(circuit, qubits)

        ls = [0 for _ in range(2**len(qubits))]
        initial_state = np.array(ls, dtype=np.complex64)

        for i in range(8):
            initial_state[i] = 1
            result = self.simulator.simulate(
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
                fail += 1
                if self.print_sim:    
                    self.rgp("r","Modded circuit: ")
                    self.rgp("r", str(result), end="\n\n")
                else:
                    self.rgp("r", "•", end="")
            else:
                success += 1
                if self.print_sim:
                    self.rgp("g","Modded circuit: ")
                    self.rgp("g", str(result), end="\n\n")
                else:
                    self.rgp("g", "•", end="")

            initial_state[i] = 0
            total_tests += 1

        self.stop = self.spent_time(self.start)
        print("\n\nTime: ", self.stop, end="\n\n", flush=True)

        f = format(((fail * 100)/total_tests), ',.2f')
        s = format(((success * 100)/total_tests), ',.2f')

        self.rgp("r", "Failed: ", str(f), "%")
        self.rgp("g", "Succeed: ", str(s), "%")

    #######################################
    # print circuit method
    #######################################

    def printCircuit(self, circuit: cirq.Circuit, qubits: 'list[cirq.NamedQubit]'):
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

            stop = self.spent_time(start)
            print("Time of printing the circuit: ", stop, "\n")

    #######################################
    # static methods
    #######################################

    @ staticmethod
    def rgp(color: str, *args, end="\n") -> None:
        if color == "r":
            print("\033[91m" + "".join(args) + "\033[0m", flush=True, end=end)
        elif color == "g":
            print("\033[92m" + "".join(args) + "\033[0m", flush=True, end=end)

    @ staticmethod
    def spent_time(start: float) -> str:
        elapsed_time = time.time() - start
        formatted_time = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
        milliseconds = (elapsed_time - int(elapsed_time)) * 1000
        final_output = f"{formatted_time}:{int(milliseconds)}"
        return final_output


if __name__ == "__main__":
    MemoryExperiment()
