from qram.circuit.stress import QRAMCircuitStress
from qram.bucket_brigade.decomp_type import ReverseMoments
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
    Main function for the QRAM circuit stress
    """

    args = parser_args("stress").parse_args()

    T_Count = args.t_count
    T_Cancel = args.t_cancel
    T_Depth = 3 if T_Count == 4 else 4

    Stress(
        eval(f"ToffoliDecompType.AN0_TD{T_Depth}_TC{T_Count}_CX6"), T_Cancel
    )

    return 0


if __name__ == "__main__":
    main()
