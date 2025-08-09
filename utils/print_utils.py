import os
import threading
import time
from datetime import timedelta

import cirq
from cirq.contrib.svg import SVGCircuit
from IPython.display import display
from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.text import Text

from utils.counting_utils import *
from utils.enhanced_svg_renderer import (
    enhanced_display_circuit,
    enhanced_export_circuit,
)

# Initialize Rich console
console = Console()

#######################################
# CORE UTILITY FUNCTIONS
#######################################


def print_colored(color: str, *args: str, end: str = "\n") -> None:
    """
    Enhanced colored text printing using Rich with backward compatibility.

    Args:
        color (str): The color code [o, r, g, v, b, y, c, w, m, k, d, u].
        args (str): The text to be printed.
        end (str): The end character.

    Returns:
        None
    """
    # Color mapping to Rich color names
    rich_colors = {
        "o": "orange1",  # Orange
        "r": "red",  # Red
        "g": "green",  # Green
        "v": "magenta",  # Violet/Magenta
        "b": "blue",  # Blue
        "y": "yellow",  # Yellow
        "c": "cyan",  # Cyan
        "w": "white",  # White
        "m": "magenta",  # Magenta
        "k": "black",  # Black
        "d": "dim",  # Dim
        "u": "underline",  # Underline
    }

    # Get the Rich color name
    rich_color = rich_colors.get(color, "white")

    # Join all arguments into a single string
    text_content = "".join(str(arg) for arg in args)

    # Handle special formatting
    if color == "d":  # Dim
        style = "dim white"
    elif color == "u":  # Underline
        style = "underline white"
    else:
        style = rich_color

    # Print with Rich formatting and reset
    console.print(text_content, style=style, end=end)


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


def format_bytes(num_bytes):
    """
    Convert bytes to a human-readable format using SI units.

    Args:
        num_bytes (int): The number of bytes.

    Returns:
        str: The human-readable format.
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024


#######################################
# ANIMATION AND LOADING FUNCTIONS
#######################################


def loading_animation(stop_event: threading.Event, title: str) -> None:
    """
    Enhanced loading animation using Rich spinner and live updates.
    """
    with Progress(
        SpinnerColumn("dots12", style="cyan"),
        TextColumn("[bold blue]Loading {task.description}..."),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(title, total=None)

        while not stop_event.is_set():
            time.sleep(0.1)

    # Show completion message
    console.print(f"[bold green]✅ Loading {title} completed![/bold green]")


def print_progress_summary(
    current: int, total: int, description: str = "Progress"
) -> None:
    """
    Print a progress summary with percentage and visual bar.

    Args:
        current (int): Current progress value.
        total (int): Total value.
        description (str): Description of the progress.
    """
    percentage = (current / total) * 100 if total > 0 else 0

    table = Table(show_header=False, box=box.SIMPLE)
    table.add_column("Description", style="bold white")
    table.add_column("Progress", style="bold cyan")
    table.add_column("Percentage", style="bold green")

    # Create visual progress bar
    bar_length = 20
    filled = int(bar_length * percentage / 100)
    bar = "█" * filled + "░" * (bar_length - filled)

    table.add_row(
        description,
        f"[cyan]{bar}[/cyan] {current}/{total}",
        f"{percentage:.1f}%",
    )

    console.print(table)


#######################################
# CIRCUIT VISUALIZATION FUNCTIONS
#######################################


def render_circuit(
    print_circuit: str,
    circuit: cirq.Circuit,
    qubits: "list[cirq.NamedQubit]",
    name: str = "bucket brigade",
) -> None:
    """
    Prints the circuit with enhanced Rich formatting and timing.

    Args:
        print_circuit (str): The print option ("Print", "Display", or "Export").
        circuit (cirq.Circuit): The circuit to be printed.
        qubits ('list[cirq.NamedQubit]'): The qubits of the circuit.
        name (str): The name of the circuit.
    """
    # Create action mapping with emojis
    action_info = {
        "Hide": {"emoji": "🔍", "action": "Hiding", "color": "orange1"},
        "Print": {"emoji": "🖨️", "action": "Printing", "color": "cyan"},
        "Display": {"emoji": "🖼️", "action": "Displaying", "color": "blue"},
        "Export": {"emoji": "💾", "action": "Exporting", "color": "green"},
    }

    if print_circuit not in action_info:
        console.print(
            f"[bold red]❌ Unknown print option: {print_circuit}[/bold red]"
        )
        return

    info = action_info[print_circuit]

    # Create header panel
    header = Panel(
        f"[bold {info['color']}]{info['emoji']}  {info['action']} Circuit: {name}[/bold {info['color']}]",
        border_style=info["color"],
        box=box.DOUBLE_EDGE,
    )
    console.print(header)

    start = time.time()

    if print_circuit == "Hide":
        # Hide the circuit by not printing anything
        console.print(
            f"[{info['color']}]Circuit {name} is hidden.[/{info['color']}]"
        )
        return

    elif print_circuit == "Print":
        # Print the circuit with Rich formatting
        console.print(f"[{info['color']}]Circuit Diagram:[/{info['color']}]")
        # Print the actual circuit (keeping original format)
        print(circuit.to_text_diagram(qubit_order=qubits))

    elif print_circuit == "Display":
        if "ToffoliDecompType" in name:
            console.print("[cyan]🔧 Using SVGCircuit display method...[/cyan]")
            svg_circuit = SVGCircuit(circuit)
            display(svg_circuit)
        else:
            console.print(
                "[cyan]🔧 Using enhanced SVG display method...[/cyan]"
            )
            # Use the enhanced renderer
            enhanced_display_circuit(circuit, qubits)

    elif print_circuit == "Export":
        console.print("[green]💾 Using enhanced export method...[/green]")
        # Use the enhanced renderer
        enhanced_export_circuit(circuit, qubits, name)
        # Early return for export to avoid timing display
        console.print("[bold green]✅ Circuit export completed![/bold green]")
        return

    # Calculate and display timing for Print and Display only
    stop_time = time.time()
    elapsed = stop_time - start

    # Format elapsed time
    if elapsed < 1:
        time_str = f"{elapsed*1000:.2f} ms"
        time_color = "green"
    elif elapsed < 10:
        time_str = f"{elapsed:.3f} s"
        time_color = "yellow"
    else:
        time_str = f"{elapsed:.2f} s"
        time_color = "red"

    # Create timing panel
    timing_panel = Panel(
        f"[white]⏱️  Time elapsed on {info['action'].lower()} the circuit: [/white]"
        f"[bold {time_color}]{time_str}[/bold {time_color}]",
        border_style="dim",
        box=box.SIMPLE,
    )
    console.print(timing_panel)


#######################################
# CONFIGURATION FUNCTION
#######################################


def print_qram_configuration(
    circuit_type: str,
    hpc: bool,
    simulate: bool,
    print_circuit: str,
    start_range_qubits: int,
    end_range_qubits: int,
    t_count: int = None,
    cvx_id: int = None,
    min_qram_size: int = None,
    t_cancel: int = None,
    specific_simulation: str = None,
    print_sim: str = None,
    shots: int = None,
) -> None:
    """
    Prints the QRAM circuit configuration with enhanced Rich formatting.

    Args:
        circuit_type (str): The type of circuit.
        hpc (bool): Whether to simulate on HPC.
        simulate (bool): Whether to simulate.
        print_circuit (str): Circuit display option.
        start_range_qubits (int): Start range of qubits.
        end_range_qubits (int): End range of qubits.
        t_count (int, optional): T count for QueryConfiguration.
        cvx_id (int, optional): CVX identifier for CV_CX configurations.
        min_qram_size (int, optional): Minimum QRAM size for hierarchical decomposition.
        t_cancel (int, optional): T cancel for combinations.
        specific_simulation (str, optional): Simulation type.
        print_sim (str, optional): Simulation display option.
        shots (int, optional): Number of shots for simulation.
    """
    # Create main title
    title = Text(
        "QRAM Circuit Configuration", style="bold yellow", justify="center"
    )
    main_panel = Panel(title, border_style="yellow", box=box.DOUBLE_EDGE)

    console.print(main_panel)

    circuit_type = (
        circuit_type
        if isinstance(circuit_type, str)
        else " + ".join(circuit_type)
    )
    length_circuit_type = max(15, len(circuit_type))

    # Create configuration table
    config_table = Table(
        show_header=True, header_style="bold white", box=box.ROUNDED
    )
    config_table.add_column("Parameter", style="bold cyan", width=35)
    config_table.add_column("Value", style="bold", width=length_circuit_type)
    config_table.add_column("Status", justify="center", width=10)

    # Add basic configuration rows
    config_table.add_row(
        "🔧 Circuit Type", f"[orange1]{circuit_type}[/orange1]", "⚙️"
    )

    hpc_status = "✅" if hpc else "❌"
    hpc_color = "green" if hpc else "red"
    config_table.add_row(
        "🖥️ Simulate on HPC",
        f"[{hpc_color}]{'Yes' if hpc else 'No'}[/{hpc_color}]",
        hpc_status,
    )

    sim_status = "✅" if simulate else "❌"
    sim_color = "green" if simulate else "red"
    config_table.add_row(
        "🔬 Simulate Decompositions",
        f"[{sim_color}]{'Yes' if simulate else 'No'}[/{sim_color}]",
        sim_status,
    )

    config_table.add_row(
        "🖼️ Circuit Display Option", f"[blue]{print_circuit}[/blue]", "🎨"
    )

    # Qubit range display
    if start_range_qubits == end_range_qubits:
        config_table.add_row(
            "🔢 QRAM Bits",
            f"[magenta]{start_range_qubits}[/magenta]",
            "🚀",
        )
    else:
        config_table.add_row(
            "🔢 Qubit Range",
            f"[magenta]{start_range_qubits} → {end_range_qubits}[/magenta]",
            "🏁",
        )

    # Add T count if provided
    if t_count is not None:
        t_depth = 3 if t_count == 4 else 4
        config_table.add_row(
            "🎯 Toffoli Config",
            f"[orange1]AN0_TD{t_depth}_TC{t_count}_CX6[/orange1]",
            "🔢",
        )

    # Add cvx_id index if provided
    if cvx_id is not None:
        config_table.add_row(
            "🔧 CV_CX Config",
            f"[cyan]CV_CX_QC5_{cvx_id}[/cyan]",
            "⚙️",
        )

    # Add minimum QRAM size if provided and valid
    if min_qram_size is not None and min_qram_size > 0:
        config_table.add_row(
            "📏 Min QRAM Size", f"[yellow]{min_qram_size}[/yellow]", "🏗️"
        )

    # Add T cancel if provided (for stress type)
    if t_cancel is not None:
        config_table.add_row(
            "🔄 T Cancel", f"[purple]{t_cancel}[/purple]", "♻️"
        )

    console.print(config_table)

    # Add simulation-specific configuration if applicable
    if simulate and specific_simulation and print_sim:
        sim_table = Table(
            title="🔬 Simulation Configuration",
            show_header=True,
            header_style="bold green",
            box=box.ROUNDED,
            title_style="bold green",
        )
        sim_table.add_column(
            "Simulation Parameter", style="bold cyan", width=35
        )
        sim_table.add_column("Value", style="bold", width=25)
        sim_table.add_column("Info", justify="center", width=10)

        sim_msg = (
            "Full Circuit" if specific_simulation == "full" else "QRAM Pattern"
        )
        sim_color = "green" if specific_simulation == "full" else "yellow"

        sim_table.add_row(
            "🎯 Simulation Type", f"[{sim_color}]{sim_msg}[/{sim_color}]", "🔍"
        )

        sim_table.add_row(
            "📊 Display Option", f"[blue]{print_sim}[/blue]", "📈"
        )

        if specific_simulation != "full" and shots:
            sim_table.add_row(
                "🎲 Shots per Simulation",
                f"[orange1]{shots:,}[/orange1]",
                "🔢",
            )

        console.print(sim_table)

    # Add summary
    total_qubits = end_range_qubits - start_range_qubits + 1
    summary_text = (
        f"[bold white]📊 Summary: [/bold white]"
        f"[cyan]{total_qubits} qubit{'s' if total_qubits != 1 else ''} configured[/cyan]"
    )

    if simulate:
        summary_text += f" [green]• Simulation enabled[/green]"
    if hpc:
        summary_text += f" [yellow]• HPC mode[/yellow]"

    summary_panel = Panel(summary_text, border_style="dim", box=box.SIMPLE)

    console.print(summary_panel)

    # Footer
    footer = Panel(
        "[dim]Configuration loaded successfully ✨[/dim]",
        border_style="dim",
        box=box.SIMPLE,
    )
    console.print(footer)


#######################################
# COMMON TABLE PRINTING FUNCTIONS
#######################################


def print_assessment_table(
    headers: list[str],
    data: list[list],
    title: str = "",
    title_style: str = "bold blue",
) -> None:
    """
    Print a formatted assessment table using Rich.

    Args:
        headers (list[str]): Table headers.
        data (list[list]): Table data rows.
        title (str): Optional table title.
        title_style (str): Style for the title.
    """
    if title:
        title_panel = Panel(
            Text(title, style=title_style, justify="center"),
            border_style="blue",
            box=box.ROUNDED,
        )
        console.print(title_panel)

    table = Table(
        show_header=True,
        header_style="bold white",
        box=box.ROUNDED,
        title_style="bold cyan",
    )

    # Add columns
    for header in headers:
        table.add_column(header, style="white", justify="left")

    # Add rows
    for row in data:
        table.add_row(*[str(cell) for cell in row])

    console.print(table)


def print_memory_usage(
    qram_bits: int, elapsed_time: str, rss: str, vms: str
) -> None:
    """
    Print memory usage information with Rich formatting.

    Args:
        qram_bits (int): Number of QRAM bits.
        elapsed_time (str): Time elapsed.
        rss (str): RSS memory usage.
        vms (str): VMS memory usage.
    """
    title = "🧠 QRAM Bucket Brigade Circuit Memory Usage"

    # Create memory info panel
    memory_info = (
        f"[cyan]• QRAM Bits:[/cyan] [bold white]{qram_bits}[/bold white]\n"
        f"[cyan]• Time Elapsed:[/cyan] [bold green]{elapsed_time}[/bold green]\n"
        f"[cyan]• RSS (Physical Memory):[/cyan] [bold yellow]{rss}[/bold yellow]\n"
        f"[cyan]• VMS (Virtual Memory):[/cyan] [bold yellow]{vms}[/bold yellow]"
    )

    panel = Panel(
        memory_info,
        title=f"[bold cyan]{title}[/bold cyan]",
        border_style="cyan",
        box=box.ROUNDED,
        padding=(1, 2),
    )

    console.print(panel)


def print_decomposition_scenario(
    circuit_type: str, decomp_scenario, circuit_name: str
) -> None:
    """
    Print decomposition scenario information with Rich formatting.

    Args:
        circuit_type (str): Type of circuit components.
        decomp_scenario: Decomposition scenario object.
        circuit_name (str): Name of the circuit.
    """
    title = f"🔧 Decomposition Scenario - {circuit_name.title()} Circuit"

    # Create decomposition info
    decomp_info = []

    # Check each component type and add to info
    if "fan_out" in circuit_type:
        decomp_info.append(
            f"[cyan]• Fan Out Decomp:[/cyan] [yellow]{decomp_scenario.dec_fan_out}[/yellow]"
        )
    if "write" in circuit_type:
        decomp_info.append(
            f"[cyan]• Write Decomp:[/cyan] [yellow]{decomp_scenario.dec_mem_write}[/yellow]"
        )
    if "query" in circuit_type:
        decomp_info.append(
            f"[cyan]• Query Decomp:[/cyan] [yellow]{decomp_scenario.dec_mem_query}[/yellow]"
        )
    if "fan_in" in circuit_type:
        decomp_info.append(
            f"[cyan]• Fan In Decomp:[/cyan] [yellow]{decomp_scenario.dec_fan_in}[/yellow]"
        )
    if "read" in circuit_type:
        decomp_info.append(
            f"[cyan]• Read Decomp:[/cyan] [yellow]{decomp_scenario.dec_mem_read}[/yellow]"
        )

    decomp_text = "\n".join(decomp_info)

    panel = Panel(
        decomp_text,
        title=f"[bold cyan]{title}[/bold cyan]",
        border_style="cyan",
        box=box.ROUNDED,
        padding=(1, 2),
    )

    console.print(panel)


def print_optimization_methods(decomp_scenario, circuit_name: str) -> None:
    """
    Print optimization methods with Rich formatting.

    Args:
        decomp_scenario: Decomposition scenario object.
        circuit_name (str): Name of the circuit.
    """
    title = f"⚡ Optimization Methods - {circuit_name.title()} Circuit"

    parallel_status = (
        "✅ YES" if decomp_scenario.parallel_toffolis else "❌ NO"
    )
    parallel_color = "green" if decomp_scenario.parallel_toffolis else "red"

    opt_info = (
        f"[cyan]• Parallel Toffolis:[/cyan] [{parallel_color}]{parallel_status}[/{parallel_color}]\n"
        f"[cyan]• Reverse Moments:[/cyan] [yellow]{decomp_scenario.reverse_moments}[/yellow]"
    )

    panel = Panel(
        opt_info,
        title=f"[bold magenta]{title}[/bold magenta]",
        border_style="magenta",
        box=box.ROUNDED,
        padding=(1, 2),
    )

    console.print(panel)


def print_stress_experiment_header(
    indices: tuple, rank: int = None, current: int = None, total: int = None
) -> None:
    """
    Print stress experiment header with Rich formatting.

    Args:
        indices (tuple): T gate indices.
        rank (int, optional): MPI rank.
        current (int, optional): Current experiment number.
        total (int, optional): Total experiments.
    """
    indices_str = " ".join(map(str, indices))

    if rank is not None:
        title = f"🧪 Stress Experiment - Rank {rank}"
        experiment_info = (
            f"[cyan]• Rank:[/cyan] [bold red]{rank}[/bold red]\n"
            f"[cyan]• Experiment:[/cyan] [bold red]{current}[/bold red] [yellow]of[/yellow] [bold red]{total}[/bold red]\n"
            f"[cyan]• T Gate Indices:[/cyan] [bold red]{indices_str}[/bold red]"
        )
    else:
        title = "🧪 Stress Experiment"
        experiment_info = f"[cyan]• T Gate Indices:[/cyan] [bold red]{indices_str}[/bold red]"

    panel = Panel(
        experiment_info,
        title=f"[bold yellow]{title}[/bold yellow]",
        border_style="yellow",
        box=box.ROUNDED,
        padding=(1, 2),
    )

    console.print(panel)


def print_stress_experiment_completion(
    indices: tuple,
    elapsed_time: str,
    rank: int = None,
    current: int = None,
    total: int = None,
) -> None:
    """
    Print stress experiment completion with Rich formatting.

    Args:
        indices (tuple): T gate indices.
        elapsed_time (str): Time elapsed.
        rank (int, optional): MPI rank.
        current (int, optional): Current experiment number.
        total (int, optional): Total experiments.
    """
    indices_str = " ".join(map(str, indices))

    if rank is not None:
        title = f"✅ Completed - Rank {rank}"
        completion_info = (
            f"[cyan]• Rank:[/cyan] [bold red]{rank}[/bold red]\n"
            f"[cyan]• Experiment:[/cyan] [bold red]{current}[/bold red] [green]of[/green] [bold red]{total}[/bold red]\n"
            f"[cyan]• T Gate Indices:[/cyan] [bold red]{indices_str}[/bold red]\n"
            f"[cyan]• Time Elapsed:[/cyan] [bold green]{elapsed_time}[/bold green]"
        )
    else:
        title = "✅ Experiment Completed"
        completion_info = (
            f"[cyan]• T Gate Indices:[/cyan] [bold red]{indices_str}[/bold red]\n"
            f"[cyan]• Time Elapsed:[/cyan] [bold green]{elapsed_time}[/bold green]"
        )

    panel = Panel(
        completion_info,
        title=f"[bold green]{title}[/bold green]",
        border_style="green",
        box=box.ROUNDED,
        padding=(1, 2),
    )

    console.print(panel)


def display_simulation_results(
    fail,
    success_measurements,
    success_fidelity,
    success_vector,
    f_pct,
    sm_pct,
    sf_pct,
    sv_pct,
    ts_pct,
    stop_time,
):
    """Display results using Rich library for enhanced visualization"""

    # Clear and create title
    print("\n")
    title = Text("🔬 Circuit Simulation Results", style="bold magenta")
    console.print(
        Panel(title, box=box.DOUBLE_EDGE, border_style="bright_blue")
    )

    # Add timing information if provided (keeping original style)
    if stop_time:
        timing_panel = Panel(
            f"[white]⏱️  Time elapsed on simulation and comparison: [/white]"
            f"[bold green]{stop_time}[/bold green]",
            border_style="dim",
            box=box.SIMPLE,
        )
        console.print(timing_panel)

    # Create main results table
    table = Table(show_header=True, header_style="bold white", box=box.ROUNDED)
    table.add_column("Status", style="bold", width=15)
    table.add_column("Count", justify="center", width=8)
    table.add_column("Percentage", justify="center", width=12)
    table.add_column("Performance", width=25)

    # Progress bar helper
    def create_bar(percentage, color):
        bar_length = 15
        filled = int(bar_length * percentage // 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        return f"[{color}]{bar}[/{color}] {percentage:.1f}%"

    # Add rows
    table.add_row(
        "[bold red]❌ Failed[/bold red]",
        f"[red]{fail}[/red]",
        f"[red]{f_pct:.2f}%[/red]",
        create_bar(f_pct, "red"),
    )

    total_success = success_measurements + success_fidelity + success_vector
    table.add_row(
        "[bold green]✅ Succeed[/bold green]",
        f"[green]{total_success}[/green]",
        f"[green]{ts_pct:.2f}%[/green]",
        create_bar(ts_pct, "green"),
    )

    console.print(table)

    # Success breakdown table
    sub_table = Table(
        title="📊 Success Breakdown",
        show_header=True,
        header_style="bold cyan",
        box=box.ROUNDED,
        title_style="bold cyan",
    )
    sub_table.add_column("Type", style="bold", width=18)
    sub_table.add_column("Count", justify="center", width=8)
    sub_table.add_column("Percentage", justify="center", width=12)
    sub_table.add_column("Performance", width=25)
    sub_table.add_column("Level of Accuracy", width=20)

    # Add breakdown rows
    sub_table.add_row(
        "[bold magenta]🚀 Output Vector[/bold magenta]",
        f"[magenta]{success_vector}[/magenta]",
        f"[magenta]{sv_pct:.2f}%[/magenta]",
        create_bar(sv_pct, "magenta"),
        "[bold magenta]🔺 Highest[/bold magenta]",
    )

    sub_table.add_row(
        "[bold blue]🎯 Fidelity[/bold blue]",
        f"[blue]{success_fidelity}[/blue]",
        f"[blue]{sf_pct:.2f}%[/blue]",
        create_bar(sf_pct, "blue"),
        "[blue]🔸 Medium[/blue]",
    )

    sub_table.add_row(
        "[bold orange1]📊 Measurements[/bold orange1]",
        f"[orange1]{success_measurements}[/orange1]",
        f"[orange1]{sm_pct:.2f}%[/orange1]",
        create_bar(sm_pct, "orange1"),
        "[orange1]🔻 Lowest[/orange1]",
    )

    console.print(sub_table)

    # Quick performance insight
    if sv_pct >= 50:
        insight = (
            "[bold green]🎉 Excellent Output Vector performance![/bold green]"
        )
    elif sv_pct >= 30:
        insight = "[yellow]👍 Good Output Vector performance, room for improvement[/yellow]"
    else:
        insight = "[red]🔧 Output Vector needs optimization[/red]"

    console.print(
        Panel(insight, title="💡 Quick Insight", border_style="yellow")
    )


#######################################
# RANGE AND MESSAGE FUNCTIONS
#######################################


def print_message(message: str) -> None:
    """
    Prints a formatted message using Rich styling.

    Args:
        message (str): The message to print.
    """
    formatted_panel = Panel(
        Text(message, style="bold white", justify="center"),
        border_style="cyan",
        box=box.DOUBLE_EDGE,
        padding=(1, 2),
    )
    console.print(formatted_panel)
    console.print("", style="white", end="")  # Reset color


def print_simulation_range(sim_range: "list[int]", step: int) -> None:
    """
    Print the range of simulation from an actual list in a visually appealing way with Rich formatting.

    Args:
        sim_range: List of simulation indices
        step: Step size between tests. If 0, shows all cases with binary representation
    """
    console.print()

    # Create title
    title = Text("🔢 Simulation Range Configuration", style="bold yellow")
    console.print(Panel(title, border_style="yellow"))
    console.print("", style="white", end="")  # Reset color

    if step == 0:
        # New mode: Show all cases with binary representation
        total_cases = len(sim_range)

        # Calculate the number of bits needed for binary representation
        max_value = max(sim_range) if sim_range else 0
        bits_needed = max_value.bit_length()

        # Create table for all simulation cases
        table = Table(
            title="📋 All Simulation Cases with Binary Representation",
            show_header=True,
            header_style="bold cyan",
            box=box.ROUNDED,
            title_style="bold green",
        )
        table.add_column(
            "Case #", style="bold white", justify="center", width=8
        )
        table.add_column(
            "Index",
            style="bold magenta",
            justify="center",
            width=len(str(max_value)) + 4,
        )
        table.add_column(
            "Binary",
            style="bold blue",
            justify="center",
            width=bits_needed + 2,
        )
        table.add_column(
            "Hex",
            style="bold green",
            justify="center",
            width=len(f"0x{max_value:X}") + 2,
        )
        table.add_column("Pattern", style="dim", width=bits_needed + 2)

        # Add rows for each simulation case
        for i, index in enumerate(sim_range, 1):
            binary_repr = format(index, f"0{bits_needed}b")
            hex_repr = f"0x{index:X}"

            # Create a visual pattern representation
            pattern = binary_repr.replace("0", "░").replace("1", "█")

            table.add_row(
                f"{i}",
                f"{index:,}",
                binary_repr,
                hex_repr,
                f"[cyan]{pattern}[/cyan]",
            )

        console.print(table)

        # Add summary for binary mode
        summary_info = (
            f"[bold white]📊 Binary Analysis:[/bold white]\n"
            f"[cyan]• Total Cases:[/cyan] [bold yellow]{total_cases:,}[/bold yellow]\n"
            f"[cyan]• Qubits Required:[/cyan] [bold yellow]{bits_needed}[/bold yellow]\n"
            f"[cyan]• Range:[/cyan] [bold yellow]{min(sim_range):,} - {max(sim_range):,}[/bold yellow]\n"
            f"[cyan]• Pattern:[/cyan] [dim]█ = 1, ░ = 0[/dim]"
        )

        summary_panel = Panel(
            summary_info,
            title="[bold]🔍 Binary Summary",
            border_style="blue",
            box=box.ROUNDED,
        )
        console.print(summary_panel)

    else:
        # Existing mode: Show start, stop, step
        start = sim_range[0] if sim_range else 0
        stop = sim_range[-1] + step if sim_range else step

        # Create table for range parameters
        table = Table(
            show_header=True, header_style="bold cyan", box=box.ROUNDED
        )
        table.add_column("Parameter", style="bold white", width=15)
        table.add_column(
            "Value",
            style="bold red",
            justify="center",
            width=len(str(stop)) + 10,
        )
        table.add_column("Description", style="dim", width=30)

        table.add_row("🚀 Start", f"{start:,}", "Initial simulation index")
        table.add_row(
            "🏁 Stop", f"{sim_range[-1]:,}", "Final simulation index"
        )
        table.add_row("📏 Step", f"{step:,}", "Increment between tests")

        console.print(table)

        # Add range summary for step mode
        total_tests = len(sim_range)
        summary = Text(f"📊 Total Tests: {total_tests:,}", style="bold green")
        console.print(Panel(summary, border_style="green"))

    console.print("", style="white", end="")  # Reset color
    console.print()


#######################################
# ASSESSMENT FUNCTIONS
#######################################


def print_assessment_main_title() -> None:
    """Print the main assessment title."""
    main_title = Panel(
        Text(
            "📊 QRAM Circuit Assessment Results",
            style="bold yellow",
            justify="center",
        ),
        border_style="yellow",
        box=box.DOUBLE_EDGE,
    )
    console.print()
    console.print(main_title)
    console.print("", style="white", end="")  # Reset color
    console.print()


def print_circuit_creation_assessment(
    data_modded: dict, start_range: int, end_range: int
) -> None:
    """Print circuit creation assessment table."""
    creation_headers = [
        "QRAM Bits",
        "Elapsed Time",
        "RSS (Memory Usage)",
        "VMS (Memory Usage)",
    ]
    creation_data = []

    for x in range(start_range, end_range + 1):
        # Check if we have sub-circuits depth data
        if len(data_modded[x]) > 9:  # Has sub-circuits depth
            creation_data.append(
                [
                    data_modded[x][0],
                    data_modded[x][7],  # Elapsed time
                    data_modded[x][8],  # RSS
                    data_modded[x][9],  # VMS
                ]
            )
        else:  # No sub-circuits depth
            creation_data.append(
                [
                    data_modded[x][0],
                    data_modded[x][6],  # Elapsed time
                    data_modded[x][7],  # RSS
                    data_modded[x][8],  # VMS
                ]
            )

    print_assessment_table(
        creation_headers,
        creation_data,
        "🏗️ Bucket Brigade Circuit Creation",
        "bold blue",
    )


def print_reference_circuit_assessment(
    data: dict, start_range: int, end_range: int
) -> None:
    """Print reference circuit assessment table."""
    # Check if we have sub-circuits depth in reference data
    sample_data = list(data.values())[0]
    has_sub_circuits_depth = len(sample_data) > 6

    if has_sub_circuits_depth:
        ref_headers = [
            "QRAM Bits",
            "Number of Qubits",
            "Depth of Circuit",
            "Sub-Circuits Depth",
            "T Depth",
            "T Count",
            "Hadamard Count",
        ]
    else:
        ref_headers = [
            "QRAM Bits",
            "Number of Qubits",
            "Depth of Circuit",
            "T Depth",
            "T Count",
            "Hadamard Count",
        ]

    ref_data = []

    for x in range(start_range, end_range + 1):
        if has_sub_circuits_depth:
            ref_data.append(
                [
                    data[x][0],
                    data[x][1],
                    data[x][2],
                    data[x][3],
                    data[x][4],
                    data[x][5],
                    data[x][6],
                ]
            )
        else:
            ref_data.append(
                [
                    data[x][0],
                    data[x][1],
                    data[x][2],
                    data[x][3],
                    data[x][4],
                    data[x][5],
                ]
            )

    print_assessment_table(
        ref_headers,
        ref_data,
        "🔍 Reference Circuit Assessment",
        "bold cyan",
    )


def print_modded_circuit_assessment(
    data_modded: dict, start_range: int, end_range: int
) -> None:
    """Print modded circuit assessment table."""
    # Check if we have sub-circuits depth in modded data
    sample_modded_data = list(data_modded.values())[0]
    has_sub_circuits_depth_modded = len(sample_modded_data) > 9

    if has_sub_circuits_depth_modded:
        modded_headers = [
            "QRAM Bits",
            "Number of Qubits",
            "Depth of Circuit",
            "Sub-Circuits Depth",
            "T Depth",
            "T Count",
            "Hadamard Count",
        ]
    else:
        modded_headers = [
            "QRAM Bits",
            "Number of Qubits",
            "Depth of Circuit",
            "T Depth",
            "T Count",
            "Hadamard Count",
        ]

    modded_data = []

    for x in range(start_range, end_range + 1):
        if has_sub_circuits_depth_modded:
            modded_data.append(
                [
                    data_modded[x][0],
                    data_modded[x][1],
                    data_modded[x][2],
                    data_modded[x][3],
                    data_modded[x][4],
                    data_modded[x][5],
                    data_modded[x][6],
                ]
            )
        else:
            modded_data.append(
                [
                    data_modded[x][0],
                    data_modded[x][1],
                    data_modded[x][2],
                    data_modded[x][3],
                    data_modded[x][4],
                    data_modded[x][5],
                ]
            )

    print_assessment_table(
        modded_headers,
        modded_data,
        "🔧 Modded Circuit Assessment",
        "bold magenta",
    )


def print_depth_analysis(
    data_modded: dict,
    data: dict,
    start_range: int,
    end_range: int,
    has_reference: bool,
) -> None:
    """Print depth analysis comparing sub-circuits depth vs circuit depth."""
    # Check if we have sub-circuits depth data
    sample_modded_data = list(data_modded.values())[0]
    has_sub_circuits_depth_modded = len(sample_modded_data) > 9

    if not has_sub_circuits_depth_modded:
        return  # No sub-circuits depth data available

    # Depth analysis title
    depth_analysis_title = Panel(
        Text(
            "🔀 Circuit Depth vs Sub-Circuits Depth Analysis",
            style="bold cyan",
            justify="center",
        ),
        border_style="cyan",
        box=box.ROUNDED,
    )
    console.print(depth_analysis_title)
    console.print("", style="white", end="")  # Reset color
    console.print()

    # Modded circuit depth comparison
    modded_depth_headers = [
        "QRAM Bits",
        "Circuit Depth (len)",
        "Sub-Circuits Depth (count)",
        "Difference",
        "Efficiency Ratio",
        "Status",
    ]
    modded_depth_data = []

    for x in range(start_range, end_range + 1):
        circuit_depth = data_modded[x][2]  # len() depth
        sub_circuits_depth = data_modded[x][3]  # count_circuit_depth()
        difference = sub_circuits_depth - circuit_depth
        efficiency_ratio = (
            sub_circuits_depth / circuit_depth if circuit_depth > 0 else 0
        )

        # Simple status without judgment
        if difference == 0:
            status = "🟢 Equal"
        elif difference > 0:
            status = f"🔵 +{difference}"
        else:
            status = f"🟡 {difference}"

        modded_depth_data.append(
            [
                x,
                circuit_depth,
                sub_circuits_depth,
                difference,
                f"{efficiency_ratio:.2f}x",
                status,
            ]
        )

    print_assessment_table(
        modded_depth_headers,
        modded_depth_data,
        "🔧 Modded Circuit - Depth Comparison",
        "bold magenta",
    )

    # Reference circuit depth comparison (if available)
    if has_reference and data:
        sample_ref_data = list(data.values())[0]
        has_sub_circuits_depth_ref = len(sample_ref_data) > 6

        if has_sub_circuits_depth_ref:
            ref_depth_headers = [
                "QRAM Bits",
                "Circuit Depth (len)",
                "Sub-Circuits Depth (count)",
                "Difference",
                "Efficiency Ratio",
                "Status",
            ]
            ref_depth_data = []

            for x in range(start_range, end_range + 1):
                circuit_depth = data[x][2]  # len() depth
                sub_circuits_depth = data[x][3]  # count_circuit_depth()
                difference = sub_circuits_depth - circuit_depth
                efficiency_ratio = (
                    sub_circuits_depth / circuit_depth
                    if circuit_depth > 0
                    else 0
                )

                # Simple status without judgment
                if difference == 0:
                    status = "🟢 Equal"
                elif difference > 0:
                    status = f"🔵 +{difference}"
                else:
                    status = f"🟡 {difference}"

                ref_depth_data.append(
                    [
                        x,
                        circuit_depth,
                        sub_circuits_depth,
                        difference,
                        f"{efficiency_ratio:.2f}x",
                        status,
                    ]
                )

            print_assessment_table(
                ref_depth_headers,
                ref_depth_data,
                "🔍 Reference Circuit - Depth Comparison",
                "bold cyan",
            )

    # Simple insights without judgment about sub-circuits behavior
    print_depth_insights(
        data_modded, start_range, end_range, has_sub_circuits_depth_modded
    )


def print_depth_insights(
    data_modded: dict,
    start_range: int,
    end_range: int,
    has_sub_circuits_depth: bool,
) -> None:
    """Print simple insights about depth analysis without judging sub-circuits behavior."""
    if not has_sub_circuits_depth:
        return

    insights = []

    # Simple statistical analysis
    total_equal = 0
    total_higher = 0
    total_lower = 0
    max_difference = 0
    min_efficiency = float("inf")
    max_efficiency = 0

    for x in range(start_range, end_range + 1):
        circuit_depth = data_modded[x][2]
        sub_circuits_depth = data_modded[x][3]
        difference = sub_circuits_depth - circuit_depth
        efficiency = (
            sub_circuits_depth / circuit_depth if circuit_depth > 0 else 0
        )

        if difference == 0:
            total_equal += 1
        elif difference > 0:
            total_higher += 1
            max_difference = max(max_difference, difference)
        else:
            total_lower += 1

        min_efficiency = min(min_efficiency, efficiency)
        max_efficiency = max(max_efficiency, efficiency)

    # Generate simple insights
    if total_equal > 0:
        insights.append(f"🟢 {total_equal} circuit(s) have equal depths")
    if total_higher > 0:
        insights.append(
            f"🔵 {total_higher} circuit(s) have different sub-circuits depth (max: +{max_difference})"
        )
    if total_lower > 0:
        insights.append(
            f"🟡 {total_lower} circuit(s) show variation in depth calculation"
        )

    insights.append(
        f"📊 Efficiency range: {min_efficiency:.2f}x - {max_efficiency:.2f}x"
    )
    insights.append(
        f"💡 Sub-circuits behave differently than simple length calculation"
    )

    if insights:
        insights_text = "\n".join([f"• {insight}" for insight in insights])
        insights_panel = Panel(
            f"[white]{insights_text}[/white]",
            title="[bold]💡 Depth Analysis Summary",
            border_style="yellow",
            box=box.ROUNDED,
        )
        console.print(insights_panel)
        console.print("", style="white", end="")  # Reset color
        console.print()


def print_reference_modded_comparison(
    data: dict, data_modded: dict, start_range: int, end_range: int
) -> None:
    """Print comparison between reference and modded circuits."""

    def calculate(i: int, j: int) -> "tuple[str, str]":
        modded_percent = (data_modded[i][j] / data[i][j]) * 100
        modded_percent_str = format(modded_percent, ",.2f")
        modded = str(data_modded[i][j]) + f"  ( {modded_percent_str}% )"

        cancelled_percent = 100.0 - modded_percent
        cancelled_percent_str = format(cancelled_percent, ",.2f")
        cancelled = (
            str(data[i][j] - data_modded[i][j])
            + f"  ( {cancelled_percent_str}% )"
        )

        return modded, cancelled

    # Comparison title
    comparison_title = Panel(
        Text(
            "📈 Reference vs Modded Circuit Comparison",
            style="bold green",
            justify="center",
        ),
        border_style="green",
        box=box.ROUNDED,
    )
    console.print(comparison_title)
    console.print("", style="white", end="")  # Reset color
    console.print()

    # Determine index offsets based on sub-circuits depth presence
    sample_data = list(data.values())[0]
    has_sub_circuits_depth = len(sample_data) > 6

    # Adjust indices based on whether sub-circuits depth is present
    if has_sub_circuits_depth:
        t_count_index = 5
        t_depth_index = 4
        circuit_depth_index = 2
        sub_circuits_depth_index = 3
    else:
        t_count_index = 4
        t_depth_index = 3
        circuit_depth_index = 2
        sub_circuits_depth_index = None

    # T count comparison
    t_count_headers = [
        "QRAM Bits",
        "T Count Reference",
        "T Count Modded (%)",
        "T Count Improvement (%)",
    ]
    t_count_data = []

    for i in range(start_range, end_range + 1):
        modded, improvement = calculate(i, t_count_index)
        t_count_data.append(
            [data[i][0], data[i][t_count_index], modded, improvement]
        )

    print_assessment_table(
        t_count_headers,
        t_count_data,
        "🎯 T Count Comparison",
        "bold red",
    )

    # T depth comparison
    t_depth_headers = [
        "QRAM Bits",
        "T Depth Reference",
        "T Depth Modded (%)",
        "T Depth Improvement (%)",
    ]
    t_depth_data = []

    for i in range(start_range, end_range + 1):
        modded, improvement = calculate(i, t_depth_index)
        t_depth_data.append(
            [data[i][0], data[i][t_depth_index], modded, improvement]
        )

    print_assessment_table(
        t_depth_headers,
        t_depth_data,
        "📏 T Depth Comparison",
        "bold orange1",
    )

    # Circuit depth comparison
    depth_headers = [
        "QRAM Bits",
        "Depth Reference",
        "Depth Modded (%)",
        "Depth Improvement (%)",
    ]
    depth_data = []

    for i in range(start_range, end_range + 1):
        modded, improvement = calculate(i, circuit_depth_index)
        depth_data.append(
            [data[i][0], data[i][circuit_depth_index], modded, improvement]
        )

    print_assessment_table(
        depth_headers,
        depth_data,
        "🔧 Circuit Depth Comparison",
        "bold purple",
    )

    # Sub-Circuits depth comparison (if applicable)
    if has_sub_circuits_depth and sub_circuits_depth_index is not None:
        sub_depth_headers = [
            "QRAM Bits",
            "Sub-Circuits Depth Reference",
            "Sub-Circuits Depth Modded (%)",
            "Sub-Circuits Depth Improvement (%)",
        ]
        sub_depth_data = []

        for i in range(start_range, end_range + 1):
            modded, improvement = calculate(i, sub_circuits_depth_index)
            sub_depth_data.append(
                [
                    data[i][0],
                    data[i][sub_circuits_depth_index],
                    modded,
                    improvement,
                ]
            )

        print_assessment_table(
            sub_depth_headers,
            sub_depth_data,
            "🔀 Sub-Circuits Depth Comparison",
            "bold blue",
        )


def print_assessment_summary() -> None:
    """Print final assessment summary."""
    summary_panel = Panel(
        "[bold green]✅ Assessment completed successfully![/bold green]\n"
        "[dim]All circuit metrics have been analyzed and compared.[/dim]",
        title="[bold]📋 Assessment Summary",
        border_style="green",
        box=box.ROUNDED,
    )
    console.print(summary_panel)
    console.print("", style="white", end="")  # Reset color
    console.print()
