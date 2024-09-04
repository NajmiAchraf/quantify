import cirq
import sys
import time

import threading

from typing import Union

import qramcircuits.bucket_brigade as bb

from qramcircuits.bucket_brigade import MirrorMethod
from qramcircuits.qram_circuit_simulator import QRAMCircuitSimulator
from qramcircuits.toffoli_decomposition import ToffoliDecompType

from utils.counting_utils import *
from utils.print_utils import *


help: str = """
How to run the main_*.py file:

Run the following command in the terminal:

    python3 main_*.py

or by adding arguments:

    python3 main_*.py y p d 2 2

Arguments:
- arg 1: Simulate Toffoli decompositions and circuit (y/n).
- arg 2: (P) print or (D) display or (H) hide circuits.
- arg 3: (F) full simulation or (D) just dots or (H) hide the simulation.
- arg 4: Start range of qubits, starting from 2.
- arg 5: End range of qubits, should be equal to or greater than the start range.
- additional arg 6: Specific simulation (a, b, m, ab, bm, abm, t).
    leave it empty to simulate the full circuit.
"""


#######################################
# QRAM Circuit Core
#######################################

class QRAMCircuitCore:
    """
    A class used to represent the QRAM circuit core.

    Attributes:
        __simulate (bool): Flag indicating whether to simulate Toffoli decompositions and circuit.
        __print_circuit (bool): Flag indicating whether to print the circuits.
        __print_sim (str): Flag indicating whether to print the full simulation result.
        __start_range_qubits (int): Start range of qubits.
        __end_range_qubits (int): End range of qubits.
        __specific_simulation (str): Specific simulation for specific qubit wire.

        __start_time (float): Start time of the experiment.
        __stop_time (str): Stop time of the experiment.

        __decomp_scenario (bb.BucketBrigadeDecompType): Decomposition scenario for the bucket brigade.
        __decomp_scenario_modded (bb.BucketBrigadeDecompType): Modified decomposition scenario for the bucket brigade.
        __bbcircuit (bb.BucketBrigade): Bucket brigade circuit.
        __bbcircuit_modded (bb.BucketBrigade): Modified bucket brigade circuit.

        __simulated (bool): Flag indicating whether the circuit has been simulated.
        __Simulator (QRAMCircuitSimulator): The QRAM circuit simulator.

    Methods:
        __init__(): Initializes the QRAMCircuitCore class.
        __del__(): Destructs the QRAMCircuitCore class.
        __get_input(): Gets user input for the experiment.

        __bb_decompose(): Decomposes the Toffoli gates in the bucket brigade circuit.
        bb_decompose_test(): Tests the bucket brigade circuit with different decomposition scenarios.

        __run(): Runs the experiment for a range of qubits.
        __core(): Core function of the experiment.
    """

    _simulate: bool = False
    _print_circuit: str = "Hide"
    _print_sim: str = "Hide"
    _start_range_qubits: int
    _end_range_qubits: int
    _specific_simulation: str = "full"

    _start_time: float = 0
    _stop_time: str = ""

    _decomp_scenario: bb.BucketBrigadeDecompType
    _decomp_scenario_modded: bb.BucketBrigadeDecompType
    _bbcircuit: bb.BucketBrigade
    _bbcircuit_modded: bb.BucketBrigade

    _simulated: bool = False
    _Simulator: QRAMCircuitSimulator


    def __init__(self):
        """
        Constructor the QRAMCircuitCore class.
        """

        self.__get_input()

        colpr("y", "Hello QRAM circuit!", end="\n\n")

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
        Destructor of the QRAMCircuitCore class.
        """

        colpr("y", "Goodbye QRAM circuit!")

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

    def _run(self, title: str="bucket brigade") -> None:
        """
        Runs the experiment for a range of qubits.
        """

        if self._decomp_scenario is None:
            colpr("r", "Decomposition scenario is None")
            return

        if title == "bilan":
            stop_event = threading.Event()
            loading_thread = threading.Thread(target=loading_animation, args=(stop_event, title,))
            loading_thread.start()

        try:
            for i in range(self._start_range_qubits, self._end_range_qubits + 1):
                if title == "bucket brigade":
                    self._start_range_qubits = i
                self._simulated = False
                self._core(i)
        finally:
            if title == "bilan":
                stop_event.set()
                loading_thread.join()

    def _core(self, nr_qubits: int) -> None:
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

        def _create_bbcircuit():
            self._bbcircuit = bb.BucketBrigade(qubits, self._decomp_scenario)

        def _create_bbcircuit_modded():
            self._bbcircuit_modded = bb.BucketBrigade(qubits, self._decomp_scenario_modded)

        thread1 = threading.Thread(target=_create_bbcircuit)
        thread2 = threading.Thread(target=_create_bbcircuit_modded)

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        self._stop_time = elapsed_time(self._start_time)
