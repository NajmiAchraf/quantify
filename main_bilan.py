from typing import Tuple

from qramcircuits.bucket_brigade import ReverseMoments
from qramcircuits.qram_circuit_bilan import QRAMCircuitBilan
from qramcircuits.toffoli_decomposition import ToffoliDecompType

from utils.arg_parser import *
from utils.print_utils import *


"""
How to run the main_bilan.py file:

Run the following command in the terminal:

    python3 main_bilan.py

or by adding arguments:

    python3 main__main_bilan.py --t_count=7 --simulate --print-circuit=p --print-simulation=f --start=2 --end=2 --specific=a

Arguments:
    --t_count: The T count for the QueryConfiguration.

Arguments (optional):
    --simulate: Simulate Toffoli decompositions and circuit (flag, no value needed).
    --print-circuit: (p) print or (d) display or (h) hide circuits.
    --print-simulation: (f) full simulation or (d) just dots or (l) loading or (h) hide the simulation.
    --start: Start range of qubits, starting from 2.
    --end: End range of qubits, should be equal to or greater than the start range.
    --specific: Specific simulation (a, b, m, ab, bm, abm, t). by default simulate the full circuit
"""


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


def parse_args() -> Tuple[int, int]:
    """
    Parse the arguments for the bilan.
    """

    args = parser_args("bilan").parse_args()

    # T count for the stress test between 4 and 7
    T_Count = args.t_count
    if not (4 <= T_Count <= 7):
        raise ValueError("The T count should be between 4 and 7.")

    return T_Count


def main() -> int:
    """
    Main function for the QRAM circuit bilan.
    """

    try:
        T_Count = parse_args()
    except ValueError as e:
        colpr("r", f"Error: {e}")
        return 1

    # FIRST BILAN : AN0_TD4_TC6_CX6
    if T_Count == 6:
        Bilan(ToffoliDecompType.AN0_TD4_TC6_CX6)

    # SECOND BILAN : AN0_TD4_TC5_CX6
    elif T_Count == 5:
        Bilan(ToffoliDecompType.AN0_TD4_TC5_CX6)

    # THIRD BILAN : AN0_TD3_TC4_CX6
    elif T_Count == 4:
        Bilan(ToffoliDecompType.AN0_TD3_TC4_CX6)


if __name__ == "__main__":
    main()
