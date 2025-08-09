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

    CVX_ID = parser_args("experiments_cv_cx").parse_args().cvx_id

    Experiment(eval(f"ToffoliDecompType.CV_CX_QC5_{CVX_ID}"))

    return 0


if __name__ == "__main__":
    main()
