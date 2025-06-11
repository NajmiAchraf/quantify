import multiprocessing
from typing import Any, List, Literal, Tuple, Union

import cirq

import utils.clifford_t_utils as ctu
from qram.bucket_brigade.base import BucketBrigadeBase
from qram.bucket_brigade.decomp_type import (
    BucketBrigadeDecompType,
    ReverseMoments,
)
from qram.bucket_brigade.fan_in import BucketBrigadeFanIn
from qram.bucket_brigade.fan_out import BucketBrigadeFanOut
from qram.bucket_brigade.fan_read import BucketBrigadeFanRead
from qram.bucket_brigade.query import BucketBrigadeQuery
from qram.bucket_brigade.read import BucketBrigadeRead
from qram.bucket_brigade.write import BucketBrigadeWrite

# Module-level component mapping for pickle compatibility
COMPONENT_CLASSES = {
    "BucketBrigadeFanOut": BucketBrigadeFanOut,
    "BucketBrigadeWrite": BucketBrigadeWrite,
    "BucketBrigadeQuery": BucketBrigadeQuery,
    "BucketBrigadeFanIn": BucketBrigadeFanIn,
    "BucketBrigadeRead": BucketBrigadeRead,
    "BucketBrigadeFanRead": BucketBrigadeFanRead,
}


# Module-level function for multiprocessing
def create_bb_component(args: Tuple[str, int, BucketBrigadeDecompType]) -> Any:
    """
    Create a bucket brigade component for multiprocessing.

    Args:
        args: Tuple of (component_name, qram_bits, decomp_scenario)

    Returns:
        Instance of the requested component or None on error
    """
    component_name, qram_bits, decomp_scenario = args
    try:
        component_class = COMPONENT_CLASSES.get(component_name)
        if component_class:
            return component_class(qram_bits, decomp_scenario)
        else:
            print(f"Unknown component: {component_name}")
            return None
    except Exception as e:
        print(f"Error creating component {component_name}: {e}")
        return None


class BucketBrigade(BucketBrigadeBase):
    """
    Implements the complete bucket-brigade quantum random-access memory (QRAM) circuit.

    Can be configured to create full QRAM circuits or individual components
    (write, query, reset, or read phases).
    """

    def __init__(
        self,
        qram_bits: int,
        decomp_scenario: BucketBrigadeDecompType,
        circuit_type: Union[
            "List[Literal['fan_out','write','query','fan_in','read','fan_read']]",
            Literal[
                "fan_out",
                "write",
                "query",
                "fan_in",
                "read",
                "fan_read",
                "classic",
            ],
        ] = "classic",
    ) -> None:
        """
        Initialize a BucketBrigade QRAM circuit.

        Args:
            qram_bits: The number of address bits for the QRAM.
            decomp_scenario: The decomposition scenario for Toffoli gates.
            circuit_type: Type of circuit to create:
                - "fan_out": Only the fan-out structure)
                - "write": Write phase only
                - "query": Query phase only
                - "fan_in": Reset phase (uncompute fan-out)
                - "read": Read phase only
                - "fan_read": Fan-read structure
                - "classic": Classic bucket brigade QRAM
        """
        # Initialize the base class
        super().__init__(qram_bits, decomp_scenario)

        # Additional attributes
        self.circuit_type = circuit_type

        # Create qubits and build circuit
        self.construct_qubits()
        self.construct_circuit()

    def construct_qubits(self) -> None:
        """
        Create all the qubits needed for the circuit, conditionally creating read/write qubit.
        """
        # Create address, ancilla, memory and target qubits with parent method
        super().construct_qubits()

        # For BucketBrigade main class, determine if read/write is needed based on circuit_type
        if self.__class__.__name__ == "BucketBrigade":
            # Check if circuit_type is already set (it won't be during parent's __init__)
            if not hasattr(self, "circuit_type"):
                # We're being called from parent's __init__, don't try to use circuit_type yet
                # The method will be called again after circuit_type is set
                self.read_write = None
                return

            # Check if any component needs read/write qubit
            needs_read_write = False

            if isinstance(self.circuit_type, str):
                # Single string case
                needs_read_write = any(
                    component in self.circuit_type
                    for component in ["write", "read", "fan_read"]
                )
            else:
                # List case
                needs_read_write = any(
                    component in ["write", "read", "fan_read"]
                    for component in self.circuit_type
                )

            # Create or clear read/write qubit based on need
            if needs_read_write:
                self.read_write = cirq.NamedQubit("read/write")
            else:
                self.read_write = None

    def construct_circuit(self) -> cirq.Circuit:
        """Build the appropriate circuit based on circuit_type."""
        self.logger.info(
            f"Constructing {self.circuit_type} circuit with {self.size_adr_n} address bits"
        )

        # Initialize empty list for components
        components = []
        # Define component order
        component_order = {
            "fan_out": ("BucketBrigadeFanOut", 0),
            "write": ("BucketBrigadeWrite", 1),
            "query": ("BucketBrigadeQuery", 2),
            "fan_in": ("BucketBrigadeFanIn", 3),
            "read": ("BucketBrigadeRead", 4),
            "fan_read": ("BucketBrigadeFanRead", 5),
        }

        # Handle different circuit_type formats
        if isinstance(self.circuit_type, str):
            # Single string case (e.g., "classic")
            if self.circuit_type == "classic":
                components.extend(
                    [
                        ("BucketBrigadeFanOut", 0),
                        ("BucketBrigadeQuery", 2),
                        ("BucketBrigadeFanIn", 3),
                    ]
                )
            elif self.circuit_type in component_order:
                components.append(component_order[self.circuit_type])
        else:
            # List case
            for component in self.circuit_type:
                if component == "classic":
                    components.extend(
                        [
                            ("BucketBrigadeFanOut", 0),
                            ("BucketBrigadeQuery", 2),
                            ("BucketBrigadeFanIn", 3),
                        ]
                    )
                elif component in component_order:
                    components.append(component_order[component])

        # Sort by order value and extract component names
        components = [
            comp[0] for comp in sorted(components, key=lambda x: x[1])
        ]

        # Ensure there's at least one component
        if not components:
            raise ValueError(
                f"No valid components specified in circuit_type: {self.circuit_type}"
            )

        # Create args list for multiprocessing
        args_list = [
            (comp_name, self.size_adr_n, self.decomp_scenario)
            for comp_name in components
        ]

        # Determine optimal pool size
        len_components = len(components)
        pool_size = max(1, min(multiprocessing.cpu_count(), len_components))

        # Use Pool for multiprocessing (more reliable than ProcessPoolExecutor for this case)
        created_components = []
        with multiprocessing.Pool(processes=pool_size) as pool:
            # Use pool.map instead of executor.submit+futures
            result_components = pool.map(create_bb_component, args_list)

            # Filter out None results
            created_components = [
                comp for comp in result_components if comp is not None
            ]

        # Process the created components
        if not created_components:
            raise ValueError("No components were successfully created")

        if len(created_components) == 1:
            # Single component case
            self._copy_component_attributes(created_components[0])
        else:
            # Multiple components case (classic or custom combination)
            # Copy attributes from first component
            self._copy_component_attributes(
                created_components[0], copy_circuit=False
            )

            # Replace the simple circuit combination with reverse_and_link
            # First, extract individual component circuits by type
            component_circuits = {}
            for component in created_components:
                # Get the component type from the class name
                component_type = component.__class__.__name__
                component_circuits[component_type] = component.circuit

            # Extract the individual circuits (use empty circuits for missing components)
            empty_circuit = cirq.Circuit()
            comp_fan_in = component_circuits.get(
                "BucketBrigadeFanOut", empty_circuit
            )
            memory_write = component_circuits.get(
                "BucketBrigadeWrite", empty_circuit
            )
            memory_query = component_circuits.get(
                "BucketBrigadeQuery", empty_circuit
            )
            memory_read = component_circuits.get(
                "BucketBrigadeRead", empty_circuit
            )
            comp_fan_out = component_circuits.get(
                "BucketBrigadeFanIn", empty_circuit
            )

            # Use the reverse_and_link method to combine the circuits with the appropriate strategy
            self.logger.info(
                "Linking circuit components using reverse_and_link"
            )
            combined_circuit = self.reverse_and_link(
                comp_fan_in,
                memory_write,
                memory_query,
                memory_read,
                comp_fan_out,
            )

            self.circuit = combined_circuit
            # Update qubit order with all qubits
            self.construct_qubit_order(self.circuit)

        self.logger.info(
            f"{(name.capitalize() for name in self.circuit_type)} circuit construction complete. "
            f"Total qubits: {len(self.circuit.all_qubits())}, "
            f"Circuit depth: {len(self.circuit)}"
        )

        return self.circuit

    def _copy_component_attributes(self, component, copy_circuit=True):
        """Copy attributes from a component to this class."""
        if copy_circuit:
            self.circuit = component.circuit
        self._qubit_order = component.qubit_order.copy()

        # Copy ancillas if available
        if hasattr(component, "all_ancillas") and component.all_ancillas:
            self.all_ancillas = component.all_ancillas

    def reverse_and_link(
        self,
        comp_fan_in: cirq.Circuit,
        memory_write_decomposed: cirq.Circuit,
        memory_query_decomposed: cirq.Circuit,
        memory_read_decomposed: cirq.Circuit,
        comp_fan_out: cirq.Circuit,
    ) -> cirq.Circuit:
        """
        Link the different parts of the circuit together with appropriate reversals.

        Args:
            comp_fan_in: Fan-in (addressing) part of the circuit
            memory_write_decomposed: Memory write access part of the circuit
            memory_read_decomposed: Memory read access part of the circuit
            memory_query_decomposed: Memory query access part of the circuit
            comp_fan_out: Fan-out (uncomputation) part of the circuit

        Returns:
            Combined circuit with all parts linked
        """
        circuit = cirq.Circuit()

        # Handle different reversal modes
        if self.decomp_scenario.reverse_moments == ReverseMoments.NO_REVERSE:
            # Standard concatenation without reversal
            circuit.append(comp_fan_in)
            circuit.append(memory_write_decomposed)
            circuit.append(memory_query_decomposed)
            circuit.append(memory_read_decomposed)
            circuit.append(comp_fan_out)
            if self.decomp_scenario.parallel_toffolis:
                circuit = BucketBrigade.stratify(circuit)

        elif self.decomp_scenario.reverse_moments == ReverseMoments.IN_TO_OUT:
            # Use fan-in for both in and out (reversed)
            circuit.append(comp_fan_in)
            circuit.append(memory_write_decomposed)
            circuit.append(memory_query_decomposed)
            circuit.append(memory_read_decomposed)
            if self.decomp_scenario.parallel_toffolis:
                circuit = BucketBrigade.stratify(circuit)
            circuit.append(comp_fan_out)

        elif self.decomp_scenario.reverse_moments == ReverseMoments.OUT_TO_IN:
            # #! Use fan-out for both in (reversed) and out
            # compute_fanin_moments = cirq.Circuit(
            #     ctu.reverse_moments(comp_fan_out)
            # )
            # if self.decomp_scenario.parallel_toffolis:
            #     comp_fan_in = BucketBrigade.stratify(compute_fanin_moments)
            #     comp_fan_in = BucketBrigade.parallelize_toffolis(comp_fan_in)

            #! Use fan-out for both in (reversed) and out
            compute_fanin_moments = cirq.Circuit(
                ctu.reverse_moments(comp_fan_in)
            )
            if self.decomp_scenario.parallel_toffolis:
                comp_fan_in = BucketBrigade.stratify(compute_fanin_moments)
                comp_fan_in = BucketBrigade.parallelize_toffolis(comp_fan_in)
            #! Use fan-out for both in (reversed) and out
            compute_fanin_moments = cirq.Circuit(
                ctu.reverse_moments(comp_fan_in)
            )
            if self.decomp_scenario.parallel_toffolis:
                comp_fan_in = BucketBrigade.stratify(compute_fanin_moments)
                comp_fan_in = BucketBrigade.parallelize_toffolis(comp_fan_in)

            # Temporarily change the mode to avoid recursion issues
            original_mode = self.decomp_scenario.reverse_moments
            self.decomp_scenario.reverse_moments = ReverseMoments.IN_TO_OUT
            circuit = self.reverse_and_link(
                comp_fan_in,
                memory_write_decomposed,
                memory_query_decomposed,
                memory_read_decomposed,
                comp_fan_out,
            )
            self.decomp_scenario.reverse_moments = original_mode

        return circuit
