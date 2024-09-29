import cirq
import sys
import time

import concurrent.futures
import threading

from typing import Union

import qramcircuits.bucket_brigade as bb

from qramcircuits.qram_circuit_simulator import QRAMCircuitSimulator
from qramcircuits.bucket_brigade import ReverseMoments
from qramcircuits.toffoli_decomposition import ToffoliDecompType

from utils.counting_utils import *
from utils.print_utils import *


MSG0 = "Start range of qubits must be greater than 1"
MSG1 = "End range of qubits must be greater than start range of qubits or equal to it"
MSG2 = "Specific simulation must be (a, b, m, ab, bm, abm, t), by default it is full circuit"
HELP: str = """
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
        __print_input__(): Prints the input arguments for the experiment.
        __arg_input__(): Gets the input arguments for the experiment.
        __get_input__(): Gets user input for the experiment.

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

        try:
            self.__arg_input__()
        except Exception as e:
            colpr("r", "\n", str(e), end="\n")
            colpr("y", HELP, end="\n\n")
            self.__get_input__()
    
        self.__print_input__()

    #######################################
    # input methods
    #######################################

    def __print_input__(self) -> None:
        """
        Prints the input arguments for the experiment.
        """

        colpr("y", "Hello QRAM circuit!", end="\n\n")

        colpr("c", f"Simulate Toffoli decompositions and circuit: {'yes' if self._simulate else 'no'}")
        colpr("c", f"{self._print_circuit} circuits")
        colpr("c", f"{self._print_sim} simulation results")
        colpr("c", f"Start Range of Qubits: {self._start_range_qubits}")
        colpr("c", f"End Range of Qubits: {self._end_range_qubits}")

        if self._simulate:
            sim_msg = "Simulate full circuit" if self._specific_simulation == "full" else f"Simulate Specific Measurement: {self._specific_simulation}"
            colpr("c", sim_msg)
        print("\n")

    def __arg_input__(self) -> None:
        """
        Gets the input arguments for the experiment.
        """

        LEN_ARGV = 6

        # check if the number of arguments is valid
        if len(sys.argv) not in {LEN_ARGV, LEN_ARGV + 1}:
            raise ValueError("Invalid number of arguments")

        # Simulate Toffoli decompositions and circuit (y/n)
        self._simulate = sys.argv[1].lower() in ["y", "yes"]

        # (P) print or (D) display or (H) hide circuits
        circuit_options = {"p": "Print", "d": "Display"}
        self._print_circuit = circuit_options.get(sys.argv[2].lower(), "Hide")

        # (F) full simulation or (D) just dots or (H) hide the simulation
        sim_options = {"d": "Dot", "f": "Full"}
        self._print_sim = sim_options.get(sys.argv[3].lower(), "Hide")

        # Start range of qubits, starting from 2
        self._start_range_qubits = int(sys.argv[4])
        if self._start_range_qubits < 2:
            raise ValueError(MSG0)

        # End range of qubits, should be equal to or greater than the start range
        self._end_range_qubits = int(sys.argv[5])
        if self._end_range_qubits < self._start_range_qubits:
            self._end_range_qubits = self._start_range_qubits

        # Specific simulation (a, b, m, ab, bm, abm, t) by default it is full circuit
        if len(sys.argv) == LEN_ARGV + 1 and self._simulate:
            if sys.argv[6] not in ['a', 'b', 'm', "ab", "bm", "abm", "t"]:
                raise ValueError(MSG2)
            self._specific_simulation = sys.argv[6]
        else:
            self._specific_simulation = "full"

    def __get_input__(self) -> None:
        """
        Gets user input for the experiment.
        """

        # Simulate Toffoli decompositions and circuit (y/n)
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

        # (P) print or (D) display or (H) hide circuits
        while True:
            var = input("(p) print or (d) display or (h) hide circuits: ").lower()
            if var in ["p", "d", "h"]:
                self._print_circuit = {"p": "Print", "d": "Display", "h": "Hide"}[var]
                break
            else:
                print("Invalid input. Please enter 'p', 'd', or 'h'.")

        # (F) full simulation or (D) just dots or (H) hide the simulation
        if self._simulate:
            while True:
                user_input = input("Print the full simulation result (f) or just the dot (d) or hide (h)? ").lower()
                if user_input in ["f", "d", "h"]:
                    self._print_sim = {"f": "Full", "d": "Dot", "h": "Hide"}[user_input]
                    break
                else:
                    print("Invalid input. Please enter 'f', 'd', or 'h'.")

        # Start range of qubits, starting from 2
        self._start_range_qubits = int(input("Start range of qubits: "))
        while self._start_range_qubits < 2:
            colpr("r", MSG0, end="\n\n")
            self._start_range_qubits = int(input("Start range of qubits: "))

        # End range of qubits, should be equal to or greater than the start range
        self._end_range_qubits = int(input("End range of qubits: "))
        while self._end_range_qubits < self._start_range_qubits:
            colpr("r", MSG1, end="\n\n")
            self._end_range_qubits = int(input("End range of qubits: "))

        # Specific simulation (a, b, m, ab, bm, abm, t) by default it is full circuit
        if self._simulate:
            while True:
                user_input = input("Simulate specific measurement for specific qubits wires? (y/n): ").lower()
                if user_input in ["y", "yes"]:
                    while self._specific_simulation not in ['a', 'b', 'm', "ab", "bm", "abm", "t"]:
                        self._specific_simulation = input("Choose specific qubits wires (a, b, m, ab, bm, abm, t): ").lower()
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
            reverse_moments: ReverseMoments = ReverseMoments.NO_REVERSE
    ) -> bb.BucketBrigadeDecompType:
        """
        Decomposes the Toffoli gates in the bucket brigade circuit.

        Args:
            toffoli_decomp_type (Union['list[ToffoliDecompType]', ToffoliDecompType]): The type of Toffoli decomposition.
            parallel_toffolis (bool): Flag indicating whether to use parallel toffolis.
            reverse_moments (bool): Flag indicating whether to reverse the input to the output.

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
                reverse_moments=reverse_moments
            )
        else:
            return bb.BucketBrigadeDecompType(
                toffoli_decomp_types=[
                    toffoli_decomp_type,    # fan_in_decomp
                    toffoli_decomp_type,    # mem_decomp
                    toffoli_decomp_type     # fan_out_decomp
                ],
                parallel_toffolis=parallel_toffolis,
                reverse_moments=reverse_moments
            )

    def bb_decompose_test(
            self,
            dec: Union['list[ToffoliDecompType]', ToffoliDecompType],
            parallel_toffolis: bool,

            dec_mod: Union['list[ToffoliDecompType]', ToffoliDecompType],
            parallel_toffolis_mod: bool,
            reverse_moments: ReverseMoments = ReverseMoments.NO_REVERSE
    ) -> None:
        """
        Tests the bucket brigade circuit with different decomposition scenarios.

        Args:
            dec (Union['list[ToffoliDecompType]', ToffoliDecompType]): The decomposition scenario for the bucket brigade.
            parallel_toffolis (bool): Flag indicating whether to use parallel toffolis for the bucket brigade.
            dec_mod (Union['list[ToffoliDecompType]', ToffoliDecompType]): The modified decomposition scenario for the bucket brigade.
            parallel_toffolis_mod (bool): Flag indicating whether to use parallel toffolis for the modified bucket brigade.
            reverse_moments (bool): Flag indicating whether to reverse the input to the output.

        Returns:
            None
        """

        # ===============REFERENCE==============

        self._decomp_scenario = self.__bb_decompose(
            dec, 
            parallel_toffolis, 
            reverse_moments
        )

        # ================MODDED================

        self._decomp_scenario_modded = self.__bb_decompose(
            dec_mod, 
            parallel_toffolis_mod,
            reverse_moments
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

        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.submit(_create_bbcircuit)
            executor.submit(_create_bbcircuit_modded)

        self._stop_time = elapsed_time(self._start_time)
