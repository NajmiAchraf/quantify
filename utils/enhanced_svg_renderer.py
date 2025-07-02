import base64
from typing import List

import cirq
from cirq.contrib.svg.svg import tdd_to_svg
from IPython.display import HTML, display
from rich.console import Console

console = Console()


class EnhancedSVGRenderer:
    """
    Basic SVG renderer with display and export functionality.
    """

    def __init__(self):
        self.console = console

    def display_circuit(
        self, circuit: cirq.Circuit, qubits: List[cirq.NamedQubit]
    ) -> None:
        """Display the circuit with standard SVG rendering."""
        console.print("[bold cyan]🖼️ Displaying circuit...[/bold cyan]")

        # Use standard Cirq SVG generation
        tdd = circuit.to_text_diagram_drawer(
            transpose=False, qubit_order=qubits
        )
        svg = tdd_to_svg(tdd)

        # Encode and display
        svg_base64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
        html = f'<img width="100%" style="background-color:white;" src="data:image/svg+xml;base64,{svg_base64}" >'

        display(HTML(html))
        console.print("[bold green]✅ Circuit displayed![/bold green]")

    def export_circuit(
        self,
        circuit: cirq.Circuit,
        qubits: List[cirq.NamedQubit],
        filename: str,
    ) -> None:
        """Export the circuit as SVG."""
        console.print(
            f"[bold blue]💾 Exporting circuit to {filename}...[/bold blue]"
        )

        # Use standard Cirq SVG generation
        tdd = circuit.to_text_diagram_drawer(
            transpose=False, qubit_order=qubits
        )
        svg = tdd_to_svg(tdd)

        with open(filename, "w") as f:
            f.write(svg)

        console.print(
            f"[bold green]✅ Circuit exported to {filename}![/bold green]"
        )


# Integration functions
def enhanced_display_circuit(
    circuit: cirq.Circuit, qubits: List[cirq.NamedQubit]
) -> None:
    """Display circuit using EnhancedSVGRenderer."""
    renderer = EnhancedSVGRenderer()
    renderer.display_circuit(circuit, qubits)


def enhanced_export_circuit(
    circuit: cirq.Circuit,
    qubits: List[cirq.NamedQubit],
    name: str = "enhanced_circuit",
) -> None:
    """Export circuit using EnhancedSVGRenderer."""
    renderer = EnhancedSVGRenderer()
    filename = f"images/{name}_enhanced.svg"
    renderer.export_circuit(circuit, qubits, filename)
