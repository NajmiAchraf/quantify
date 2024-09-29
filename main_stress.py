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

def main():
    """
    Main function for the QRAM circuit stress
    """

    """ 20 cores - 40T : 2s 800 ms * nbr combinations
    1T : 40 combinations (2min 40s)
    2T : 780 combinations (33min 20s)
    3T : 9880 combinations (6h 53min 20s)
    4T : 91390 combinations (2d 1h 43min 20s)
    5T : 655200 combinations (7d 14h 40min)
    6T : 3769920 combinations (43d 14h 40min)
    7T : 17710040 combinations (4mo 1d 14h 40min)
    8T : 70840320 combinations (1yr 1mo 1d 14h 40min)
    9T : 248125560 combinations (3yr 10mo 1d 14h 40min)
    10T: 775587120 combinations (12yr 3mo 1d 14h 40min)
    11T: 2147418000 combinations (33yr 1mo 1d 14h 40min)
    12T: 5368545000 combinations (82yr 1mo 1d 14h 40min)
    13T: 12175663500 combinations (186yr 1mo 1d 14h 40min)
    14T: 25140840600 combinations (384yr 1mo 1d 14h 40min)
    15T: 47890098560 combinations (730yr 1mo 1d 14h 40min)
    16T: 84884442625 combinations (1290yr 1mo 1d 14h 40min)
    17T: 139197564450 combinations (2119yr 1mo 1d 14h 40min)
    18T: 213458046575 combinations (3240yr 1mo 1d 14h 40min)
    19T: 308585716355 combinations (4690yr 1mo 1d 14h 40min)
    
    20T: 424442148451 combinations (6450yr 1mo 1d 14h 40min)

    ...

    39T: 40 combinations (2min 40s)
    40T: 1 combinations (2s 800 ms)
    """

    # QRAMCircuitStress(1).bb_decompose_test(
    #     dec=ToffoliDecompType.NO_DECOMP,
    #     parallel_toffolis=False,

    #     dec_mod=[
    #         ToffoliDecompType.RELATIVE_PHASE_TD_4_CXD_3,
    #         ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
    #         ToffoliDecompType.RELATIVE_PHASE_TD_4_CXD_3,
    #     ],

    #     parallel_toffolis_mod=True,
    #     reverse_moments=ReverseMoments.OUT_TO_IN
    # )

    """ 20 cores - 28T : 2s 800 ms * nbr combinations
    1T : 28 combinations (1min 45s)
    2T : 378 combinations (17min 15s)
    3T : 3276 combinations (2h 32min 52s)
    4T : 20475 combinations (15h 55min 30s)
    5T : 98280 combinations (3d 4h 26min 24s)
    6T : 376740 combinations (12d 5h 1min 12s)
    7T : 1184040 combinations (1mo 10d 10h 20min 40s)
    8T : 3108105 combinations (3mo 1d 1h 35min 20s)
    9T : 6906900 combinations (6mo 1d 1h 35min 20s)
    10T: 13123110 combinations (1yr 1mo 1d 1h 35min 20s)
    11T: 21474180 combinations (1yr 8mo 1d 1h 35min 20s)
    12T: 30421755 combinations (1yr 11mo 1d 1h 35min 20s)
    13T: 37442160 combinations (2yr 1mo 1d 1h 35min 20s)

    14T: 40116600 combinations (2yr 2mo 1d 1h 35min 20s)

    15T: 37442160 combinations (2yr 1mo 1d 1h 35min 20s)
    16T: 30421755 combinations (1yr 11mo 1d 1h 35min 20s)
    17T: 21474180 combinations (1yr 8mo 1d 1h 35min 20s)
    18T: 13123110 combinations (1yr 1mo 1d 1h 35min 20s)
    19T: 6906900 combinations (6mo 1d 1h 35min 20s)
    20T: 3108105 combinations (3mo 1d 1h 35min 20s)
    21T: 1184040 combinations (1mo 10d 10h 20min 40s)
    22T: 376740 combinations (12d 5h 1min 12s)
    23T: 98280 combinations (3d 4h 26min 24s)
    24T: 20475 combinations (15h 55min 30s)
    25T: 3276 combinations (2h 32min 52s)
    26T: 378 combinations (17min 15s)
    27T: 28 combinations (1min 45s)
    28T: 1 combinations (1s 630 ms)
    """

    QRAMCircuitStress(1).bb_decompose_test(
        dec=ToffoliDecompType.NO_DECOMP,
        parallel_toffolis=False,

        dec_mod=[
            ToffoliDecompType.RELATIVE_PHASE_TD_4_CXD_3,
            ToffoliDecompType.AN0_TD3_TC4_CX6,
            ToffoliDecompType.RELATIVE_PHASE_TD_4_CXD_3,
        ],

        parallel_toffolis_mod=True,
        reverse_moments=ReverseMoments.OUT_TO_IN
    )

if __name__ == "__main__":
    main()
