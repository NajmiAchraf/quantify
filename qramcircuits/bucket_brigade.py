import cirq
from enum import Enum, auto
import multiprocessing
import numpy as np

import optimizers as qopt
from qramcircuits.toffoli_decomposition import ToffoliDecomposition, ToffoliDecompType

import utils.clifford_t_utils as ctu
import utils.misc_utils as miscutils

from utils.counting_utils import *
from utils.print_utils import *


class ReverseMoments(Enum):

    NO_REVERSE = auto()

    IN_TO_OUT = auto()

    OUT_TO_IN = auto()


class BucketBrigadeDecompType:
    def __init__(self, toffoli_decomp_types, parallel_toffolis, reverse_moments=ReverseMoments.NO_REVERSE):
        self.dec_fan_in = toffoli_decomp_types[0]
        self.dec_mem = toffoli_decomp_types[1]
        self.dec_fan_out = toffoli_decomp_types[2]

        # Should the Toffoli decompositions be parallelized?
        # In this case it is assumed that the ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4
        # is used (not checked, for the moment)...
        # We are not sure how to design this. Keep it.
        self.parallel_toffolis = parallel_toffolis

        # If the FANIN is better in terms of depth than the FANOUT
        # we can reverse the FANIN to FANOUT or vice versa
        self.reverse_moments = reverse_moments

    # def get_dec_fan_in(self):
    #     return self.dec_fan_in
    #
    # def get_dec_fan_out(self):
    #     return self.dec_fan_out
    #
    # def get_dec_mem(self):
    #     return  self.dec_mem

    def get_decomp_types(self):
        return [self.dec_fan_in,
                self.dec_mem,
                self.dec_fan_out]


class BucketBrigade():

    def __init__(self, qubits, decomp_scenario):

        self._qubit_order = []

        self.decomp_scenario = decomp_scenario
        self.qubits = qubits
        self.size_adr_n = len(qubits)

        self.circuit = self.construct_circuit(qubits)

        # # Cancel other CNOTs
        # qopt.CancelNghCNOTs().apply_until_nothing_changes(self.circuit,
        #                                                   count_cnot_of_circuit)

    @staticmethod
    def optimize_clifford_t_cnot_gates(circuit_1: cirq.Circuit):
        while True:
            # Allow the optimization of Clifford + T gates
            miscutils.flag_operations(circuit_1, [
                cirq.ops.H,
                cirq.ops.T,
                cirq.ops.T**-1,
                cirq.ops.S,
                cirq.ops.S**-1,
                cirq.ops.Z
            ])
            circuit_before = circuit_1.copy()

            # Cancel the neighboring gates
            qopt.CancelNghGates(transfer_flag=True).optimize_circuit(circuit_1)

            # Transform the neighboring gates
            qopt.TransformeNghGates(transfer_flag=True).optimize_circuit(circuit_1)

            if circuit_1 == circuit_before:
                break

        # The hope is that the neighboring gates are CNOTs that will transfer
        # optimization flags
        qopt.CancelNghCNOTs(transfer_flag=True) \
            .apply_until_nothing_changes(circuit_1, count_cnot_of_circuit)

        # Clean the empty moments
        cirq.optimizers.DropEmptyMoments().optimize_circuit(circuit_1)

        # clean all the flags
        miscutils.remove_all_flags(circuit_1)

    @property
    def qubit_order(self):
        return self._qubit_order

    def get_b_ancilla_name(self, i, n):
        return "b_" + str(miscutils.my_bin(i, n))

    def construct_fan_structure(self, qubits):
        n = len(qubits)
        all_ancillas = []

        # Create initial ancillas
        anc_created = [cirq.NamedQubit(self.get_b_ancilla_name(i, n)) for i in range(2)]
        all_ancillas += anc_created

        # Initialize compute fan-in moments with initial CNOT operations
        compute_fanin_moments = [
            cirq.Moment([cirq.ops.CNOT(qubits[0], anc_created[0])]),
            cirq.Moment([cirq.ops.CNOT(anc_created[0], anc_created[1])])
        ]

        # we will need the ancillae
        anc_previous = anc_created

        # Iterate to create ancillas and Toffoli gates
        for i in range(1, n):
            anc_created = [cirq.NamedQubit(self.get_b_ancilla_name(j, n)) for j in range(2 ** i, 2 ** (i + 1))]

            # Ensure the number of created ancillas equals the number of previous ancillas
            assert len(anc_created) == len(anc_previous)

            # Create Toffoli and CNOT operations for the current iteration
            compute_fanin_moments += self.create_toffoli_and_cnot_moments(qubits, anc_previous, anc_created, i)

            # Prepare ancillas for the next iteration
            anc_previous = self.interleave_ancillas(anc_created, anc_previous)

        assert len(anc_previous) == 2 ** n

        return anc_previous, compute_fanin_moments

    @staticmethod
    def create_toffoli_and_cnot_moments(qubits, anc_previous, anc_created, i):
        toffoli_moments = []
        cnot_moment_ops = []

        for j in range(2 ** i):
            ccx_first_control = qubits[i]
            ccx_second_control = anc_previous[j]
            ccx_target = anc_created[j]

            # Add Toffoli gate
            toffoli_moments.append(cirq.Moment([cirq.TOFFOLI(ccx_first_control, ccx_second_control, ccx_target)]))

            # Prepare CNOT operation
            cnot_control = ccx_target
            cnot_target = ccx_second_control
            cnot_moment_ops.append(cirq.ops.CNOT(cnot_control, cnot_target))

        # Add CNOT operations as a single moment
        toffoli_moments.append(cirq.Moment(cnot_moment_ops))

        return toffoli_moments

    @staticmethod
    def interleave_ancillas(anc_created, anc_previous):
        interleaved_ancillas = []
        for l in range(len(anc_created)):
            interleaved_ancillas.append(anc_created[l])
            interleaved_ancillas.append(anc_previous[l])
        return interleaved_ancillas

    def wiring_memory(self, all_ancillas, memory, target):
        memory_operations = []
        for i in range(len(memory)):
            mem_toff = cirq.TOFFOLI.on(
                all_ancillas[len(memory) - 1 - i],
                memory[i],
                target
            )
            memory_operations.append(cirq.Moment([mem_toff]))

        return memory_operations

    def toffoli_gate_decomposer(self, circuit, decomp_scenario, permutation):
        if not self.decomp_scenario.parallel_toffolis:
            permutation = [0, 1, 2]

        circuit = cirq.Circuit(
            ToffoliDecomposition.construct_decomposed_moments(
                circuit, decomp_scenario, permutation
            )
        )

        if permutation == [0, 2, 1] \
            and decomp_scenario == self.decomp_scenario.dec_mem \
            and decomp_scenario in [
            ToffoliDecompType.FOUR_ANCILLA_TDEPTH_1_A,
            ToffoliDecompType.FOUR_ANCILLA_TDEPTH_1_B,
            ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4,
            ToffoliDecompType.ZERO_ANCILLA_TDEPTH_4_INV,
            ToffoliDecompType.AN0_TD4_TC6_CX6,
            ToffoliDecompType.AN0_TD4_TC5_CX6,
            ToffoliDecompType.AN0_TD3_TC4_CX6,
            ToffoliDecompType.TD_4_CXD_8,
            ToffoliDecompType.TD_4_CXD_8_INV,
            ToffoliDecompType.TD_5_CXD_6,
            ToffoliDecompType.TD_5_CXD_6_INV,
        ]:
            BucketBrigade.optimize_clifford_t_cnot_gates(circuit)

        if self.decomp_scenario.parallel_toffolis:
            circuit = BucketBrigade.parallelize_toffolis(
                cirq.Circuit(circuit.all_operations())
            )
            BucketBrigade.optimize_clifford_t_cnot_gates(circuit)

        return circuit

    def reverse_and_link(self, comp_fan_in, memory_decomposed, comp_fan_out) -> cirq.Circuit:
        circuit = cirq.Circuit()

        if self.decomp_scenario.reverse_moments == ReverseMoments.NO_REVERSE:
            circuit.append(comp_fan_in)
            circuit.append(memory_decomposed)
            circuit.append(comp_fan_out)
            if self.decomp_scenario.parallel_toffolis:
                circuit = BucketBrigade.stratify(circuit)

        elif self.decomp_scenario.reverse_moments == ReverseMoments.IN_TO_OUT:
            circuit.append(comp_fan_in)
            circuit.append(memory_decomposed)
            if self.decomp_scenario.parallel_toffolis:
                circuit = BucketBrigade.stratify(circuit)
            comp_fan_out = ctu.reverse_moments(comp_fan_in)
            circuit.append(comp_fan_out)

        elif self.decomp_scenario.reverse_moments == ReverseMoments.OUT_TO_IN:
            compute_fanin_moments = ctu.reverse_moments(comp_fan_out)
            if self.decomp_scenario.parallel_toffolis:
                comp_fan_in = BucketBrigade.stratify(cirq.Circuit(compute_fanin_moments))

                comp_fan_in = BucketBrigade.parallelize_toffolis(
                    cirq.Circuit(comp_fan_in.all_operations())
                )

            self.decomp_scenario.reverse_moments = ReverseMoments.IN_TO_OUT
            circuit = self.reverse_and_link(comp_fan_in, memory_decomposed, comp_fan_out)
            self.decomp_scenario.reverse_moments = ReverseMoments.OUT_TO_IN

        return circuit

    def construct_qubit_order(self, circuit, qubits, all_ancillas, memory, target):
        self._qubit_order += qubits[::-1]
        self._qubit_order += sorted(all_ancillas)
        self._qubit_order += memory[::-1]

        all_qubits = circuit.all_qubits()
        for qub in ToffoliDecomposition(None, None).ancilla:
            if qub in all_qubits:
                self._qubit_order += [qub]

        self._qubit_order += [target]

    def construct_circuit(self, qubits):
        n = len(qubits)
        memory = [cirq.NamedQubit("m" + miscutils.my_bin(i, n)) for i in range(2 ** n)]
        target = cirq.NamedQubit("target")

        # Construct the fanin structure
        all_ancillas, compute_fanin_moments = self.construct_fan_structure(qubits)

        # Wiring the memory
        compute_memory_moments = self.wiring_memory(all_ancillas, memory, target)

        # Construct the fanout structure
        compute_fanout_moments = ctu.reverse_moments(compute_fanin_moments)

        # Parallelize the decomposition of Toffoli gates with multiprocessing
        with multiprocessing.Pool(processes=3) as pool:
            fanin_args = (compute_fanin_moments, self.decomp_scenario.dec_fan_in, [0, 1, 2])
            mem_args = (compute_memory_moments, self.decomp_scenario.dec_mem, [0, 2, 1])
            fanout_args = (compute_fanout_moments, self.decomp_scenario.dec_fan_out, [1, 0, 2])

            circuits = pool.starmap(self.toffoli_gate_decomposer, [fanin_args, mem_args, fanout_args])

        comp_fan_in, memory_decomposed, comp_fan_out = circuits

        # Link the circuits and apply the reverse moments
        circuit = self.reverse_and_link(comp_fan_in, memory_decomposed, comp_fan_out)

        # Construct the qubit order
        self.construct_qubit_order(circuit, qubits, all_ancillas, memory, target)

        return circuit

    @staticmethod
    def parallelize_toffolis(circuit_1):

        # Assume that the first and the last moment are only with Hadamards
        # Remove the moments for the optimisation to work
        circuit_2 = circuit_1[1:-1]
        # circuit_2 = circuit_1
        # print(circuit_2)

        """
            This is to say that as long as the circuit has been changed
            Very expensive in terms of computation, because drawing the
            circuit takes a lot of time
        """
        # str_circ = ""
        # while str_circ != str(circuit_2):
        #     str_circ = str(circuit_2)
        old_circuit_2 = cirq.Circuit()
        while old_circuit_2 != circuit_2:
            old_circuit_2 = cirq.Circuit(circuit_2)

            qopt.CommuteTGatesToStart().optimize_circuit(circuit_2)

            cirq.optimizers.DropEmptyMoments().optimize_circuit(circuit_2)

            qopt.ParallelizeCNOTSToLeft().optimize_circuit(circuit_2)

            # print(circuit_2)

            # print("... reinsert")
            circuit_2 = cirq.Circuit(circuit_2.all_operations()
                                     # ,strategy=cirq.InsertStrategy.NEW
                                     )
        # circuit_1 = circuit_2
        circuit_1 = cirq.Circuit(circuit_1[0] + circuit_2 + circuit_1[-1])

        # return circuit_1
        return BucketBrigade.stratified_circuit(circuit_1)

    @staticmethod
    def stratify(circuit):
        # Define the categories for stratification
        categories = [
            cirq.H,
            cirq.T,
            cirq.T**-1,
            # cirq.CNOT,
            # Add other gate families as needed
        ]

        # Stratify the circuit
        return cirq.optimizers.stratified_circuit(circuit, categories=categories)

    @staticmethod
    def stratified_circuit(circuit):
        old_circuit = cirq.Circuit()

        while old_circuit != circuit:
            old_circuit = cirq.Circuit(circuit)

            # Compress the circuit without stratification
            circuit = cirq.Circuit(circuit.all_operations())

            # Stratify the circuit
            circuit = BucketBrigade.stratify(circuit)

            # Drop empty moments
            cirq.optimizers.DropEmptyMoments().optimize_circuit(circuit)

        return circuit

    """
        Verifications
    """

    def verify_number_qubits(self):

        # The Toffoli ancilla are not counted, because we assume at this state
        # that the circuit is not decomposed
        formula_from_paper = self.size_adr_n + 2**(self.size_adr_n + 1) + 1

        # If decomposed, the Toffoli would introduce this number of ancilla
        # I am passing None to qubits in the ToffoliDecomposition, because
        # I do not care about the decomposition circuit, but about a number
        # that depends only on the decomposition_type
        [dec_fan_in, dec_fan_out, dec_mem] = self.decomp_scenario.get_decomp_types()
        local_toffoli = max(
            ToffoliDecomposition(dec_fan_in, None).number_of_ancilla() or 0,
            ToffoliDecomposition(dec_fan_out, None).number_of_ancilla() or 0,
            ToffoliDecomposition(dec_mem, None).number_of_ancilla() or 0)
        formula_from_paper += local_toffoli

        # The total number of qubits from the circuit
        circ_qubits = len(self.circuit.all_qubits())

        print("have {} == {} should".format(circ_qubits, formula_from_paper))
        verif = (circ_qubits == formula_from_paper)
        return verif

    def verify_depth(self, Alexandru_scenario=False):
        """"
            We consider a mixture of Toffoli decompositions
            For the moment, the mixture is of two types
            For each type we have a number of CNOTs - a tuple with two values
        """
        # [dec_fan_in, dec_fan_out, dec_mem] = self.decomp_scenario.get_decomp_types()

        num_toffolis_per_type = np.array([2**self.size_adr_n - 2,
                                          2**self.size_adr_n,
                                          2**self.size_adr_n - 2])
        if (Alexandru_scenario):
            num_toffolis_per_type = np.array([self.size_adr_n - 1,
                                              1,
                                              self.size_adr_n - 1])  # it's rather the number of parallel Tofollis
        # if self.dec_fan_in == ToffoliDecompType.ZERO_ANCILLA_TDEPTH_3:
        #     toff_dec_depth_per_type = np.array([10, 0, 0])
        # if self.dec_fan_out == ToffoliDecompType.ZERO_ANCILLA_TDEPTH_3:
        #     toff_dec_depth_per_type += np.array([0, 0, 10])
        # if self.dec_mem == ToffoliDecompType.ZERO_ANCILLA_TDEPTH_3:
        #     toff_dec_depth_per_type += np.array([0, 9, 0])
        toff_dec_depth_per_type = [
            ToffoliDecomposition(self.decomp_scenario.dec_fan_in).depth,
            ToffoliDecomposition(self.decomp_scenario.dec_mem).depth,
            ToffoliDecomposition(self.decomp_scenario.dec_fan_out).depth,
        ]

        formula_from_paper = 0
        for elem in zip(num_toffolis_per_type, toff_dec_depth_per_type):
            formula_from_paper += elem[0] * elem[1]
        # depth after decomposition
        # if self.decomposition_type == ToffoliDecompType.NO_DECOMP:
        #     toff_dec_depth_per_type = (1, 0)
        #     num_toffolis_per_type = (3 * 2**self.size_adr_n - 4, 0)
        #
        # elif self.decomposition_type == ToffoliDecompType.ZERO_ANCILLA_TDEPTH_3:
        #     """
        #         The Toffoli decomposition has depth 10, but the Toffolis
        #         that are touching the memory have the same target such that,
        #         for all but one, the Hadamard gate on the target is cancelled
        #         leaving the depth, for all but one, being 9 instead of 10
        #     """
        #     toff_dec_depth_per_type = (10, 9)
        #     num_toffolis_per_type = (2 * 2**self.size_adr_n - 4, 2**self.size_adr_n)
        #
        # elif self.decomposition_type == ToffoliDecompType.ONE_ANCILLA_TDEPTH_2:
        #     toff_dec_depth_per_type = (13, 12)
        #     num_toffolis_per_type = (2 * 2**self.size_adr_n - 4, 2**self.size_adr_n)
        #
        # elif self.decomposition_type == ToffoliDecompType.FOUR_ANCILLA_TDEPTH_1_A:
        #     toff_dec_depth_per_type = (7, 0)
        #     num_toffolis_per_type = (3 * 2**self.size_adr_n - 4, 0)
        #
        # elif self.decomposition_type == ToffoliDecompType.FOUR_ANCILLA_TDEPTH_1_B:
        #
        #     num_toffolis_fan = 2 ** (self.size_adr_n + 1) - 4
        #     num_toffolis_mem = 2 ** self.size_adr_n
        #     num_toffolis_per_type = (num_toffolis_fan, num_toffolis_mem)
        #
        #     toff_dec_depth_per_type = (7, 13)

        depth_coupling_nodes = 2*self.size_adr_n + 2

        # formula_from_paper = 0
        # for elem in zip(num_toffolis_per_type, toff_dec_depth_per_type):
        #     formula_from_paper += elem[0] * elem[1]

        formula_from_paper += depth_coupling_nodes

        """
            Special cases
        """
        reduced_depth = 0  # it's the canceled cnots and hadamards for olivia's scenario
        if (self.decomp_scenario.dec_mem == ToffoliDecompType.FOUR_ANCILLA_TDEPTH_1_B):
            # 8=2(3cnots +1hadmard)
            reduced_depth = 8 * (2 ** self.size_adr_n - 1)

        formula_from_paper -= reduced_depth
        # if self.decomposition_type in [ToffoliDecompType.ZERO_ANCILLA_TDEPTH_3, ToffoliDecompType.ONE_ANCILLA_TDEPTH_2]:
        #     # This is the "one Toffoli with depth 10"
        #     formula_from_paper += 1
        # elif self.decomposition_type == ToffoliDecompType.FOUR_ANCILLA_TDEPTH_1_B:
        #     # The mixture leaves 8 depth which are not cancelled
        #     formula_from_paper += 8

        circ_depth = len(self.circuit)

        print("have {} == {} should".format(circ_depth, formula_from_paper))
        verif = (circ_depth == formula_from_paper)
        return verif

    def verify_T_count(self):
        # if self.decomposition_type == ToffoliDecompType.NO_DECOMP:
        #     t_count_toffoli = 0
        # elif self.decomposition_type in \
        #         [ToffoliDecompType.ZERO_ANCILLA_TDEPTH_3,
        #         ToffoliDecompType.ONE_ANCILLA_TDEPTH_2,
        #         ToffoliDecompType.FOUR_ANCILLA_TDEPTH_1_A,
        #         ToffoliDecompType.FOUR_ANCILLA_TDEPTH_1_B]:
        #     t_count_toffoli = 7
        num_toffolis_per_type = np.array([2 ** self.size_adr_n - 2,
                                          2 ** self.size_adr_n - 2,
                                          2 ** self.size_adr_n])

        # [dec_fan_in, dec_fan_out, dec_mem] = self.decomp_scenario.get_decomp_types()

        toff_dec_t_count_per_type = [
            ToffoliDecomposition(self.decomp_scenario.dec_fan_in).number_of_t,
            ToffoliDecomposition(self.decomp_scenario.dec_fan_out).number_of_t,
            ToffoliDecomposition(self.decomp_scenario.dec_mem).number_of_t
        ]

        formula_from_paper = 0
        for elem in zip(toff_dec_t_count_per_type, num_toffolis_per_type):
            formula_from_paper += elem[0]*elem[1]

        nr_t = count_t_of_circuit(self.circuit)

        print("have {} == {} should".format(nr_t, formula_from_paper))
        verif = (formula_from_paper == nr_t)
        return verif

    def verify_T_depth(self, Alexandru_scenario=False):
        # if self.decomposition_type == ToffoliDecompType.NO_DECOMP:
        #     tof_dec_t_depth = 0
        # elif self.decomposition_type == ToffoliDecompType.ZERO_ANCILLA_TDEPTH_3:
        #     tof_dec_t_depth = 3
        # elif self.decomposition_type == ToffoliDecompType.ONE_ANCILLA_TDEPTH_2:
        #     tof_dec_t_depth = 2
        # elif self.decomposition_type in \
        #         [ToffoliDecompType.FOUR_ANCILLA_TDEPTH_1_A,
        #          ToffoliDecompType.FOUR_ANCILLA_TDEPTH_1_B]:
        #     tof_dec_t_depth = 1
        num_toffolis_per_type = np.array([2 ** self.size_adr_n - 2,
                                          2 ** self.size_adr_n - 2,
                                          2 ** self.size_adr_n])

        if (Alexandru_scenario):
            num_toffolis_per_type = np.array([self.size_adr_n - 1, 1,
                                              self.size_adr_n - 1])  # it's rather the number of parallel Tofollis
        # [dec_fan_in, dec_fan_out, dec_mem] = self.decomp_scenario.get_decomp_types()

        toff_dec_t_depth_per_type = [
            ToffoliDecomposition(self.decomp_scenario.dec_fan_in).t_depth,
            ToffoliDecomposition(self.decomp_scenario.dec_fan_out).t_depth,
            ToffoliDecomposition(self.decomp_scenario.dec_mem).t_depth
        ]

        formula_from_paper = 0
        for elem in zip(toff_dec_t_depth_per_type, num_toffolis_per_type):
            formula_from_paper += elem[0] * elem[1]

        t_depth = count_t_depth_of_circuit(self.circuit)

        print("have {} == {} should".format(t_depth, formula_from_paper))
        verif = (t_depth == formula_from_paper)
        return verif

    def verify_hadamard_count(self, Alexandru_scenario=False):
        # if self.decomposition_type == ToffoliDecompType.NO_DECOMP:
        #     formula_from_paper = 0
        # else:
        #     # This formula assumes that Hadamard gates are optimized in pairs
        #     formula_from_paper = 4 * 2**self.size_adr_n - 6
        num_toffolis_per_type = np.array([2 ** self.size_adr_n - 2,
                                          2 ** self.size_adr_n - 2,
                                          2 ** self.size_adr_n])

        # [dec_fan_in, dec_fan_out, dec_mem] = self.decomp_scenario.get_decomp_types()

        toff_dec_H_count_per_type = [
            ToffoliDecomposition(
                self.decomp_scenario.dec_fan_in).number_of_hadamards,
            ToffoliDecomposition(
                self.decomp_scenario.dec_fan_out).number_of_hadamards,
            ToffoliDecomposition(
                self.decomp_scenario.dec_mem).number_of_hadamards
        ]

        formula_from_paper = 0
        for elem in zip(toff_dec_H_count_per_type, num_toffolis_per_type):
            formula_from_paper += elem[0] * elem[1]
        """
        special cases
        """
        num_of_canceled_H = 0
        if (self.decomp_scenario.dec_mem in [ToffoliDecompType.FOUR_ANCILLA_TDEPTH_1_A, ToffoliDecompType.FOUR_ANCILLA_TDEPTH_1_B] or Alexandru_scenario):
            num_of_canceled_H = 2**(self.size_adr_n+1)-2
        formula_from_paper -= num_of_canceled_H
        nr_h = count_h_of_circuit(self.circuit)
        print("have {} == {} should".format(nr_h, formula_from_paper))
        verif = (formula_from_paper == nr_h)
        return verif

    def verify_cnot_count(self, Alexandru_scenario=False):
        """"
            We consider a mixture of Toffoli decompositions
            For the moment, the mixture is of two types
            For each type we have a number of CNOTs - a tuple with two values
        """
        # [dec_fan_in, dec_fan_out, dec_mem] = self.decomp_scenario.get_decomp_types()

        num_toffolis_per_type = np.array([2 ** self.size_adr_n - 2,
                                          2 ** self.size_adr_n,
                                          2 ** self.size_adr_n - 2])

        toff_dec_cnot_count_per_type = [
            ToffoliDecomposition(
                self.decomp_scenario.dec_fan_in).number_of_cnots,
            ToffoliDecomposition(self.decomp_scenario.dec_mem).number_of_cnots,
            ToffoliDecomposition(
                self.decomp_scenario.dec_fan_out).number_of_cnots
        ]

        # if self.decomposition_type == ToffoliDecompType.NO_DECOMP:
        #     num_cnots_dec_per_type = (0, 0)
        #     num_toffolis = 3 * 2 ** self.size_adr_n - 4
        #     num_toffolis_per_type = (num_toffolis, 0)
        #
        # elif self.decomposition_type == ToffoliDecompType.ZERO_ANCILLA_TDEPTH_3:
        #     num_cnots_dec_per_type = (7, 0)
        #     num_toffolis = 3 * 2 ** self.size_adr_n - 4
        #     num_toffolis_per_type = (num_toffolis, 0)
        #
        # elif self.decomposition_type == ToffoliDecompType.ONE_ANCILLA_TDEPTH_2:
        #     num_cnots_dec_per_type = (10, 0)
        #     num_toffolis = 3 * 2 ** self.size_adr_n - 4
        #     num_toffolis_per_type = (num_toffolis, 0)
        #
        # elif self.decomposition_type == ToffoliDecompType.FOUR_ANCILLA_TDEPTH_1_A:
        #     num_cnots_dec_per_type = (16, 0)
        #     num_toffolis = 3 * 2 ** self.size_adr_n - 4
        #     num_toffolis_per_type = (num_toffolis, 0)
        #
        # elif self.decomposition_type == ToffoliDecompType.FOUR_ANCILLA_TDEPTH_1_B:
        """
        A bit misleading, because this decomposition is not entirely used 
        alone, but in conjunction with the FOUR_ANCILLA_TDEPTH_1_A
        
        The following formula_from_paper is because:
        -> we received notes from Olivia on the 11 November 2019
        
        Theoretically, FOUR_ANCILLA_TDEPTH_1_B has 18 CNOTs, but after
        cancelling out, only 12 remain...and 6 which are added (see below)
        """
        # num_cnots_dec_per_type = (16, 12)
        #
        # num_toffolis_fan = 2 ** (self.size_adr_n + 1) - 4
        # num_toffolis_mem = 2 ** self.size_adr_n
        # num_toffolis_per_type = (num_toffolis_fan, num_toffolis_mem)

        # See naming from arxiv: 1502.03450
        num_coupling_nodes = 2 * 2 ** self.size_adr_n

        formula_from_paper = 0
        for elem in zip(num_toffolis_per_type, toff_dec_cnot_count_per_type):
            formula_from_paper += elem[0] * elem[1]
        formula_from_paper += num_coupling_nodes

        # if self.decomposition_type == ToffoliDecompType.FOUR_ANCILLA_TDEPTH_1_B:
        #     """
        #     The mixture leaves 6 CNOTS. See Olivia notes.
        #     """
        #     formula_from_paper += 6
        """
        special cases
        """
        num_of_canceled_cnot = 0
        if (self.decomp_scenario.dec_mem == ToffoliDecompType.FOUR_ANCILLA_TDEPTH_1_B):
            num_of_canceled_cnot = 6*(2 ** self.size_adr_n-1)
        formula_from_paper -= num_of_canceled_cnot
        nr_cnot = count_cnot_of_circuit(self.circuit)
        # print("have {} == {} should".format(nr_cnot, formula_from_paper))
        verif = (formula_from_paper == nr_cnot)
        return verif
