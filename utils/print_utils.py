import cirq
import cirq.optimizers
import time
from datetime import timedelta

import threading

from IPython.display import display
from cirq.contrib.svg import SVGCircuit, circuit_to_svg
from utils.counting_utils import *


#######################################
# static methods
#######################################

def colpr(color: str, *args: str, end: str="\n") -> None:
    """
    Prints colored text.

    Args:
        color (str): The color of the text [r, g, v, b, y, c, w, m, k, d, u].
        args (str): The text to be printed.
        end (str): The end character.

    Returns:
        None
    """

    colors = {
        "r": "\033[91m",
        "g": "\033[92m",
        "v": "\033[95m",
        "b": "\033[94m",
        "y": "\033[93m",
        "c": "\033[96m",
        "w": "\033[97m",
        "m": "\033[95m",
        "k": "\033[90m",
        "d": "\033[2m",
        "u": "\033[4m"
    }
    print(colors[color] + "".join(args) + "\033[0m", flush=True, end=end)


def elapsed_time(start: float) -> str:
    """
    Format the elapsed time from the start time to the current time.

    Args:
        start (float): The start time in seconds.

    Returns:
        str: The formatted elapsed time.
    """

    elapsed_time = time.time() - start
    delta = timedelta(seconds=elapsed_time)

    weeks = delta.days // 7
    days = delta.days % 7
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = delta.microseconds // 1000

    if weeks > 0:
        return f"{weeks}w {days}d {hours}h {minutes}min {seconds}s {milliseconds}ms"
    elif days > 0:
        return f"{days}d {hours}h {minutes}min {seconds}s {milliseconds}ms"
    elif hours > 0:
        return f"{hours}h {minutes}min {seconds}s {milliseconds}ms"
    elif minutes > 0:
        return f"{minutes}min {seconds}s {milliseconds}ms"
    elif seconds > 0:
        return f"{seconds}s {milliseconds}ms"
    else:
        return f"{milliseconds}ms"


def loading_animation(stop_event: threading.Event, title: str) -> None:
    animation = "|/-\\"
    idx = 0
    while not stop_event.is_set():
        print(f"\rLoading {title} {animation[idx % len(animation)]}", end="")
        idx += 1
        time.sleep(0.1)
    print("\r" + " " * (10 + len(title)) + "\r", end="")


def format_bytes(num_bytes):
    """
    Convert bytes to a human-readable format using SI units.

    Args:
        num_bytes (int): The number of bytes.

    Returns:
        str: The human-readable format.
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num_bytes < 1024:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024


def printCircuit(
        print_circuit: str,
        circuit: cirq.Circuit,
        qubits: 'list[cirq.NamedQubit]',
        name: str = "bucket brigade"
) -> None:
    """
    Prints the circuit.

    Args:
        circuit (cirq.Circuit): The circuit to be printed.
        qubits ('list[cirq.NamedQubit]'): The qubits of the circuit.
        name (str): The name of the circuit.

    Returns:
        None
    """
    if print_circuit == "Print":
        # Print the circuit
        start = time.time()

        colpr("c", f"Print {name} circuit:" , end="\n\n")
        print(
            circuit.to_text_diagram(
                # use_unicode_characters=False,
                qubit_order=qubits
            ),
            end="\n\n"
        )

        stop = elapsed_time(start)
        colpr("w", "Time elapsed on printing the circuit: ", stop, end="\n\n")

    elif print_circuit == "Display":
        # Display the circuit
        start = time.time()

        colpr("c", f"Display {name} circuit:" , end="\n\n")

        display(SVGCircuit(circuit))

        stop = elapsed_time(start)
        colpr("w", "Time elapsed on displaying the circuit: ", stop, end="\n\n")

    # # Save the circuit as an SVG file
    # with open(f"images/{self.__start_range_qubits}_{name}_circuit.svg", "w") as f:
    #     f.write(sv.circuit_to_svg(circuit))
