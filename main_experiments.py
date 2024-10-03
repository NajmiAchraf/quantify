from qramcircuits.bucket_brigade import ReverseMoments
from qramcircuits.qram_circuit_experiments import QRAMCircuitExperiments
from qramcircuits.toffoli_decomposition import ToffoliDecompType


"""
How to run the main_experiments.py file:

Run the following command in the terminal:

    python3 main_experiments.py

or by adding arguments:

    python3 main_experiments.py y p d 2 2

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


def main(T_Count: int) -> None:
    """
    Main function for the QRAM circuit experiments.
    """

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
    main(7)
