import concurrent.futures
import threading

import cirq

import utils.clifford_t_utils as ctu
import utils.counting_utils as count

from .parallelize_controlled_gates_base import ParallelizeControlledGatesBase


class ParallelizeCNOTSToLeft(ParallelizeControlledGatesBase):

    def __init__(self, transfer_flag: bool = False):
        # Call the super constructor with X gate types
        super().__init__(gate_types={cirq.X}, transfer_flag=transfer_flag)

    def is_target_gate(self, operation) -> bool:
        """Check if operation is a CNOT or controlled parallel X gate."""
        return ctu.is_controlled_parallel_x(operation)

    def needs_conversion_to_controlled(self, operation) -> bool:
        """Check if CNOT needs conversion to controlled parallel X."""
        return operation.gate == cirq.ops.CNOT or operation.gate == cirq.ops.CX

    def merge_controlled_parallel_gate(self, op1, op2):
        """Override base class method with CNOT-specific logic."""
        return self.merge_controlled_parallel_x(op1, op2)

    def controlled_gate_to_controlled_parallel_gate(
        self, circuit, index, operation
    ):
        """Override base class method with CNOT-specific logic."""
        return self.cnot_to_controlled_parallel_x(circuit, index, operation)

    def merge_controlled_parallel_x(self, op1, op2):
        """Merge two Controlled X operations into a single Controlled Parallel X operation."""
        # Ensure both operations have the same control qubits
        if (
            (len(op1.controls) != len(op2.controls))
            and (len(op1.controls) != 1)
            and op1.controls[0] != op2.controls[0]
        ):
            raise ValueError(
                "Control qubits must be the same for both operations"
            )

        # Merge the target qubits from both operations
        merged_qubits = op1.sub_operation.qubits + op2.sub_operation.qubits

        # Create a ParallelGate with X gates for the merged qubits
        parallel_x_gate = cirq.ParallelGate(cirq.ops.X, len(merged_qubits))

        # Create a ControlledOperation with the ParallelGate
        controlled_parallel_x = cirq.ControlledOperation(
            op1.controls, parallel_x_gate(*merged_qubits)
        )

        return controlled_parallel_x

    def cnot_to_controlled_parallel_x(self, circuit, index, operation):
        """Convert a CNOT to controlled parallel X."""
        p_op = cirq.GateOperation(cirq.ops.X, [operation.qubits[1]])
        current_controlled_op = cirq.ControlledOperation(
            [operation.qubits[0]], p_op
        )

        circuit.clear_operations_touching(operation.qubits, [index])
        circuit.insert(
            index + 1,
            current_controlled_op,
            strategy=cirq.InsertStrategy.INLINE,
        )

        return current_controlled_op

    def commute_t_gates_to_start(self, circuit: cirq.Circuit):
        number_t_commutes = 0

        parallel_t_gates = [cirq.Moment()]

        lock = threading.Lock()

        def process_operation(mi, op, circuit, parallel_t_gates):
            nonlocal number_t_commutes
            if ctu.is_t_or_s_gate(op):
                pi = mi
                all_ok = True
                while pi is not None:
                    pi = circuit.prev_moment_operating_on(op.qubits, pi)

                    if pi is None:
                        break

                    op_pi = circuit.operation_at(op.qubits[0], pi)

                    if (
                        not ctu.is_controlled_parallel_x(op_pi)
                        or not ctu.has_control_qubit(op_pi, op.qubits[0])
                    ) and not ctu.is_t_or_s_gate(op_pi):
                        all_ok = False

                    if not all_ok:
                        break

                if all_ok:
                    with lock:
                        if parallel_t_gates[0].operates_on(op.qubits):
                            parallel_t_gates.insert(0, cirq.Moment())

                        parallel_t_gates[0] = parallel_t_gates[
                            0
                        ].with_operation(op)
                        circuit.clear_operations_touching(op.qubits, [mi])
                        number_t_commutes += 1

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for mi, moment in enumerate(circuit):
                for op in moment:
                    futures.append(
                        executor.submit(
                            process_operation,
                            mi,
                            op,
                            circuit,
                            parallel_t_gates,
                        )
                    )
            concurrent.futures.wait(futures)

        # print(number_t_commutes)

        for par_t_mom in parallel_t_gates:
            if len(par_t_mom.operations) > 0:
                circuit.insert(0, par_t_mom)

    def optimize_circuit(self, circuit: cirq.Circuit) -> cirq.Circuit:
        # Remove the first and last moments if they are H gates
        if len(circuit) < 3:
            return circuit

        _circuit_ = cirq.Circuit(circuit[1:-1])

        while True:
            previous_circuit_state = _circuit_.copy()

            # Move T gates toward the beginning
            self.commute_t_gates_to_start(_circuit_)

            # Clean up the _circuit_
            _circuit_ = cirq.drop_negligible_operations(_circuit_)
            _circuit_ = cirq.drop_empty_moments(_circuit_)

            super().optimize_circuit(_circuit_)

            _circuit_ = cirq.Circuit(_circuit_.all_operations())

            if previous_circuit_state == _circuit_:
                return cirq.Circuit(circuit[0] + _circuit_ + circuit[-1])
