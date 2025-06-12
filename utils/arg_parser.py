import argparse
from typing import List, Literal, Tuple, Union

from utils.types import type_qram

# Help messages
MSG0 = "Qubit range must start at least from 2 and the end range must be greater than or equal to the start range, for example 2-5 (start-end) or 2 (single start)"
MSG1 = "Specific simulation must be one of (qram, full), by default it is qram pattern."

# Circuit type flags - powers of 2 for bitwise operations
CIRCUIT_FAN_OUT = 1  # 2^0
CIRCUIT_WRITE = 2  # 2^1
CIRCUIT_QUERY = 4  # 2^2
CIRCUIT_FAN_IN = 8  # 2^3
CIRCUIT_READ = 16  # 2^4
CIRCUIT_FAN_READ = 32  # 2^5

# Map of flag values to circuit type names
CIRCUIT_TYPE_MAP = {
    CIRCUIT_FAN_OUT: "fan_out",
    CIRCUIT_WRITE: "write",
    CIRCUIT_QUERY: "query",
    CIRCUIT_FAN_IN: "fan_in",
    CIRCUIT_READ: "read",
    CIRCUIT_FAN_READ: "fan_read",
}


def parse_t_count(value: str) -> int:
    """
    Parse the T count for the QueryConfiguration.
    Ensures the T count is between 4 and 7.
    """

    t_count: int = int(value)
    if not (4 <= t_count <= 7):
        raise argparse.ArgumentTypeError(
            "The T count should be between 4 and 7."
        )
    return t_count


def parse_t_count_bilan(value: str) -> int:
    """
    Parse the T count for the QueryConfiguration.
    Ensures the T count is between 4 and 7.
    """

    t_count: int = int(value)
    if not (4 <= t_count <= 6):
        raise argparse.ArgumentTypeError(
            "The T count should be between 4 and 6."
        )
    return t_count


def parse_t_cancel(value: str) -> int:
    """
    Parse the T cancel for the combinations.
    Ensures the T cancel is greater than 1.
    """

    t_cancel: int = int(value)
    if t_cancel < 1:
        raise argparse.ArgumentTypeError(
            "The T cancel should be greater than 1."
        )
    return t_cancel


def parse_print_circuit(value: str) -> str:
    """
    Parse the print circuit option.
    """

    if value not in ["p", "d", "e", "h"]:
        raise argparse.ArgumentTypeError(
            "The print circuit option should be one of (p, d, e, h)."
        )

    circuit_options = {
        "p": "Print",
        "d": "Display",
        "e": "Export",
        "h": "Hide",
    }
    return circuit_options[value]


def parse_print_simulation(value: str) -> str:
    """
    Parse the print simulation option.
    """

    if value not in ["f", "d", "l", "h"]:
        raise argparse.ArgumentTypeError(
            "The print simulation option should be one of (f, d, l, h)."
        )

    simulation_options = {"d": "Dot", "f": "Full", "l": "Loading", "h": "Hide"}
    return simulation_options[value]


def parse_qubit_range(value: str) -> Tuple[int, int]:
    """
    Parse a qubit range from a string.
    The string can be a single integer or a range in the form 'start-end'.
    """

    if "-" in value:
        start, end = map(int, value.split("-"))
    else:
        start = end = int(value)

    if start < 2 or end < 2 or end < start:
        raise argparse.ArgumentTypeError(MSG0 + ".")

    return start, end


def parse_shots(value: str) -> int:
    """
    Parse the number of shots for the simulation.
    """

    shots: int = int(value)
    if shots < 10:
        raise argparse.ArgumentTypeError(
            "The number of shots should be greater than 10."
        )
    return shots


def parse_circuit_type(value: str) -> Union[List[str], str]:
    """
    Parse the circuit type using a digital approach.

    The value must be an integer where each bit represents a circuit component:
        1 = fan_out, 2 = write, 4 = query, 8 = fan_in,
        16 = read, 32 = fan_read

    Examples:
        3 = fan_out + write (1+2)
        7 = fan_out + write + query (1+2+4)
        13 = fan_out + query + fan_in (1+4+8)

    Returns:
        Union[List[str], str]: Returns a list of component names when multiple
        components are selected, or a single string when only one component is selected.
    """
    # Calculate the maximum valid value (sum of all defined flags)
    all_valid_flags = sum(CIRCUIT_TYPE_MAP.keys())

    # Parse as an integer
    try:
        flag_value = int(value)

        # Check if any undefined bits are set
        if flag_value > all_valid_flags or flag_value <= 0:
            flag_options = ", ".join(
                [
                    f"{flag}={CIRCUIT_TYPE_MAP[flag]}"
                    for flag in CIRCUIT_TYPE_MAP
                ]
            )
            raise argparse.ArgumentTypeError(
                f"Invalid circuit type value: {value}. Must be a value between 1 and {all_valid_flags}.\n"
                f"Available components: {flag_options}\n"
                f"Examples: 3=fan_out+write, 13=fan_out+query+fan_in"
            )

        # Convert flag value to list of circuit types
        selected_types = [
            CIRCUIT_TYPE_MAP[flag]
            for flag in CIRCUIT_TYPE_MAP
            if flag & flag_value
        ]

        # Return either a list of strings (multiple components) or a single string (one component)
        return selected_types if len(selected_types) > 1 else selected_types[0]

    except ValueError:
        # Not an integer
        flag_options = ", ".join(
            [f"{flag}={CIRCUIT_TYPE_MAP[flag]}" for flag in CIRCUIT_TYPE_MAP]
        )
        raise argparse.ArgumentTypeError(
            f"Invalid circuit type: {value}. Must be a numeric value.\n"
            f"Available components: {flag_options}\n"
            f"Examples: 3=fan_out+write, 13=fan_out+query+fan_in"
        )


def parser_args(qram_type: type_qram) -> argparse.ArgumentParser:
    """
    Parse the arguments for the core functions.

    Args:
        qram_type (type_qram): The type of QRAM experiment.

    Returns:
        argparse.ArgumentParser: The argument parser with the defined arguments.
    """

    parser = argparse.ArgumentParser(
        description=f"QRAM {qram_type.capitalize()} Arguments"
    )

    parser.add_argument(
        "--qubit-range",
        type=parse_qubit_range,
        nargs="?",
        default=(2, 2),
        help=f"{MSG0}, by default it is 2.",
    )

    if qram_type == "experiments" or qram_type == "stress":
        parser.add_argument(
            "--t-count",
            type=parse_t_count,
            nargs="?",
            default=7,
            required=True,
            help="The T count for the QueryConfiguration it should be between 4 and 7, by default it is 7.",
        )
    elif qram_type == "assessment":
        parser.add_argument(
            "--t-count",
            type=parse_t_count_bilan,
            nargs="?",
            default=6,
            required=True,
            help="The T count for the QueryConfiguration it should be between 4 and 6, by default it is 6.",
        )

    if qram_type == "stress":
        parser.add_argument(
            "--t-cancel",
            type=parse_t_cancel,
            nargs="?",
            default=1,
            help="The T cancel for the combinations it should be greater than 0, by default it is 1.",
        )

    if qram_type != "assessment":
        parser.add_argument(
            "--shots",
            type=parse_shots,
            nargs="?",
            default=50,
            help="The number of shots for the simulation, except for specific 'full' simulation case, by default it is 50.",
        )
        parser.add_argument(
            "--hpc",
            action="store_true",
            help="Run the experiment on HPC, need `OpenMPI` and `mpi4py` installed.",
        )
        parser.add_argument(
            "--simulate",
            action="store_true",
            help="Simulate Toffoli decompositions and QRAM circuits.",
        )
        parser.add_argument(
            "--print-circuit",
            type=parse_print_circuit,
            nargs="?",
            default="h",
            help="(p) print or (d) display or (e) export or (h) hide circuits, by default it is hide",
        )
        parser.add_argument(
            "--print-simulation",
            type=parse_print_simulation,
            nargs="?",
            default="h",
            help="Print (f) full simulation, (d) just dots, (l) loading or (h) hide the simulation, by default it is hide.",
        )
        parser.add_argument(
            "--specific",
            type=str,
            choices=["qram", "full"],
            nargs="?",
            default="qram",
            help=MSG1,
        )
        parser.add_argument(
            "--circuit-type",
            type=parse_circuit_type,
            nargs="?",
            default=["fan_out", "query", "fan_in"],
            help="""Circuit type to use as a numeric value where:
            1=fan_out, 2=write, 4=query, 8=fan_in, 16=read, 32=fan_read
            Examples: 3=fan_out+write, 7=fan_out+write+query, 13=fan_out+query+fan_in (default)""",
        )

    return parser
