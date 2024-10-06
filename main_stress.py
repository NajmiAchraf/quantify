from typing import Tuple

from qramcircuits.bucket_brigade import ReverseMoments
from qramcircuits.qram_circuit_stress import QRAMCircuitStress
from qramcircuits.toffoli_decomposition import ToffoliDecompType

from utils.arg_parser import *
from utils.print_utils import *


"""
How to run the main_stress.py file:

Run the following command in the terminal:

    python3 main_stress.py

or by adding arguments:

    python3 main__stress.py --t_count=7 --t_cancel=2 --simulate --print-circuit=p --print-simulation=f --start=2 --end=2 --specific=a

Arguments:
    --t_count: The T count for the QueryConfiguration.
    --t_cancel: The T cancel for the combinations.

Arguments (optional):
    --simulate: Simulate Toffoli decompositions and circuit (flag, no value needed).
    --print-circuit: (p) print or (d) display or (h) hide circuits.
    --print-simulation: (f) full simulation or (d) just dots or (l) loading or (h) hide the simulation.
    --start: Start range of qubits, starting from 2.
    --end: End range of qubits, should be equal to or greater than the start range.
    --specific: Specific simulation (a, b, m, ab, bm, abm, t). by default simulate the full circuit
"""


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
