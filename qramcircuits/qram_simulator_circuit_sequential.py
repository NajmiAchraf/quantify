from qramcircuits.qram_simulator_circuit_core import QRAMSimulatorCircuitCore


#######################################
# QRAM Simulator Circuit Sequential
#######################################

class QRAMSimulatorCircuitSequential(QRAMSimulatorCircuitCore):
    """
    The QRAMSimulatorCircuitSequential class to simulate the bucket brigade circuit sequentially.

    Methods:
        __init__(*args, **kwargs): Constructor of the QRAMSimulatorCircuitSequential class
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Constructor of the QRAMSimulatorCircuitSequential class.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """

        super().__init__(*args, **kwargs)

        sim_range, step, message = self._circuit_configuration()

        self._begin_configurations()

        self._prints(sim_range, step, message)

        # reset the simulation results ########################################################

        self._simulation_results = {}

        # simulation is not parallelized ######################################################

        results: 'list[tuple[int, int, int]]' = self._sequential_execution(sim_range, step)

        self._print_simulation_results(results, sim_range, step)
