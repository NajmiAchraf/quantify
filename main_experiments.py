from typing import Tuple

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


def parse_args() -> Tuple[int, int]:
    """
    Parse the arguments for the experiments.
    """

    args = parser_args("experiment").parse_args()
    print(args)

    # T count for the stress test between 4 and 7
    T_Count = args.t_count
    if not (4 <= T_Count <= 7):
        raise ValueError("The T count should be between 4 and 7.")

    return T_Count


def main() -> int:
    """
    Main function for the QRAM circuit experiments.
    """

    try:
        T_Count = parse_args()
    except ValueError as e:
        colpr("r", f"Error: {e}")
        return 1

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
