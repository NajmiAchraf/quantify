from qramcircuits.bucket_brigade import ReverseMoments
from qramcircuits.qram_circuit_experiments import QRAMCircuitExperiments
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
        reverse_moments=ReverseMoments.OUT_TO_IN
    )


def main() -> int:
    """
    Main function for the QRAM circuit experiments.
    """

    T_Count = parser_args("experiment").parse_args().t_count

    # DEFAULT EXPERIMENT : AN0_TD4_TC7_CX6
    if T_Count == 7:
        Experiment(ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4)

    # FIRST EXPERIMENT : AN0_TD4_TC6_CX6
    elif T_Count == 6:
        Experiment(ToffoliDecompType.AN0_TD4_TC6_CX6)

    # SECOND EXPERIMENT : AN0_TD4_TC5_CX6
    elif T_Count == 5:
        Experiment(ToffoliDecompType.AN0_TD4_TC5_CX6)

    # THIRD EXPERIMENT : AN0_TD3_TC4_CX6
    elif T_Count == 4:
        Experiment(ToffoliDecompType.AN0_TD3_TC4_CX6)


if __name__ == "__main__":
    main()
