import cirq
import cirq.optimizers
import os
import psutil
import sys
import time

import multiprocessing
import threading

from typing import Union

import qramcircuits.bucket_brigade as bb

from qramcircuits.bucket_brigade import MirrorMethod
from qramcircuits.qram_circuit_simulator import QRAMCircuitSimulator
from qramcircuits.toffoli_decomposition import ToffoliDecompType
from utils.counting_utils import *
from utils.print_utils import *


help: str = """
How to run the main.py file:

Run the following command in the terminal:

    python3 main.py

or by adding arguments:

    python3 main.py y p d 2 2

Arguments:
- arg 1: Simulate Toffoli decompositions and circuit (y/n).
- arg 2: (P) print or (D) display or (H) hide circuits.
- arg 3: (F) full simulation or (D) just dots or (H) hide the simulation.
- arg 4: Start range of qubits, starting from 2.
- arg 5: End range of qubits, should be equal to or greater than the start range.
- additional arg 6: Specific simulation (a, b, m, ab, bm, abm, t).
    leave it empty to simulate the full circuit.
    only for full circuit we compare the output vector.
"""


#######################################
# QRAM Circuit Experiments
#######################################

class QRAMCircuitExperiments:
    """
    A class used to represent the QRAM circuit experiments.

    Attributes:
        __simulate (bool): Flag indicating whether to simulate Toffoli decompositions and circuit.
        __print_circuit (bool): Flag indicating whether to print the circuits.
        __print_sim (str): Flag indicating whether to print the full simulation result.
        __start_range_qubits (int): Start range of qubits.
        __end_range_qubits (int): End range of qubits.
        __start_time (float): Start time of the experiment.
        __stop_time (str): Stop time of the experiment.
        __decomp_scenario (bb.BucketBrigadeDecompType): Decomposition scenario for the bucket brigade.
        __decomp_scenario_modded (bb.BucketBrigadeDecompType): Modified decomposition scenario for the bucket brigade.
        __bbcircuit (bb.BucketBrigade): Bucket brigade circuit.
        __bbcircuit_modded (bb.BucketBrigade): Modified bucket brigade circuit.
        __simulator (cirq.Simulator): Cirq simulator.
        __specific_simulation (str): Specific simulation for specific qubit wire.
        __simulated (bool): Flag indicating whether the circuit has been simulated.

    Methods:
        __init__(): Initializes the QRAMCircuitExperiments class.
        __del__(): Destructs the QRAMCircuitExperiments class.
        __get_input(): Gets user input for the experiment.
        __bb_decompose(): Decomposes the Toffoli gates in the bucket brigade circuit.
        bb_decompose_test(): Tests the bucket brigade circuit with different decomposition scenarios.
        __run(): Runs the experiment for a range of qubits.
        __core(): Core function of the experiment.
        __results(): Prints the results of the experiment.
        __essential_checks(): Performs essential checks on the experiment.
        __verify_circuit_depth_count(): Verifies the depth and count of the circuit.
        __bilan(): Collect the bilan of the experiment.
        __print_bilan(): Prints the bilan of the experiment.
        __simulate_circuit(): Simulates the circuit.
    """

    _simulate: bool = False
    _print_circuit: str = "Hide"
    _print_sim: str = "Hide"
    _start_range_qubits: int
    _end_range_qubits: int
    _specific_simulation: str = "full"
    _simulated: bool = False

    _start_time: float = 0
    _stop_time: str = ""

    _data: multiprocessing.managers.DictProxy = multiprocessing.Manager().dict()
    _data_modded: multiprocessing.managers.DictProxy = multiprocessing.Manager().dict()
    _simulation_bilan: list = []
    _decomp_scenario: bb.BucketBrigadeDecompType
    _decomp_scenario_modded: bb.BucketBrigadeDecompType
    _bbcircuit: bb.BucketBrigade
    _bbcircuit_modded: bb.BucketBrigade
    _Simulator: QRAMCircuitSimulator


    def __init__(self):
        """
        Constructor the QRAMCircuitExperiments class.
        """

        self.__get_input()

        colpr("y", "Hello QRAM circuit experiments!", end="\n\n")

        colpr("c", f"Simulate Toffoli decompositions and circuit: {'yes' if self._simulate else 'no'}")
        colpr("c", f"{self._print_circuit} circuits")
        colpr("c", f"{self._print_sim} simulation results")
        colpr("c", f"Start Range of Qubits: {self._start_range_qubits}")
        colpr("c", f"End Range of Qubits: {self._end_range_qubits}")

        if self._simulate:
            if self._specific_simulation == "full":
                colpr("c", f"Simulate full circuit")
            else:
                colpr("c", f"Simulate Specific Measurement: {self._specific_simulation}")
        print("\n")

    def __del__(self):
        """
        Destructor of the QRAMCircuitExperiments class.
        """

        colpr("y", "Goodbye QRAM circuit experiments!")

    def __get_input(self) -> None:
        """
        Gets user input for the experiment.
        """

        flag = True
        msg0 = "Start range of qubits must be greater than 1"
        msg1 = "End range of qubits must be greater than start range of qubits or equal to it"
        msg2 = "Specific simulation must be (a, b, m, ab, bm, abm, t), by default it is full circuit"
        len_argv = 6
        
        try:
            if len(sys.argv) == len_argv or len(sys.argv) == len_argv + 1:
                if sys.argv[1].lower() in ["y", "yes"]:
                    self._simulate = True

                if sys.argv[2].lower() == "p":
                    self._print_circuit = "Print"
                elif sys.argv[2].lower() == "d":
                    self._print_circuit = "Display"

                if sys.argv[3].lower() == "d":
                    self._print_sim = "Dot"
                elif sys.argv[3].lower() == "f":
                    self._print_sim = "Full"

                self._start_range_qubits = int(sys.argv[4])
                if self._start_range_qubits < 2:
                    colpr("r", msg0, end="\n\n")
                    raise Exception

                self._end_range_qubits = int(sys.argv[5])
                if self._end_range_qubits < self._start_range_qubits:
                    self._end_range_qubits = self._start_range_qubits

                if len(sys.argv) == len_argv + 1 and self._simulate:
                    if str(sys.argv[6]) not in ['a', 'b', 'm', "ab", "bm", "abm", "t"]:
                        colpr("r", msg2, end="\n\n")
                        raise Exception
                    self._specific_simulation = str(sys.argv[6])
        except Exception:
            flag = False
            colpr("y", help, end="\n\n")

        if not flag or len(sys.argv) < len_argv or len_argv + 1 < len(sys.argv) :
            while True:
                user_input = input("Simulate Toffoli decompositions and circuit? (y/n): ").lower()
                if user_input in ["y", "yes"]:
                    self._simulate = True
                    break
                elif user_input in ["n", "no"]:
                    self._simulate = False
                    break
                else:
                    print("Invalid input. Please enter 'y' or 'n'.")

            while True:
                var = input("(p) print or (d) display or (h) hide circuits: ").lower()
                if var == "p":
                    self._print_circuit = "Print"
                    break
                elif var == "d":
                    self._print_circuit = "Display"
                    break
                elif var == "h":
                    self._print_circuit = "Hide"
                    break
                else:
                    print("Invalid input. Please enter 'p', 'd', or 'h'.")

            if self._simulate:
                while True:
                    user_input = input("Print the full simulation result (f) or just the dot (d) or hide (h)? ").lower()
                    if user_input == "f":
                        self._print_sim = "Full"
                        break
                    elif user_input == "d":
                        self._print_sim = "Dot"
                        break
                    elif user_input == "h":
                        self._print_sim = "Hide"
                        break
                    else:
                        print("Invalid input. Please enter 'f', 'd', or 'h'.")

            self._start_range_qubits = int(input("Start range of qubits: "))
            while self._start_range_qubits < 2:
                colpr("r", msg0, end="\n\n")
                self._start_range_qubits = int(input("Start range of qubits: "))

            self._end_range_qubits = int(input("End range of qubits: "))
            while self._end_range_qubits < self._start_range_qubits:
                colpr("r", msg1, end="\n\n")
                self._end_range_qubits = int(input("End range of qubits: "))

            if self._simulate:            
                while True:
                    user_input = input("Simulate specific measurement for specific qubits wires? (y/n): ").lower()
                    if user_input in ["y", "yes"]:
                        while self._specific_simulation not in ['a', 'b', 'm', "ab", "bm", "abm", "t"]:
                            self._specific_simulation = input("Choose specific qubits wires (a, b, m, ab, bm, abm, abmt, t): ").lower()
                        break
                    elif user_input in ["n", "no"]:
                        break
                    else:
                        print("Invalid input. Please enter 'y' or 'n'.")

    #######################################
    # decomposition methods
    #######################################

    def __bb_decompose(
            self,
            toffoli_decomp_type: Union['list[ToffoliDecompType]', ToffoliDecompType],
            parallel_toffolis: bool,
            mirror_method: MirrorMethod = MirrorMethod.NO_MIRROR
    ) -> bb.BucketBrigadeDecompType:
        """
        Decomposes the Toffoli gates in the bucket brigade circuit.

        Args:
            toffoli_decomp_type (Union['list[ToffoliDecompType]', ToffoliDecompType]): The type of Toffoli decomposition.
            parallel_toffolis (bool): Flag indicating whether to use parallel toffolis.
            mirror_method (bool): Flag indicating whether to mirror the input to the output.

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
                parallel_toffolis=parallel_toffolis,
                mirror_method=mirror_method
            )
        else:
            return bb.BucketBrigadeDecompType(
                toffoli_decomp_types=[
                    toffoli_decomp_type,    # fan_in_decomp
                    toffoli_decomp_type,    # mem_decomp
                    toffoli_decomp_type     # fan_out_decomp
                ],
                parallel_toffolis=parallel_toffolis,
                mirror_method=mirror_method
            )

    def bb_decompose_test(
            self,
            dec: Union['list[ToffoliDecompType]', ToffoliDecompType],
            parallel_toffolis: bool,

            dec_mod: Union['list[ToffoliDecompType]', ToffoliDecompType],
            parallel_toffolis_mod: bool,
            mirror_method: MirrorMethod = MirrorMethod.NO_MIRROR
    ) -> None:
        """
        Tests the bucket brigade circuit with different decomposition scenarios.

        Args:
            dec (Union['list[ToffoliDecompType]', ToffoliDecompType]): The decomposition scenario for the bucket brigade.
            parallel_toffolis (bool): Flag indicating whether to use parallel toffolis for the bucket brigade.
            dec_mod (Union['list[ToffoliDecompType]', ToffoliDecompType]): The modified decomposition scenario for the bucket brigade.
            parallel_toffolis_mod (bool): Flag indicating whether to use parallel toffolis for the modified bucket brigade.
            mirror_method (bool): Flag indicating whether to mirror the input to the output.

        Returns:
            None
        """

        # ===============REFERENCE==============

        self._decomp_scenario = self.__bb_decompose(
            dec, 
            parallel_toffolis, 
            mirror_method
        )

        # ================MODDED================

        self._decomp_scenario_modded = self.__bb_decompose(
            dec_mod, 
            parallel_toffolis_mod,
            mirror_method
        )

        self._run()

    #######################################
    # core functions
    #######################################

    def _run(self) -> None:
        """
        Runs the experiment for a range of qubits.
        """

        if self._decomp_scenario is None:
            colpr("r", "Decomposition scenario is None")
            return

        for i in range(self._start_range_qubits, self._end_range_qubits + 1):
            self._start_range_qubits = i
            self._simulated = False
            self._core(i, "results")

        # This is for final bilan from 2 qubits to 8 qubits
        self._start_range_qubits = 2
        self._end_range_qubits = 7

        # Reset data for multiple tests on series
        self._data = multiprocessing.Manager().dict()
        self._data_modded = multiprocessing.Manager().dict()

        stop_event = threading.Event()
        loading_thread = threading.Thread(target=loading_animation, args=(stop_event, 'bilan',))
        loading_thread.start()

        try:
            for i in range(self._start_range_qubits, self._end_range_qubits + 1):
                self._core(i, state="bilan")
        finally:
            stop_event.set()
            loading_thread.join()

        self.__print_bilan()

    def _core(self, nr_qubits: int, state: str) -> None:
        """
        Core function of the experiment.
        """

        qubits: 'list[cirq.NamedQubit]' = []

        qubits.clear()
        for i in range(nr_qubits):
            qubits.append(cirq.NamedQubit("a" + str(i)))

        # prevent from simulate the circuit if the number of qubits is greater than 4
        if nr_qubits > 4:
            self._simulate = False

        self._start_time = time.time()

        # Use multiprocessing.Pool to parallelize the construction
        with multiprocessing.Pool(processes=2) as pool:
            results = pool.starmap(bb.BucketBrigade, [
                (qubits, self._decomp_scenario),
                (qubits, self._decomp_scenario_modded)
            ])

        # Retrieve the results
        self._bbcircuit, self._bbcircuit_modded = results

        self._stop_time = elapsed_time(self._start_time)

        if state == "bilan":
            self.__bilan(nr_qubits=nr_qubits)
        elif state == "results":
            self._results()
        else:
            return

    def _results(self) -> None:
        """
        Prints the results of the experiment.
        """

        print(f"{'='*150}\n\n")

        self._Simulator = QRAMCircuitSimulator(
            self._bbcircuit,
            self._bbcircuit_modded,
            self._specific_simulation,
            self._start_range_qubits,
            self._print_circuit,
            self._print_sim
        )

        if not self._simulate:
            self.__essential_checks()
        elif self._simulate:
            self._simulate_circuit()

        print(f"\n\n{'='*150}")

    #######################################
    # essential checks methods
    #######################################

    def __essential_checks(self) -> None:
        """
        Performs essential checks on the experiment.
        """

        process = psutil.Process(os.getpid())

        """
        rss: aka “Resident Set Size”, this is the non-swapped physical memory a process has used. On UNIX it matches “top“‘s RES column).
        vms: aka “Virtual Memory Size”, this is the total amount of virtual memory used by the process. On UNIX it matches “top“‘s VIRT column.
        """

        colpr(
            "c",
            "Bucket Brigade circuit creation:\n"
            "\t• {:<1} Qbits\n"
            "\t• Time elapsed on creation: {:<12}\n"
            "\t• RSS (Memory Usage): {:<10}\n"
            "\t• VMS (Memory Usage): {:<10}".format(
                self._start_range_qubits,
                self._stop_time,
                format_bytes(process.memory_info().rss),
                format_bytes(process.memory_info().vms)),
            end="\n\n")

        name = "bucket brigade" if self._decomp_scenario.get_decomp_types()[0] == ToffoliDecompType.NO_DECOMP else "reference"
        for decirc in [
            [self._decomp_scenario, self._bbcircuit, name], 
            [self._decomp_scenario_modded, self._bbcircuit_modded, "modded"]
        ]:
            colpr("y", f"Decomposition scenario of {decirc[2]} circuit:", end="\n\n")
            print(
                "\t• fan_in_decomp: \t{}\n"
                "\t• mem_decomp:    \t{}\n"
                "\t• fan_out_decomp:\t{}\n\n".format(
                    decirc[0].dec_fan_in,
                    decirc[0].dec_mem,
                    decirc[0].dec_fan_out
                ))

            colpr("y", f"Optimization methods of {decirc[2]} circuit:", end="\n\n")
            print(
                "\t• parallel_toffolis:\t{}\n"
                "\t• mirror_method:    \t{}\n\n".format(
                    "YES !!" if decirc[0].parallel_toffolis else "NO !!",
                    decirc[0].mirror_method
                ))

            for decomposition_type in self._Simulator._fan_in_mem_out(decirc[0]):
                if decomposition_type == ToffoliDecompType.NO_DECOMP:
                    continue
                circuit, qubits = self._Simulator._create_decomposition_circuit(decomposition_type)
                printCircuit(self._print_circuit, circuit, qubits, f"decomposition {str(decomposition_type)}")

            self.__verify_circuit_depth_count(decirc[0], decirc[1], decirc[2])
            printCircuit(self._print_circuit, decirc[1].circuit, decirc[1].qubit_order, decirc[2])

    def __verify_circuit_depth_count(
            self, 
            decomp_scenario: bb.BucketBrigadeDecompType,
            bbcircuit: bb.BucketBrigade, 
            name: str
    ) -> None:
        """
        Verifies the depth and count of the circuit.

        Args:
            decomp_scenario (bb.BucketBrigadeDecompType): The decomposition scenario for the bucket brigade.
            bbcircuit (bb.BucketBrigade): Bucket brigade circuit.
            name (str): The name of the circuit.

        Returns:
            None
        """

        # Collect data for multiple qubit configurations
        data = []
        
        colpr("y", f"Verifying the depth and count of the {name} circuit:", end="\n\n")
    
        num_qubits = len(bbcircuit.circuit.all_qubits())
        circuit_depth = len(bbcircuit.circuit)
    
        if decomp_scenario.get_decomp_types()[0] == ToffoliDecompType.NO_DECOMP:
            data.append([self._start_range_qubits, num_qubits, circuit_depth, '-', '-', '-'])
        else:
            t_depth = count_t_depth_of_circuit(bbcircuit.circuit)
            t_count = count_t_of_circuit(bbcircuit.circuit)
            hadamard_count = count_h_of_circuit(bbcircuit.circuit)
            data.append([self._start_range_qubits, num_qubits, circuit_depth, t_depth, t_count, hadamard_count])

        # Create the Markdown table
        table = "| Qubits Range     | Number of Qubits | Depth of the Circuit | T Depth          | T Count          | Hadamard Count    |\n"
        table += "|------------------|------------------|----------------------|------------------|------------------|-------------------|\n"
        
        for row in data:
            table += f"| {row[0]:<16} | {row[1]:<16} | {row[2]:<20} | {row[3]:<16} | {row[4]:<16} | {row[5]:<17} |\n"

        print(table)

    def __bilan(self, nr_qubits: int) -> None:
        """
        Collect the bilan of the experiment
        """

        process = psutil.Process(os.getpid())

        if self._decomp_scenario.dec_fan_in != ToffoliDecompType.NO_DECOMP:

            num_qubits = len(self._bbcircuit.circuit.all_qubits())
            circuit_depth = len(self._bbcircuit.circuit)

            t_depth = count_t_depth_of_circuit(self._bbcircuit.circuit)
            t_count = count_t_of_circuit(self._bbcircuit.circuit)
            hadamard_count = count_h_of_circuit(self._bbcircuit.circuit)

            self._data[nr_qubits] = [
                nr_qubits,
                num_qubits,
                circuit_depth,
                t_depth,
                t_count,
                hadamard_count
            ]

        num_qubits = len(self._bbcircuit_modded.circuit.all_qubits())
        circuit_depth = len(self._bbcircuit_modded.circuit)

        t_depth = count_t_depth_of_circuit(self._bbcircuit_modded.circuit)
        t_count = count_t_of_circuit(self._bbcircuit_modded.circuit)
        hadamard_count = count_h_of_circuit(self._bbcircuit_modded.circuit)

        rss = format_bytes(process.memory_info().rss)
        vms = format_bytes(process.memory_info().vms)
        
        self._data_modded[nr_qubits] = [
            nr_qubits,
            num_qubits,
            circuit_depth,
            t_depth,
            t_count,
            hadamard_count,
            self._stop_time,
            rss,
            vms
        ]

    def __print_bilan(self) -> None:
        """
        Prints the bilan of the experiment.
        """

        colpr("y", "\n\nBilan of the experiment:", end="\n\n")

        # Bilan of essential checks
        colpr("b", "Creation of the Bucket Brigade Circuits:", end="\n\n")
        table = "| Qubits Range     | Elapsed Time               | RSS (Memory Usage)     | VMS (Memory Usage)     |\n"
        table += "|------------------|----------------------------|------------------------|------------------------|\n"

        for x in range(self._start_range_qubits, self._end_range_qubits + 1):
            table += f"| {self._data_modded[x][0]:<16} | {self._data_modded[x][6]:<26} | {self._data_modded[x][7]:<22} | {self._data_modded[x][8]:<22} |\n"

        print(table, end="\n\n")

        # Bilan of simulation circuit
        if self._simulate:
            colpr('b', "Simulation circuit result: ", end="\n\n")

            colpr("r", "\t• Failed: ", str(self._simulation_bilan[0]), "%")
            if str(self._simulation_bilan[4]) == 0:
                colpr("g", "\t• Succeed: ", str(self._simulation_bilan[1]), "%", end="\n\n")
            else:
                colpr("y", "\t• Succeed: ", str(self._simulation_bilan[1]), "%", end="\t( ")
                colpr("b", "Measurements: ", str(self._simulation_bilan[2]), "%", end=" • ")
                colpr("g", "Output vector: ", str(self._simulation_bilan[3]), "%", end=" )\n\n")

        # Bilan of the reference circuit
        if self._decomp_scenario.dec_fan_in != ToffoliDecompType.NO_DECOMP:
            colpr("b", "Reference circuit bilan:", end="\n\n")

            table = "| Qubits Range     | Number of Qubits | Depth of the Circuit | T Depth          | T Count          | Hadamard Count    |\n"
            table += "|------------------|------------------|----------------------|------------------|------------------|-------------------|\n"

            for x in range(self._start_range_qubits, self._end_range_qubits + 1):
                table += f"| {self._data[x][0]:<16} | {self._data[x][1]:<16} | {self._data[x][2]:<20} | {self._data[x][3]:<16} | {self._data[x][4]:<16} | {self._data[x][5]:<17} |\n"

            print(table, end="\n\n")

        # Bilan of the modded circuit
        colpr("b", "Modded circuit bilan:", end="\n\n")
        table = "| Qubits Range     | Number of Qubits | Depth of the Circuit | T Depth          | T Count          | Hadamard Count    |\n"
        table += "|------------------|------------------|----------------------|------------------|------------------|-------------------|\n"

        for x in range(self._start_range_qubits, self._end_range_qubits + 1):
            table += f"| {self._data_modded[x][0]:<16} | {self._data_modded[x][1]:<16} | {self._data_modded[x][2]:<20} | {self._data_modded[x][3]:<16} | {self._data_modded[x][4]:<16} | {self._data_modded[x][5]:<17} |\n"

        print(table, end="\n\n")

        # Comparing bilans
        if self._decomp_scenario.dec_fan_in != ToffoliDecompType.NO_DECOMP:

            def calculate(i: int, j: int) -> 'tuple[str, str]':
                modded_percent = format(((self._data_modded[i][j] / self._data[i][j]) * 100), ',.2f')
                modded = str(self._data_modded[i][j]) + f"  ( {modded_percent} )"
                cancelled_percent = format((100 - eval(modded_percent)), ',.2f')
                cancelled = str(self._data[i][j] - self._data_modded[i][j]) + f"  ( {cancelled_percent} )"

                return modded, cancelled

            colpr("y", "Comparing bilans", end="\n\n")

            colpr("b", "T count comparison:", end="\n\n")
            table = "| Qubits Range     | T Count Reference  | T Count Modded (%) | T Count Cancelled (%)  |\n"
            table += "|------------------|--------------------|--------------------|------------------------|\n"

            for i in range(self._start_range_qubits, self._end_range_qubits + 1):
                modded, cancelled = calculate(i, 4)
                table += f"| {self._data[i][0]:<16} | {self._data[i][4]:<18} | {modded :<18} | {cancelled:<22} |\n"

            print(table, end="\n\n")

            colpr("b", "T depth comparison:", end="\n\n")
            table = "| Qubits Range     | T Depth Reference  | T Depth Modded (%) | T Depth Cancelled (%)  |\n"
            table += "|------------------|--------------------|--------------------|------------------------|\n"

            for i in range(self._start_range_qubits, self._end_range_qubits + 1):
                modded, cancelled = calculate(i, 3)
                table += f"| {self._data[i][0]:<16} | {self._data[i][3]:<18} | {modded :<18} | {cancelled:<22} |\n"

            print(table, end="\n\n")

            colpr("b", "Depth of the circuit comparison:", end="\n\n")
            table = "| Qubits Range     | Depth Reference    | Depth Modded (%)   | Depth Cancelled (%)    |\n"
            table += "|------------------|--------------------|--------------------|------------------------|\n"

            for i in range(self._start_range_qubits, self._end_range_qubits + 1):
                modded, cancelled = calculate(i, 2)
                table += f"| {self._data[i][0]:<16} | {self._data[i][2]:<18} | {modded :<18} | {cancelled:<22} |\n"

            print(table, end="\n\n")

    #######################################
    # simulate circuit method
    #######################################

    def _simulate_circuit(self) -> None:
        """
        Simulates the circuit.
        """

        if self._simulated:
            return
        self._simulated = True

        self._Simulator._run_simulation()

        self._simulation_bilan = self._Simulator.get_simulation_bilan()
