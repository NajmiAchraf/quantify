import cirq
import cirq.optimizers
import math
import numpy as np
import os
import psutil
import sys
import time

from IPython.display import display
from cirq.contrib.svg import SVGCircuit, circuit_to_svg
from typing import Union

import qramcircuits.bucket_brigade as bb
from qramcircuits.bucket_brigade import MirrorMethod
from qramcircuits.toffoli_decomposition import ToffoliDecompType, ToffoliDecomposition
from utils.counting_utils import *


help: str = """
How to run the QRAMCircuitExperiments.py file:

Run the following command in the terminal:

    python3 QRAMCircuitExperiments.py

or by adding arguments:

    python3 QRAMCircuitExperiments.py y y n 2 2

Arguments:
- arg 1: Simulate Toffoli decompositions and circuit (y/n).
- arg 2: (P) print or (D) display or (H hide) circuits.
- arg 3: Print full simulation result (y/n).
- arg 4: Start range of qubits, starting from 2.
- arg 5: End range of qubits, should be equal to or greater than the start range.
- additional arg 6: Specific simulation (a, b, m, ab, bm, abm, abmt, t).
    leave it empty to simulate the full circuit.
    only for full circuit we compare the output vector.
"""


class QRAMCircuitExperiments:
    """
    A class used to represent the QRAM circuit experiments.

    Attributes:
        __simulate (bool): Flag indicating whether to simulate Toffoli decompositions and circuit.
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
        __fan_in_mem_out(): Returns the fan-in, memory, and fan-out decomposition types.
        __create_decomposition_circuit(): Creates a Toffoli decomposition circuit.
        __decomposed_circuit(): Creates a Toffoli decomposition with measurements circuit.
        __simulate_decompositions(): Simulates the Toffoli decompositions.
        __simulate_decomposition(): Simulates a Toffoli decomposition.
        __simulate_circuit(): Simulates the circuit.
        _simulation_a_qubits(): Simulates the circuit and measure addressing of the a qubits.
        _simulation_b_qubits(): Simulates the circuit and measure uncomputation of FANOUT.
        _simulation_m_qubits(): Simulates the circuit and measure computation of MEM.
        _simulation_ab_qubits(): Simulates the circuit and measure addressing and uncomputation of the a and b qubits.
        _simulation_bm_qubits(): Simulates the circuit and measure computation and uncomputation of the b and m qubits.
        _simulation_abm_qubits(): Simulates the circuit and measure addressing and uncomputation and computation of the a, b, and m qubits.
        _simulation_abmt_qubits(): Simulates the circuit and measure addressing and uncomputation and computation of the a, b, m, and target qubits.
        _simulation_t_qubits(): Simulates the addressing and uncomputation and computation of the a, b, and m qubits and measure only the target qubit.
        _simulation_full_qubits(): Simulates the circuit and measure all full circuit.
        __simulation(): Simulates the circuit.
        __simulate_and_compare(): Simulate and compares the results of the simulation and measurement.
        __printCircuit(): Prints the circuit.
        __colpr(): Prints colored text.
        __spent_time(): Calculates the spent time.
    """

    __simulate: bool = False
    __print_circuit: str = "Hide"
    __print_sim: bool = False
    __start_range_qubits: int
    __end_range_qubits: int
    __specific_simulation: str = "full"
    __simulated: bool = False

    __start_time: float = 0
    __stop_time: str = ""

    __data: list = []
    __data_modded: list = []
    __simulation_results: list = []
    __decomp_scenario: bb.BucketBrigadeDecompType
    __decomp_scenario_modded: bb.BucketBrigadeDecompType
    __bbcircuit: bb.BucketBrigade
    __bbcircuit_modded: bb.BucketBrigade
    __simulator: cirq.Simulator = cirq.Simulator()


    def __init__(self):
        """
        Constructor the QRAMCircuitExperiments class.
        """

        self.__get_input()

        self.__colpr("y", "Hello QRAM circuit experiments!", end="\n\n")

        self.__colpr("c", f"Simulate Toffoli decompositions and circuit: {'yes' if self.__simulate else 'no'}")
        self.__colpr("c", f"{self.__print_circuit} circuits")
        self.__colpr("c", f"Print the full simulation result: {'yes' if self.__print_sim else 'no'}")
        self.__colpr("c", f"Start Range of Qubits: {self.__start_range_qubits}")
        self.__colpr("c", f"End Range of Qubits: {self.__end_range_qubits}")

        if self.__simulate:
            if self.__specific_simulation == "full":
                self.__colpr("c", f"Simulate full circuit")
            else:
                self.__colpr("c", f"Simulate Specific Measurement: {self.__specific_simulation}")
        print("\n")

    def __del__(self):
        """
        Destructor of the QRAMCircuitExperiments class.
        """

        self.__colpr("y", "Goodbye QRAM circuit experiments!")

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
        msg2 = "Specific simulation must be (a, b, m, ab, bm, abm, abmt, t), by default it is full circuit"
        len_argv = 6
        
        try:
            if len(sys.argv) == len_argv or len(sys.argv) == len_argv + 1:
                if sys.argv[1].lower() in ["y", "yes"]:
                    self.__simulate = True

                if sys.argv[2].lower() == "p":
                    self.__print_circuit = "Print"
                elif sys.argv[2].lower() == "d":
                    self.__print_circuit = "Display"

                if sys.argv[3].lower() in ["y", "yes"]:
                    self.__print_sim = True

                self.__start_range_qubits = int(sys.argv[4])
                if self.__start_range_qubits < 2:
                    self.__colpr("r", msg0, end="\n\n")
                    raise Exception

                self.__end_range_qubits = int(sys.argv[5])
                if self.__end_range_qubits < self.__start_range_qubits:
                    self.__end_range_qubits = self.__start_range_qubits

                if len(sys.argv) == len_argv + 1 and self.__simulate:
                    if str(sys.argv[6]) not in ['a', 'b', 'm', "ab", "bm", "abm", "abmt", "t"]:
                        self.__colpr("r", msg2, end="\n\n")
                        raise Exception
                    self.__specific_simulation = str(sys.argv[6])
        except Exception:
            flag = False
            self.__colpr("y", help, end="\n\n")

        if not flag or len(sys.argv) < len_argv or len_argv + 1 < len(sys.argv) :
            while True:
                user_input = input("Simulate Toffoli decompositions and circuit? (y/n): ").lower()
                if user_input in ["y", "yes"]:
                    self.__simulate = True
                    break
                elif user_input in ["n", "no"]:
                    self.__simulate = False
                    break
                else:
                    print("Invalid input. Please enter 'y' or 'n'.")

            while True:
                var = input("(p) print or (d) display or (h) hide circuits: ").lower()
                if var == "p":
                    self.__print_circuit = "Print"
                    break
                elif var == "d":
                    self.__print_circuit = "Display"
                    break
                elif var == "h":
                    self.__print_circuit = "Hide"
                    break
                else:
                    print("Invalid input. Please enter 'p', 'd', or 'h'.")

            if self.__simulate:
                while True:
                    user_input = input("Print full simulation result? (y/n): ").lower()
                    if user_input in ["y", "yes"]:
                        self.__print_sim = True
                        break
                    elif user_input in ["n", "no"]:
                        self.__print_sim = False
                        break
                    else:
                        print("Invalid input. Please enter 'y' or 'n'.")

            self.__start_range_qubits = int(input("Start range of qubits: "))
            while self.__start_range_qubits < 2:
                self.__colpr("r", msg0, end="\n\n")
                self.__start_range_qubits = int(input("Start range of qubits: "))

            self.__end_range_qubits = int(input("End range of qubits: "))
            while self.__end_range_qubits < self.__start_range_qubits:
                self.__colpr("r", msg1, end="\n\n")
                self.__end_range_qubits = int(input("End range of qubits: "))

            if self.__simulate:            
                while True:
                    user_input = input("Simulate specific measurement for specific qubits wires? (y/n): ").lower()
                    if user_input in ["y", "yes"]:
                        while self.__specific_simulation not in ['a', 'b', 'm', "ab", "bm", "abm", "abmt", "t"]:
                            self.__specific_simulation = input("Choose specific qubits wires (a, b, m, ab, bm, abm, abmt, t): ").lower()
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

        self.__decomp_scenario = self.__bb_decompose(
            dec, 
            parallel_toffolis, 
            mirror_method
        )

        # ================MODDED================

        self.__decomp_scenario_modded = self.__bb_decompose(
            dec_mod, 
            parallel_toffolis_mod,
            mirror_method
        )

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
            self.__core(False)

        # This is for final bilan from 2 qubits to 6 qubits
        self.__start_range_qubits = 2
        self.__end_range_qubits = 6

        # Clear data for multiple tests on series
        self.__data.clear()
        self.__data_modded.clear()

        for i in range(self.__start_range_qubits, self.__end_range_qubits + 1):
            self.__start_range_qubits = i
            self.__core(True)
        self.__print_bilan()

    def __core(self, bilan: bool) -> None:
        """
        Core function of the experiment.

        Args:
            None

        Returns:
            None
        """

        qubits: 'list[cirq.NamedQubit]' = []

        nr_qubits = self.__start_range_qubits

        qubits.clear()
        for i in range(nr_qubits):
            qubits.append(cirq.NamedQubit("a" + str(i)))

        # prevent from simulate the circuit if the number of qubits is greater than 4
        if nr_qubits > 4:
            self.__simulate = False

        self.__start_time = time.time()

        self.__bbcircuit = bb.BucketBrigade(
            qubits=qubits, 
            decomp_scenario=self.__decomp_scenario)

        self.__bbcircuit_modded = bb.BucketBrigade(
            qubits=qubits, 
            decomp_scenario=self.__decomp_scenario_modded)

        self.__stop_time = self.__spent_time(self.__start_time)

        if bilan:
            self.__bilan()
        else:
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

        if self.__simulate:
            return

        process = psutil.Process(os.getpid())
        # print("\npid", os.getpid())

        """
        rss: aka “Resident Set Size”, this is the non-swapped physical memory a process has used. On UNIX it matches “top“‘s RES column).
        vms: aka “Virtual Memory Size”, this is the total amount of virtual memory used by the process. On UNIX it matches “top“‘s VIRT column.
        """

        self.__colpr(
            "c",
            "Bucket Brigade circuit creation:\n"
            "\t• {:<1} Qbits\n"
            "\t• Time spent on creation: {:<12}\n"
            "\t• rss: {:<10}\n"
            "\t• vms: {:<10}".format(
                self.__start_range_qubits,
                self.__stop_time, process.memory_info().rss,
                process.memory_info().vms),
            end="\n\n")

        name = "bucket brigade" if self.__decomp_scenario.get_decomp_types()[0] == ToffoliDecompType.NO_DECOMP else "reference"
        for decirc in [
            [self.__decomp_scenario, self.__bbcircuit, name], 
            [self.__decomp_scenario_modded, self.__bbcircuit_modded, "modded"]
        ]:
            self.__colpr("y", f"Decomposition scenario of {decirc[2]} circuit:", end="\n\n")
            print(
                "\t• fan_in_decomp: \t{}\n"
                "\t• mem_decomp:    \t{}\n"
                "\t• fan_out_decomp:\t{}\n\n".format(
                    decirc[0].dec_fan_in,
                    decirc[0].dec_mem,
                    decirc[0].dec_fan_out
                ))

            self.__colpr("y", f"Optimization methods of {decirc[2]} circuit:", end="\n\n")
            print(
                "\t• parallel_toffolis:\t{}\n"
                "\t• mirror_method:    \t{}\n\n".format(
                    "YES !!" if decirc[0].parallel_toffolis else "NO !!",
                    decirc[0].mirror_method
                ))

            for decomposition_type in self.__fan_in_mem_out(decirc[0]):
                if decomposition_type == ToffoliDecompType.NO_DECOMP:
                    continue
                circuit, qubits = self.__create_decomposition_circuit(decomposition_type)
                self.__printCircuit(circuit, qubits, f"decomposition {str(decomposition_type)}")

            self.__verify_circuit_depth_count(decirc[0], decirc[1], decirc[2])
            self.__printCircuit(decirc[1].circuit, decirc[1].qubit_order, decirc[2])

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
        
        self.__colpr("y", f"Verifying the depth and count of the {name} circuit:", end="\n\n")
    
        num_qubits = len(bbcircuit.circuit.all_qubits())
        circuit_depth = len(bbcircuit.circuit)
    
        if decomp_scenario.get_decomp_types()[0] == ToffoliDecompType.NO_DECOMP:
            data.append([self.__start_range_qubits, num_qubits, circuit_depth, '-', '-', '-'])
        else:
            t_depth = count_t_depth_of_circuit(bbcircuit.circuit)
            t_count = count_t_of_circuit(bbcircuit.circuit)
            hadamard_count = count_h_of_circuit(bbcircuit.circuit)
            data.append([self.__start_range_qubits, num_qubits, circuit_depth, t_depth, t_count, hadamard_count])

        # Create the Markdown table
        table = "| Qubits Range     | Number of Qubits | Depth of the Circuit | T Depth          | T Count          | Hadamard Count    |\n"
        table += "|------------------|------------------|----------------------|------------------|------------------|-------------------|\n"
        
        for row in data:
            table += f"| {row[0]:<16} | {row[1]:<16} | {row[2]:<20} | {row[3]:<16} | {row[4]:<16} | {row[5]:<17} |\n"
        
        print(table)

    def __bilan(self) -> None:
        """
        Collect the bilan of the experiment

        Args:
            None

        Returns:
            None
        """

        if self.__decomp_scenario.dec_fan_in != ToffoliDecompType.NO_DECOMP:

            num_qubits = len(self.__bbcircuit.circuit.all_qubits())
            circuit_depth = len(self.__bbcircuit.circuit)

            t_depth = count_t_depth_of_circuit(self.__bbcircuit.circuit)
            t_count = count_t_of_circuit(self.__bbcircuit.circuit)
            hadamard_count = count_h_of_circuit(self.__bbcircuit.circuit)
            
            self.__data.append([
                self.__start_range_qubits,
                num_qubits,
                circuit_depth,
                t_depth,
                t_count,
                hadamard_count
            ])

        num_qubits = len(self.__bbcircuit_modded.circuit.all_qubits())
        circuit_depth = len(self.__bbcircuit_modded.circuit)

        t_depth = count_t_depth_of_circuit(self.__bbcircuit_modded.circuit)
        t_count = count_t_of_circuit(self.__bbcircuit_modded.circuit)
        hadamard_count = count_h_of_circuit(self.__bbcircuit_modded.circuit)
        
        self.__data_modded.append([
            self.__start_range_qubits,
            num_qubits,
            circuit_depth,
            t_depth,
            t_count,
            hadamard_count
        ])

    def __print_bilan(self) -> None:
        """
        Prints the bilan of the experiment.

        Args:
            None

        Returns:
            None
        """

        self.__colpr("y", "\n\nBilan of the experiment", end="\n\n")

        if self.__decomp_scenario.dec_fan_in != ToffoliDecompType.NO_DECOMP:
            self.__colpr("b", "Reference circuit bilan:", end="\n\n")
            # Create the Markdown table
            table = "| Qubits Range     | Number of Qubits | Depth of the Circuit | T Depth          | T Count          | Hadamard Count    |\n"
            table += "|------------------|------------------|----------------------|------------------|------------------|-------------------|\n"

            for row in self.__data:
                table += f"| {row[0]:<16} | {row[1]:<16} | {row[2]:<20} | {row[3]:<16} | {row[4]:<16} | {row[5]:<17} |\n"

            print(table, end="\n\n")

        # Create the Markdown table
        self.__colpr("b", "Modded circuit bilan:", end="\n\n")
        table = "| Qubits Range     | Number of Qubits | Depth of the Circuit | T Depth          | T Count          | Hadamard Count    |\n"
        table += "|------------------|------------------|----------------------|------------------|------------------|-------------------|\n"

        for row in self.__data_modded:
            table += f"| {row[0]:<16} | {row[1]:<16} | {row[2]:<20} | {row[3]:<16} | {row[4]:<16} | {row[5]:<17} |\n"

        print(table, end="\n\n")

        self.__colpr('y', "Simulation circuit result: ", end="\n\n")

        self.__colpr("r", "Failed: ", str(self.__simulation_results[0]), "%")
        self.__colpr("g", "Succeed: ", str(self.__simulation_results[1]), "%", end="\n\n")

        if self.__decomp_scenario.dec_fan_in != ToffoliDecompType.NO_DECOMP:
            self.__colpr("y", "Comparing bilans", end="\n\n")

            self.__colpr("b", "T count comparison:", end="\n\n")
            table = "| Qubits Range     | T Count Reference  | T Count Modded     | T Count Cancelled      |\n"
            table += "|------------------|--------------------|--------------------|------------------------|\n"

            for i in range(len(self.__data)):
                modded_percent = format(((self.__data_modded[i][4] / self.__data[i][4]) * 100), ',.2f')
                modded = str(self.__data_modded[i][4]) + f" ({modded_percent}%)"
                cancelled_percent = format((100 - eval(modded_percent)), ',.2f')
                cancelled = str(self.__data[i][4] - self.__data_modded[i][4]) + f" ({cancelled_percent}%)"

                table += f"| {self.__data[i][0]:<16} | {self.__data[i][4]:<18} | {modded :<18} | {cancelled:<22} |\n"

            print(table, end="\n\n")

            self.__colpr("b", "T depth comparison:", end="\n\n")
            table = "| Qubits Range     | T Depth Reference  | T Depth Modded     | T Depth Cancelled      |\n"
            table += "|------------------|--------------------|--------------------|------------------------|\n"

            for i in range(len(self.__data)):
                modded_percent = format(((self.__data_modded[i][3] / self.__data[i][3]) * 100), ',.2f')
                modded = str(self.__data_modded[i][3]) + f" ({modded_percent}%)"
                cancelled_percent = format((100 - eval(modded_percent)), ',.2f')
                cancelled = str(self.__data[i][3] - self.__data_modded[i][3]) + f" ({cancelled_percent}%)"

                table += f"| {self.__data[i][0]:<16} | {self.__data[i][3]:<18} | {modded :<18} | {cancelled:<22} |\n"

            print(table, end="\n\n")

            self.__colpr("b", "Depth of the circuit comparison:", end="\n\n")
            table = "| Qubits Range     | Depth Reference    | Depth Modded       | Depth Cancelled        |\n"
            table += "|------------------|--------------------|--------------------|------------------------|\n"

            for i in range(len(self.__data)):
                modded_percent = format(((self.__data_modded[i][2] / self.__data[i][2]) * 100), ',.2f')
                modded = str(self.__data_modded[i][2]) + f" ({modded_percent}%)"
                cancelled_percent = format((100 - eval(modded_percent)), ',.2f')
                cancelled = str(self.__data[i][2] - self.__data_modded[i][2]) + f" ({cancelled_percent}%)"

                table += f"| {self.__data[i][0]:<16} | {self.__data[i][2]:<18} | {modded :<18} | {cancelled:<22} |\n"

            print(table, end="\n\n")

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

    def __create_decomposition_circuit(
            self, 
            decomposition_type: ToffoliDecompType
    ) -> 'tuple[cirq.Circuit, list[cirq.NamedQubit]]':
        """
        Creates a Toffoli decomposition circuit.

        Args:
            decomposition_type (ToffoliDecompType): The type of Toffoli decomposition.

        Returns:
            'tuple[cirq.Circuit, list[cirq.NamedQubit]]': The Toffoli decomposition circuit and qubits.
        """
        
        circuit = cirq.Circuit()

        qubits = [cirq.NamedQubit("q" + str(i)) for i in range(3)]

        decomp = ToffoliDecomposition(
            decomposition_type=decomposition_type,
            qubits=qubits)

        if decomp.number_of_ancilla() > 0:
            qubits += [decomp.ancilla[i] for i in range(int(decomp.number_of_ancilla()))]

        circuit.append(decomp.decomposition())

        return circuit, qubits

    def __decomposed_circuit(
            self, 
            decomposition_type: ToffoliDecompType
    ) -> 'tuple[cirq.Circuit, list[cirq.NamedQubit], np.array]':
        """
        Creates a Toffoli decomposition with measurements circuit.

        Args:
            decomposition_type (ToffoliDecompType): The type of Toffoli decomposition.

        Returns:
            'tuple[cirq.Circuit, list[cirq.NamedQubit], np.array]': The Toffoli decomposition circuit, qubits, and initial state.
        """

        circuit, qubits = self.__create_decomposition_circuit(decomposition_type)

        measurements = []
        for qubit in qubits:
            if qubit.name[0] == "q":
                measurements.append(cirq.measure(qubit))

        circuit.append(measurements)
        cirq.optimizers.SynchronizeTerminalMeasurements().optimize_circuit(circuit)

        if decomposition_type != ToffoliDecompType.NO_DECOMP:
            self.__printCircuit(circuit, qubits, f"decomposition {str(decomposition_type)}")

        ls = [0 for _ in range(2**len(qubits))]
        initial_state = np.array(ls, dtype=np.complex64)
    
        return circuit, qubits, initial_state

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

        self.__colpr("y", "\nSimulating the decompositions ... comparing the results of the decompositions to the Toffoli gate.", end="\n\n")

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

        circuit, qubits, initial_state = self.__decomposed_circuit(ToffoliDecompType.NO_DECOMP)
        circuit_modded, qubits_modded, initial_state_modded = self.__decomposed_circuit(decomposition_type)

        nbr_anc = ToffoliDecomposition.numbers_of_ancilla(decomposition_type)

        """ 0 ancilla
            0 0 0 0 -> 0 : start
            0 0 0 0 -> 1 : step
            ...
            0 1 1 1 -> 7
            1 0 0 0 -> 8 : stop
        """
        """ 2 ancilla
            0 0 0 0 0 0 -> 0 : start
            0 0 0 1 0 0 -> 4 : step
            0 0 1 0 0 0 -> 8
            ...
            0 1 1 1 0 0 -> 28
            1 0 0 0 0 0 -> 32 : stop
        """
        start = 0
        step = 2 ** nbr_anc
        stop = 8 * step

        self.__colpr("c", "Simulating the decomposition ... ", str(decomposition_type),  end="\n\n")

        for i in range(start, stop, step):
            j = math.floor(i/step) # reverse the 2 ** nbr_anc binary number

            initial_state[j] = 1
            initial_state_modded[i] = 1

            result = self.__simulator.simulate(
                circuit,
                qubit_order=qubits,
                initial_state=initial_state
            )

            result_modded = self.__simulator.simulate(
                circuit_modded,
                qubit_order=qubits_modded,
                initial_state=initial_state_modded
            )

            # Extract specific measurements
            measurements = result.measurements
            measurements_modded = result_modded.measurements

            if self.__print_sim:
                self.__colpr("c", f"Index of array {j} {i}", end="\n")
                self.__colpr("w", f"Toffoli circuit result: ")
                self.__colpr("w", str(result))

            try:
                # Compare specific measurements for the specific qubits
                for o_qubit in qubits:
                    for qubit in measurements.keys():
                        if str(o_qubit) == str(qubit):
                            assert np.array_equal(
                                measurements.get(qubit, np.array([])),
                                measurements_modded.get(qubit, np.array([]))
                            )
            except Exception:
                fail += 1
                if self.__print_sim:    
                    self.__colpr("r","decomposed toffoli circuit result: ")
                    self.__colpr("r", str(result_modded), end="\n\n")
                else:
                    self.__colpr("r", "•", end="")
            else:
                success += 1
                if self.__print_sim:
                    self.__colpr("g","decomposed toffoli circuit result: ")
                    self.__colpr("g", str(result_modded), end="\n\n")
                else:
                    self.__colpr("g", "•", end="")

            initial_state[j] = 0
            initial_state_modded[i] = 0
            total_tests += 1

        self.__stop_time = self.__spent_time(self.__start_time)

        f = format(((fail * 100)/total_tests), ',.2f')
        s = format(((success * 100)/total_tests), ',.2f')

        self.__colpr("r", "\n\nFailed: ", str(f), "%")
        self.__colpr("g", "Succeed: ", str(s), "%", end="\n\n")

        self.__colpr("w", "Time spent on the decomposition simulation: ", self.__stop_time, end="\n\n")

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

        # Construct the method name
        method_name = f"_simulation_{self.__specific_simulation}_qubits"

        # Get the method from the class instance
        method = getattr(self, method_name, None)

        # Check if the method exists and call it
        if callable(method):
            method()
        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{method_name}'")

    def _simulation_a_qubits(self) -> None:
        """
        Simulates the circuit and measure addressing of the a qubits.

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

        start = 0
        # step = 2**(2**self.start_range_qubits+1) * (2**(2**self.start_range_qubits))
        step = 2 ** ( 2 * ( 2 ** self.__start_range_qubits ) + 1 )
        stop = step * ( 2 ** self.__start_range_qubits )
        self.__colpr("y", "\nSimulating the circuit ... checking the addressing of the a qubits.", end="\n\n")
        self.__simulation(start, stop, step)

    def _simulation_b_qubits(self) -> None:
        """
        Simulates the circuit and measure uncomputation of FANOUT.

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

        start = 0
        step = 2 ** ( 2 ** self.__start_range_qubits + 1 )
        stop = step * ( 2 ** ( 2 ** self.__start_range_qubits ) )
        self.__colpr("y", "\nSimulating the circuit ... checking the uncomputation of FANOUT...were the b qubits are returned to their initial state.", end="\n\n")
        self.__simulation(start, stop, step)

    def _simulation_m_qubits(self) -> None:
        """
        Simulates the circuit and measure computation of MEM.

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
        0 000 00000001 00000000 0 -> 512 : stop
        """

        start = 0
        step = 2
        stop = step * ( 2 ** ( 2 ** self.__start_range_qubits ) )
        self.__colpr("y", "\nSimulating the circuit ... checking the computation of MEM...were the m qubits are getting the result of the computation.", end="\n\n")
        self.__simulation(start, stop, step)

    def _simulation_ab_qubits(self) -> None:
        """
        Simulates the circuit and measure addressing and uncomputation of the a and b qubits.

        Args:
            None

        Returns:
            None
        """

        """ 2
        the range of a and b qubits
        0 00 0000 0000 0 -> 0 : start
        0 00 0001 0000 0 -> 32 : step
        0 00 0010 0000 0 -> 64
        0 00 0011 0000 0 -> 96
        ...
        0 00 1111 0000 0 -> 480
        0 01 0000 0000 0 -> 512
        ...
        0 11 1111 0000 0 -> 2016
        1 00 0000 0000 0 -> 2048 : stop
        """
        """ 3
        the range of a and b qubits
        0 000 00000000 00000000 0 -> 0 : start
        0 000 00000001 00000000 0 -> 512 : step
        ...
        0 000 11111111 00000000 0 -> 65536
        0 001 00000000 00000000 0 -> 131072
        ...
        0 100 11111111 00000000 0 -> 589824
        ...
        1 000 00000000 00000000 0 -> 1048576 : stop
        """

        start = 0
        step_b = 2 ** ( 2 ** self.__start_range_qubits + 1 )

        step_a = 2 ** ( 2 * ( 2 ** self.__start_range_qubits ) + 1 )
        stop = step_a * ( 2 ** self.__start_range_qubits )
        self.__colpr("y", "\nSimulating the circuit ... checking the addressing and uncomputation of the a and b qubits.", end="\n\n")
        self.__simulation(start, stop, step_b)

    def _simulation_bm_qubits(self) -> None:
        """
        Simulates the circuit and measure computation and uncomputation of the b and m qubits.

        Args:
            None

        Returns:
            None
        """

        """ 2
        the range of b and m qubits
        0 00 0000 0000 0 -> 0 : start
        0 00 0000 0001 0 -> 2 : step
        0 00 0000 0010 0 -> 4
        0 00 0000 0011 0 -> 6
        ...
        0 00 0000 1111 0 -> 30
        0 00 0001 0000 0 -> 32
        ...
        0 00 1111 0000 0 -> 480
        0 01 0000 0000 0 -> 512 : stop
        """
        """ 3
        the range of b and m qubits
        0 000 00000000 00000000 0 -> 0 : start
        0 000 00000000 00000001 0 -> 2 : step
        0 000 00000000 00000010 0 -> 4
        0 000 00000000 00000011 0 -> 6
        ...
        0 000 00000000 00001111 0 -> 30
        0 000 00000000 00010000 0 -> 32
        ...
        0 000 00000000 11111111 0 -> 510
        0 000 00000001 00000000 0 -> 512
        ...
        0 000 11111111 00000000 0 -> 65536
        0 001 00000000 00000000 0 -> 131072 : stop
        """

        start = 0
        step_m = 2

        step_b = 2 ** ( 2 ** self.__start_range_qubits + 1 )
        stop = step_b * ( 2 ** ( 2 ** self.__start_range_qubits ) )
        self.__colpr("y", "\nSimulating the circuit ... checking the addressing and uncomputation of the b and m qubits.", end="\n\n")
        self.__simulation(start, stop, step_m)

    def _simulation_abm_qubits(self) -> None:
        """
        Simulates the circuit and measure addressing and uncomputation and computation of the a, b, and m qubits.

        Args:
            None

        Returns:
            None
        """

        """ 2
        the range of a, b, and m qubits
        0 00 0000 0000 0 -> 0 : start
        0 00 0000 0001 0 -> 2 : step
        0 00 0000 0010 0 -> 4
        0 00 0000 0011 0 -> 6
        ...
        0 00 0000 1111 0 -> 30
        0 00 0001 0000 0 -> 32
        ...
        0 00 1111 0000 0 -> 480
        0 01 0000 0000 0 -> 512
        ...
        0 11 1111 0000 0 -> 2016
        1 00 0000 0000 0 -> 2048 : stop
        """
        """ 3
        the range of a, b, and m qubits
        0 000 00000000 00000000 0 -> 0 : start
        0 000 00000000 00000001 0 -> 2 : step
        0 000 00000000 00000010 0 -> 4
        0 000 00000000 00000011 0 -> 6
        ...
        0 000 00000000 00001111 0 -> 30
        0 000 00000000 00010000 0 -> 32
        ...
        0 000 00000000 11111111 0 -> 510
        0 000 00000001 00000000 0 -> 512
        ...
        0 000 11111111 00000000 0 -> 65536
        0 001 00000000 00000000 0 -> 131072
        ...
        0 100 11111111 00000000 0 -> 589824
        ...
        1 000 00000000 00000000 0 -> 1048576 : stop
        """

        start = 0
        step_m = 2
        step_a = 2 ** ( 2 * ( 2 ** self.__start_range_qubits ) + 1 )
        stop = step_a * ( 2 ** self.__start_range_qubits )
        self.__colpr("y", "\nSimulating the circuit ... checking the addressing and uncomputation of the a, b, and m qubits.", end="\n\n")
        self.__simulation(start, stop, step_m)

    def _simulation_abmt_qubits(self) -> None:
        """
        _simulation_abmt_qubits(): Simulates the circuit and measure addressing and uncomputation and computation of the a, b, m, and target qubits.

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
        print("\nSimulating the circuit ... checking the addressing and uncomputation of the a, b, m, and target qubits.", end="\n\n")
        self.__simulation(start, stop, 1)

    def _simulation_t_qubits(self) -> None:
        """
        Simulates the addressing and uncomputation and computation of the a, b, and m qubits and measure only the target qubit.

        Args:
            None

        Returns:
            None
        """

        """ 2
        the range of a, b, and m qubits
        0 00 0000 0000 0 -> 0 : start
        0 00 0000 0001 0 -> 2 : step
        0 00 0000 0010 0 -> 4
        0 00 0000 0011 0 -> 6
        ...
        0 00 0000 1111 0 -> 30
        0 00 0001 0000 0 -> 32
        ...
        0 00 1111 0000 0 -> 480
        0 01 0000 0000 0 -> 512
        ...
        0 11 1111 0000 0 -> 2016
        1 00 0000 0000 0 -> 2048 : stop
        """
        """ 3
        the range of a, b, and m qubits
        0 000 00000000 00000000 0 -> 0 : start
        0 000 00000000 00000001 0 -> 2 : step
        0 000 00000000 00000010 0 -> 4
        0 000 00000000 00000011 0 -> 6
        ...
        0 000 00000000 00001111 0 -> 30
        0 000 00000000 00010000 0 -> 32
        ...
        0 000 00000000 11111111 0 -> 510
        0 000 00000001 00000000 0 -> 512
        ...
        0 000 11111111 00000000 0 -> 65536
        0 001 00000000 00000000 0 -> 131072
        ...
        0 100 11111111 00000000 0 -> 589824
        ...
        1 000 00000000 00000000 0 -> 1048576 : stop
        """

        start = 0
        step_m = 2
        step_a = 2 ** ( 2 * ( 2 ** self.__start_range_qubits ) + 1 )
        stop = step_a * ( 2 ** self.__start_range_qubits )
        print("\nSimulating the circuit ... checking the addressing and uncomputation of the a, b, and m qubits and measure only the target qubit.", end="\n\n")
        self.__simulation(start, stop, step_m)

    def _simulation_full_qubits(self) -> None:
        """
        Simulates the circuit and measure all qubits.

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
        print("\nSimulating the circuit ... checking the all qubits.", end="\n\n")
        self.__simulation(start, stop, 1)

    def __simulation(self, start:int, stop:int, step:int) -> None:
        """
        Simulates the circuit.

        Args:
            start (int): The start index.
            stop (int): The stop index.
            step (int): The step index.

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
            if self.__specific_simulation == "full":
                measurements.append(cirq.measure(qubit))
            else:
                for _name in self.__specific_simulation:
                    if qubit.name.startswith(_name):
                        measurements.append(cirq.measure(qubit))

        self.__bbcircuit.circuit.append(measurements)
        cirq.optimizers.SynchronizeTerminalMeasurements().optimize_circuit(self.__bbcircuit.circuit)

        name = "bucket brigade" if self.__decomp_scenario.get_decomp_types()[0] == ToffoliDecompType.NO_DECOMP else "reference"
        self.__printCircuit(self.__bbcircuit.circuit, self.__bbcircuit.qubit_order, name)

        ls = [0 for _ in range(2**len(self.__bbcircuit.qubit_order))]
        initial_state = np.array(ls, dtype=np.complex64)

        # add measurements to the modded circuit ##############################################
        measurements_modded = []
        for qubit in self.__bbcircuit_modded.qubit_order:
            if self.__specific_simulation == "full":
                measurements_modded.append(cirq.measure(qubit))
            else:
                for _name in self.__specific_simulation:
                    if qubit.name.startswith(_name):
                        measurements_modded.append(cirq.measure(qubit))

        self.__bbcircuit_modded.circuit.append(measurements_modded)
        cirq.optimizers.SynchronizeTerminalMeasurements().optimize_circuit(self.__bbcircuit_modded.circuit)

        self.__printCircuit(self.__bbcircuit_modded.circuit, self.__bbcircuit_modded.qubit_order, "modded")

        ls_modded = [0 for _ in range(2**len(self.__bbcircuit_modded.qubit_order))]
        initial_state_modded = np.array(ls_modded, dtype=np.complex64)

        print("start =", start,"\tstop =", stop,"\tstep =", step, end="\n\n")

        _type = "output vector" if self.__specific_simulation == "full" else "measurements"
        self.__colpr("c", f"Simulating both the modded and {name} circuits and comparing their {_type} ...", end="\n\n")

        for i in range(start, stop, step):
            initial_state[i] = 1
            initial_state_modded[i] = 1

            f, s = self.__simulate_and_compare(i, initial_state, initial_state_modded)
            fail += f
            success += s

            initial_state[i] = 0
            initial_state_modded[i] = 0
            total_tests += 1

        self.__stop_time = self.__spent_time(self.__start_time)

        f = format(((fail * 100)/total_tests), ',.2f')
        s = format(((success * 100)/total_tests), ',.2f')

        self.__colpr("r", "\n\nFailed: ", str(f), "%")
        self.__colpr("g", "Succeed: ", str(s), "%", end="\n\n")

        self.__simulation_results = [f, s]

        self.__colpr("w", "Time spent on simulation and comparison: ", self.__stop_time, end="\n\n")

    def __simulate_and_compare(
            self,
            i: int,
            initial_state: np.ndarray,
            initial_state_modded: np.ndarray
        ) -> 'tuple[int, int]':
        """
        Simulate and compares the results of the simulation.

        Args:
            i (int): The index of the simulation.
            initial_state (np.ndarray): The initial state of the circuit.
            initial_state_modded (np.ndarray): The initial state of the modded circuit.

        Returns:
            int: The number of failed tests.
            int: The number of successful tests.
        """

        fail:int = 0
        success:int = 0

        name = "bucket brigade" if self.__decomp_scenario.get_decomp_types()[0] == ToffoliDecompType.NO_DECOMP else "reference"

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

        # Extract specific measurements
        measurements = result.measurements
        measurements_modded = result_modded.measurements

        if self.__print_sim:
            self.__colpr("c", f"Index of array {i}", end="\n")
            self.__colpr("w", f"{name} circuit result: ")
            self.__colpr("w", str(result))

        try:
            if self.__specific_simulation == "full":
                if self.__print_sim:
                    self.__colpr("c", "Comparing the output vector of the circuits ...", end="\n")
                # Compare final state which is the output vector, only for all qubits
                assert np.array_equal(
                    np.array(np.around(result.final_state[i])),
                    np.array(np.around(result_modded.final_state[i]))
                )
            else:
                if self.__print_sim:
                    self.__colpr("c", "Comparing the measurements of the circuits ...", end="\n")
                # Compare specific measurements for the specific qubits
                for o_qubit in self.__bbcircuit.qubit_order:
                    for qubit in measurements.keys():
                        if str(o_qubit) == str(qubit):
                            assert np.array_equal(
                                measurements.get(qubit, np.array([])),
                                measurements_modded.get(qubit, np.array([]))
                            )
        except Exception:
            fail += 1
            if self.__print_sim:
                self.__colpr("r", "Modded circuit result: ")
                self.__colpr("r", str(result_modded), end="\n\n")
            else:
                self.__colpr("r", "•", end="")
        else:
            success += 1
            if self.__print_sim:
                self.__colpr("g", "Modded circuit result: ")
                self.__colpr("g", str(result_modded), end="\n\n")
            else:
                self.__colpr("g", "•", end="")

        return (fail, success)

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

        if self.__print_circuit == "Print":
            # Print the circuit
            start = time.time()

            self.__colpr("c", f"Print {name} circuit:" , end="\n\n")
            print(
                circuit.to_text_diagram(
                    # use_unicode_characters=False,
                    qubit_order=qubits
                ),
                end="\n\n"
            )

            stop = self.__spent_time(start)
            self.__colpr("w", "Time of printing the circuit: ", stop, end="\n\n")

        elif self.__print_circuit == "Display":
            # Display the circuit
            start = time.time()

            self.__colpr("c", f"Display {name} circuit:" , end="\n\n")

            display(SVGCircuit(circuit))

            stop = self.__spent_time(start)
            self.__colpr("w", "Time of displaying the circuit: ", stop, end="\n\n")

        # # Save the circuit as an SVG file
        # with open(f"images/{self.__start_range_qubits}_{name}_circuit.svg", "w") as f:
        #     f.write(sv.circuit_to_svg(circuit))

    #######################################
    # static methods
    #######################################

    @ staticmethod
    def __colpr(color: str, *args: str, end: str="\n") -> None:
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
        hms = "%H:%M:%S"
        if elapsed_time < 60:
            hms = "%S"
        elif elapsed_time < 3600:
            hms = "%M:%S"
        formatted_time = time.strftime(hms, time.gmtime(elapsed_time))
        milliseconds = (elapsed_time - int(elapsed_time)) * 1000
        final_output = f"{formatted_time},{int(milliseconds)}"
        return final_output


#######################################
# main function
#######################################

def main():
    """
    Main function of the experiments.
    """

    qram: QRAMCircuitExperiments = QRAMCircuitExperiments()

    # 18701s (5h 11m 41s) to simulate 3 qubits and still not finished
    """ #! THE ORIGINAL BUCKET BRIGADE DECOMPOSITION (THE SECOND BEST)
    (0) ~ The Bucket brigade decomposition described in the paper with standard 7-T gate decomposition (QC10) for QUERY (mem) and the relative phase Toffoli decomposition (TD 4 CX 4) for FANIN and mirror the input to the output for FANOUT.
        * parallel toffolis: #! NOT FULLY SIMULATED
            #*    Depth |  Circuit  |  T Gate  | Count of T Gates
            #* 2 qubits |    30     |    10    |        36
            #* 3 qubits |    45     |    18    |        80
            #* 4 qubits |    64     |    31    |       168
            #* 5 qubits |    91     |    53    |       344
            #* 6 qubits |   134     |    92    |       696
        * parallel toffolis && cancel ngh T gates in all qubits : #! NOT FULLY SIMULATED
            #*    Depth |  Circuit  |  T Gate  | Count of T Gates
            #* 2 qubits |    27     |     8    |        32
            #* 3 qubits |    38     |    12    |        72
            #* 4 qubits |    49     |    17    |       152
            #* 5 qubits |    60     |    23    |       312
            #* 6 qubits |    71     |    30    |       632
        * parallel toffolis && cancel ngh T gates in all qubits same fans: #! FULLY SIMULATED
            #*    Depth |  Circuit  |  T Gate  | Count of T Gates
            #* 2 qubits |    33     |    13    |        40
            #* 3 qubits |    52     |    24    |        96
            #* 4 qubits |    71     |    36    |       208
            #* 5 qubits |    90     |    49    |       432
            #* 6 qubits |   109     |    63    |       880
        * parallel toffolis && cancel ngh T gates in all qubits && mirror the input to the output:
            #*    Depth |  Circuit  |  T Gate  | Count of T Gates
            #* 2 qubits |    32     |    12    |        40
            #* 3 qubits |    46     |    20    |        96
            #* 4 qubits |    60     |    30    |       208
            #* 5 qubits |    74     |    42    |       432
            #* 6 qubits |    88     |    56    |       880
        * parallel toffolis && cancel ngh T gates in all qubits && mirror the input to the output && stratify decompositions:
            #*    Depth |  Circuit  |  T Gate  | Count of T Gates
            #* 2 qubits |    36     |    13    |        40
            #* 3 qubits |    50     |    17    |        96
            #* 4 qubits |    64     |    21    |       208
            #* 5 qubits |    78     |    25    |       432
            #* 6 qubits |    92     |    29    |       880
            #* 7 qubits |   106     |    33    |      1776
        * parallel toffolis && cancel ngh T gates in all qubits && mirror the input to the output && stratify decompositions and circuit:
            #*    Depth |  Circuit  |  T Gate  | Count of T Gates
            #* 2 qubits |    35     |    13    |        40
            #* 3 qubits |    49     |    17    |        96
            #* 4 qubits |    63     |    21    |       208
            #* 5 qubits |    77     |    25    |       432
            #* 6 qubits |    91     |    29    |       880
            #* 7 qubits |   105     |    33    |      1776
    """
    # qram.bb_decompose_test(
    #     dec=ToffoliDecompType.NO_DECOMP,
    #     parallel_toffolis=False,

    #     dec_mod=[
    #         ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4_COMPUTE,
    #         ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
    #         ToffoliDecompType.ZERO_ANCILLA_TDEPTH_0_UNCOMPUTE,
    #     ],
    #     parallel_toffolis_mod=True,
    #     mirror_method=MirrorMethod.IN_TO_OUT #! BY DEFAULT IS NO_MIRROR
    # )

    # qram.bb_decompose_test(
    #     dec=ToffoliDecompType.NO_DECOMP,
    #     parallel_toffolis=False,

    #     dec_mod=[
    #         ToffoliDecompType.RELATIVE_PHASE_TD_4_CX_4, #! SIMILAR TO TDEPTH_4_COMPUTE
    #         ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
    #         # ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4_INV,
    #         ToffoliDecompType.RELATIVE_PHASE_TD_4_CX_4,
    #     ],
    #     parallel_toffolis_mod=True,
    #     mirror_method=MirrorMethod.IN_TO_OUT
    # )

    """#! THE BUCKET BRIGADE DECOMPOSITION (THE BEST ONE)
    (1) ~ The Bucket brigade standard 7-T gate decomposition (QC10) for QUERY (mem) and the relative phase Toffoli decomposition (TD 4 CX 3) for FANOUT and mirror the output to the input for FANIN.
        * parallel toffolis && cancel ngh T gates in all qubits && stratify decompositions and circuit:
            #*    Depth |  Circuit  |  T Gate  | Count of T Gates
            #* 2 qubits |    34     |    13    |        40
            #* 3 qubits |    49     |    18    |        96
            #* 4 qubits |    63     |    23    |       208
            #* 5 qubits |    77     |    28    |       432
            #* 6 qubits |    91     |    33    |       880
            #* 7 qubits |   105     |    38    |      1776
        * parallel toffolis && cancel ngh T gates in all qubits && mirror the output to the input && stratify decompositions and circuit:
            #*    Depth |  Circuit  |  T Gate  | Count of T Gates
            #* 2 qubits |    33     |    13    |        40
            #* 3 qubits |    45     |    17    |        96
            #* 4 qubits |    57     |    21    |       208
            #* 5 qubits |    69     |    25    |       432
            #* 6 qubits |    81     |    29    |       880
            #* 7 qubits |    93     |    33    |      1776
            #* 8 qubits |   105     |    37    |      3568
    """
    # qram.bb_decompose_test(
    #     dec=ToffoliDecompType.NO_DECOMP,
    #     parallel_toffolis=False,

    #     dec_mod=[
    #         ToffoliDecompType.RELATIVE_PHASE_TD_4_CX_3,
    #         ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
    #         ToffoliDecompType.RELATIVE_PHASE_TD_4_CX_3,
    #     ],
    #     parallel_toffolis_mod=True,
    #     mirror_method=MirrorMethod.OUT_TO_IN #! BY DEFAULT IS NO_MIRROR
    # )

    qram.bb_decompose_test(
        dec=[
            ToffoliDecompType.RELATIVE_PHASE_TD_4_CX_3,
            ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
            ToffoliDecompType.RELATIVE_PHASE_TD_4_CX_3,
        ],
        parallel_toffolis=True,

        dec_mod=[
            ToffoliDecompType.RELATIVE_PHASE_TD_4_CX_3,
            ToffoliDecompType.ANCILLA_0_TD4_MOD,
            ToffoliDecompType.RELATIVE_PHASE_TD_4_CX_3,
        ],

        parallel_toffolis_mod=True,
        mirror_method=MirrorMethod.OUT_TO_IN #! BY DEFAULT IS NO_MIRROR
    )

    # qram.bb_decompose_test(
    #     dec=[
    #         ToffoliDecompType.RELATIVE_PHASE_TD_4_CX_3,
    #         ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
    #         ToffoliDecompType.RELATIVE_PHASE_TD_4_CX_3,
    #     ],
    #     parallel_toffolis=True,

    #     dec_mod=[
    #         ToffoliDecompType.RELATIVE_PHASE_TD_0_CX_3,
    #         ToffoliDecompType.ANCILLA_0_TD4_MOD,
    #         ToffoliDecompType.RELATIVE_PHASE_TD_0_CX_3,
    #     ],

    #     parallel_toffolis_mod=True,
    #     mirror_method=MirrorMethod.OUT_TO_IN #! BY DEFAULT IS NO_MIRROR
    # )

    """
    (2) ~ The Bucket brigade standard 7-T gate decomposition (QC10) for QUERY (mem) and the standard 7-T gate decomposition (QC10) Depth of T 5 and of CNOT 6 Inverse for FANIN and mirror the input to the output for FANOUT.
        * parallel toffolis && cancel ngh T gates in all qubits && mirror the input to the output:
            #*    Depth |  Circuit  |  T Gate  | Count of T Gates
            #* 2 qubits |    36     |    16    |        52
            #* 3 qubits |    58     |    24    |       124
            #* 4 qubits |    80     |    32    |       268
        * parallel toffolis && cancel ngh T gates in all qubits && delete 2 neighbor T gates in a qubits && mirror the input to the output:
            #*    Depth |  Circuit  |  T Gate  | Count of T Gates
            #* 2 qubits |    36     |    14    |        48
            #* 3 qubits |    58     |    22    |       120
            #* 4 qubits |    80     |    30    |       264
        * parallel toffolis && cancel ngh T gates in all qubits && mirror the input to the output && stratify decompositions and circuit:
            #*    Depth |  Circuit  |  T Gate  | Count of T Gates
            #* 2 qubits |    41     |    15    |        48
            #* 3 qubits |    63     |    23    |       120
            #* 4 qubits |    85     |    31    |       264
            #* 5 qubits |   107     |    39    |       552
            #* 6 qubits |   129     |    47    |      1128
            #* 7 qubits |   151     |    55    |      2280

    """
    # qram.bb_decompose_test(
    #     dec=ToffoliDecompType.NO_DECOMP,
    #     parallel_toffolis=False,

    #     dec_mod=[
    #         ToffoliDecompType.TD_5_CXD_6_INV,
    #         ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
    #         ToffoliDecompType.TD_5_CXD_6,
    #     ],
    #     parallel_toffolis_mod=True,
    #     mirror_method=MirrorMethod.IN_TO_OUT
    # )

    """
    (3) ~ The Bucket brigade standard 7-T gate decomposition (QC10) for QUERY (mem) and the standard 7-T gate decomposition (QC10) Depth of T 5 and of CNOT 6 Inverse for FANIN and standard 7-T gate decomposition inverted (QC10) for FANOUT.
        * parallel toffolis && cancel ngh T gates only in target qubit:
            #*    Depth |  Circuit
            #* 2 qubits |    36  
            #* 3 qubits |    62
            #* 4 qubits |    92
        * parallel toffolis && cancel ngh T gates in all qubits:
            #*    Depth |  Circuit  | T Gate
            #* 2 qubits |    36     |   17
            #* 3 qubits |    59     |   29
            #* 4 qubits |    85     |   43
    """
    # qram.bb_decompose_test(
    #     dec=ToffoliDecompType.NO_DECOMP,
    #     parallel_toffolis=False,

    #     dec_mod=[
    #         ToffoliDecompType.TD_5_CXD_6_INV,
    #         ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
    #         ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4_INV,
    #     ],
    #     parallel_toffolis_mod=True,
    #     mirror_method=False
    # )

    """
        The Bucket brigade standard 7-T gate decomposition (QC10).
        Depth of the circuit decomposition is 46 for 2 qubits WITH parallel toffolis.
        Simulation passed.
    """

    # qram.bb_decompose_test(
    #     ToffoliDecompType.NO_DECOMP,
    #     False,
    #     [
    #         ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
    #         ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
    #         ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4_INV,
    #     ],
    #     True
    # )

    # qram.bb_decompose_test(
    #     ToffoliDecompType.NO_DECOMP,
    #     False,
    #     [
    #         ToffoliDecompType.TD_5_CXD_6_INV,
    #         ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
    #         ToffoliDecompType.TD_5_CXD_6,
    #     ],
    #     True
    # )

    # qram.bb_decompose_test( # mix1 better in 3 qubits and up __{2q: 36, 3q: 61, 4q: 91(88)}__
    #     dec=ToffoliDecompType.NO_DECOMP,
    #     parallel_toffolis=False,
    #     dec_mod=[
    #         ToffoliDecompType.TD_5_CXD_6,
    #         ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
    #         ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
    #     ],
    #     parallel_toffolis_mod=True,
    #     mirror_method=False
    # )

    # qram.bb_decompose_test( # mix2 __{2q: 36, 3q: 70, 4q: 110}__
    #     ToffoliDecompType.NO_DECOMP,
    #     False,
    #     [
    #         ToffoliDecompType.TD_4_CXD_8_INV,
    #         ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
    #         ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
    #     ],
    #     True
    # )


def old_tests():

    qram: QRAMCircuitExperiments = QRAMCircuitExperiments()

    """
        The Bucket brigade all controlled V, 𝑉† and X decompositions (QC5).
        Depth of the circuit decomposition is 46 for 2 qubits
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
        #! Depth of the circuit decomposition is 36 for 2 qubits and 68 for 3 qubits WITH parallel toffolis.
        #! After eliminating the T gates, the depth of the T gate stabilizes at 4 for all numbers of qubits, and the depth of the circuit decomposition is __{ 34 }__ for 2 qubits and __{ 62 }__ for 3 qubits WITH parallel toffolis.
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
        #! Depth of the circuit decomposition is 34 for 2 qubits and 63 for 3 qubits WITH parallel toffolis.
        #! After eliminating the T gates, the depth of the T gate stabilizes at 4 for all numbers of qubits, and the depth of the circuit decomposition is __{ 32 }__ for 2 qubits and __{ 57 }__ for 3 qubits WITH parallel toffolis.
        Simulation passed.
    """
    # for i in [4, 6]:
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
        #! Depth of the circuit decomposition is 34 for 2 qubits and 63 for 3 qubits WITH parallel toffolis.
        #! After eliminating the T gates, the depth of the T gate stabilizes at 4 for all numbers of qubits, and the depth of the circuit decomposition is __{ 31 }__ for 2 qubits and __{ 56 }__ for 3 qubits WITH parallel toffolis and __{ 97 }__ for 4 qubits.
        Simulation passed.
    """
    for i in [1, 3]:
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

if __name__ == "__main__":
    main()
