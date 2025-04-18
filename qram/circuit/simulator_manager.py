from qram.simulator.base import QRAMSimulatorBase
from qram.simulator.circuit_hpc import QRAMSimulatorCircuitHPC
from qram.simulator.circuit_parallel import QRAMSimulatorCircuitParallel
from qram.simulator.circuit_sequential import QRAMSimulatorCircuitSequential
from qram.simulator.decomposition import QRAMSimulatorDecompositions

#######################################
# QRAM Circuit Simulator Manager
#######################################


class QRAMCircuitSimulatorManager:
    """
    The QRAMCircuitSimulatorManager class to manage the QRAM circuit simulation.

    Methods:
        __init__(*args, **kwargs): Constructor of the QRAMCircuitSimulatorManager class.
        get_simulation_assessment(): Returns the simulation assessment.
        _run_simulation(is_stress: bool = False): Runs the simulation.
    """

    _simulator: "QRAMSimulatorBase"

    def __init__(self, *args, **kwargs) -> None:
        """
        Constructor of the QRAMCircuitSimulatorManager class.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """

        self.args = args
        self.kwargs = kwargs

    def get_simulation_assessment(self) -> "list[str]":
        return self._simulator.get_simulation_assessment()

    def _run_simulation(self, is_stress: bool = False) -> None:
        """
        Runs the simulation.

        Args:
            is_stress (bool): If True, runs the simulation in stress mode which hides the simulation print output.
        """

        if is_stress:
            self.kwargs["print_sim"] = "Hide"
        elif not is_stress and not self.kwargs.get("hpc"):
            QRAMSimulatorDecompositions(*self.args, **self.kwargs)

        if self.kwargs.get("hpc"):
            self._simulator = QRAMSimulatorCircuitHPC(
                is_stress, *self.args, **self.kwargs
            )
        elif not self.kwargs.get("hpc"):
            if self.kwargs.get("specific_simulation") != "full":
                self._simulator = QRAMSimulatorCircuitSequential(
                    is_stress, *self.args, **self.kwargs
                )
            else:
                self._simulator = QRAMSimulatorCircuitParallel(
                    is_stress, *self.args, **self.kwargs
                )
