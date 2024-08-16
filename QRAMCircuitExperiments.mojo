# import os.path as path
from python import Python
from sys import argv

def main():
    # # Add the directory containing the modules to the Python path
    Python.add_to_path('/home/anajmi/Desktop/quantify-mojo')

    # current_dir = path.dirname(path.abspath(__file__))
    # module_dir = path.join(current_dir, 'quantify-mojo')
    # Python.add_to_path(module_dir)

    # Import the modules as if they were Python modules
    sis = Python.import_module("sys")
    sis.argv = Python.list()

    for arg in argv():
        sis.argv.append(arg)

    QRAMModule = Python.import_module("QRAMCircuitExperiments")
    QRAM = QRAMModule.QRAMCircuitExperiments

    ToffoliDecompModule = Python.import_module("qramcircuits.toffoli_decomposition")
    ToffoliDecompType = ToffoliDecompModule.ToffoliDecompType

    MirrorMethodModule = Python.import_module("qramcircuits.bucket_brigade")
    MirrorMethod = MirrorMethodModule.MirrorMethod

    ls0 = Python.list()

    ls0.append(ToffoliDecompType.RELATIVE_PHASE_TD_4_CX_3)
    ls0.append(ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4)
    ls0.append(ToffoliDecompType.RELATIVE_PHASE_TD_4_CX_3)

    ls1 = Python.list()

    ls1.append(ToffoliDecompType.RELATIVE_PHASE_TD_4_CX_3)
    ls1.append(ToffoliDecompType.ANCILLA_0_TD4_MOD)
    ls1.append(ToffoliDecompType.RELATIVE_PHASE_TD_4_CX_3)

    # Call the function from the imported module
    QRAM().bb_decompose_test(
        dec=ls0,
        parallel_toffolis=True,
        dec_mod=ls1,
        parallel_toffolis_mod=True,
        mirror_method=MirrorMethod.OUT_TO_IN
    )
