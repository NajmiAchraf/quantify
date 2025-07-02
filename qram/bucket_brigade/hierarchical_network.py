import logging
import multiprocessing
from typing import Any, Dict, List, Optional, Set, Tuple

import cirq

from qram.bucket_brigade.decomp_type import BucketBrigadeDecompType
from qram.bucket_brigade.fan_in import BucketBrigadeFanIn
from qram.bucket_brigade.fan_out import BucketBrigadeFanOut
from qram.bucket_brigade.fan_read import BucketBrigadeFanRead
from qram.bucket_brigade.query import BucketBrigadeQuery
from qram.bucket_brigade.read import BucketBrigadeRead
from qram.bucket_brigade.write import BucketBrigadeWrite
from qramcircuits.toffoli_decomposition import ToffoliDecomposition
from utils.print_utils import render_circuit
from utils.types import type_circuit


# Function for multiprocessing component creation
def _create_component_mp(
    args: Tuple[
        str,
        int,
        BucketBrigadeDecompType,
        List[cirq.Qid],
        List[cirq.Qid],
        List[cirq.Qid],
        cirq.Qid,
        Optional[cirq.Qid],
    ],
) -> Tuple[str, Any]:
    """
    Create a bucket brigade component for multiprocessing.

    Args:
        args: Tuple containing (component_name, bits, decomp_scenario, address_qubits,
                              routing_qubits, memory_qubits, target, read_write)

    Returns:
        Tuple of (component_name, component_instance)
    """
    (
        component_name,
        bits,
        decomp_scenario,
        address_qubits,
        routing_qubits,
        memory_qubits,
        target,
        read_write,
    ) = args

    try:
        if component_name == "fan_out":
            component = BucketBrigadeFanOut(bits, decomp_scenario)
            component.address = address_qubits
            component.all_ancillas = routing_qubits

        elif component_name == "write":
            component = BucketBrigadeWrite(bits, decomp_scenario)
            component.all_ancillas = routing_qubits
            component.memory = memory_qubits
            component.target = target
            component.read_write = read_write

        elif component_name == "query":
            component = BucketBrigadeQuery(bits, decomp_scenario)
            component.all_ancillas = routing_qubits
            component.memory = memory_qubits
            component.target = target

        elif component_name == "fan_in":
            component = BucketBrigadeFanIn(bits, decomp_scenario)
            component.address = address_qubits
            component.all_ancillas = routing_qubits

        elif component_name == "read":
            component = BucketBrigadeRead(bits, decomp_scenario)
            component.all_ancillas = routing_qubits
            component.memory = memory_qubits
            component.target = target
            component.read_write = read_write

        elif component_name == "fan_read":
            component = BucketBrigadeFanRead(bits, decomp_scenario)
            component.address = address_qubits
            component.all_ancillas = routing_qubits
            component.target = target
            component.read_write = read_write
        else:
            return (component_name, None)

        return (component_name, component)

    except Exception as e:
        import traceback

        print(f"Error creating {component_name} component: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return (component_name, None)


class HierarchicalBucketBrigadeNetwork:
    """
    Implements a hierarchical Bucket Brigade QRAM that follows the natural tree structure.

    The hierarchy follows the address bit structure:
    - a0 is always inside bucket brigade circuits (cannot create subcircuit from it)
    - Higher-order bits (a1, a2, etc.) control branching at different levels
    - For n-bit QRAM: a_{n-1} controls top-level split, a_{n-2} controls second level, etc.

    Components are grouped by type across all branches (fan_out, write, query, fan_in, read, fan_read).
    """

    def __init__(
        self,
        qram_bits: int,
        min_qram_size: int,
        decomp_scenario: BucketBrigadeDecompType,
        circuit_type: type_circuit,
    ):
        """
        Initialize a hierarchical bucket brigade network.

        Args:
            qram_bits: Number of address bits in the QRAM
            min_qram_size: Minimum QRAM size for hierarchical decomposition
            decomp_scenario: Decomposition scenario for Toffoli gates
            circuit_type: Type of circuit components to include:
                - Single component: "fan_out", "write", "query", "fan_in", "read", "fan_read"
                - Multiple components: ["fan_out", "write", "query", ...]
        """
        if qram_bits < 1:
            raise ValueError("qram_bits must be at least 1")
        if min_qram_size < 1 or min_qram_size > qram_bits:
            raise ValueError("min_qram_size must be between 1 and qram_bits")

        self.qram_bits = qram_bits
        self.decomp_scenario = decomp_scenario
        self.circuit_type = circuit_type
        self.min_qram_size = min_qram_size
        self.logger = logging.getLogger(__name__)

        # Cache for component circuits to avoid redundant creation
        self._component_cache = {}
        self._circuit_cache = {}

        # Create shared target and read/write qubits
        self.target = cirq.NamedQubit("target")

        # Determine if read/write qubit is needed based on circuit_type
        self.read_write = self._create_read_write_qubit()

        # Create address qubits with standard naming a0, a1, a2, ...
        # where a0 is LSB (rightmost) and a_{n-1} is MSB (leftmost)
        self.address = [cirq.NamedQubit(f"a{i}") for i in range(qram_bits)]

        # Parse circuit_type to determine which components to include
        self.enabled_components = self._parse_circuit_type(circuit_type)

        # Store component subcircuits by type for sequential grouping
        self.component_subcircuits: Dict[str, List[cirq.CircuitOperation]] = {
            "fan_out": [],
            "write": [],
            "query": [],
            "fan_in": [],
            "read": [],
            "fan_read": [],
        }

        # Track which address bits are used as controllers for hierarchy display
        self.controlling_bits = set()

        # Track the branches we'll need for qubit allocation
        self.needed_branches: Set[str] = set()

        # Initialize routing and memory qubit dictionaries
        self.routing_qubits: Dict[str, cirq.Qid] = {}
        self.memory_qubits: Dict[str, cirq.Qid] = {}

        # Initialize qubit order list
        self._qubit_order = []

        # Build the circuit (this will determine needed branches)
        self.circuit = self.build()

        # Construct qubit order after circuit is built
        self.construct_qubit_order(self.circuit)

        self.logger.info(
            f"Created hierarchical bucket brigade network with {qram_bits} address bits, "
            f"components: {self.enabled_components}"
        )

    def _create_read_write_qubit(self) -> Optional[cirq.Qid]:
        """Create read/write qubit if needed by any component in circuit_type."""
        # Components that need read/write qubit
        needs_read_write = {"write", "read", "fan_read"}

        # Parse circuit_type to check if any component needs read/write
        if isinstance(self.circuit_type, str):
            if self.circuit_type in needs_read_write:
                return cirq.NamedQubit("read_write")
        else:
            # List case
            if any(comp in needs_read_write for comp in self.circuit_type):
                return cirq.NamedQubit("read_write")

        return None

    def _parse_circuit_type(self, circuit_type: type_circuit) -> List[str]:
        """Parse circuit_type and return list of enabled components."""
        all_components = [
            "fan_out",
            "write",
            "query",
            "fan_in",
            "read",
            "fan_read",
        ]

        if isinstance(circuit_type, str):
            if circuit_type in all_components:
                return [circuit_type]
            else:
                raise ValueError(f"Unknown component: {circuit_type}")
        else:
            # List case
            enabled = []
            for comp in circuit_type:
                if comp in all_components:
                    enabled.append(comp)
                else:
                    self.logger.warning(f"Unknown component: {comp}")

            if not enabled:
                raise ValueError(
                    "No valid components specified in circuit_type"
                )

            return enabled

    def _collect_needed_branches(
        self, control_bit_index: int, prefix: str
    ) -> None:
        """
        Recursively collect all branches that will be needed for the hierarchical structure.

        Args:
            control_bit_index: Index of the address bit controlling this level
            prefix: Binary path prefix for this branch
        """
        # Track this bit as a controller
        self.controlling_bits.add(control_bit_index)

        # Calculate the size of subcircuits at this level
        subcircuit_bits = control_bit_index  # Exclude the control bit itself

        # If subcircuits are at minimum size, we need these branches
        if subcircuit_bits <= self.min_qram_size:
            # We need branches for both left and right
            left_branch = prefix + "0"
            right_branch = prefix + "1"
            self.needed_branches.add(left_branch)
            self.needed_branches.add(right_branch)
        else:
            # Continue hierarchical collection
            self._collect_needed_branches(control_bit_index - 1, prefix + "0")
            self._collect_needed_branches(control_bit_index - 1, prefix + "1")

    def _initialize_qubits_for_branches(self):
        """Initialize only the qubits needed for the identified branches."""
        # Create memory qubits for all possible addresses
        for i in range(2**self.qram_bits):
            binary = bin(i)[2:].zfill(self.qram_bits)
            self.memory_qubits[f"m{binary}"] = cirq.NamedQubit(f"m{binary}")

        # Create routing qubits only for the branches we actually need
        for branch in self.needed_branches:
            # For each branch, create routing qubits for the subcircuit
            # The branch represents the prefix, so we need to determine how many bits
            # the subcircuit at this branch will have

            # Find the subcircuit size for this branch
            subcircuit_bits = self.min_qram_size

            # Create routing qubits for this subcircuit
            for i in range(2**subcircuit_bits):
                binary = bin(i)[2:].zfill(subcircuit_bits)
                full_path = branch + binary
                qubit_name = f"b_{full_path}"
                if qubit_name not in self.routing_qubits:
                    self.routing_qubits[qubit_name] = cirq.NamedQubit(
                        qubit_name
                    )

    @property
    def all_ancillas(self) -> List[cirq.Qid]:
        """Get all routing/ancilla qubits used in the hierarchical network."""
        return list(self.routing_qubits.values())

    @property
    def memory(self) -> List[cirq.Qid]:
        """Get all memory qubits used in the hierarchical network."""
        return list(self.memory_qubits.values())

    @property
    def qubit_order(self) -> List[cirq.Qid]:
        """Get the qubit order for visualization."""
        return self._qubit_order.copy()

    def construct_qubit_order(self, circuit: cirq.Circuit) -> None:
        """
        Construct the order of qubits for circuit visualization or execution.

        Args:
            circuit: The complete circuit
        """
        # Clear any previous ordering
        self._qubit_order = []

        # Get only qubits that are actually used in the circuit
        circuit_qubits = circuit.all_qubits()

        # Add address qubits in reverse order (LSB to MSB)
        for qubit in reversed(self.address):
            if qubit in circuit_qubits:
                self._qubit_order.append(qubit)

        # Add ancilla qubits in sorted order (only those used in circuit)
        ancilla_qubits = [
            q for q in sorted(self.all_ancillas) if q in circuit_qubits
        ]
        self._qubit_order.extend(ancilla_qubits)

        # Add memory qubits in reverse order (only those used in circuit)
        memory_qubits = [
            q for q in reversed(self.memory) if q in circuit_qubits
        ]
        self._qubit_order.extend(memory_qubits)

        # Add any Toffoli decomposition ancillas that are present in the circuit
        try:
            toffoli_ancillas = ToffoliDecomposition(None, None).ancilla
            for qubit in toffoli_ancillas:
                if qubit in circuit_qubits and qubit not in self._qubit_order:
                    self._qubit_order.append(qubit)
        except Exception as e:
            # If ToffoliDecomposition fails, just log and continue
            self.logger.debug(f"Could not get Toffoli ancillas: {e}")

        # Add target qubit if used in circuit
        if (
            self.target is not None
            and self.target in circuit_qubits
            and self.target not in self._qubit_order
        ):
            self._qubit_order.append(self.target)

        # Add read/write qubit last, if it exists and is used in circuit
        if (
            self.read_write is not None
            and self.read_write in circuit_qubits
            and self.read_write not in self._qubit_order
        ):
            self._qubit_order.append(self.read_write)

        # Ensure we don't have duplicate qubits
        seen = set()
        unique_order = []
        for qubit in self._qubit_order:
            if qubit not in seen:
                seen.add(qubit)
                unique_order.append(qubit)
        self._qubit_order = unique_order

        self.logger.debug(
            f"Constructed qubit order with {len(self._qubit_order)} qubits"
        )

    def build(self) -> cirq.Circuit:
        """Build the hierarchical bucket brigade network with grouped components."""
        # Reset controlling bits tracker and needed branches
        self.controlling_bits = set()
        self.needed_branches = set()

        # Clear component cache for fresh build
        self._component_cache = {}
        self._circuit_cache = {}

        # If we're at or below minimum size, build a flat QRAM
        if self.qram_bits <= self.min_qram_size:
            # For flat QRAM, we need all possible paths
            for i in range(2**self.qram_bits):
                binary = bin(i)[2:].zfill(self.qram_bits)
                self.memory_qubits[f"m{binary}"] = cirq.NamedQubit(
                    f"m{binary}"
                )
                # For flat QRAM, we just need one set of routing qubits
                self.routing_qubits[f"b_{binary}"] = cirq.NamedQubit(
                    f"b_{binary}"
                )
            return self._build_flat_qram()

        # First pass: collect all needed branches
        self._collect_needed_branches(self.qram_bits - 1, "")

        # Initialize qubits only for needed branches
        self._initialize_qubits_for_branches()

        # Clear component subcircuits for fresh build
        for component_type in self.component_subcircuits:
            self.component_subcircuits[component_type] = []

        # Collect all component subcircuits from the hierarchy
        # Start from the highest address bit index (MSB)
        self._collect_component_subcircuits(self.qram_bits - 1, "")

        # Build the final circuit by grouping components sequentially
        circuit = cirq.Circuit()
        component_sequence = [
            "fan_out",
            "write",
            "query",
            "fan_in",
            "read",
            "fan_read",
        ]

        for component_type in component_sequence:
            if component_type in self.enabled_components:
                if self.component_subcircuits[component_type]:
                    self.logger.info(
                        f"Adding {len(self.component_subcircuits[component_type])} {component_type} subcircuits"
                    )
                    circuit.append(self.component_subcircuits[component_type])

        return circuit

    def _collect_component_subcircuits(
        self, control_bit_index: int, prefix: str
    ) -> None:
        """
        Recursively collect component subcircuits for all branches.

        Args:
            control_bit_index: Index of the address bit controlling this level
            prefix: Binary path prefix for this branch
        """
        control_bit = self.address[control_bit_index]

        # Calculate the size of subcircuits at this level
        subcircuit_bits = control_bit_index  # Exclude the control bit itself

        # If subcircuits are at minimum size, create component subcircuits
        if subcircuit_bits <= self.min_qram_size:
            # Create subcircuits for left branch (control_bit = 0)
            left_ops = self._create_component_subcircuits_direct(
                subcircuit_bits, prefix + "0"
            )
            if left_ops:
                for component_type, ops in left_ops.items():
                    for op in ops:
                        # Control by current bit with value 0
                        controlled_op = op.controlled_by(
                            control_bit, control_values=[0]
                        )
                        self.component_subcircuits[component_type].append(
                            controlled_op
                        )

            # Create subcircuits for right branch (control_bit = 1)
            right_ops = self._create_component_subcircuits_direct(
                subcircuit_bits, prefix + "1"
            )
            if right_ops:
                for component_type, ops in right_ops.items():
                    for op in ops:
                        # Control by current bit with value 1
                        controlled_op = op.controlled_by(
                            control_bit, control_values=[1]
                        )
                        self.component_subcircuits[component_type].append(
                            controlled_op
                        )
        else:
            # Continue hierarchical collection and then control the results

            # Temporarily store current component counts
            temp_counts = {
                comp: len(self.component_subcircuits[comp])
                for comp in self.component_subcircuits
            }

            # Collect subcircuits for left branch
            self._collect_component_subcircuits(
                control_bit_index - 1, prefix + "0"
            )

            # Get the new operations added for left branch
            left_ops_added = {}
            for comp in self.component_subcircuits:
                current_count = len(self.component_subcircuits[comp])
                if current_count > temp_counts[comp]:
                    left_ops_added[comp] = self.component_subcircuits[comp][
                        temp_counts[comp] :
                    ]
                    # Remove them temporarily
                    self.component_subcircuits[comp] = (
                        self.component_subcircuits[comp][: temp_counts[comp]]
                    )

            # Collect subcircuits for right branch
            self._collect_component_subcircuits(
                control_bit_index - 1, prefix + "1"
            )

            # Get the new operations added for right branch
            right_ops_added = {}
            for comp in self.component_subcircuits:
                current_count = len(self.component_subcircuits[comp])
                if current_count > temp_counts[comp]:
                    right_ops_added[comp] = self.component_subcircuits[comp][
                        temp_counts[comp] :
                    ]
                    # Remove them temporarily
                    self.component_subcircuits[comp] = (
                        self.component_subcircuits[comp][: temp_counts[comp]]
                    )

            # Now add back the operations with proper control hierarchy
            for comp in self.component_subcircuits:
                # Add left branch operations controlled by control_bit=0
                if comp in left_ops_added:
                    for op in left_ops_added[comp]:
                        controlled_op = op.controlled_by(
                            control_bit, control_values=[0]
                        )
                        self.component_subcircuits[comp].append(controlled_op)

                # Add right branch operations controlled by control_bit=1
                if comp in right_ops_added:
                    for op in right_ops_added[comp]:
                        controlled_op = op.controlled_by(
                            control_bit, control_values=[1]
                        )
                        self.component_subcircuits[comp].append(controlled_op)

    def _create_component_subcircuits_direct(
        self, bits: int, prefix: str
    ) -> Dict[str, List[cirq.CircuitOperation]]:
        """
        Create component subcircuits directly without additional controls.

        Args:
            bits: Number of address bits for this QRAM
            prefix: Binary prefix for routing and memory qubits

        Returns:
            Dictionary of component operations (without controls)
        """
        if bits < 1:
            return {}

        # Get the address qubits for this level (a0 through a_{bits-1})
        address_qubits = self.address[:bits]

        # Check if we've already created circuits for this configuration
        cache_key = f"{bits}_{prefix}"
        if cache_key in self._circuit_cache:
            return self._circuit_cache[cache_key]

        # Create bucket brigade components with proper qubit assignments
        components = self._create_bucket_brigade_components(
            bits, prefix, address_qubits
        )

        # Create individual circuits for enabled component types
        result = {}
        component_sequence = [
            "fan_out",
            "write",
            "query",
            "fan_in",
            "read",
            "fan_read",
        ]

        for component_name in component_sequence:
            if component_name in self.enabled_components:
                if component_name in components and components[component_name]:
                    component = components[component_name]

                    # Build the component's individual circuit
                    component_circuit = (
                        self._build_individual_component_circuit(
                            component, component_name
                        )
                    )

                    if component_circuit and len(component_circuit) > 0:
                        # Create frozen circuit operation (without control)
                        frozen_circuit = cirq.FrozenCircuit(component_circuit)
                        # Fix: Add use_repetition_ids=True to avoid the warning
                        circuit_op = cirq.CircuitOperation(
                            frozen_circuit, use_repetition_ids=True
                        )

                        if component_name not in result:
                            result[component_name] = []
                        result[component_name].append(circuit_op)

        # Cache the result for future use
        self._circuit_cache[cache_key] = result
        return result

    def _build_individual_component_circuit(
        self, component, component_name: str
    ) -> Optional[cirq.Circuit]:
        """
        Build the circuit for an individual component.

        Args:
            component: The bucket brigade component instance
            component_name: Name of the component type

        Returns:
            Circuit containing only this component's operations
        """
        # Use component's identity to check cache
        component_id = id(component)
        if component_id in self._component_cache:
            return self._component_cache[component_id]

        try:
            # Call construct_circuit to build the component's circuit
            component.construct_circuit()

            if hasattr(component, "circuit") and component.circuit:
                # Cache the circuit for future reuse
                self._component_cache[component_id] = component.circuit
                return component.circuit
            else:
                self.logger.warning(
                    f"Component {component_name} has no circuit"
                )
                return cirq.Circuit()

        except Exception as e:
            self.logger.error(f"Error building {component_name} circuit: {e}")
            import traceback

            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return cirq.Circuit()

    def _build_flat_qram(self) -> cirq.Circuit:
        """Build a flat (non-hierarchical) QRAM for the full address space."""
        return self._build_flat_qram_for_branch(self.qram_bits, "")

    def _build_flat_qram_for_branch(
        self, bits: int, prefix: str
    ) -> Optional[cirq.Circuit]:
        """
        Build a flat QRAM circuit for a specific branch.

        Args:
            bits: Number of address bits for this QRAM
            prefix: Binary prefix for routing and memory qubits

        Returns:
            Complete QRAM circuit for this branch
        """
        if bits < 1:
            return cirq.Circuit()

        circuit = cirq.Circuit()

        # Get the address qubits for this level (a0 through a_{bits-1})
        address_qubits = self.address[:bits]

        # Create bucket brigade components with proper qubit assignments
        components = self._create_bucket_brigade_components(
            bits, prefix, address_qubits
        )

        # Build only the enabled components in the correct sequence
        component_sequence = [
            "fan_out",
            "write",
            "query",
            "fan_in",
            "read",
            "fan_read",
        ]

        for component_name in component_sequence:
            if component_name in self.enabled_components:
                if component_name in components and components[component_name]:
                    component_circuit = (
                        self._build_individual_component_circuit(
                            components[component_name], component_name
                        )
                    )
                    if component_circuit:
                        circuit.append(component_circuit)
                else:
                    # Use empty circuit for missing enabled components
                    self.logger.debug(
                        f"Using empty circuit for missing component: {component_name}"
                    )

        return circuit

    def _create_bucket_brigade_components(
        self, bits: int, prefix: str, address_qubits: List[cirq.Qid]
    ) -> Dict[str, any]:
        """
        Create and configure bucket brigade components for a specific branch.
        Only creates components that are enabled in circuit_type.
        Uses multiprocessing for parallel component creation.

        Args:
            bits: Number of address bits
            prefix: Binary prefix for qubit naming
            address_qubits: Address qubits to use

        Returns:
            Dictionary of configured components (only enabled ones)
        """
        # Check component cache first
        cache_key = f"{bits}_{prefix}"
        if cache_key in self._component_cache:
            return self._component_cache[cache_key]

        # Get routing qubits for this branch - they should follow the pattern b_{prefix}{binary}
        routing_qubits = []
        for i in range(2**bits):
            binary = bin(i)[2:].zfill(bits)
            full_path = prefix + binary
            qubit_name = f"b_{full_path}"
            if qubit_name in self.routing_qubits:
                routing_qubits.append(self.routing_qubits[qubit_name])
            else:
                # Create the qubit if it doesn't exist (shouldn't happen if _initialize_qubits_for_branches works correctly)
                self.logger.warning(
                    f"Creating missing routing qubit: {qubit_name}"
                )
                self.routing_qubits[qubit_name] = cirq.NamedQubit(qubit_name)
                routing_qubits.append(self.routing_qubits[qubit_name])

        # Get memory qubits for this branch
        memory_qubits = []
        for i in range(2**bits):
            binary = bin(i)[2:].zfill(bits)
            full_path = prefix + binary
            memory_key = f"m{full_path}"
            if memory_key in self.memory_qubits:
                memory_qubits.append(self.memory_qubits[memory_key])
            else:
                # Create the qubit if it doesn't exist
                self.logger.warning(
                    f"Creating missing memory qubit: {memory_key}"
                )
                self.memory_qubits[memory_key] = cirq.NamedQubit(memory_key)
                memory_qubits.append(self.memory_qubits[memory_key])

        # Ensure we have the expected number of qubits
        expected_routing = 2**bits
        expected_memory = 2**bits

        if len(routing_qubits) != expected_routing:
            self.logger.error(
                f"Expected {expected_routing} routing qubits for bits={bits}, prefix='{prefix}', got {len(routing_qubits)}"
            )
            self.logger.error(
                f"Available routing qubits: {list(self.routing_qubits.keys())}"
            )
            return {}

        if len(memory_qubits) != expected_memory:
            self.logger.error(
                f"Expected {expected_memory} memory qubits for bits={bits}, prefix='{prefix}', got {len(memory_qubits)}"
            )
            return {}

        # Create a list of component creation tasks
        component_tasks = []
        for component_name in self.enabled_components:
            component_tasks.append(
                (
                    component_name,
                    bits,
                    self.decomp_scenario,
                    address_qubits,
                    routing_qubits,
                    memory_qubits,
                    self.target,
                    self.read_write,
                )
            )

        # Use multiprocessing only if we have multiple components to create
        components = {}
        if len(component_tasks) > 1:
            try:
                # Determine optimal pool size
                pool_size = max(
                    1, min(multiprocessing.cpu_count(), len(component_tasks))
                )

                # Use Pool for multiprocessing
                with multiprocessing.Pool(processes=pool_size) as pool:
                    results = pool.map(_create_component_mp, component_tasks)

                    # Process results
                    for component_name, component in results:
                        if component is not None:
                            components[component_name] = component
            except Exception as e:
                self.logger.error(
                    f"Error in multiprocessing component creation: {e}"
                )
                # Fall back to sequential creation
                self._create_components_sequentially(
                    components, component_tasks
                )
        else:
            # For a single component, just create it directly
            self._create_components_sequentially(components, component_tasks)

        # Cache the components for future use
        self._component_cache[cache_key] = components
        return components

    def _create_components_sequentially(
        self, components_dict, component_tasks
    ):
        """Create components sequentially as a fallback if multiprocessing fails."""
        for task in component_tasks:
            component_name, component = _create_component_mp(task)
            if component is not None:
                components_dict[component_name] = component

    def get_subcircuit(
        self, component_type: str, level: Optional[int] = None
    ) -> Optional[cirq.FrozenCircuit]:
        """
        Extract a specific component type subcircuit as a FrozenCircuit.

        Args:
            component_type: Type of component ('fan_out', 'write', 'query', 'fan_in', 'read', 'fan_read')
            level: Specific level to extract (None for all levels)

        Returns:
            FrozenCircuit for the requested component type, or None if component is disabled
        """
        if component_type not in self.enabled_components:
            self.logger.warning(
                f"Component {component_type} is not enabled in this circuit"
            )
            return None

        if component_type not in self.component_subcircuits:
            return None

        subcircuits = self.component_subcircuits[component_type]
        if not subcircuits:
            return None

        # If level is specified, try to get that specific level
        if level is not None and 0 <= level < len(subcircuits):
            # Create a circuit with just that level
            circuit = cirq.Circuit([subcircuits[level]])
            return cirq.FrozenCircuit(circuit)

        # Return all subcircuits of this type
        circuit = cirq.Circuit(subcircuits)
        return cirq.FrozenCircuit(circuit)

    def get_component_count(self) -> Dict[str, int]:
        """Get the count of subcircuits for each component type."""
        return {
            component_type: len(subcircuits)
            for component_type, subcircuits in self.component_subcircuits.items()
        }

    def get_enabled_components(self) -> List[str]:
        """Get list of enabled components."""
        return self.enabled_components.copy()

    def get_all_qubits(self) -> List[cirq.Qid]:
        """Get all qubits used in the hierarchical network."""
        if self.circuit:
            return list(self.circuit.all_qubits())
        return []

    def get_qubit_order(self) -> List[cirq.Qid]:
        """Get a sensible order of qubits for visualization."""
        return self.qubit_order

    def visualize(self):
        """Visualize the hierarchical QRAM network circuit."""
        if not self.circuit:
            print("Circuit not yet constructed")
            return

        print(f"HIERARCHICAL BUCKET BRIGADE NETWORK:")
        print(
            f"Hierarchical Bucket Brigade Network with {self.qram_bits} address bits"
        )
        print(f"Minimum decomposition size: {self.min_qram_size}")
        print(f"Enabled components: {self.enabled_components}")

        all_qubits = self.get_all_qubits()
        address_qubits = sorted(
            [q for q in all_qubits if q.name.startswith("a")]
        )
        routing_qubits = sorted(
            [q for q in all_qubits if q.name.startswith("b_")]
        )
        memory_qubits = sorted(
            [q for q in all_qubits if q.name.startswith("m")]
        )

        print("\nAddress Qubit Hierarchy:")
        for i, qubit in enumerate(address_qubits):
            if i == 0:
                print(
                    f"  {qubit.name}: Inside bucket brigade circuits (memory access)"
                )
            elif i in self.controlling_bits:
                # Correct level calculation
                # For hierarchical control, higher index = higher level
                # The highest controlling bit gets the highest level number
                sorted_controlling_bits = sorted(
                    self.controlling_bits, reverse=True
                )
                try:
                    level_index = sorted_controlling_bits.index(i)
                    level = level_index + 1
                    print(f"  {qubit.name}: Controls level {level} branching")
                except ValueError:
                    print(f"  {qubit.name}: Error in level calculation")
            else:
                print(f"  {qubit.name}: Not used in current decomposition")

        print("\nComponent Subcircuit Counts:")
        component_counts = self.get_component_count()
        for component_type in [
            "fan_out",
            "write",
            "query",
            "fan_in",
            "read",
            "fan_read",
        ]:
            count = component_counts[component_type]
            status = (
                "enabled"
                if component_type in self.enabled_components
                else "disabled"
            )
            print(f"  {component_type}: {count} subcircuits ({status})")

        print("\nRouting Qubits:")
        routing_by_level = {}
        for qubit in routing_qubits:
            # Extract level from b_xxx format
            path = qubit.name[2:]  # Remove "b_"
            level = len(path)
            if level not in routing_by_level:
                routing_by_level[level] = []
            routing_by_level[level].append(qubit.name)

        for level in sorted(routing_by_level.keys()):
            qubits = routing_by_level[level][:5]  # Show first 5
            remaining = len(routing_by_level[level]) - 5
            print(
                f"  Level {level}: {qubits}{f' + {remaining} more' if remaining > 0 else ''}"
            )

        print("\nMemory Qubits:")
        memory_sample = memory_qubits[:10]  # Show first 10
        remaining_memory = len(memory_qubits) - 10
        print(
            f"  {[q.name for q in memory_sample]}{f' + {remaining_memory} more' if remaining_memory > 0 else ''}"
        )

        print("\nCircuit Information:")
        print(f"  Total qubits: {len(all_qubits)}")
        print(f"  Circuit depth: {len(self.circuit)}")
        print(
            f"  Hierarchical levels: {self.qram_bits - self.min_qram_size + 1}"
        )

        print("\nCircuit Structure (component grouping):")
        print(
            "  Sequential order: fan_out -> write -> query -> fan_in -> read -> fan_read"
        )
        print(
            "  Each group contains all subcircuits of that type across all branches"
        )
        print("  Disabled components are skipped (use empty circuits)")

        print("\nCircuit Structure:")
        print(self.circuit)
