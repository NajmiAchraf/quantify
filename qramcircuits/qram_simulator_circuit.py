import cirq
import cirq.optimizers
import itertools
import time

import multiprocessing
import threading

import qramcircuits.bucket_brigade as bb

from qramcircuits.qram_simulator_base import QRAMSimulatorBase
from qramcircuits.qram_simulator_decomposition import QRAMSimulatorDecompositions
from qramcircuits.toffoli_decomposition import ToffoliDecompType

from utils.print_utils import colpr, printRange, printCircuit, loading_animation


#######################################
# QRAM Simulator Circuit
#######################################

class QRAMSimulatorCircuit(QRAMSimulatorBase):
    """
    The QRAMCircuitSimulator class to simulate the bucket brigade circuit.

    Methods:
        _run_simulation(is_stress): Runs the simulation.
        _circuit_configuration(): Unified simulation function for all qubit types.
        _add_measurements(bbcircuit): Adds measurements to the circuit and returns the initial state.
        _simulation_manager(): Manages the simulation.
        _hpc_simulation(): Runs the simulation on high-performance computing.
        _parallel_simulation(sim_range, step): Simulates the circuit using multiprocessing.
        _sequential_simulation(sim_range, step): Simulates the circuit sequentially.
    """

    def _run_simulation(self, is_stress: bool = False) -> None:
        """
        Runs the simulation.
        """

        self._is_stress = is_stress

        if is_stress:
            self._print_sim = "Hide"
        elif not is_stress and not self._hpc:
            QRAMSimulatorDecompositions(
                self._bbcircuit,
                self._bbcircuit_modded,
                self._specific_simulation,
                self._qubits_number,
                self._print_circuit,
                self._print_sim,
                self._hpc,
                self._shots
            )

        self._simulation_manager()

    def _circuit_configuration(self) -> 'tuple[list[int], int, str]':
        """
        Unified simulation function for all qubit types.
        """

        self._simulation_kind = "bb"

        simulation_configs = {
            "a": {
                "step": 2 ** (2 * (2 ** self._qubits_number) + 1),
                "stop_multiplier": 2 ** self._qubits_number,
                "message": "<==================== Simulating the circuit ... Checking the addressing of the a qubits =====================>\n"
            },
            "b": {
                "step": 2 ** (2 ** self._qubits_number + 1),
                "stop_multiplier": 2 ** (2 ** self._qubits_number),
                "message": "<==================== Simulating the circuit ... Checking the uncomputation of FANOUT ... were the b qubits are returned to their initial state =====================>\n"
            },
            "m": {
                "step": 2,
                "stop_multiplier": 2 ** (2 ** self._qubits_number),
                "message": "<==================== Simulating the circuit ... Checking the computation of MEM ... were the m qubits are getting the result of the computation =====================>\n"
            },
            "ab": {
                "step": 2 ** (2 ** self._qubits_number + 1),
                "stop_multiplier": 2 ** self._qubits_number,
                "message": "<==================== Simulating the circuit ... Checking the addressing and uncomputation of the a and b qubits =====================>\n"
            },
            "bm": {
                "step": 2,
                "stop_multiplier": 2 ** (2 ** self._qubits_number),
                "message": "<==================== Simulating the circuit ... Checking the addressing and uncomputation of the b and m qubits =====================>\n"
            },
            "abm": {
                "step": 2,
                "stop_multiplier": 2 ** (2 ** self._qubits_number),
                "message": "<==================== Simulating the circuit ... Checking the addressing and uncomputation of the a, b, and m qubits =====================>\n"
            },
            "t": {
                "step": 2,
                "stop_multiplier": 2 ** (2 ** self._qubits_number),
                "message": "<==================== Simulating the circuit ... Checking the addressing and uncomputation of the a, b, and m qubits and measure only the target qubit =====================>\n"
            },
            "full": {
                "step": 1,
                "stop_multiplier": 2 ** (2 * (2 ** self._qubits_number) + self._qubits_number + 1),
                "message": "<==================== Simulating the circuit ... Checking all qubits =====================>\n"
            },
            "qram": {
                "step": 1,
                "stop_multiplier": None,
                "message": "Simulating the circuit ... Checking the QRAM logic and measure only the target qubit ..."
            }
        }

        config = simulation_configs.get(self._specific_simulation)
        if not config:
            raise ValueError(f"Unknown simulation type: {self._specific_simulation}")

        start = 0
        step = config["step"]
        if self._specific_simulation != "qram":
            stop = step * config.get("stop_multiplier", 1)
            sim_range = list(range(start, stop, step))
        else:
            def generate_qram_patterns() -> 'list[int]':
                """2
                0 00 1000 0001 0 -> 258 : start
                0 01 0100 0010 0 -> 644
                0 10 0010 0100 0 -> 1096
                0 11 0001 1000 0 -> 1584
                """

                """3
                0 000 10000000 00000001 0 -> 65538 : start
                0 001 01000000 00000010 0 -> 163844
                0 010 00100000 00000100 0 -> 278536
                0 011 00010000 00001000 0 -> 401424
                0 100 00001000 00010000 0 -> 528416
                0 101 00000100 00100000 0 -> 657472
                0 110 00000010 01000000 0 -> 787584
                0 111 00000001 10000000 0 -> 918272
                """

                for n in range(self._qubits_number + 1):
                    lines = []
                    num_ids = 2 ** n
                    control_length = 2 ** n
                    # Generate active lines
                    for i in range(num_ids):
                        flag = '0'
                        identifier = format(i, f'0{n}b')
                        control1 = format(1 << (control_length - 1 - i), f'0{control_length}b')
                        control2 = format(1 << i, f'0{control_length}b')
                        final_bit = '0'
                        decimal_value = int(f"{flag}{identifier}{control1}{control2}{final_bit}", 2)
                        lines.append(decimal_value)
                return lines


            sim_range = generate_qram_patterns()

        return sim_range, step, config["message"]

    def _add_measurements(self, bbcircuit: bb.BucketBrigade) -> None:
        """
        Adds measurements to the circuit and returns the initial state.

        Args:
            bbcircuit (bb.BucketBrigade): The bucket brigade circuit.
        """

        measurements = []
        for qubit in bbcircuit.qubit_order:
            if self._specific_simulation in ["full", "qram"]:
                measurements.append(cirq.measure(qubit))
            else:
                for _name in self._specific_simulation:
                    if qubit.name.startswith(_name):
                        measurements.append(cirq.measure(qubit))

        bbcircuit.circuit.append(measurements)
        cirq.optimizers.SynchronizeTerminalMeasurements().optimize_circuit(bbcircuit.circuit)

    def _simulation_manager(self) -> None:
        """
        Simulates the circuit.

        Args:
            sim_range ('list[int]'): The range of the simulation.
            step (int): The step index.
            message (str): The message to print.
        """

        sim_range, step, message = self._circuit_configuration()

        self._start_time = time.time()

        # add measurements to circuits ########################################################

        self._add_measurements(self._bbcircuit)

        self._add_measurements(self._bbcircuit_modded)

        # prints ##############################################################################

        if not self._is_stress and not self._hpc:

            name = "bucket brigade" if self._decomp_scenario.get_decomp_types()[0] == ToffoliDecompType.NO_DECOMP else "reference"

            colpr("y", '\n', message, end="\n\n")

            printCircuit(self._print_circuit, self._bbcircuit.circuit, self._bbcircuit.qubit_order, name)

            printCircuit(self._print_circuit, self._bbcircuit_modded.circuit, self._bbcircuit_modded.qubit_order, "modded")

            printRange(sim_range[0], sim_range[-1], step)

            colpr("c", f"Simulating both the modded and {name} circuits and comparing their output vector and measurements ...", end="\n\n")

        if self._hpc:
            self._hpc_multiprocessing_simulation(sim_range, step)

        elif not self._hpc:
            if self._specific_simulation != "full" and self._simulation_kind == "bb":
                self._sequential_circuit_simulation(sim_range, step)
            else:
                self._parallel_circuit_simulation(sim_range, step)

    def _hpc_multiprocessing_simulation(self, sim_range: 'list[int]', step: int) -> None:
        """
        Simulates the circuit using multiprocessing and MPI.

        Args:
            sim_range ('list[int]'): The range of the simulation.
            step (int): The step index
        """

        from mpi4py import MPI

        # Initialize MPI ######################################################################

        comm = MPI.COMM_WORLD
        rank = comm.Get_rank()
        size = comm.Get_size()

        # Prints ##############################################################################

        if rank == 0:
            print(f"{'='*150}\n\n")
    
            name = "bucket brigade" if self._decomp_scenario.get_decomp_types()[0] == ToffoliDecompType.NO_DECOMP else "reference"

            printRange(sim_range[0], sim_range[-1], step)

            colpr("c", f"Simulating both the modded and {name} circuits and comparing their output vector and measurements ...", end="\n\n")

        # Split the total work into chunks based on the number of ranks #######################

        chunk_size_per_rank = len(sim_range) // size
        if rank < size - 1:
            local_work_range = sim_range[rank * chunk_size_per_rank : (rank + 1) * chunk_size_per_rank]
        else:
            local_work_range = sim_range[rank * chunk_size_per_rank :]

        # wait for all MPI processes to reach this point ######################################

        comm.Barrier()

        # reset the simulation results ########################################################

        self._simulation_results = {}

        # Use multiprocessing to parallelize the simulation ###################################

        results: 'list[tuple[int, int, int]]' = []

        if self._specific_simulation != "full" and self._simulation_kind == "bb":
            results = self._sequential_execution(local_work_range, step)
        else:
            results = self._parallel_execution(local_work_range, step)

        # Ensure results are serializable #####################################################

        serializable_result = [list(item) for item in results]

        # Gather the results from all MPI processes ###########################################

        all_results = comm.gather(serializable_result, root=0)

        # Combine the results from all MPI processes ##########################################

        if rank == 0:
            root_results = list(itertools.chain(*all_results))

            self._print_simulation_results(root_results, sim_range, step)

            print(f"{'='*150}\n\n")

    def _parallel_circuit_simulation(self, sim_range: 'list[int]', step: int) -> None:
        """
        Simulates the circuit using multiprocessing.

        Args:
            sim_range ('list[int]'): The range of the simulation.
            step (int): The step index.
        """

        # reset the simulation results ########################################################

        self._simulation_results = multiprocessing.Manager().dict()
        if self._hpc:
            self._simulation_results = {}

        # use thread to load the simulation ###################################################

        if self._print_sim == "Loading":
            stop_event = threading.Event()
            loading_thread = threading.Thread(target=loading_animation, args=(stop_event, 'simulation',))
            loading_thread.start()

        # Use multiprocessing to parallelize the simulation ###################################

        try:
            results: 'list[tuple[int, int, int]]' = self._parallel_execution(sim_range, step)

        finally:
            if self._print_sim == "Loading":
                stop_event.set()
                loading_thread.join()

        self._print_simulation_results(results, sim_range, step)

    def _sequential_circuit_simulation(self, sim_range: 'list[int]', step: int) -> None:
        """
        Simulates the circuit without using multiprocessing.

        Args:
            range ('list[int]'): The range of the simulation.
            step (int): The step index.
        """

        # reset the simulation results ########################################################

        self._simulation_results = {}

        # simulation is not parallelized ######################################################

        results: 'list[tuple[int, int, int]]' = self._sequential_execution(sim_range, step)

        self._print_simulation_results(results, sim_range, step)
