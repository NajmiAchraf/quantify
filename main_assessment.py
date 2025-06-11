from qram.circuit.assessment import QRAMCircuitAssessment
from qram.bucket_brigade.decomp_type import ReverseMoments
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
            ToffoliDecompType.RELATIVE_PHASE_TD_4_CXD_3,  # fan_in
            ToffoliDecompType.RELATIVE_PHASE_TD_4_CXD_3,  # mem_write
            ToffoliDecompType.AN0_TD4_TC7_CX6,  # mem_query
            ToffoliDecompType.RELATIVE_PHASE_TD_4_CXD_3,  # mem_read
            ToffoliDecompType.RELATIVE_PHASE_TD_4_CXD_3,  # fan_out
        ],
        parallel_toffolis=True,
        dec_mod=[
            ToffoliDecompType.RELATIVE_PHASE_TD_4_CXD_3,  # fan_in
            ToffoliDecompType.RELATIVE_PHASE_TD_4_CXD_3,  # mem_write
            QueryConfiguration,  # mem_query
            ToffoliDecompType.RELATIVE_PHASE_TD_4_CXD_3,  # mem_read
            ToffoliDecompType.RELATIVE_PHASE_TD_4_CXD_3,  # fan_out
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
