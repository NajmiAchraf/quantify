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
import random as rd

class MemoryExperiment:
    """
    A class that represents a memory experiment using QRAM circuits.

    Attributes:
        dec_sim (bool): Flag indicating whether to simulate Toffoli decompositions.
        print_circuit (bool): Flag indicating whether to print the circuits.
        print_sim (bool): Flag indicating whether to print the full simulation result.
        start_range_qubits (int): Start range of qubits.
        end_range_qubits (int): End range of qubits.
        start_time (float): Start time of the experiment.
        stop_time (str): Stop time of the experiment.
        decomp_scenario (bb.BucketBrigadeDecompType): Decomposition scenario for the bucket brigade.
        decomp_scenario_modded (bb.BucketBrigadeDecompType): Modified decomposition scenario for the bucket brigade.
        bbcircuit (bb.BucketBrigade): Bucket brigade circuit.
        bbcircuit_modded (bb.BucketBrigade): Modified bucket brigade circuit.
        simulator (cirq.Simulator): Cirq simulator.

    Methods:
        __init__(): Initializes the MemoryExperiment class.
        get_input(): Gets user input for the experiment.
        main(): Main function of the experiment.
        bb_decompose(): Decomposes the Toffoli gates in the bucket brigade circuit.
        bb_decompose_test(): Tests the bucket brigade circuit with different decomposition scenarios.
        run(): Runs the experiment for a range of qubits.
        core(): Core function of the experiment.
        results(): Prints the results of the experiment.
        essential_checks(): Performs essential checks on the experiment.
        check_depth_of_circuit(): Checks the depth of the circuit decomposition.
    """

    dec_sim: bool = False
    print_circuit: bool = False
    print_sim: bool = False
    start_range_qubits: int
    end_range_qubits: int
    
    start_time: float = 0
    stop_time: str = ""

    decomp_scenario: bb.BucketBrigadeDecompType
    decomp_scenario_modded: bb.BucketBrigadeDecompType
    bbcircuit: bb.BucketBrigade
    bbcircuit_modded: bb.BucketBrigade
    simulator: cirq.Simulator = cirq.Simulator()


    def __init__(self):
        """
        Constructor the MemoryExperiment class.
        """
        self.get_input()
        self.main()

    def __del__(self):
        """
        Destructor of the MemoryExperiment class.
        """
        print("Memory experiment is done!")

    def get_input(self):
        """
        Gets user input for the experiment.
        """
        flag = True
        msg0 = "Start range of qubits must be greater than 1"
        msg1 = "End range of qubits must be greater than start range of qubits or equal to it"
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
        """
        Main function of the experiment.
        """
        print("Hello QRAM circuit experiments!")
        print("Print the Circuit: {}, Start Range of Qubits: {}, End Range of Qubits: {}".format(
            "yes" if self.print_circuit else "no",
            self.start_range_qubits,
            self.end_range_qubits
        ))

        """
            The Bucket brigade decomposition described in the paper.
            Depth of the circuit decomposition is 30 for 2 qubits WITH parallel Toffoli.
            ? Simulation not passed.
        """
        # self.bb_decompose_test(
        #     ToffoliDecompType.NO_DECOMP,
        #     False,
        #     [
        #         ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4_COMPUTE,
        #         ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
        #         ToffoliDecompType.ZERO_ANCILLA_TDEPTH_0_UNCOMPUTE
        #     ],
        #     True
        # )

        """
            The Bucket brigade standard 7-T gate decomposition (QC10).
            Depth of the circuit decomposition is 46 for 2 qubits WITH parallel Toffoli.
            Simulation passed.
        """
        # self.bb_decompose_test(
        #     ToffoliDecompType.NO_DECOMP,
        #     False,
        #     ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
        #     True
        # )

        # self.bb_decompose_test(
        #     ToffoliDecompType.NO_DECOMP,
        #     False,
        #     ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4_TEST,
        #     True
        # )

        """
            The Bucket brigade all controlled V, 𝑉† and X decompositions (QC5).
            Depth of the circuit decomposition is 46 for 2 qubits WITHOUT parallel Toffoli.
            Simulation passed.
        """
        # for i in range(8):
        #     self.bb_decompose_test(
        #         ToffoliDecompType.NO_DECOMP,
        #         False,
        #         eval(f"ToffoliDecompType.CV_CX_QC5_{i}"),
        #         False
        #     )

        """
            The Bucket brigade all controlled V, 𝑉† and X decompositions (QC5) for the FANIN and FANOUT AND standard 7-T gate decomposition (QC10) for QUERY (mem).
            ! Depth of the circuit decomposition is 36 for 2 qubits WITH parallel Toffoli.
            Simulation passed.
        """
        for i in [0, 2, 5, 7]:
            self.bb_decompose_test(
                ToffoliDecompType.NO_DECOMP,
                False,
                [
                    eval(f"ToffoliDecompType.CV_CX_QC5_{i}"),
                    ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
                    eval(f"ToffoliDecompType.CV_CX_QC5_{i}"),
                ],
                True
            )

        """
            The Bucket brigade all controlled V, 𝑉† and X decompositions (QC5) for the FANIN and FANOUT AND standard 7-T gate decomposition (QC10) for QUERY (mem).
            ! Depth of the circuit decomposition is 34 for 2 qubits WITH parallel Toffoli.
            Simulation passed.
        """
        for i in [1, 3, 4, 6]:
            self.bb_decompose_test(
                ToffoliDecompType.NO_DECOMP,
                False,
                [
                    eval(f"ToffoliDecompType.CV_CX_QC5_{i}"),
                    ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
                    eval(f"ToffoliDecompType.CV_CX_QC5_{i}"),
                ],
                True
            )

        """
            The Bucket brigade controlled V, 𝑉† and X decomposition (QC5)
            Depth of the circuit decomposition is 46 for 2 qubits WITHOUT parallel Toffoli.
            Simulation passed.
        """
        # self.bb_decompose_test(
        #     ToffoliDecompType.NO_DECOMP,
        #     False,
        #     [
        #         eval(f"ToffoliDecompType.CV_CX_QC5_{rd.randint(0, 7)}"),
        #         eval(f"ToffoliDecompType.CV_CX_QC5_{rd.randint(0, 7)}"),
        #         eval(f"ToffoliDecompType.CV_CX_QC5_{rd.randint(0, 7)}")
        #     ],
        #     False
        # )

        """
            Comparaison between 7-T gate decomposition (QC10) and controlled V, 𝑉† and X decomposition (QC5)
            Simulation passed.
        """
        # self.bb_decompose_test(
        #     ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
        #     True,
        #     [
        #         eval(f"ToffoliDecompType.CV_CX_QC5_{rd.randint(0, 7)}"),
        #         eval(f"ToffoliDecompType.CV_CX_QC5_{rd.randint(0, 7)}"),
        #         eval(f"ToffoliDecompType.CV_CX_QC5_{rd.randint(0, 7)}")
        #     ],
        #     False
        # )

    #######################################
    # decomposition methods
    #######################################

    def bb_decompose(
        self,
        toffoli_decomp_type: Union['list[ToffoliDecompType]', ToffoliDecompType],
        parallel_toffolis: bool
    ):
        """
        Decomposes the Toffoli gates in the bucket brigade circuit.

        Args:
            toffoli_decomp_type (Union['list[ToffoliDecompType]', ToffoliDecompType]): The type of Toffoli decomposition.
            parallel_toffolis (bool): Flag indicating whether to use parallel Toffoli gates.

        Returns:
            bb.BucketBrigadeDecompType: The decomposition scenario for the bucket brigade.
        """
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
        """
        Tests the bucket brigade circuit with different decomposition scenarios.

        Args:
            dec (Union['list[ToffoliDecompType]', ToffoliDecompType]): The decomposition scenario for the bucket brigade.
            parallel_toffolis (bool): Flag indicating whether to use parallel Toffoli gates for the bucket brigade.
            dec_mod (Union['list[ToffoliDecompType]', ToffoliDecompType]): The modified decomposition scenario for the bucket brigade.
            parallel_toffolis_mod (bool): Flag indicating whether to use parallel Toffoli gates for the modified bucket brigade.
        """
        # ===============REFERENCE==============

        self.decomp_scenario = self.bb_decompose(dec, parallel_toffolis)

        # ================MODDED================

        self.decomp_scenario_modded = self.bb_decompose(
            dec_mod, parallel_toffolis_mod)

        self.run()

    #######################################
    # core functions
    #######################################

    def run(self):
        """
        Runs the experiment for a range of qubits.
        """
        if self.decomp_scenario is None:
            self.rgp("r", "Decomposition scenario is None")
            return
        for i in range(self.start_range_qubits, self.end_range_qubits + 1):
            self.start_range_qubits = i
            self.core()

    def core(self):
        """
        Core function of the experiment.
        """
        qubits: 'list[cirq.NamedQubit]' = []
        for i in range(self.start_range_qubits, self.start_range_qubits + 1):
            nr_qubits = i
            qubits.clear()
            for i in range(nr_qubits):
                qubits.append(cirq.NamedQubit("a" + str(i)))

            self.start_time = time.time()

            self.bbcircuit = bb.BucketBrigade(
                qubits, decomp_scenario=self.decomp_scenario)
            
            self.bbcircuit_modded = bb.BucketBrigade(
                qubits, decomp_scenario=self.decomp_scenario_modded)

            self.stop_time = self.spent_time(self.start_time)

            self.results()

    def results(self):
        """
        Prints the results of the experiment.
        """
        print(f"{'='*150}\n\n")

        self.essential_checks()

        self.simulate_decompositions()

        self.simulate_circuit()

        print(f"\n\n{'='*150}")

    #######################################
    # essential checks methods
    #######################################

    def essential_checks(self):
        """
        Performs essential checks on the experiment.
        """
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
                self.stop_time, process.memory_info().rss,
                process.memory_info().vms),
            flush=True)

        name = "bucket brigade" if self.decomp_scenario.get_decomp_types()[0] == ToffoliDecompType.NO_DECOMP else "reference"
        for decirc in [
            [self.decomp_scenario, self.bbcircuit, name], 
            [self.decomp_scenario_modded, self.bbcircuit_modded, "modded"]
        ]:
            print(
                f"--> decomp scenario of {decirc[2]} circuit:\n"
                "fan_in_decomp:\t\t{}\n"
                "mem_decomp:\t\t{}\n"
                "fan_out_decomp:\t\t{}\n"
                "parallel_toffolis:\t{}\n".format(
                    decirc[0].dec_fan_in,
                    decirc[0].dec_mem,
                    decirc[0].dec_fan_out,
                    "YES !!" if decirc[0].parallel_toffolis else "NO !!"
                ))

            self.check_depth_of_circuit(decirc[1], decirc[0])
            self.printCircuit(decirc[1].circuit, decirc[1].qubit_order, decirc[2])

    def check_depth_of_circuit(self, bbcircuit: bb.BucketBrigade, decomp_scenario: bb.BucketBrigadeDecompType):
        """
        Checks the depth of the circuit decomposition.

        Args:
            decomp_scenario (bb.BucketBrigadeDecompType): The decomposition scenario for the bucket brigade.
        """
        if decomp_scenario.get_decomp_types()[0] != ToffoliDecompType.NO_DECOMP:
            print("\nChecking depth of the circuit decomposition...", end="\n\n")

            print("Number of qubits: ", end="")
            try:
                assert (bbcircuit.verify_number_qubits() == True)
            except Exception:
                self.rgp("r", "Number of qubits failed\n")
            else:
                self.rgp("g", "Number of qubits passed\n")

            print("Depth of the circuit: ", end="")
            try:
                assert (bbcircuit.verify_depth(
                    Alexandru_scenario=self.decomp_scenario.parallel_toffolis) == True)
            except Exception:
                self.rgp("r", "Depth of the circuit failed\n")
            else:
                self.rgp("g", "Depth of the circuit passed\n")

            print("T count: ", end="")
            try:
                assert (bbcircuit.verify_T_count() == True)
            except Exception:
                self.rgp("r", "T count failed\n")
            else:
                self.rgp("g", "T count passed\n")

            print("T depth: ", end="")
            try:
                assert (bbcircuit.verify_T_depth(
                    Alexandru_scenario=self.decomp_scenario.parallel_toffolis) == True)
            except Exception:
                self.rgp("r", "T depth failed\n")
            else:
                self.rgp("g", "T depth passed\n")

            # assert (bbcircuit.verify_hadamard_count(Alexandru_scenario=self.decomp_scenario.parallel_toffolis) == True)
            # assert (bbcircuit.verify_cnot_count(Alexandru_scenario=self.decomp_scenario.parallel_toffolis) == True)

            print("\n")

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
                if decomposition_type == ToffoliDecompType.NO_DECOMP:
                    continue
                self._simulate_decomposition(decomposition_type)

    def _simulate_decomposition(self, decomposition_type: ToffoliDecompType):
        fail:int = 0
        success:int = 0
        total_tests:int = 0

        self.start_time = time.time()
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

        self.printCircuit(circuit, qubits, "decomposition")

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
                    self.rgp("r","Modded circuit result: ")
                    self.rgp("r", str(result), end="\n\n")
                else:
                    self.rgp("r", "•", end="")
            else:
                success += 1
                if self.print_sim:
                    self.rgp("g","Modded circuit result: ")
                    self.rgp("g", str(result), end="\n\n")
                else:
                    self.rgp("g", "•", end="")

            initial_state[i] = 0
            total_tests += 1

        self.stop_time = self.spent_time(self.start_time)
        print("\n\nTime: ", self.stop_time, end="\n\n", flush=True)

        f = format(((fail * 100)/total_tests), ',.2f')
        s = format(((success * 100)/total_tests), ',.2f')

        self.rgp("r", "Failed: ", str(f), "%")
        self.rgp("g", "Succeed: ", str(s), "%")

    #######################################
    # simulate circuit methods
    #######################################

    def simulate_circuit(self):
        # self.simulation_a_qubits()

        # self.simulation_b_qubits()

        # self.simulation_m_qubits()

        self.simulation_full()

    def simulation_a_qubits(self):
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
        print("\nSimulating the circuit ... checking the addressing of the a qubits.", end="\n\n")
        self._simulation(start, stop, step, "a")

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
        print("\nSimulating the circuit ... checking the uncomputation of FANOUT...were the b qubits are returned to their initial state.", end="\n\n")
        self._simulation(start, stop, step, "b")

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
        print("\nSimulating the circuit ... checking the uncomputation of MEM...were the m qubits are returned to their initial state.", end="\n\n")
        self._simulation(start, stop, step, "m")

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
        print("\nSimulating the circuit ... checking the full range of qubits.", end="\n\n")
        self._simulation(start, stop, 1)

    def _simulation(self, start:int, stop:int, step:int, qubit_name:str="full"):
        fail:int = 0
        success:int = 0
        total_tests:int = 0

        self.start_time = time.time()

        # add measurements to the reference circuit ############################################
        measurements = []
        for i in range(len(self.bbcircuit.qubit_order)):
            if qubit_name == "full" or self.bbcircuit.qubit_order[i].name.startswith(qubit_name):
                measurements.append(cirq.measure(self.bbcircuit.qubit_order[i]))

        self.bbcircuit.circuit.append(measurements)

        name = "bucket brigade" if self.decomp_scenario.get_decomp_types()[0] == ToffoliDecompType.NO_DECOMP else "reference"
        self.printCircuit(self.bbcircuit.circuit, self.bbcircuit.qubit_order, name)

        ls = [0 for _ in range(2**len(self.bbcircuit.qubit_order))]
        initial_state = np.array(ls, dtype=np.complex64)

        # add measurements to the modded circuit ##############################################
        measurements_modded = []
        for i in range(len(self.bbcircuit.qubit_order)):
            if qubit_name == "full" or self.bbcircuit.qubit_order[i].name.startswith(qubit_name):
                measurements_modded.append(cirq.measure(self.bbcircuit.qubit_order[i]))

        self.bbcircuit_modded.circuit.append(measurements_modded)

        self.printCircuit(self.bbcircuit_modded.circuit, self.bbcircuit_modded.qubit_order, "modded")

        ls_modded = [0 for _ in range(2**len(self.bbcircuit_modded.qubit_order))]
        initial_state_modded = np.array(ls_modded, dtype=np.complex64)

        print("start =", start,"\tstop =", stop,"\tstep =", step, end="\n\n")

        print(f"Modded circuit to be simulated and compared to the {name} circuit:" , end="\n\n") 

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
                print(f"{name} circuit result: ")
                print(str(result))

            try:
                assert (np.array_equal(
                    np.array(np.around(result.final_state)), 
                    np.array(np.around(result_modded.final_state))))
            except Exception:
                fail += 1
                if self.print_sim:
                    self.rgp("r","Modded circuit result: ")
                    self.rgp("r", str(result_modded), end="\n\n")
                else:
                    self.rgp("r", "•", end="")
            else:
                success += 1
                if self.print_sim:
                    self.rgp("g","Modded circuit result: ")
                    self.rgp("g", str(result_modded), end="\n\n")
                else:
                    self.rgp("g", "•", end="")

            initial_state[i] = 0
            initial_state_modded[i] = 0
            total_tests += 1

        self.stop_time = self.spent_time(self.start_time)
        print("\n\nTime of simulation and comparison: ", self.stop_time, end="\n\n", flush=True)

        f = format(((fail * 100)/total_tests), ',.2f')
        s = format(((success * 100)/total_tests), ',.2f')

        self.rgp("r", "Failed: ", str(f), "%")
        self.rgp("g", "Succeed: ", str(s), "%")

    #######################################
    # print circuit method
    #######################################

    def printCircuit(self, circuit: cirq.Circuit, qubits: 'list[cirq.NamedQubit]', name: str = "bucket brigade"):
        if self.print_circuit:
            # Print the circuit
            start = time.time()

            print(f"Print {name} circuit:")
            print(
                circuit.to_text_diagram(
                    # use_unicode_characters=False,
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
