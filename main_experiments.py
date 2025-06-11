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
        dec_mod=[
            ToffoliDecompType.RELATIVE_PHASE_TD_4_CXD_3,  # fan_out
            ToffoliDecompType.RELATIVE_PHASE_TD_4_CXD_3,  # mem_write
            QueryConfiguration,  # mem_query
            ToffoliDecompType.RELATIVE_PHASE_TD_4_CXD_3,  # fan_in
            ToffoliDecompType.RELATIVE_PHASE_TD_4_CXD_3,  # mem_read
        ],
        parallel_toffolis_mod=True,
        reverse_moments=ReverseMoments.OUT_TO_IN,
    )


def main() -> int:
    """
    Main function for the QRAM circuit experiments.
    """

    T_Count = parser_args("experiments").parse_args().t_count
    T_Depth = 3 if T_Count == 4 else 4

    Experiment(eval(f"ToffoliDecompType.AN0_TD{T_Depth}_TC{T_Count}_CX6"))

    return 0


if __name__ == "__main__":
    main()
