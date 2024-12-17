from qramcircuits.bucket_brigade import ReverseMoments
from qram.circuit.bilan import QRAMCircuitBilan
from qramcircuits.toffoli_decomposition import ToffoliDecompType

from utils.arg_parser import *
from utils.print_utils import *


#######################################
# QRAM Circuit Bilan
#######################################


def Bilan(QueryConfiguration: ToffoliDecompType) -> None:
    """
    Bilan function for the QRAM circuit bilan.
    """

    QRAMCircuitBilan().bb_decompose_test(
        dec=[
            ToffoliDecompType.RELATIVE_PHASE_TD_4_CXD_3,
            ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
            ToffoliDecompType.RELATIVE_PHASE_TD_4_CXD_3,
        ],
        parallel_toffolis=True,

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
    Main function for the QRAM circuit bilan.
    """

    T_Count = parser_args("bilan").parse_args().t_count

    # FIRST BILAN : AN0_TD4_TC6_CX6
    if T_Count == 6:
        Bilan(ToffoliDecompType.AN0_TD4_TC6_CX6)

    # SECOND BILAN : AN0_TD4_TC5_CX6
    elif T_Count == 5:
        Bilan(ToffoliDecompType.AN0_TD4_TC5_CX6)

    # THIRD BILAN : AN0_TD3_TC4_CX6
    elif T_Count == 4:
        Bilan(ToffoliDecompType.AN0_TD3_TC4_CX6)

    return 0

if __name__ == "__main__":
    main()
