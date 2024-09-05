from qramcircuits.bucket_brigade import MirrorMethod
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

def main():
    """
    Main function for the QRAM circuit stress
    """

    # QRAMCircuitStress(2).bb_decompose_test(
    #     dec=ToffoliDecompType.NO_DECOMP,
    #     parallel_toffolis=False,

    #     dec_mod=[
    #         ToffoliDecompType.RELATIVE_PHASE_TD_4_CX_3,
    #         ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
    #         ToffoliDecompType.RELATIVE_PHASE_TD_4_CX_3,
    #     ],

    #     parallel_toffolis_mod=True,
    #     mirror_method=MirrorMethod.OUT_TO_IN
    # )

    QRAMCircuitStress(2).bb_decompose_test(
        dec=ToffoliDecompType.NO_DECOMP,
        parallel_toffolis=False,

        dec_mod=[
            ToffoliDecompType.RELATIVE_PHASE_TD_4_CX_3,
            ToffoliDecompType.ANCILLA_0_TD4_MOD,
            ToffoliDecompType.RELATIVE_PHASE_TD_4_CX_3,
        ],

        parallel_toffolis_mod=True,
        mirror_method=MirrorMethod.OUT_TO_IN
    )

if __name__ == "__main__":
    main()
