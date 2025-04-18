from qram.circuit.assessment import QRAMCircuitAssessment
from qramcircuits.bucket_brigade import ReverseMoments
from qramcircuits.toffoli_decomposition import ToffoliDecompType
from utils.arg_parser import *
from utils.print_utils import *

#######################################
# QRAM Circuit Assessment
#######################################


def Assessment(QueryConfiguration: ToffoliDecompType) -> None:
    """
    Assessment function for the QRAM circuit assessment.
    """

    QRAMCircuitAssessment().bb_decompose_test(
        dec=[
            ToffoliDecompType.RELATIVE_PHASE_TD_4_CXD_3,
            ToffoliDecompType.AN0_TD4_TC7_CX6,
            ToffoliDecompType.RELATIVE_PHASE_TD_4_CXD_3,
        ],
        parallel_toffolis=True,
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
    Main function for the QRAM circuit assessment.
    """

    T_Count = parser_args("assessment").parse_args().t_count
    T_Depth = 3 if T_Count == 4 else 4

    Assessment(eval(f"ToffoliDecompType.AN0_TD{T_Depth}_TC{T_Count}_CX6"))

    return 0


if __name__ == "__main__":
    main()
