import cirq
import cirq.optimizers
import time
from datetime import timedelta

import base64

import threading

from IPython.display import  SVG, display, HTML
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
        colpr("b", f"\rLoading {title} {animation[idx % len(animation)]}", end="")
        idx += 1
        time.sleep(0.1)
    print("\r" + " " * (10 + len(title)) + "\r", end="")
    colpr("y", f"Loading {title} done")


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

_html_template = '<img width="{}" style="background-color:white;" src="data:image/svg+xml;base64,{}" >'

def display_rescaled_svg(circuit: cirq.Circuit) -> None:
    """
    Display the circuit as a rescaled SVG.

    Args:
        circuit (cirq.Circuit): The circuit to be displayed.

    Returns:
        None
    """
    # Convert the circuit to SVG
    svg_data = circuit_to_svg(circuit)
    # Encode the SVG data to base64
    svg_base64 = base64.b64encode(svg_data.encode('utf-8')).decode('utf-8')
    # Display the SVG with a fixed width to avoid horizontal scrolling
    html = _html_template.format("100%", svg_base64)
    display(HTML(html))

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
        colpr("w", "Time elapsed on printing the circuit: ", end=" ")
        colpr("r", stop, end="\n\n")

    elif print_circuit == "Display":
        # Display the circuit
        start = time.time()

        colpr("c", f"Display {name} circuit:" , end="\n\n")

        if "ToffoliDecompType" in name:
            display(SVGCircuit(circuit))
        else:
            display_rescaled_svg(circuit)

        stop = elapsed_time(start)
        colpr("w", "Time elapsed on displaying the circuit: ", end=" ")
        colpr("r", stop, end="\n\n")

    # # Save the circuit as an SVG file
    # with open(f"images/{self.__start_range_qubits}_{name}_circuit.svg", "w") as f:
    #     f.write(sv.circuit_to_svg(circuit))

def printRange(start: int, stop: int, step: int) -> None:
    """
    Print the range of simulation in a visually appealing way with colors.
    """
    colpr("y", "Simulation Range:", end="\n\n")

    colpr("w", "+------------------+------------------+------------------+", end="\n")
    colpr("w", "|", end="")
    colpr("w", "      Start       ", end="")
    colpr("w", "|", end="")
    colpr("w", "      Stop        ", end="")
    colpr("w", "|", end="")
    colpr("w", "      Step        ", end="")
    colpr("w", "|", end="\n")
    colpr("w", "+------------------+------------------+------------------+", end="\n")

    colpr("w", "|", end="")
    colpr("r", f"{start:^17} ", end="")
    colpr("w", "|", end="")
    colpr("r", f"{stop:^17} ", end="")
    colpr("w", "|", end="")
    colpr("r", f"{step:^17} ", end="")
    colpr("w", "|", end="\n")
    colpr("w", "+------------------+------------------+------------------+", end="\n\n")
