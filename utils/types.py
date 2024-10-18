from typing import Literal

# Define the custom type for QRAM types
type_qram = Literal["core", "bilan", "experiments", "stress"]

# Define the custom type for the simulation types
type_print_circuit = Literal["Print", "Display", "Hide"]
type_print_sim = Literal["Dot", "Full", "Loading", "Hide"]
type_specific_simulation = Literal["a", "b", "m", "ab", "bm", "abm", "t", "full"]
type_simulation_kind = Literal["bb", "dec"]