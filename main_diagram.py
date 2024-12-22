from graphviz import Digraph

# Constants for module colors
COLOR_MODULE_CLASSES_INHERITANCE = 'dodgerblue'
COLOR_MODULE_CLASSES_INHERITANCE_COMPOSITION = 'darkblue'
COLOR_MODULE_CLASSES_COMPOSITION = 'darkorange'
COLOR_MODULE_CLASSES_OPTIMIZATION = 'gold'
COLOR_MODULE_MAIN = 'darkgreen'
COLOR_MODULE_UTILS = 'red'

# Constants for relation types
COLOR_RELATIONS = {
    'Inheritance': {'color': 'cyan', 'style': 'solid'},
    'Composition': {'color': 'orange', 'style': 'dashed'},
    'Optimization': {'color': 'yellow', 'style': 'dotted'},
    'Execution': {'color': 'lime', 'style': 'bold'},
    'Utils': {'color': 'lightcoral', 'style': 'dotted'}
}

# Module definitions with descriptions and colors
MODULES = {
    # Class Inheritance
    'qram/circuit/core.py\nQRAMCircuitCore Class': {
        'description': 'Constructs QRAM Circuits',
        'color': COLOR_MODULE_CLASSES_INHERITANCE,
        'type': 'Class Inheritance'
    },
    'qram/circuit/stress.py\nQRAMCircuitStress Class': {
        'description': 'Performs stress testing on QRAM Circuits',
        'color': COLOR_MODULE_CLASSES_INHERITANCE,
        'type': 'Class Inheritance'
    },
    'qram/circuit/experiments.py\nQRAMCircuitExperiments Class': {
        'description': 'Handles experiments for QRAM Circuits',
        'color': COLOR_MODULE_CLASSES_INHERITANCE,
        'type': 'Class Inheritance'
    },
    'qram/circuit/bilan.py\nQRAMCircuitBilan Class': {
        'description': 'Generates bilan reports for QRAM Circuits',
        'color': COLOR_MODULE_CLASSES_INHERITANCE,
        'type': 'Class Inheritance'
    },

    # Class Inheritance Composition
    'qram/simulator/base.py\nQRAMSimulatorBase Class': {
        'description': 'Base class for QRAM Simulators',
        'color': COLOR_MODULE_CLASSES_INHERITANCE_COMPOSITION,
        'type': 'Class Inheritance Composition'
    },
    'qram/simulator/decomposition.py\nQRAMSimulatorDecompositions Class': {
        'description': 'Simulates Toffoli decompositions',
        'color': COLOR_MODULE_CLASSES_INHERITANCE_COMPOSITION,
        'type': 'Class Inheritance Composition'
    },
    'qram/simulator/circuit_core.py\nQRAMSimulatorCircuitCore Class': {
        'description': 'Core class for QRAM Circuit Simulators',
        'color': COLOR_MODULE_CLASSES_INHERITANCE_COMPOSITION,
        'type': 'Class Inheritance Composition'
    },
    'qram/simulator/circuit_hpc.py\nQRAMSimulationCircuitHPC Class': {
        'description': 'Simulates QRAM Circuit on HPC',
        'color': COLOR_MODULE_CLASSES_INHERITANCE_COMPOSITION,
        'type': 'Class Inheritance Composition'
    },
    'qram/simulator/circuit_parallel.py\nQRAMSimulatorCircuitParallel Class': {
        'description': 'Simulates QRAM Circuit in parallel',
        'color': COLOR_MODULE_CLASSES_INHERITANCE_COMPOSITION,
        'type': 'Class Inheritance Composition'
    },
    'qram/simulator/circuit_sequential.py\nQRAMSimulatorCircuitSequential Class': {
        'description': 'Simulates QRAM Circuit sequentially',
        'color': COLOR_MODULE_CLASSES_INHERITANCE_COMPOSITION,
        'type': 'Class Inheritance Composition'
    },

    # Class Composition
    'qram/circuit/simulator_manager.py\nQRAMCircuitSimulatorManager Class': {
        'description': 'Simulates QRAM Circuits',
        'color': COLOR_MODULE_CLASSES_COMPOSITION,
        'type': 'Class Composition'
    },
    'qramcircuits/bucket_brigade.py\nBucketBrigade Class': {
        'description': 'Creates Bucket Brigade for QRAM Circuit',
        'color': COLOR_MODULE_CLASSES_COMPOSITION,
        'type': 'Class Composition'
    },

    # Class Optimization
    'optimizers/transforme_ngh_gates.py\nTransformeNghGates Class': {
        'description': "Transforms (T and T) or (T^-1 and T^-1) or (S and S) or (S^-1 and S^-1)\ngates that are neighbor horizontally on series qubits",
        'color': COLOR_MODULE_CLASSES_OPTIMIZATION,
        'type': 'Class Optimization'
    },
    'optimizers/cancel_ngh_clifford_t_gates.py\nCancelNGHCliffordTGates Class': {
        'description': "Cancels (H and H) or (T and T^-1) or (S and S^-1) or (Z and Z)\ngates that are neighbor horizontally on series qubits",
        'color': COLOR_MODULE_CLASSES_OPTIMIZATION,
        'type': 'Class Optimization'
    },
    'optimizers/cancel_ngh_cnots.py\nCancelNghCNOTs Class': {
        'description': "Cancels two neighbouring CNOTs",
        'color': COLOR_MODULE_CLASSES_OPTIMIZATION,
        'type': 'Class Optimization'
    },
    'optimizers/commute_t_to_start.py\nCommuteTGatesToStart Class': {
        'description': "Commutes T gates to the start of the circuit",
        'color': COLOR_MODULE_CLASSES_OPTIMIZATION,
        'type': 'Class Optimization'
    },
    'optimizers/parallelize_cnots.py\nParallelizeCNOTs Class': {
        'description': "Parallelizes CNOTs",
        'color': COLOR_MODULE_CLASSES_OPTIMIZATION,
        'type': 'Class Optimization'
    },
    'optimizers/cancel_t_gates.py\nCancelTGates Class': {
        'description': "Cancel T gates in a circuit",
        'color': COLOR_MODULE_CLASSES_OPTIMIZATION,
        'type': 'Class Optimization'
    },

    # Main Executions
    'main_experiments.py\nMainExperiments': {
        'description': 'Executes QRAMCircuitExperiments',
        'color': COLOR_MODULE_MAIN,
        'type': 'Main'
    },
    'main_bilan.py\nMainBilan': {
        'description': 'Executes QRAMCircuitBilan',
        'color': COLOR_MODULE_MAIN,
        'type': 'Main'
    },
    'main_stress.py\nMainStress': {
        'description': 'Executes QRAMCircuitStress',
        'color': COLOR_MODULE_MAIN,
        'type': 'Main'
    },

    # Utils
    'utils/arg_parser.py': {
        'description': 'Parses command line arguments',
        'color': COLOR_MODULE_UTILS,
        'type': 'Utils'
    },
    'utils/print_utils.py': {
        'description': 'Prints formatted outputs',
        'color': COLOR_MODULE_UTILS,
        'type': 'Utils'
    }
}

def add_cluster(graph, cluster_name, label, color, fontcolor, module_type):
    """
    Adds a clustered subgraph to the main graph.

    Args:
        graph (Digraph): The main graph object.
        cluster_name (str): Unique name for the cluster.
        label (str): Label for the cluster.
        color (str): Fill color for the cluster.
        fontcolor (str): Font color for the cluster label.
        module_type (str): Type of modules to include in the cluster.
    """
    with graph.subgraph(name=f'cluster_{cluster_name}') as sub:
        sub.attr(style='filled', color=color, label=label, fontcolor=fontcolor, fontsize='25', margin='15')
        for module, attrs in MODULES.items():
            if attrs['type'] == module_type:
                sub.node(
                    module,
                    f"{module}\n{attrs['description']}",
                    style='filled',
                    fillcolor=attrs['color'],
                    fontcolor='white' if attrs['color'] not in ['red', 'gold'] else 'black',
                    shape='box',
                    fontsize='17'
                )

def create_diagram(engine='twopi', fmt='pdf', output_name='main_diagram'):
    """
    Creates and renders the QRAM Circuit Module Dependencies Diagram.

    Args:
        engine (str): Graphviz layout engine to use.
        fmt (str): Output format (e.g., 'pdf', 'png').
        output_name (str): Base name for the output file.
    """
    # Initialize the graph with a black background and A4 size
    dot = Digraph(
        comment='QRAM Circuit Module Dependencies Diagram',
        format=fmt,
        engine=engine
    )
    dot.attr(
        rankdir='LR',
        splines='ortho',
        bgcolor='black',
        fontcolor='white',
        color='black',
        style='rounded',
        shape='box',
        size='8.27,11.69',   # A4 size in inches
        ratio='auto',        # Changed from 'fill' to 'auto' to maintain aspect ratio
        margin='0',
        square='False',      # Changed from 'True' to 'False'
        overlap='false',     # Prevent overlapping of nodes
        nodesep='1.0',       # Increased separation between nodes
        ranksep='1.5',       # Increased separation between ranks
    )

    # Add clustered subgraphs for better organization
    add_cluster(dot, 'classes_inheritance', 'Classes Inheritance', 'gray30', 'white', 'Class Inheritance')
    add_cluster(dot, 'classes_inheritance_composition', 'Classes Inheritance Composition', 'gray40', 'white', 'Class Inheritance Composition')
    add_cluster(dot, 'classes_composition', 'Classes Composition', 'gray50', 'white', 'Class Composition')
    add_cluster(dot, 'classes_optimization', 'Classes Optimization', 'gray70', 'black', 'Class Optimization')
    add_cluster(dot, 'utils', 'Utils', 'gray90', 'black', 'Utils')
    add_cluster(dot, 'main_executions', 'Main Executions', 'gray10', 'white', 'Main')

    # Define dependencies with relation types
    dependencies = [
        # Class Inheritance
        ("qram/circuit/experiments.py\nQRAMCircuitExperiments Class",
         "qram/circuit/core.py\nQRAMCircuitCore Class", 'Inheritance'),
        ("qram/circuit/bilan.py\nQRAMCircuitBilan Class",
         "qram/circuit/core.py\nQRAMCircuitCore Class", 'Inheritance'),
        ("qram/circuit/stress.py\nQRAMCircuitStress Class",
         "qram/circuit/experiments.py\nQRAMCircuitExperiments Class", 'Inheritance'),

        # Class Inheritance Composition
        ("qram/simulator/decomposition.py\nQRAMSimulatorDecompositions Class",
         "qram/simulator/base.py\nQRAMSimulatorBase Class", 'Inheritance'),
        ("qram/simulator/circuit_core.py\nQRAMSimulatorCircuitCore Class",
         "qram/simulator/base.py\nQRAMSimulatorBase Class", 'Inheritance'),
        ("qram/simulator/circuit_hpc.py\nQRAMSimulationCircuitHPC Class",
         "qram/simulator/circuit_core.py\nQRAMSimulatorCircuitCore Class", 'Inheritance'),
        ("qram/simulator/circuit_parallel.py\nQRAMSimulatorCircuitParallel Class",
         "qram/simulator/circuit_core.py\nQRAMSimulatorCircuitCore Class", 'Inheritance'),
        ("qram/simulator/circuit_sequential.py\nQRAMSimulatorCircuitSequential Class",
         "qram/simulator/circuit_core.py\nQRAMSimulatorCircuitCore Class", 'Inheritance'),

        # Class Composition
        ("qram/simulator/decomposition.py\nQRAMSimulatorDecompositions Class",
         "qram/circuit/simulator_manager.py\nQRAMCircuitSimulatorManager Class", 'Composition'),
        ("qram/simulator/circuit_hpc.py\nQRAMSimulationCircuitHPC Class",
         "qram/circuit/simulator_manager.py\nQRAMCircuitSimulatorManager Class", 'Composition'),
        ("qram/simulator/circuit_parallel.py\nQRAMSimulatorCircuitParallel Class",
         "qram/circuit/simulator_manager.py\nQRAMCircuitSimulatorManager Class", 'Composition'),
        ("qram/simulator/circuit_sequential.py\nQRAMSimulatorCircuitSequential Class",
         "qram/circuit/simulator_manager.py\nQRAMCircuitSimulatorManager Class", 'Composition'),
        ("qram/circuit/simulator_manager.py\nQRAMCircuitSimulatorManager Class",
         "qram/circuit/core.py\nQRAMCircuitCore Class", 'Composition'),
        ("qramcircuits/bucket_brigade.py\nBucketBrigade Class",
         "qram/circuit/core.py\nQRAMCircuitCore Class", 'Composition'),

        # Class Optimization
        ("optimizers/transforme_ngh_gates.py\nTransformeNghGates Class",
         "qramcircuits/bucket_brigade.py\nBucketBrigade Class", 'Optimization'),
        ("optimizers/cancel_ngh_clifford_t_gates.py\nCancelNGHCliffordTGates Class",
         "qramcircuits/bucket_brigade.py\nBucketBrigade Class", 'Optimization'),
        ("optimizers/cancel_ngh_cnots.py\nCancelNghCNOTs Class",
         "qramcircuits/bucket_brigade.py\nBucketBrigade Class", 'Optimization'),
        ("optimizers/commute_t_to_start.py\nCommuteTGatesToStart Class",
         "qramcircuits/bucket_brigade.py\nBucketBrigade Class", 'Optimization'),
        ("optimizers/parallelize_cnots.py\nParallelizeCNOTs Class",
         "qramcircuits/bucket_brigade.py\nBucketBrigade Class", 'Optimization'),
        ("optimizers/cancel_t_gates.py\nCancelTGates Class",
         "qram/circuit/stress.py\nQRAMCircuitStress Class", 'Optimization'),

        # Main Executions
        ("main_experiments.py\nMainExperiments",
         "qram/circuit/experiments.py\nQRAMCircuitExperiments Class", 'Execution'),
        ("main_bilan.py\nMainBilan",
         "qram/circuit/bilan.py\nQRAMCircuitBilan Class", 'Execution'),
        ("main_stress.py\nMainStress",
         "qram/circuit/stress.py\nQRAMCircuitStress Class", 'Execution'),

        # Utils
        ("utils/arg_parser.py",
         "qram/circuit/core.py\nQRAMCircuitCore Class", 'Utils'),
        ("utils/arg_parser.py",
         "main_experiments.py\nMainExperiments", 'Utils'),
        ("utils/arg_parser.py",
         "main_bilan.py\nMainBilan", 'Utils'),
        ("utils/arg_parser.py",
         "main_stress.py\nMainStress", 'Utils'),
        ("utils/print_utils.py",
         "qram/circuit/core.py\nQRAMCircuitCore Class", 'Utils'),
        ("utils/print_utils.py",
         "qram/circuit/stress.py\nQRAMCircuitStress Class", 'Utils'),
        ("utils/print_utils.py",
         "qram/circuit/experiments.py\nQRAMCircuitExperiments Class", 'Utils'),
        ("utils/print_utils.py",
         "qram/circuit/bilan.py\nQRAMCircuitBilan Class", 'Utils')
    ]

    # Add edges with appropriate styles
    for src, dst, relation in dependencies:
        relation_attrs = COLOR_RELATIONS.get(relation, {'color': 'white', 'style': 'solid'})
        dot.edge(
            src,
            dst,
            xlabel=relation,
            color=relation_attrs['color'],
            fontcolor='white',
            style=relation_attrs['style'],
            fontsize='17'
        )

    # Add legend
    add_legend(dot)

    # Render the diagram
    dot.render(output_name, view=True)

def add_legend(graph):
    """
    Adds a legend to the graph.

    Args:
        graph (Digraph): The main graph object.
    """

    with graph.subgraph(name='cluster_legend') as legend:
        legend.attr(
            style='filled',
            color='gray30',
            label='Legend',
            fontsize='25',
            fontcolor='white',
            bgcolor='gray20',
            margin='15'
        )
        # Legend entries
        legend.node('Inheritance', shape='none', label='Inheritance', fontsize='17', fontcolor='black', fillcolor='cyan', style='filled')
        legend.node('Composition', shape='none', label='Composition', fontsize='17', fontcolor='black', fillcolor='orange', style='filled')
        legend.node('Optimization', shape='none', label='Optimization', fontsize='17', fontcolor='black', fillcolor='yellow', style='filled')
        legend.node('Execution', shape='none', label='Execution', fontsize='17', fontcolor='black', fillcolor='lime', style='filled')
        legend.node('Utils', shape='none', label='Utils', fontsize='17', fontcolor='black', fillcolor='lightcoral', style='filled')

        # Arrange legend items vertically
        legend.edge('Inheritance', 'Composition', style='invis')
        legend.edge('Composition', 'Optimization', style='invis')
        legend.edge('Optimization', 'Execution', style='invis')
        legend.edge('Execution', 'Utils', style='invis')

if __name__ == "__main__":
    # Define engines and formats
    engines = ['dot']
    formats = ['pdf']

    # Generate diagrams for each engine and format
    for engine in engines:
        for fmt in formats:
            output = f'main_diagram'
            create_diagram(engine=engine, fmt=fmt, output_name=output)
