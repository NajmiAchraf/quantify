import argparse
from typing import Literal, Tuple

# Help messages
MSG0 = "Start range of qubits must be at least 2"
MSG1 = "End range of qubits must be greater than or equal to the start range of qubits"
MSG2 = "Specific simulation must be one of (a, b, m, ab, bm, abm, t), by default it is full circuit"

# Define the custom type for QRAM types
type_qram = Literal["core", "bilan", "experiment", "stress"]

def parse_t_count(t_count: str) -> int:
    """
    Parse the T count for the QueryConfiguration.
    Ensures the T count is between 4 and 7.
    """
    t_count = int(t_count)
    if not (4 <= t_count <= 7):
        raise argparse.ArgumentTypeError("The T count should be between 4 and 7.")
    return t_count

def parse_t_cancel(t_cancel: str) -> int:
    """
    Parse the T cancel for the combinations.
    Ensures the T cancel is greater than 1.
    """
    t_cancel = int(t_cancel)
    if t_cancel < 1:
        raise argparse.ArgumentTypeError("The T cancel should be greater than 1.")
    return t_cancel

def parse_print_circuit(print_circuit: str) -> str:
    """
    Parse the print circuit option.
    """
    circuit_options = {"p": "Print", "d": "Display", "h": "Hide"}
    return circuit_options[print_circuit]

def parse_print_simulation(print_simulation: str) -> str:
    """
    Parse the print simulation option.
    """
    simulation_options = {"d": "Dot", "f": "Full", 'l': "Loading", "h": "Hide"}
    return simulation_options[print_simulation]

def parse_qubit_range(value: str) -> Tuple[int, int]:
    """
    Parse a qubit range from a string.
    The string can be a single integer or a range in the form 'start-end'.
    """
    if '-' in value:
        start_str, end_str = value.split('-')
        start = int(start_str)
        end = int(end_str)
    else:
        start = int(value)
        end = start
    
    if end < start:
        start, end = end, start

    if start < 2:
        raise argparse.ArgumentTypeError(MSG0)
    if end < 2:
        raise argparse.ArgumentTypeError(MSG0)

    return start, end

def parser_args(qram_type: type_qram) -> argparse.ArgumentParser:
    """
    Parse the arguments for the core functions.

    Args:
        qram_type (type_qram): The type of QRAM experiment.

    Returns:
        argparse.ArgumentParser: The argument parser with the defined arguments.
    """
    parser = argparse.ArgumentParser(description="QRAM Experiment Arguments")

    if qram_type == "stress":
        parser.add_argument("--t_cancel", type=parse_t_cancel, required=True, help="The T cancel for the combinations it should be greater than 1.")

    if qram_type != "core":
        parser.add_argument("--t_count", type=parse_t_count, nargs='?', required=True, help="The T count for the QueryConfiguration it should be between 4 and 7.")

    parser.add_argument('--hpc', action='store_true', help="Run the experiment on HPC")
    parser.add_argument('--simulate', action='store_true', help="Simulate Toffoli decompositions and circuit")
    parser.add_argument('--print_circuit', type=parse_print_circuit, choices=['p', 'd', 'h'], nargs='?', default="h",
                        help="(p) print or (d) display or (h) hide circuits")
    parser.add_argument('--print_simulation', type=parse_print_simulation, choices=['f', 'd', 'l', 'h'], nargs='?', default="h",
                        help="Print (f) full simulation, (d) just dots, (l) loading or (h) hide the simulation")
    parser.add_argument('--qubit_range', type=parse_qubit_range, nargs='?', default=(2, 2), help=f"{MSG0} or {MSG1}")
    parser.add_argument('--specific', type=str, choices=['a', 'b', 'm', 'ab', 'bm', 'abm', 't'], nargs='?', default="full",
                        help=MSG2)

    return parser