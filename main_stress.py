from qramcircuits.bucket_brigade import ReverseMoments
from qram.circuit.stress import QRAMCircuitStress
from qramcircuits.toffoli_decomposition import ToffoliDecompType

from utils.arg_parser import *
from utils.print_utils import *


#######################################
# QRAM Circuit Stress
#######################################


def Stress(QueryConfiguration: ToffoliDecompType, T_Cancel: int) -> None:
    """
    Experiment function for the QRAM circuit experiments.
    """

    QRAMCircuitStress(T_Cancel).bb_decompose_test(
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
    Main function for the QRAM circuit stress
    """

    args = parser_args("stress").parse_args()

    T_Count = args.t_count
    T_Cancel = args.t_cancel

    # DEFAULT EXPERIMENT : Stress test for AN0_TD4_TC7_CX6
    if T_Count == 7:
        Stress(ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4, T_Cancel)

    # FIRST EXPERIMENT : Stress test for AN0_TD4_TC6_CX6
    elif T_Count == 6:
        Stress(ToffoliDecompType.AN0_TD4_TC6_CX6, T_Cancel)

    # SECOND EXPERIMENT : Stress test for AN0_TD4_TC5_CX6
    elif T_Count == 5:
        Stress(ToffoliDecompType.AN0_TD4_TC5_CX6, T_Cancel)

    # THIRD EXPERIMENT : Stress test for AN0_TD3_TC4_CX6
    elif T_Count == 4:
        Stress(ToffoliDecompType.AN0_TD3_TC4_CX6, T_Cancel)

    return 0

if __name__ == "__main__":
    main()
