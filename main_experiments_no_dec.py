from qram.bucket_brigade.decomp_type import ReverseMoments
from qram.circuit.experiments import QRAMCircuitExperiments
from qramcircuits.toffoli_decomposition import ToffoliDecompType
from utils.arg_parser import *
from utils.print_utils import *

#######################################
# QRAM Circuit Experiments
#######################################


def Experiment(QueryConfiguration: ToffoliDecompType) -> None:
    """
    Experiment function for the QRAM circuit experiments.
    """

    QRAMCircuitExperiments().bb_decompose_test(
        dec=ToffoliDecompType.NO_DECOMP,
        parallel_toffolis=False,
        dec_mod=ToffoliDecompType.NO_DECOMP,
        parallel_toffolis_mod=False,
        reverse_moments=ReverseMoments.OUT_TO_IN,
    )


def main() -> int:
    """
    Main function for the QRAM circuit experiments.
    """

    Experiment(eval(f"ToffoliDecompType.AN0_TD{T_Depth}_TC{T_Count}_CX6"))

    return 0


if __name__ == "__main__":
    main()
