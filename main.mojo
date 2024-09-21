from python import Python
from sys import argv
from pathlib import cwd

def main():
    # Add the directory containing the modules to the Python path
    current_dir = str(cwd())
    Python.add_to_path(current_dir)

    # Import the modules as if they were Python modules
    sis = Python.import_module("sys")
    sis.argv = Python.list()

    for arg in argv():
        sis.argv.append(arg)

    ReverseMomentsModule = Python.import_module("qramcircuits.bucket_brigade")
    ReverseMoments = ReverseMomentsModule.ReverseMoments

    QRAMModule = Python.import_module("qramcircuits.qram_circuit_experiments")
    QRAM = QRAMModule.QRAMCircuitExperiments

    # QRAMSModule = Python.import_module("qramcircuits.qram_circuit_stress")
    # QRAMS = QRAMModule.QRAMCircuitsStress

    ToffoliDecompModule = Python.import_module("qramcircuits.toffoli_decomposition")
    ToffoliDecompType = ToffoliDecompModule.ToffoliDecompType

    bbr = Python.list()

    bbr.append(ToffoliDecompType.RELATIVE_PHASE_TD_4_CXD_3)
    bbr.append(ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4)
    bbr.append(ToffoliDecompType.RELATIVE_PHASE_TD_4_CXD_3)

    bbm = Python.list()

    bbm.append(ToffoliDecompType.RELATIVE_PHASE_TD_4_CXD_3)
    bbm.append(ToffoliDecompType.AN0_TD3_TC4_CX6)
    bbm.append(ToffoliDecompType.RELATIVE_PHASE_TD_4_CXD_3)

    # Call the function from the imported module
    QRAM().bb_decompose_test(
        dec=bbr,
        parallel_toffolis=True,
        dec_mod=bbm,
        parallel_toffolis_mod=True,
        reverse_moments=ReverseMoments.OUT_TO_IN
    )
