import concurrent.futures
import threading

import cirq

import utils.clifford_t_utils as ctu


class CommuteTGatesToStart:

    def optimize_circuit(self, circuit: cirq.Circuit):
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

                        parallel_t_gates[0] = parallel_t_gates[0].with_operation(op)
                        circuit.clear_operations_touching(op.qubits, [mi])
                        number_t_commutes += 1

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for mi, moment in enumerate(circuit):
                for op in moment:
                    futures.append(
                        executor.submit(
                            process_operation, mi, op, circuit, parallel_t_gates
                        )
                    )
            concurrent.futures.wait(futures)

        # print(number_t_commutes)

        for par_t_mom in parallel_t_gates:
            if len(par_t_mom.operations) > 0:
                circuit.insert(0, par_t_mom)
