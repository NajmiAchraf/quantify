import copy
import itertools
import multiprocessing
import os
import time
from multiprocessing.managers import DictProxy

import cirq
import fasteners
import numpy as np

import optimizers as qopt
from qram.circuit.experiments import QRAMCircuitExperiments
from utils.counting_utils import *
from utils.print_utils import *

#######################################
# QRAM Circuit Stress
#######################################


class QRAMCircuitStress(QRAMCircuitExperiments):
    """
    QRAM circuit stress experiment.

    Attributes:
        _stress_assessment (DictProxy): The stress assessment.
        _combinations (itertools.combinations[tuple[int, ...]]): The combinations.
        __circuit_save (cirq.Circuit): The circuit save.
        __circuit_modded_save (cirq.Circuit): The modded circuit save.
        __length_combinations (int): The length of the combinations.
        __nbr_combinations (int): The number of combinations.
        __t_count (int): The T count.
        __rank (int): The rank of the MPI process.
        __chunk (int): The chunk size for the MPI process.

    Methods:
        __init__(nbr_combinations: int = 1): Initializes the QRAM circuit stress experiment.

        _core(nr_qubits: int): Core function of the experiment.
        _stress(): Stress experiment for the bucket brigade circuit.
        __initialize_circuits(): Initializes the circuits for the stress experiment.
        __generate_combinations(): Generates combinations of T gate indices.
        __simulate_local(combinations): Simulates the stress experiment locally.
        __simulate_with_multiprocessing(combinations): Uses multiprocessing to parallelize the stress testing.
        __simulate_sequentially(combinations): Simulates the stress experiment sequentially.
        __simulate_hpc(combinations): Uses MPI to parallelize the stress testing.
        __run_non_simulation(combinations): Runs the stress experiment without simulation.
        __extract_results(): Extracts and prints the results of the stress experiment.
        _stress_experiment(indices: tuple[int, ...]): Runs a single stress experiment.
        __print_assessment(): Prints the assessment of the stress experiment.
        __export_assessment(): Exports the assessment of the stress experiment.

        _simulate_circuit(): Simulates the circuit.
    """

    _stress_assessment: "DictProxy[str, list[str]]" = (
        multiprocessing.Manager().dict()
    )

    _combinations: "itertools.combinations[tuple[int, ...]]"

    __circuit_save: cirq.Circuit
    __circuit_modded_save: cirq.Circuit

    __length_combinations: int = 0
    __nbr_combinations: int = 1
    __t_count: int = 2

    __rank: int
    __chunk: int

    def __init__(self, nbr_combinations: int = 1) -> None:
        super().__init__()

        self.__nbr_combinations = nbr_combinations

    #######################################
    # core functions
    #######################################

    def _core(self, nr_qubits: int) -> None:
        """
        Core function of the experiment.
        """

        super(QRAMCircuitExperiments, self)._core(qram_bits=nr_qubits)

        self._stress()

    def _stress(self) -> None:
        """
        Stress experiment for the bucket brigade circuit.
        """

        self.__initialize_circuits()
        self._start_time = time.time()
        combinations = self.__generate_combinations()

        if self._simulate and not self._hpc:
            self.__simulate_local(combinations)
        elif self._simulate and self._hpc:
            self.__simulate_hpc(combinations)
        elif not self._simulate and not self._hpc:
            self.__run_non_simulation(combinations)

    def __initialize_circuits(self):
        self.__circuit_save = copy.deepcopy(self._bbcircuit.circuit)
        self.__circuit_modded_save = copy.deepcopy(
            self._bbcircuit_modded.circuit
        )
        self.__t_count = count_t_of_circuit(self.__circuit_modded_save)

    def __generate_combinations(self):
        combinations = itertools.combinations(
            range(1, self.__t_count + 1), self.__nbr_combinations
        )
        self._combinations = copy.deepcopy(combinations)
        return combinations

    def __simulate_local(self, combinations):
        self.__simulate_sequentially(combinations)
        self.__extract_results()

    def __simulate_sequentially(self, combinations):
        """
        On each combination, we use multiprocessing to parallelize the stress testing
        """

        for indices in combinations:
            self._stress_experiment(indices)
            self.__length_combinations += 1

    def __simulate_hpc(self, combinations):
        """
        Use MPI to parallelize the stress testing
        """

        from mpi4py import MPI

        # Initialize MPI
        comm = MPI.COMM_WORLD
        self.__rank = comm.Get_rank()
        size = comm.Get_size()

        # Determine the range of work for this MPI process
        total_work = list(copy.deepcopy(combinations))

        # Split the total work into chunks based on the number of ranks
        work_chunks = np.array_split(total_work, size)
        local_work = (
            work_chunks[self.__rank] if self.__rank < len(work_chunks) else []
        )
        self.__chunk = (
            len(work_chunks[self.__rank])
            if self.__rank < len(work_chunks)
            else 0
        )

        result = []
        for indices in local_work:
            self.__length_combinations += 1
            result.append(self._stress_experiment(indices))

        # Ensure results are serializable
        serializable_result = {
            map_name: value
            for item in result
            for map_name, value in item.items()
        }

        # Gather results from all MPI processes
        results = comm.gather(serializable_result, root=0)

        if self.__rank == 0:
            self.__length_combinations = 0
            for _ in combinations:
                self.__length_combinations += 1

            for item in results:
                for map_name, value in item.items():
                    if len(value) != 0:
                        self._stress_assessment[map_name] = value

            self.__extract_results()

    def __run_non_simulation(self, combinations):
        for indices in combinations:
            time.sleep(0.5)
            self._stress_experiment(indices)
            self.__length_combinations += 1
        self.__extract_results()

    def __extract_results(self):
        """
        Extract the results.
        """

        self._stop_time = elapsed_time(self._start_time)
        if self._simulate:
            self.__print_assessment()
            self.__export_assessment()

        # Print completion summary with Rich formatting
        completion_panel = Panel(
            f"[bold green]✅ Stress Testing Completed![/bold green]\n"
            f"[cyan]• Total Combinations Tested:[/cyan] [bold white]{self.__length_combinations:,}[/bold white]\n"
            f"[cyan]• Time Elapsed:[/cyan] [bold yellow]{self._stop_time}[/bold yellow]",
            title="[bold]🧪 Stress Test Summary",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
        console.print(completion_panel)
        console.print("", style="white", end="")  # Reset color
        console.print()

    def _stress_experiment(
        self, indices: "tuple[int, ...]"
    ) -> "DictProxy[str, list[str]]":
        """
        Stress experiment for the bucket brigade circuit.

        Args:
            indices (tuple[int, ...]): The indices.
        """

        # Ensure the lock file exists
        lock_file = "file.lock"
        if not os.path.exists(lock_file):
            open(lock_file, "w").close()

        start = time.time()

        with fasteners.InterProcessLock(lock_file):
            if self._hpc:
                print_stress_experiment_header(
                    indices,
                    rank=self.__rank,
                    current=self.__length_combinations,
                    total=self.__chunk,
                )
            else:
                print_stress_experiment_header(indices)

        self._bbcircuit.circuit = copy.deepcopy(self.__circuit_save)
        self._bbcircuit_modded.circuit = copy.deepcopy(
            self.__circuit_modded_save
        )

        self._bbcircuit_modded.circuit = qopt.CancelTGate(
            self._bbcircuit_modded.circuit, self._bbcircuit_modded.qubit_order
        ).optimize_circuit(indices)

        self._simulated = False
        self._results()

        if self._simulate:
            self._stress_assessment[",".join(map(str, indices))] = (
                self._simulator_manager.get_simulation_assessment()
            )

        elapsed = elapsed_time(start)

        with fasteners.InterProcessLock(lock_file):
            if self._hpc:
                print_stress_experiment_completion(
                    indices,
                    elapsed,
                    rank=self.__rank,
                    current=self.__length_combinations,
                    total=self.__chunk,
                )
            else:
                print_stress_experiment_completion(indices, elapsed)

        return self._stress_assessment

    #######################################
    # print and export assessment methods
    #######################################

    def __print_assessment(self) -> None:
        """
        Print the assessment of the stress experiment.
        """

        title = "🧪 Stress Experiment Assessment"

        # Create main title panel
        title_panel = Panel(
            Text(title, style="bold yellow", justify="center"),
            border_style="yellow",
            box=box.DOUBLE_EDGE,
        )
        console.print()
        console.print(title_panel)
        console.print("", style="white", end="")  # Reset color
        console.print()

        # Create assessment table
        table = Table(
            title="📊 Stress Test Results",
            show_header=True,
            header_style="bold white",
            box=box.ROUNDED,
            title_style="bold cyan",
        )

        # Calculate the required width for the "T Gate Index" column
        t_gate_index_width = max(20, self.__nbr_combinations * 3 + 13)

        table.add_column(
            "T Gate Index", style="bold cyan", width=t_gate_index_width
        )
        table.add_column("Failed (%)", style="bold red", justify="center")
        table.add_column("Succeed (%)", style="bold green", justify="center")
        table.add_column(
            "Measurements (%)", style="bold yellow", justify="center"
        )
        table.add_column(
            "Output Vector (%)", style="bold blue", justify="center"
        )

        copied_combinations = copy.deepcopy(self._combinations)

        # Add data rows
        for indices in copied_combinations:
            bil = ",".join(map(str, indices))
            assessment = self._stress_assessment[bil]

            table.add_row(
                bil, assessment[0], assessment[1], assessment[2], assessment[3]
            )

        console.print(table)
        console.print("", style="white", end="")  # Reset color
        console.print()

    def __export_assessment(self) -> None:
        """
        Export the assessment of the stress experiment.
        """

        # Create export header with Rich formatting
        export_panel = Panel(
            "[bold blue]📁 Exporting Stress Assessment Results...[/bold blue]",
            border_style="blue",
            box=box.ROUNDED,
        )
        console.print(export_panel)
        console.print("", style="white", end="")  # Reset color

        csv = "T Gate Index 0"
        for i in range(self.__nbr_combinations - 1):
            csv += f",T Gate Index {i + 1}"

        csv += ",Failed (%),Succeed (%),Measurements (%),Output Vector (%)\n"
        for indices in self._combinations:
            bil = ",".join(map(str, indices))
            csv += f"{bil},{self._stress_assessment[bil][0]},{self._stress_assessment[bil][1]},{self._stress_assessment[bil][2]},{self._stress_assessment[bil][3]}\n"

        directory = f"data/{self._decomp_scenario_modded.dec_mem_query}"
        if not os.path.exists(directory):
            os.makedirs(directory)
        time_elapsed = self._stop_time.replace(" ", "")
        time_stamp_start = time.strftime(
            "%Y%m%d-%H%M%S", time.localtime(self._start_time)
        )
        time_stamp_end = time.strftime("%Y%m%d-%H%M%S")

        filename = (
            f"{directory}/stress"
            f"_{self._start_range_qubits}qubits"
            f"_{self.__t_count}T"
            f"_{self.__nbr_combinations}-comb"
            f"_{self.__length_combinations}-{self._specific_simulation}-tests"
            f"_{self._shots}-shots"
            f"_{time_elapsed}"
            f"_{time_stamp_start}"
            f"_{time_stamp_end}.csv"
        )

        # export in file
        with open(filename, "w") as file:
            file.write(csv)

        # Success export message
        export_success_panel = Panel(
            f"[bold green]✅ Export Completed![/bold green]\n"
            f"[cyan]📁 File:[/cyan] [white]{filename}[/white]\n"
            f"[cyan]📊 Records:[/cyan] [white]{len(self._stress_assessment):,}[/white]",
            title="[bold]Export Success",
            border_style="green",
            box=box.ROUNDED,
        )
        console.print(export_success_panel)
        console.print("", style="white", end="")  # Reset color
        console.print()

    #######################################
    # simulate circuit method
    #######################################

    def _simulate_circuit(self) -> None:
        """
        Simulates the circuit.
        """

        super()._simulate_circuit(is_stress=True)
