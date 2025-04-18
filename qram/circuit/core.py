import concurrent.futures
import sys
import threading
import time
from typing import Union

import cirq

import qramcircuits.bucket_brigade as bb
from qram.circuit.simulator_manager import QRAMCircuitSimulatorManager
from qramcircuits.bucket_brigade import ReverseMoments
from qramcircuits.toffoli_decomposition import ToffoliDecompType
from utils.arg_parser import parser_args
from utils.print_utils import colpr, elapsed_time, loading_animation
from utils.types import type_print_circuit, type_print_sim, type_specific_simulation

#######################################
# QRAM Circuit Core
#######################################


class QRAMCircuitCore:
    """
    A class used to represent the QRAM circuit core.

    Attributes:
        _hpc (bool): Flag indicating whether to use High Performance Computing (HPC) mode.
        _simulate (bool): Flag indicating whether to simulate Toffoli decompositions and circuit.
        _print_circuit (type_print_circuit): Flag indicating whether to print the full circuit.
        _print_sim (type_print_sim): Flag indicating whether to print the full simulation result.
        _start_range_qubits (int): Start range of qubits.
        _end_range_qubits (int): End range of qubits.
        _specific_simulation (type_specific_simulation): Specific simulation for specific qubit wire.

        _start_time (float): Start time of the experiment.
        _stop_time (str): Stop time of the experiment.

        _decomp_scenario (bb.BucketBrigadeDecompType): Decomposition scenario for the bucket brigade.
        _decomp_scenario_modded (bb.BucketBrigadeDecompType): Modified decomposition scenario for the bucket brigade.
        _bbcircuit (bb.BucketBrigade): Bucket brigade circuit.
        _bbcircuit_modded (bb.BucketBrigade): Modified bucket brigade circuit.

        _simulated (bool): Flag indicating whether the circuit has been simulated.
        _Simulator (QRAMCircuitSimulator): The QRAM circuit simulator.

    Methods:
        __init__(): Initializes the QRAMCircuitCore class.

        __print_input__(): Prints the input arguments for the experiment.
        __arg_input__(): Gets the input arguments for the experiment.

        __bb_decompose(toffoli_decomp_type, parallel_toffolis, reverse_moments): Decomposes the Toffoli gates in the bucket brigade circuit.
        bb_decompose_test(dec, parallel_toffolis, dec_mod, parallel_toffolis_mod, reverse_moments): Tests the bucket brigade circuit with different decomposition scenarios.

        _run(title): Runs the experiment for a range of qubits.
        _core(nr_qubits): Core function of the experiment.
    """

    _shots: int = 50
    _hpc: bool = False
    _simulate: bool = False
    _print_circuit: type_print_circuit = "Hide"
    _print_sim: type_print_sim = "Hide"
    _start_range_qubits: int
    _end_range_qubits: int = 0
    _specific_simulation: type_specific_simulation = "qram"

    _start_time: float = 0
    _stop_time: str = ""

    _decomp_scenario: bb.BucketBrigadeDecompType
    _decomp_scenario_modded: bb.BucketBrigadeDecompType
    _bbcircuit: bb.BucketBrigade
    _bbcircuit_modded: bb.BucketBrigade

    _simulated: bool = False
    _simulator_manager: QRAMCircuitSimulatorManager

    def __init__(self):
        """
        Constructor for the QRAMCircuitCore class.
        """

        try:
            self.__arg_input__()
        except Exception as e:
            colpr("r", "\nError occurred while parsing arguments:", str(e), end="\n")
            sys.exit(1)

        if not self._hpc:
            self.__print_input__()

    #######################################
    # input methods
    #######################################

    def __print_input__(self) -> None:
        """
        Prints the input arguments for the experiment.
        """

        colpr("y", "========== QRAM Circuit Configuration ==========", end="\n\n")

        colpr("w", "Simulate circuit on HPC:", end=" ")
        colpr("r", f"{'Yes' if self._hpc else 'No'}")

        colpr("w", "Simulate Toffoli decompositions and circuit:", end=" ")
        colpr("r", f"{'Yes' if self._simulate else 'No'}")

        colpr("w", "Circuit display option:", end=" ")
        colpr("r", f"{self._print_circuit}")

        colpr("w", "Start range of qubits:", end=" ")
        colpr("r", f"{self._start_range_qubits}")

        colpr("w", "End range of qubits:", end=" ")
        colpr("r", f"{self._end_range_qubits}")

        if self._simulate:

            sim_msg = (
                "Simulate full circuit"
                if self._specific_simulation == "full"
                else f"Simulate specific measurement: {self._specific_simulation} qubits"
            )
            colpr("w", "Simulation type:", end=" ")
            colpr("r", sim_msg)

            colpr("w", "Simulation display option:", end=" ")
            colpr("r", f"{self._print_sim}")

            if self._specific_simulation != "full":
                colpr("w", "Number of shots for the each simulation:", end=" ")
                colpr("r", f"{self._shots}")

        colpr("y", "\n================================================\n")

    def __arg_input__(self) -> None:
        """
        Gets the input arguments for the experiment using argparse.
        """

        args = parser_args("core").parse_known_args()[0]

        # Number of shots for the simulation
        self._shots = args.shots

        # High Performance Computing (HPC) mode
        self._hpc = args.hpc
        if self._hpc:
            try:
                import mpi4py
            except ImportError:
                raise RuntimeError(
                    "`mpi4py` is not installed. Please install it to run the experiment in HPC mode, and it requires OpenMPI to be installed in the system."
                )

        # Simulate Toffoli decompositions and circuit
        self._simulate = args.simulate

        # (P) print or (D) display or (H) hide circuits
        self._print_circuit = args.print_circuit

        # (F) full simulation or (D) just dots or (H) hide the simulation
        self._print_sim = args.print_simulation

        # Start and end range of qubits
        self._start_range_qubits, self._end_range_qubits = args.qubit_range

        # Specific simulation (a, b, m, ab, bm, abm, t) by default it is full circuit
        self._specific_simulation = args.specific

    #######################################
    # decomposition methods
    #######################################

    def __bb_decompose(
        self,
        toffoli_decomp_type: Union["list[ToffoliDecompType]", ToffoliDecompType],
        parallel_toffolis: bool,
        reverse_moments: ReverseMoments = ReverseMoments.NO_REVERSE,
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
                    toffoli_decomp_type[0],  # fan_in_decomp
                    toffoli_decomp_type[1],  # mem_decomp
                    toffoli_decomp_type[2],  # fan_out_decomp
                ],
                parallel_toffolis=parallel_toffolis,
                reverse_moments=reverse_moments,
            )
        else:
            return bb.BucketBrigadeDecompType(
                toffoli_decomp_types=[
                    toffoli_decomp_type,  # fan_in_decomp
                    toffoli_decomp_type,  # mem_decomp
                    toffoli_decomp_type,  # fan_out_decomp
                ],
                parallel_toffolis=parallel_toffolis,
                reverse_moments=reverse_moments,
            )

    def bb_decompose_test(
        self,
        dec: Union["list[ToffoliDecompType]", ToffoliDecompType],
        parallel_toffolis: bool,
        dec_mod: Union["list[ToffoliDecompType]", ToffoliDecompType],
        parallel_toffolis_mod: bool,
        reverse_moments: ReverseMoments = ReverseMoments.NO_REVERSE,
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
            dec, parallel_toffolis, reverse_moments
        )

        # ================MODDED================

        self._decomp_scenario_modded = self.__bb_decompose(
            dec_mod, parallel_toffolis_mod, reverse_moments
        )

        self._run()

    #######################################
    # core functions
    #######################################

    def _run(self, title: str = "bucket brigade") -> None:
        """
        Runs the experiment for a range of qubits.
        """

        if self._decomp_scenario is None:
            colpr("r", "Decomposition scenario is None")
            return

        animate = False
        if title == "assessment" and not self._hpc:
            animate = True

        if animate:
            stop_event = threading.Event()
            loading_thread = threading.Thread(
                target=loading_animation,
                args=(
                    stop_event,
                    title,
                ),
            )
            loading_thread.start()

        try:
            for i in range(self._start_range_qubits, self._end_range_qubits + 1):
                if title == "bucket brigade":
                    self._start_range_qubits = i
                self._simulated = False
                self._core(i)
        finally:
            if animate:
                stop_event.set()
                loading_thread.join()

    def _core(self, nr_qubits: int) -> None:
        """
        Core function of the experiment.
        """

        self._start_time = time.time()

        if nr_qubits > 3 and self._print_sim == "Full":
            self._print_sim = "Dot"

        qubits: "list[cirq.NamedQubit]" = []

        qubits.clear()
        for i in range(nr_qubits):
            qubits.append(cirq.NamedQubit("a" + str(i)))

        def _create_bbcircuit():
            self._bbcircuit = bb.BucketBrigade(qubits, self._decomp_scenario)

        def _create_bbcircuit_modded():
            self._bbcircuit_modded = bb.BucketBrigade(
                qubits, self._decomp_scenario_modded
            )

        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.submit(_create_bbcircuit)
            executor.submit(_create_bbcircuit_modded)

        self._stop_time = elapsed_time(self._start_time)

        if self._simulate:
            self._simulator_manager = QRAMCircuitSimulatorManager(
                bbcircuit=self._bbcircuit,
                bbcircuit_modded=self._bbcircuit_modded,
                specific_simulation=self._specific_simulation,
                qubits_number=self._start_range_qubits,
                print_circuit=self._print_circuit,
                print_sim=self._print_sim,
                hpc=self._hpc,
                shots=self._shots,
            )
