import multiprocessing
import threading

from qram.simulator.circuit_core import QRAMSimulatorCircuitCore
from utils.print_utils import loading_animation

#######################################
# QRAM Simulator Circuit Parallel
#######################################


class QRAMSimulatorCircuitParallel(QRAMSimulatorCircuitCore):
    """
    The QRAMSimulatorCircuitParallel class to simulate the bucket brigade circuit using multiprocessing.

    Methods:
        __init__(*args, **kwargs): Constructor of the QRAMSimulatorCircuitParallel class.
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Constructor of the QRAMSimulatorCircuitParallel class.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """

        super().__init__(*args, **kwargs)

        sim_range, step, message = self._circuit_configuration()

        self._begin_configurations()

        self._prints(sim_range, step, message)

        # reset the simulation results ########################################################

        self._simulation_results = multiprocessing.Manager().dict()
        if self._hpc:
            self._simulation_results = {}

        # use thread to load the simulation ###################################################

        if self._print_sim == "Loading":
            stop_event = threading.Event()
            loading_thread = threading.Thread(
                target=loading_animation,
                args=(
                    stop_event,
                    "simulation",
                ),
            )
            loading_thread.start()

        # Use multiprocessing to parallelize the simulation ###################################

        try:
            results: "list[tuple[int, int, int]]" = self._parallel_execution(
                sim_range, step
            )

        finally:
            if self._print_sim == "Loading":
                stop_event.set()
                loading_thread.join()

        self._print_simulation_results(results, sim_range, step)
