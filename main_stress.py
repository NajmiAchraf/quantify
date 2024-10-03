from qramcircuits.bucket_brigade import ReverseMoments
from qramcircuits.qram_circuit_stress import QRAMCircuitStress
from qramcircuits.toffoli_decomposition import ToffoliDecompType


"""
How to run the main_stress.py file:

Run the following command in the terminal:

    python3 main_stress.py

or by adding arguments:

    python3 main_stress.py y h h 2 2

Arguments:
- arg 1: Simulate Toffoli decompositions and circuit (y/n).
- arg 2: (P) print or (D) display or (H) hide circuits.
- arg 3: (F) full simulation or (D) just dots or (H) hide the simulation.
- arg 4: Start range of qubits, starting from 2.
- arg 5: End range of qubits, should be equal to or greater than the start range.
- additional arg 6: Specific simulation (a, b, m, ab, bm, abm, t).
    leave it empty to simulate the full circuit.
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


def main(T_Count: int, T_Cancel: int) -> None:
    """
    Main function for the QRAM circuit stress
    """

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
    main(
        T_Count=6,
        T_Cancel=1
    )
