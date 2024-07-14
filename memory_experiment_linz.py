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
        __simulate (bool): Flag indicating whether to simulate Toffoli decompositions.
        __print_circuit (bool): Flag indicating whether to print the circuits.
        __print_sim (bool): Flag indicating whether to print the full simulation result.
        __start_range_qubits (int): Start range of qubits.
        __end_range_qubits (int): End range of qubits.
        __start_time (float): Start time of the experiment.
        __stop_time (str): Stop time of the experiment.
        __decomp_scenario (bb.BucketBrigadeDecompType): Decomposition scenario for the bucket brigade.
        __decomp_scenario_modded (bb.BucketBrigadeDecompType): Modified decomposition scenario for the bucket brigade.
        __bbcircuit (bb.BucketBrigade): Bucket brigade circuit.
        __bbcircuit_modded (bb.BucketBrigade): Modified bucket brigade circuit.
        __simulator (cirq.Simulator): Cirq simulator.
        __additional_simulation (str): Additional simulation for specific qubit wire.
        __simulated (bool): Flag indicating whether the circuit has been simulated.

    Methods:
        __init__(): Initializes the MemoryExperiment class.
        __del__(): Destructs the MemoryExperiment class.
        __get_input(): Gets user input for the experiment.
        __bb_decompose(): Decomposes the Toffoli gates in the bucket brigade circuit.
        bb_decompose_test(): Tests the bucket brigade circuit with different decomposition scenarios.
        __run(): Runs the experiment for a range of qubits.
        __core(): Core function of the experiment.
        __results(): Prints the results of the experiment.
        __essential_checks(): Performs essential checks on the experiment.
        __check_depth_of_circuit(): Checks the depth of the circuit decomposition.
        __fan_in_mem_out(): Returns the fan-in, memory, and fan-out decomposition types.
        __simulate_decompositions(): Simulates the Toffoli decompositions.
        __simulate_decomposition(): Simulates a Toffoli decomposition.
        __simulation_a_qubits(): Simulates the addressing of the a qubits.
        __simulation_b_qubits(): Simulates the uncomputation of FANOUT.
        __simulation_m_qubits(): Simulates the uncomputation of MEM.
        __simulation_full(): Simulates the full range of qubits.
        __simulation(): Simulates the circuit.
        __printCircuit(): Prints the circuit.
        __colpr(): Prints colored text.
        __spent_time(): Calculates the spent time.
    """

    __simulate: bool = False
    __print_circuit: bool = False
    __print_sim: bool = False
    __start_range_qubits: int
    __end_range_qubits: int
    __additional_simulation: str = ""
    __simulated: bool = False

    __start_time: float = 0
    __stop_time: str = ""

    __decomp_scenario: bb.BucketBrigadeDecompType
    __decomp_scenario_modded: bb.BucketBrigadeDecompType
    __bbcircuit: bb.BucketBrigade
    __bbcircuit_modded: bb.BucketBrigade
    __simulator: cirq.Simulator = cirq.Simulator()


    def __init__(self):
        """
        Constructor the MemoryExperiment class.
        """

        self.__get_input()

        print("Hello QRAM circuit experiments!")
        print("Print the Circuit: {}, Start Range of Qubits: {}, End Range of Qubits: {}".format(
            "yes" if self.__print_circuit else "no",
            self.__start_range_qubits,
            self.__end_range_qubits
        ))

    def __del__(self):
        """
        Destructor of the MemoryExperiment class.
        """

        print("Memory experiment is done!")

    def __get_input(self) -> None:
        """
        Gets user input for the experiment.

        Args:
            None

        Returns:
            None
        """

        flag = True
        msg0 = "Start range of qubits must be greater than 1"
        msg1 = "End range of qubits must be greater than start range of qubits or equal to it"
        len_argv = 6

        if len(sys.argv) == len_argv or len(sys.argv) == len_argv + 1:
            if sys.argv[1].lower() in ["y", "yes"]:
                self.__simulate = True

            if sys.argv[2].lower() in ["y", "yes"]:
                self.__print_circuit = True

            if sys.argv[3].lower() in ["y", "yes"]:
                self.__print_sim = True

            self.__start_range_qubits = int(sys.argv[4])
            if self.__start_range_qubits < 2:
                print(msg0)
                flag = False

            self.__end_range_qubits = int(sys.argv[5])
            if self.__end_range_qubits < self.__start_range_qubits:
                self.__end_range_qubits = self.__start_range_qubits

            if len(sys.argv) == len_argv + 1:
                self.__additional_simulation += str(sys.argv[6])

        if flag == False or len(sys.argv) < len_argv or len_argv + 1 < len(sys.argv) :
            if input("Simulate Toffoli decompositions and circuit? (y/n): ").lower() in ["y", "yes"]:
                self.__simulate = True

            if input("Print circuits? (y/n): ").lower() in ["y", "yes"]:
                self.__print_circuit = True

            if input("Print full simulation result? (y/n): ").lower() in ["y", "yes"]:
                self.__print_sim = True

            self.__start_range_qubits = int(input("Start range of qubits: "))
            while self.__start_range_qubits < 2:
                print(msg0)
                self.__start_range_qubits = int(input("Start range of qubits: "))

            self.__end_range_qubits = int(input("End range of qubits: "))
            while self.__end_range_qubits < self.__start_range_qubits:
                print(msg1)
                self.__end_range_qubits = int(input("End range of qubits: "))

            if self.__simulate:
                self.__additional_simulation = input("Choose additional simulation for specific qubit wire (a, b, m): ")
                for c in "abm":
                    if c not in self.__additional_simulation:
                        self.__additional_simulation = input("Choose additional simulation for specific qubit wire (a, b, m): ")

    #######################################
    # decomposition methods
    #######################################

    def __bb_decompose(
        self,
        toffoli_decomp_type: Union['list[ToffoliDecompType]', ToffoliDecompType],
        parallel_toffolis: bool
    ) -> bb.BucketBrigadeDecompType:
        """
        Decomposes the Toffoli gates in the bucket brigade circuit.

        Args:
            toffoli_decomp_type (Union['list[ToffoliDecompType]', ToffoliDecompType]): The type of Toffoli decomposition.
            parallel_toffolis (bool): Flag indicating whether to use parallel toffolis.

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
    ) -> None:
        """
        Tests the bucket brigade circuit with different decomposition scenarios.

        Args:
            dec (Union['list[ToffoliDecompType]', ToffoliDecompType]): The decomposition scenario for the bucket brigade.
            parallel_toffolis (bool): Flag indicating whether to use parallel toffolis for the bucket brigade.
            dec_mod (Union['list[ToffoliDecompType]', ToffoliDecompType]): The modified decomposition scenario for the bucket brigade.
            parallel_toffolis_mod (bool): Flag indicating whether to use parallel toffolis for the modified bucket brigade.
        
        Returns:
            None
        """

        # ===============REFERENCE==============

        self.__decomp_scenario = self.__bb_decompose(dec, parallel_toffolis)

        # ================MODDED================

        self.__decomp_scenario_modded = self.__bb_decompose(
            dec_mod, parallel_toffolis_mod)

        self.__run()

    #######################################
    # core functions
    #######################################

    def __run(self) -> None:
        """
        Runs the experiment for a range of qubits.

        Args:
            None

        Returns:
            None
        """

        if self.__decomp_scenario is None:
            self.__colpr("r", "Decomposition scenario is None")
            return
        for i in range(self.__start_range_qubits, self.__end_range_qubits + 1):
            self.__start_range_qubits = i
            self.__simulated = False
            self.__core()

    def __core(self) -> None:
        """
        Core function of the experiment.

        Args:
            None

        Returns:
            None
        """

        qubits: 'list[cirq.NamedQubit]' = []
        for i in range(self.__start_range_qubits, self.__start_range_qubits + 1):
            nr_qubits = i
            qubits.clear()
            for i in range(nr_qubits):
                qubits.append(cirq.NamedQubit("a" + str(i)))
            
            # prevent from simulate the circuit if the number of qubits is greater than 4
            if nr_qubits > 4:
                self.__simulate = False

            self.__start_time = time.time()

            self.__bbcircuit = bb.BucketBrigade(
                qubits, decomp_scenario=self.__decomp_scenario)
            
            self.__bbcircuit_modded = bb.BucketBrigade(
                qubits, decomp_scenario=self.__decomp_scenario_modded)

            self.__stop_time = self.__spent_time(self.__start_time)

            self.__results()

    def __results(self) -> None:
        """
        Prints the results of the experiment.

        Args:
            None
        
        Returns:
            None
        """

        print(f"{'='*150}\n\n")

        self.__essential_checks()

        self.__simulate_decompositions()

        self.__simulate_circuit()

        print(f"\n\n{'='*150}")

    #######################################
    # essential checks methods
    #######################################

    def __essential_checks(self) -> None:
        """
        Performs essential checks on the experiment.

        Args:
            None

        Returns:
            None
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
                self.__start_range_qubits,
                self.__stop_time, process.memory_info().rss,
                process.memory_info().vms),
            flush=True)

        name = "bucket brigade" if self.__decomp_scenario.get_decomp_types()[0] == ToffoliDecompType.NO_DECOMP else "reference"
        for decirc in [
            [self.__decomp_scenario, self.__bbcircuit, name], 
            [self.__decomp_scenario_modded, self.__bbcircuit_modded, "modded"]
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

            self.__check_depth_of_circuit(decirc[1], decirc[0])
            self.__printCircuit(decirc[1].circuit, decirc[1].qubit_order, decirc[2])

    def __check_depth_of_circuit(
            self, 
            bbcircuit: bb.BucketBrigade, 
            decomp_scenario: bb.BucketBrigadeDecompType
    ) -> None:
        """
        Checks the depth of the circuit decomposition.

        Args:
            decomp_scenario (bb.BucketBrigadeDecompType): The decomposition scenario for the bucket brigade.
        
        Returns:
            None
        """
        print("\nChecking depth of the circuit decomposition...", end="\n\n")

        print("Number of qubits: ", end="")
        try:
            assert (bbcircuit.verify_number_qubits() == True)
        except Exception:
            self.__colpr("v", "Number of qubits not as expected\n")
        else:
            self.__colpr("g", "Number of qubits passed\n")

        print("Depth of the circuit: ", end="")
        try:
            assert (bbcircuit.verify_depth(
                Alexandru_scenario=self.__decomp_scenario.parallel_toffolis) == True)
        except Exception:
            self.__colpr("v", "Depth of the circuit not as expected\n")
        else:
            self.__colpr("g", "Depth of the circuit passed\n")

        if decomp_scenario.get_decomp_types()[0] != ToffoliDecompType.NO_DECOMP:

            print("T count: ", end="")
            try:
                assert (bbcircuit.verify_T_count() == True)
            except Exception:
                self.__colpr("v", "T count not as expected\n")
            else:
                self.__colpr("g", "T count passed\n")

            print("T depth: ", end="")
            try:
                assert (bbcircuit.verify_T_depth(
                    Alexandru_scenario=self.__decomp_scenario.parallel_toffolis) == True)
            except Exception:
                self.__colpr("v", "T depth not as expected\n")
            else:
                self.__colpr("g", "T depth passed\n")

            # assert (bbcircuit.verify_hadamard_count(Alexandru_scenario=self.decomp_scenario.parallel_toffolis) == True)
            # assert (bbcircuit.verify_cnot_count(Alexandru_scenario=self.decomp_scenario.parallel_toffolis) == True)

            print("\n")

    #######################################
    # simulate decompositions methods
    #######################################

    def __fan_in_mem_out(
            self, 
            decomp_scenario: bb.BucketBrigadeDecompType
    ) -> 'list[ToffoliDecompType]':
        """
        Returns the fan-in, memory, and fan-out decomposition types.

        Args:
            decomp_scenario (bb.BucketBrigadeDecompType): The decomposition scenario for the bucket brigade.

        Returns:
            'list[ToffoliDecompType]': The fan-in, memory, and fan-out decomposition types.
        """

        return list(set(decomp_scenario.get_decomp_types()))

    def __simulate_decompositions(self) -> None:
        """
        Simulates the Toffoli decompositions.

        Args:
            None

        Returns:
            None
        """

        if not self.__simulate:
            return

        for decomp_scenario in [self.__decomp_scenario, self.__decomp_scenario_modded]:
            for decomposition_type in self.__fan_in_mem_out(decomp_scenario):
                if decomposition_type == ToffoliDecompType.NO_DECOMP:
                    continue
                self.__simulate_decomposition(decomposition_type)

    def __simulate_decomposition(self, decomposition_type: ToffoliDecompType) -> None:
        """
        Simulates a Toffoli decomposition.

        Args:
            decomposition_type (ToffoliDecompType): The type of Toffoli decomposition.
        
        Returns:
            None
        """

        fail:int = 0
        success:int = 0
        total_tests:int = 0

        self.__start_time = time.time()
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

        self.__printCircuit(circuit, qubits, "decomposition")

        ls = [0 for _ in range(2**len(qubits))]
        initial_state = np.array(ls, dtype=np.complex64)

        for i in range(8):
            initial_state[i] = 1
            result = self.__simulator.simulate(
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
                if self.__print_sim:    
                    self.__colpr("r","Modded circuit result: ")
                    self.__colpr("r", str(result), end="\n\n")
                else:
                    self.__colpr("r", "•", end="")
            else:
                success += 1
                if self.__print_sim:
                    self.__colpr("g","Modded circuit result: ")
                    self.__colpr("g", str(result), end="\n\n")
                else:
                    self.__colpr("g", "•", end="")

            initial_state[i] = 0
            total_tests += 1

        self.__stop_time = self.__spent_time(self.__start_time)
        print("\n\nTime spent on the decomposition simulation: ", self.__stop_time, end="\n\n", flush=True)

        f = format(((fail * 100)/total_tests), ',.2f')
        s = format(((success * 100)/total_tests), ',.2f')

        self.__colpr("r", "Failed: ", str(f), "%")
        self.__colpr("g", "Succeed: ", str(s), "%")

    #######################################
    # simulate circuit methods
    #######################################

    def __simulate_circuit(self) -> None:
        """
        Simulates the circuit.

        Args:
            None

        Returns:
            None
        """

        if not self.__simulate:
            return

        self.__simulation_a_qubits()

        self.__simulation_b_qubits()

        self.__simulation_m_qubits()

        self.__simulation_full()

    def __simulation_a_qubits(self) -> None:
        """
        Simulates the addressing of the a qubits.

        Args:
            None

        Returns:
            None
        """

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

        if "a" not in self.__additional_simulation:
            return
        start = 0
        # step = 2**(2**self.start_range_qubits+1) * (2**(2**self.start_range_qubits))
        step = 2 ** ( 2 * ( 2 ** self.__start_range_qubits ) + 1 )
        stop = step * ( 2 ** self.__start_range_qubits )
        print("\nSimulating the circuit ... checking the addressing of the a qubits.", end="\n\n")
        self.__simulation(start, stop, step, "a")

    def __simulation_b_qubits(self) -> None:
        """
        Simulates the uncomputation of FANOUT.

        Args:
            None
        
        Returns:
            None
        """

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

        if "b" not in self.__additional_simulation:
            return
        start = 0
        step = 2 ** ( 2 ** self.__start_range_qubits + 1 )
        stop = step * ( 2 ** ( 2 ** self.__start_range_qubits ) )
        print("\nSimulating the circuit ... checking the uncomputation of FANOUT...were the b qubits are returned to their initial state.", end="\n\n")
        self.__simulation(start, stop, step, "b")

    def __simulation_m_qubits(self) -> None:
        """
        Simulates the uncomputation of MEM.

        Args:
            None
        
        Returns:
            None
        """

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

        if "m" not in self.__additional_simulation:
            return
        start = 0
        step = 2
        stop = step * ( 2 ** ( 2 ** self.__start_range_qubits ) )
        print("\nSimulating the circuit ... checking the uncomputation of MEM...were the m qubits are returned to their initial state.", end="\n\n")
        self.__simulation(start, stop, step, "m")

    def __simulation_full(self) -> None:
        """
        Simulates the full range of qubits.

        Args:
            None
        
        Returns:
            None
        """

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
        stop = 2 ** ( 2 * ( 2 ** self.__start_range_qubits ) + self.__start_range_qubits + 1 )
        print("\nSimulating the circuit ... checking the full range of qubits.", end="\n\n")
        self.__simulation(start, stop, 1)

    def __simulation(self, start:int, stop:int, step:int, qubit_name:str="full") -> None:
        """
        Simulates the circuit.

        Args:
            start (int): The start index.
            stop (int): The stop index.
            step (int): The step index.
            qubit_name (str): The name of the qubit.
        
        Returns:
            None
        """

        if self.__simulated:
            return
        self.__simulated = True

        fail:int = 0
        success:int = 0
        total_tests:int = 0

        self.__start_time = time.time()

        # add measurements to the reference circuit ############################################
        measurements = []
        for qubit in self.__bbcircuit.qubit_order:
            if qubit_name == "full" or qubit.name.startswith(qubit_name):
                measurements.append(cirq.measure(qubit))

        self.__bbcircuit.circuit.append(measurements)

        name = "bucket brigade" if self.__decomp_scenario.get_decomp_types()[0] == ToffoliDecompType.NO_DECOMP else "reference"
        self.__printCircuit(self.__bbcircuit.circuit, self.__bbcircuit.qubit_order, name)

        ls = [0 for _ in range(2**len(self.__bbcircuit.qubit_order))]
        initial_state = np.array(ls, dtype=np.complex64)

        # add measurements to the modded circuit ##############################################
        measurements_modded = []
        for qubit in self.__bbcircuit_modded.qubit_order:
            if qubit_name == "full" or qubit.name.startswith(qubit_name):
                measurements_modded.append(cirq.measure(qubit))

        self.__bbcircuit_modded.circuit.append(measurements_modded)

        self.__printCircuit(self.__bbcircuit_modded.circuit, self.__bbcircuit_modded.qubit_order, "modded")

        ls_modded = [0 for _ in range(2**len(self.__bbcircuit_modded.qubit_order))]
        initial_state_modded = np.array(ls_modded, dtype=np.complex64)

        print("start =", start,"\tstop =", stop,"\tstep =", step, end="\n\n")

        print(f"Modded circuit to be simulated and compared to the {name} circuit:" , end="\n\n") 

        for i in range(start, stop, step):
            initial_state[i] = 1
            initial_state_modded[i] = 1

            result = self.__simulator.simulate(
                self.__bbcircuit.circuit,
                qubit_order=self.__bbcircuit.qubit_order,
                initial_state=initial_state
            )

            result_modded = self.__simulator.simulate(
                self.__bbcircuit_modded.circuit,
                qubit_order=self.__bbcircuit_modded.qubit_order,
                initial_state=initial_state_modded
            )

            if qubit_name == "full":
                if self.__print_sim:
                    print("index =", str(i))
                    print(f"{name} circuit result: ")
                    print(result)

                try:
                    assert (np.array_equal(
                        np.array(np.around(result.final_state[i])), 
                        np.array(np.around(result_modded.final_state[i]))))
                except Exception:
                    fail += 1
                    if self.__print_sim:
                        self.__colpr("r","Modded circuit result: ")
                        self.__colpr("r", str(result_modded), end="\n\n")
                    else:
                        self.__colpr("r", "•", end="")
                else:
                    success += 1
                    if self.__print_sim:
                        self.__colpr("g","Modded circuit result: ")
                        self.__colpr("g", str(result_modded), end="\n\n")
                    else:
                        self.__colpr("g", "•", end="")

            elif qubit_name in "abm":
                # Extract specific measurements
                measurements = result.measurements
                measurements_modded = result_modded.measurements

                if self.__print_sim:
                    print("index =", str(i))
                    print(f"{name} circuit measurements:")
                    self.__colpr("w","measurements: ", end="")
                    for qubit in measurements.keys():
                        m = str(measurements.get(qubit, np.array([]))[0])
                        self.__colpr("w", qubit, "=", m, end=" ")
                    print("")

                try:
                    # Compare specific measurements
                    for qubit in measurements.keys():
                        assert np.array_equal(
                            measurements.get(qubit, np.array([])),
                            measurements_modded.get(qubit, np.array([]))
                        )
                except Exception:
                    fail += 1
                    if self.__print_sim:
                        self.__colpr("r","Modded circuit measurements: ")
                        self.__colpr("r","measurements: ", end="")
                        for qubit in measurements_modded.keys():
                            m = str(measurements_modded.get(qubit, np.array([]))[0])
                            self.__colpr("r", qubit, "=", m, end=" ")
                        print("\n")
                    else:
                        self.__colpr("r", "•", end="")
                else:
                    success += 1
                    if self.__print_sim:
                        self.__colpr("g","Modded circuit measurements: ")
                        self.__colpr("g","measurements: ", end="")
                        for qubit in measurements_modded.keys():
                            m = str(measurements_modded.get(qubit, np.array([]))[0])
                            self.__colpr("g", qubit, "=", m, end=" ")
                        print("\n")
                    else:
                        self.__colpr("g", "•", end="")

            initial_state[i] = 0
            initial_state_modded[i] = 0
            total_tests += 1

        self.__stop_time = self.__spent_time(self.__start_time)
        print("\n\nTime of simulation and comparison: ", self.__stop_time, end="\n\n", flush=True)

        f = format(((fail * 100)/total_tests), ',.2f')
        s = format(((success * 100)/total_tests), ',.2f')

        self.__colpr("r", "Failed: ", str(f), "%")
        self.__colpr("g", "Succeed: ", str(s), "%")

    #######################################
    # print circuit method
    #######################################

    def __printCircuit(
            self, 
            circuit: cirq.Circuit, 
            qubits: 'list[cirq.NamedQubit]', 
            name: str = "bucket brigade"
    ) -> None:
        """
        Prints the circuit.

        Args:
            circuit (cirq.Circuit): The circuit to be printed.
            qubits ('list[cirq.NamedQubit]'): The qubits of the circuit.
            name (str): The name of the circuit.
        
        Returns:
            None
        """

        if self.__print_circuit:
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

            stop = self.__spent_time(start)
            print("Time of printing the circuit: ", stop, "\n")

    #######################################
    # static methods
    #######################################

    @ staticmethod
    def __colpr(color: str, *args, end="\n") -> None:
        """
        Prints colored text.

        Args:
            color (str): The color of the text [r, g, v, b, y, c, w, m, k, d, u].
            args (str): The text to be printed.
            end (str): The end character.
        
        Returns:
            None
        """

        colors = {
            "r": "\033[91m",
            "g": "\033[92m",
            "v": "\033[95m",
            "b": "\033[94m",
            "y": "\033[93m",
            "c": "\033[96m",
            "w": "\033[97m",
            "m": "\033[95m",
            "k": "\033[90m",
            "d": "\033[2m",
            "u": "\033[4m"
        }
        print(colors[color] + "".join(args) + "\033[0m", flush=True, end=end)

    @ staticmethod
    def __spent_time(start: float) -> str:
        """
        Calculates the spent time.

        Args:
            start (float): The start time.

        Returns:
            str: The spent time.
        """

        elapsed_time = time.time() - start
        formatted_time = time.strftime("%M:%S", time.gmtime(elapsed_time))
        milliseconds = (elapsed_time - int(elapsed_time)) * 1000
        final_output = f"{formatted_time},{int(milliseconds)}"
        return final_output


#######################################
# main function
#######################################

def main():
    """
    Main function of the experiment.
    """

    qram: MemoryExperiment = MemoryExperiment()

    """
        The Bucket brigade decomposition described in the paper.
        Depth of the circuit decomposition is 30 for 2 qubits and 45 for 3 qubits WITH parallel toffolis.
        ? Simulation not passed.
    """
    # qram.bb_decompose_test(
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
        Depth of the circuit decomposition is 46 for 2 qubits WITH parallel toffolis.
        Simulation passed.
    """
    # qram.bb_decompose_test(
    #     ToffoliDecompType.NO_DECOMP,
    #     False,
    #     ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
    #     True
    # )

    # qram.bb_decompose_test(
    #     ToffoliDecompType.NO_DECOMP,
    #     False,
    #     ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4_TEST,
    #     True
    # )

    """
        The Bucket brigade all controlled V, 𝑉† and X decompositions (QC5).
        Depth of the circuit decomposition is 46 for 2 qubits WITHOUT parallel toffolis.
        Simulation passed.
    """
    # for i in range(8):
    #     qram.bb_decompose_test(
    #         ToffoliDecompType.NO_DECOMP,
    #         False,
    #         eval(f"ToffoliDecompType.CV_CX_QC5_{i}"),
    #         False
    #     )

    """
        The Bucket brigade all controlled V, 𝑉† and X decompositions (QC5) for the FANIN and FANOUT AND standard 7-T gate decomposition (QC10) for QUERY (mem).
        ! Depth of the circuit decomposition is 36 for 2 qubits and 68 for 3 qubits WITH parallel toffolis.
        ! After eliminating the T gates, the depth of the T gate stabilizes at 4 for all numbers of qubits, and the depth of the circuit decomposition is 34 for 2 qubits and 62 for 3 qubits WITH parallel toffolis.
        Simulation passed.
    """
    # for i in [0, 2, 5, 7]:
    #     qram.bb_decompose_test(
    #         ToffoliDecompType.NO_DECOMP,
    #         False,
    #         [
    #             eval(f"ToffoliDecompType.CV_CX_QC5_{i}"),
    #             ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
    #             eval(f"ToffoliDecompType.CV_CX_QC5_{i}"),
    #         ],
    #         True
    #     )

    """
        The Bucket brigade all controlled V, 𝑉† and X decompositions (QC5) for the FANIN and FANOUT AND standard 7-T gate decomposition (QC10) for QUERY (mem).
        ! Depth of the circuit decomposition is 34 for 2 qubits and 63 for 3 qubits WITH parallel toffolis.
        ! After eliminating the T gates, the depth of the T gate stabilizes at 4 for all numbers of qubits, and the depth of the circuit decomposition is 32 for 2 qubits and 57 for 3 qubits WITH parallel toffolis.
        Simulation passed.
    """
    for i in [1, 3, 4, 6]:
        qram.bb_decompose_test(
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
        Depth of the circuit decomposition is 46 for 2 qubits WITHOUT parallel toffolis.
        Simulation passed.
    """
    # qram.bb_decompose_test(
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
    # qram.bb_decompose_test(
    #     ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
    #     True,
    #     [
    #         eval(f"ToffoliDecompType.CV_CX_QC5_{rd.randint(0, 7)}"),
    #         eval(f"ToffoliDecompType.CV_CX_QC5_{rd.randint(0, 7)}"),
    #         eval(f"ToffoliDecompType.CV_CX_QC5_{rd.randint(0, 7)}")
    #     ],
    #     False
    # )


if __name__ == "__main__":
    main()
