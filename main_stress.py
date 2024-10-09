from typing import Tuple

from qramcircuits.bucket_brigade import ReverseMoments
from qramcircuits.qram_circuit_stress import QRAMCircuitStress
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


def parse_args() -> Tuple[int, int]:
    """
    Parse the arguments for the stress test.
    """

    args = parser_args("stress").parse_args()

    # T count for the stress test between 4 and 7
    T_Count = args.t_count
    if not (4 <= T_Count <= 7):
        raise ValueError("The T count should be between 4 and 7.")
    
    # T cancel for the stress test above 1
    T_Cancel = args.t_cancel
    if T_Cancel < 1:
        raise ValueError("The T cancel should be greater than 1.")
    
    return T_Count, T_Cancel


def main() -> int:
    """
    Main function for the QRAM circuit stress
    """

    try:
        T_Count, T_Cancel = parse_args()
    except ValueError as e:
        colpr("r", f"Error: {e}")
        return 1

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


if __name__ == "__main__":
    main()
