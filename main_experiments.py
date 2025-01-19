from qram.circuit.experiments import QRAMCircuitExperiments
from qramcircuits.bucket_brigade import ReverseMoments
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
        dec_mod=[
            ToffoliDecompType.RELATIVE_PHASE_TD_4_CXD_3,
            QueryConfiguration,
            ToffoliDecompType.RELATIVE_PHASE_TD_4_CXD_3,
        ],
        parallel_toffolis_mod=True,
        reverse_moments=ReverseMoments.OUT_TO_IN,
    )


def main() -> int:
    """
    Main function for the QRAM circuit experiments.
    """

    T_Count = parser_args("experiments").parse_args().t_count

    Experiment(eval(f"ToffoliDecompType.AN0_TD4_TC{T_Count}_CX6"))

    return 0


if __name__ == "__main__":
    main()
