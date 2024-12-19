import itertools

try:
    from mpi4py import MPI
except ImportError:
    pass

from qram.simulator.circuit_core import QRAMSimulatorCircuitCore
from qramcircuits.toffoli_decomposition import ToffoliDecompType
from utils.print_utils import colpr, printRange

#######################################
# QRAM Simulator Circuit HPC
#######################################


class QRAMSimulatorCircuitHPC(QRAMSimulatorCircuitCore):
    """
    The QRAMSimulatorCircuitHPC class to simulate the bucket brigade circuit on high-performance computing.

    Methods:
        __init__(*args, **kwargs): Constructor of the QRAMSimulatorCircuitHPC class.
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Constructor of the QRAMSimulatorCircuitHPC class.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """

        super().__init__(*args, **kwargs)

        sim_range, step, message = self._circuit_configuration()

        self._begin_configurations()

        # Initialize MPI ######################################################################

        comm = MPI.COMM_WORLD
        rank = comm.Get_rank()
        size = comm.Get_size()

        # Prints ##############################################################################

        if rank == 0 and not self._is_stress:
            print(f"{'='*150}\n\n")

            name = (
                "bucket brigade"
                if self._decomp_scenario.get_decomp_types()[0]
                == ToffoliDecompType.NO_DECOMP
                else "reference"
            )

            printRange(sim_range[0], sim_range[-1], step)

            colpr(
                "c",
                f"Simulating both the modded and {name} circuits and comparing their output vector and measurements ...",
                end="\n\n",
            )

        # Split the total work into chunks based on the number of ranks #######################

        chunk_size_per_rank = len(sim_range) // size
        if rank < size - 1:
            local_work_range = sim_range[
                rank * chunk_size_per_rank : (rank + 1) * chunk_size_per_rank
            ]
        else:
            local_work_range = sim_range[rank * chunk_size_per_rank :]

        # wait for all MPI processes to reach this point ######################################

        comm.Barrier()

        # reset the simulation results ########################################################

        self._simulation_results = {}

        # Use multiprocessing to parallelize the simulation ###################################

        results: "list[tuple[int, int, int]]" = []

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

            if not self._is_stress:
                print(f"{'='*150}\n\n")
