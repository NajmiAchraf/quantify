import time

import cirq

import optimizers as qopt
import qramcircuits.bucket_brigade as bb
from mathematics.draper0406142 import CarryLookaheadAdder
from qramcircuits.toffoli_decomposition import ToffoliDecomposition, ToffoliDecompType


def main():
    """
    print("Hello QRAM circuits!")

    #Create the qubis of the circuits

    nr_qubits = 5
    qubits = []
    for i in range(nr_qubits):
        qubits.append(cirq.NamedQubit("a" + str(i)))

    # #
    # #
    # # #Create the search
    # #
    search = [0, 1, 2, 3]
    # search = list(range(0, 15))
    #

    """
    # Bucket brigade
    """
    print("*** Bucket Brigade:")

    decomp_scenario = bb.BucketBrigadeDecompType(
        [
            ToffoliDecompType.AN0_TD4_TC7_CX6_COMPUTE,    # fan_in_decomp
            ToffoliDecompType.AN0_TD4_TC7_CX6,  # mem_decomp
            ToffoliDecompType.ZERO_ANCILLA_TDEPTH_0_UNCOMPUTE,    # fan_out_decomp
        ],
        True
    )

    no_decomp = bb.BucketBrigadeDecompType(
        [
            ToffoliDecompType.NO_DECOMP,  # fan_in_decomp
            ToffoliDecompType.AN0_TD4_TC7_CX6,  # mem_decomp
            ToffoliDecompType.NO_DECOMP,  # fan_out_decomp
        ],
        True
    )


    olivia_decomposition = bb.BucketBrigadeDecompType(
        [
            ToffoliDecompType.FOUR_ANCILLA_TDEPTH_1_A,    # fan_in_decomp
            ToffoliDecompType.FOUR_ANCILLA_TDEPTH_1_A,    # mem_decomp
            ToffoliDecompType.FOUR_ANCILLA_TDEPTH_1_A,    # fan_out_decomp
        ],
        False
    )

    bbcircuit = bb.BucketBrigade(qubits,
                                 decomp_scenario = decomp_scenario)
    #
    # print(bbcircuit.circuit.to_text_diagram(use_unicode_characters=False,
    #                                         qubit_order = bbcircuit.qubit_order))

    # #Verification
    print("Verify N_q:      {}\n".format(bbcircuit.verify_number_qubits()))
    print("Verify D:        {}\n".format(bbcircuit.verify_depth(
        Alexandru_scenario=decomp_scenario.parallel_toffolis))
    )
    print("Verify T_c:      {}\n".format(bbcircuit.verify_T_count()))
    print("Verify T_d:      {}\n".format(bbcircuit.verify_T_depth(
        Alexandru_scenario=decomp_scenario.parallel_toffolis))
    )
    print("Verify H_c:      {}\n".format(bbcircuit.verify_hadamard_count(
        Alexandru_scenario=decomp_scenario.parallel_toffolis))
    )
    print("Verify CNOT_c:   {}\n".format(bbcircuit.verify_cnot_count(
        Alexandru_scenario=olivia_decomposition.parallel_toffolis))
    )

    # qopt.CommuteTGatesToStart().optimize_circuit(bbcircuit.circuit)
    #
    # print(bbcircuit.circuit)

    # qopt.SearchCNOTPattern().optimize_circuit(bbcircuit.circuit)

    # qopt.CancelNghCNOTs().apply_until_nothing_changes(bbcircuit.circuit,
    #                                                   cu.count_cnot_of_circuit)
    # print(bbcircuit.circuit)
    # print("*** Large Depth Small Width:")
    # """
    # be sure while testing that the number of search values are a power of 2
    # and that the binary decomposition of each search value is less or equal to the number of qubits' address
    # like if we have 4 qubits then the search values should range between 0 and 15
    # """
    # ldsmcircuit = ldsw.LargeDepthSmallWidth(qubits,
    #                                         search,
    #                                         decomp_type = MPMCTDecompType.ALLOW_DECOMP)
    # print((ldsmcircuit.circuit))
    # print("Verify N_q:      {}\n".format(ldsmcircuit.verify_number_qubits()))
    # print("Verify D:        {}\n".format(ldsmcircuit.verify_depth()))
    # print("Verify T_c:      {}\n".format(ldsmcircuit.verify_T_count()))
    # print("Verify T_d:      {}\n".format(ldsmcircuit.verify_T_depth()))
    # print("Verify H_c:      {}\n".format(ldsmcircuit.verify_hadamard_count()))
    # print("Verify CNOT_c:   {}\n".format(ldsmcircuit.verify_cnot_count()))
    # #
    # qopt.CommuteTGatesToStart().optimize_circuit(ldsmcircuit.circuit)

    # print("*** Small Depth Large Width:")
    # #be sure while testing that the number of search values are a power of 2
    # #and that the binary decomposition of each search value is less or equal to the number of qubits' address
    # # like if we have 4 qubits then the search values should range between 0 and 15
    # sdlwcircuit = sdlw.SmallDepthLargeWidth(qubits,
    #                                         search,
    #                                         decomp_type = MPMCTDecompType.ALLOW_DECOMP)
    # print(sdlwcircuit.circuit)
    # print("Verify N_q:      {}\n".format(sdlwcircuit.verify_number_qubits()))
    # print("Verify D:        {}\n".format(sdlwcircuit.verify_depth()))  #still working on the depth
    # print("Verify T_d:      {}\n".format(sdlwcircuit.verify_T_depth()))
    # print("Verify T_c:      {}\n".format(sdlwcircuit.verify_T_count()))
    # print("Verify H_c:      {}\n".format(sdlwcircuit.verify_hadamard_count()))
    # print("Verify CNOT_c:   {}\n".format(sdlwcircuit.verify_cnot_count()))

    """
        CLA example
    """
    # Size of the operand; At this stage always gives the even number >= to the wanted size
    n = 10
    A = [cirq.NamedQubit("A" + str(i)) for i in range(n)]

    # Second operand
    B = [cirq.NamedQubit("B" + str(i)) for i in range(n)]

    # CLA class with the default decomposition strategy (NO_DECOMP)
    decompositon_strategy = [
        (ToffoliDecompType.NO_DECOMP, ToffoliDecompType.NO_DECOMP)
    ] * 2
    cl = CarryLookaheadAdder(A, B, decompositon_strategy=decompositon_strategy)
    # Printing the CLA circuit
    # print(cl.circuit)

    results = []
    for n in range(8, 32, 2):

        # First operand
        A = [cirq.NamedQubit("A" + str(i)) for i in range(n)]

        # Second operand
        B = [cirq.NamedQubit("B" + str(i)) for i in range(n)]

        # CLA class with the default decomposition strategy (NO_DECOMP)
        decompositon_strategy = [
            (ToffoliDecompType.NO_DECOMP, ToffoliDecompType.NO_DECOMP)
        ] * 2
        cl = CarryLookaheadAdder(A, B, decompositon_strategy=decompositon_strategy)
        # Printing the CLA circuit
        results.append(len(cl.circuit))
    print(results)


def main_linz():

    print("Hello QRAM circuit experiments!")

    qubits = []
    # for i in range(2, 16):
    for i in range(2, 5):

        nr_qubits = i

        qubits.clear()

        for i in range(nr_qubits):
            qubits.append(cirq.NamedQubit("a" + str(i)))

        # #
        # #
        # # #Create the search
        # #
        search = [0, 1, 2, 3]
        # search = list(range(0, 15))
        #

        """
            Bucket brigade
        """

        decomp_scenario = bb.BucketBrigadeDecompType(
            [
                # fan_in_decomp
                ToffoliDecompType.AN0_TD4_TC7_CX6_COMPUTE,
                # mem_decomp
                ToffoliDecompType.AN0_TD4_TC7_CX6,
                # fan_out_decomp
                ToffoliDecompType.ZERO_ANCILLA_TDEPTH_0_UNCOMPUTE,
            ],
            parallel_toffolis=False,
        )

        # *************************************************************************** #
        # Simulation without parallelization optimization                             #
        # *************************************************************************** #

        start1 = time.time()
        bbcircuitoff = bb.BucketBrigade(qubits, decomp_scenario=decomp_scenario)

        stop1 = time.time() - start1

        # print(bbcircuitoff.circuit.to_text_diagram(use_unicode_characters=False,
        #                                         qubit_order = bbcircuitoff.qubit_order))

        # print all operations in the circuit list
        operations = bbcircuitoff.circuit.all_operations()
        print(operations)
        for op in operations:
            # the T gate or the T**-1 gate
            if op.gate == cirq.T or op.gate == cirq.T**-1:
                pass
                # print(op)

        # run simulation without parallelization optimization
        bbcircuitoff.verify_number_qubits()
        bbcircuitoff.verify_depth(Alexandru_scenario=decomp_scenario.parallel_toffolis)

        # *************************************************************************** #
        # Simulation with parallelization optimization                                #
        # *************************************************************************** #

        decomp_scenario.parallel_toffolis = True
        start2 = time.time()
        bbcircuit = bb.BucketBrigade(qubits, decomp_scenario=decomp_scenario)
        stop2 = time.time() - start2

        # print(bbcircuit.circuit.to_text_diagram(use_unicode_characters=False,
        #                                         qubit_order=bbcircuit.qubit_order))

        # # Verification
        bbcircuit.verify_number_qubits()
        bbcircuit.verify_depth(Alexandru_scenario=decomp_scenario.parallel_toffolis)

        # bbcircuit.verify_T_count()
        # bbcircuit.verify_T_depth(
        #     Alexandru_scenario=decomp_scenario.parallel_toffolis)
        # bbcircuit.verify_hadamard_count(
        #     Alexandru_scenario=decomp_scenario.parallel_toffolis)
        # bbcircuit.verify_cnot_count(
        #     Alexandru_scenario=decomp_scenario.parallel_toffolis)

        # end = time.time()
        print(
            "--> exp bucket brigade, ",
            nr_qubits,
            ",",
            stop1,
            ",",
            stop2,
            ",",
            flush=True,
        )

    # qopt.CommuteTGatesToStart().optimize_circuit(bbcircuit.circuit)
    #
    # print(bbcircuit.circuit)

    # qopt.SearchCNOTPattern().optimize_circuit(bbcircuit.circuit)

    # qopt.CancelNghCNOTs().apply_until_nothing_changes(bbcircuit.circuit,
    #                                                   cu.count_cnot_of_circuit)
    # print(bbcircuit.circuit)
    # print("*** Large Depth Small Width:")
    # """
    # be sure while testing that the number of search values are a power of 2
    # and that the binary decomposition of each search value is less or equal to the number of qubits' address
    # like if we have 4 qubits then the search values should range between 0 and 15
    # """
    # ldsmcircuit = ldsw.LargeDepthSmallWidth(qubits,
    #                                         search,
    #                                         decomp_type = MPMCTDecompType.ALLOW_DECOMP)
    # print((ldsmcircuit.circuit))
    # print("Verify N_q:      {}\n".format(ldsmcircuit.verify_number_qubits()))
    # print("Verify D:        {}\n".format(ldsmcircuit.verify_depth()))
    # print("Verify T_c:      {}\n".format(ldsmcircuit.verify_T_count()))
    # print("Verify T_d:      {}\n".format(ldsmcircuit.verify_T_depth()))
    # print("Verify H_c:      {}\n".format(ldsmcircuit.verify_hadamard_count()))
    # print("Verify CNOT_c:   {}\n".format(ldsmcircuit.verify_cnot_count()))
    # #
    # qopt.CommuteTGatesToStart().optimize_circuit(ldsmcircuit.circuit)

    # print("*** Small Depth Large Width:")
    # #be sure while testing that the number of search values are a power of 2
    # #and that the binary decomposition of each search value is less or equal to the number of qubits' address
    # # like if we have 4 qubits then the search values should range between 0 and 15
    # sdlwcircuit = sdlw.SmallDepthLargeWidth(qubits,
    #                                         search,
    #                                         decomp_type = MPMCTDecompType.ALLOW_DECOMP)
    # print(sdlwcircuit.circuit)
    # print("Verify N_q:      {}\n".format(sdlwcircuit.verify_number_qubits()))
    # print("Verify D:        {}\n".format(sdlwcircuit.verify_depth()))  #still working on the depth
    # print("Verify T_d:      {}\n".format(sdlwcircuit.verify_T_depth()))
    # print("Verify T_c:      {}\n".format(sdlwcircuit.verify_T_count()))
    # print("Verify H_c:      {}\n".format(sdlwcircuit.verify_hadamard_count()))
    # print("Verify CNOT_c:   {}\n".format(sdlwcircuit.verify_cnot_count()))


if __name__ == "__main__":

    # import cProfile
    # cProfile.run("main()")
    main()
    main_linz()
