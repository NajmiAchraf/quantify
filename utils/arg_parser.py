import argparse
from typing import Literal

MSG0 = "Start range of qubits must be at least 2"
MSG1 = "End range of qubits must be greater than start range of qubits or equal to it"
MSG2 = "Specific simulation must be (a, b, m, ab, bm, abm, t), by default it is full circuit"

type_qram = Literal["core", "bilan", "experiment", "stress"]

def parser_args(qram_type: type_qram) -> argparse.ArgumentParser:
    """
    Parse the arguments for the core functions.

    Returns:
        argparse.Namespace: The parsed
    """

    parser = argparse.ArgumentParser(description="QRAM Experiment Arguments")

    if qram_type == "stress":
        parser.add_argument("--t_cancel", type=int, required=True, help="The T cancel for the combinations.")

    if qram_type != "core":
        parser.add_argument("--t_count", type=int, required=True, help="The T count for the QueryConfiguration.")

    parser.add_argument('--simulate', action='store_true', help="Simulate Toffoli decompositions and circuit")
    parser.add_argument('--print_circuit', type=str, choices=['p', 'd', 'h'], nargs='?', default="h",
                        help="(p) print or (d) display or (h) hide circuits")
    parser.add_argument('--print_simulation', type=str, choices=['f', 'd', 'l', 'h'], nargs='?', default="h",
                        help="Print (f) full simulation, (d) just dots, (l) loading or (h) hide the simulation")
    parser.add_argument('--start', type=int, nargs='?', default=2, help=MSG0)
    parser.add_argument('--end', type=int, nargs='?', default=0, help=MSG1)
    parser.add_argument('--specific', type=str, choices=['a', 'b', 'm', 'ab', 'bm', 'abm', 't'], nargs='?', default="full",
                        help=MSG2)

    return parser
