# main_diagram.py
from graphviz import Digraph

def create_diagram(engine='twopi', fmt='pdf', output_name='main_diagram'):
    # Initialize the graph with a black background
    dot = Digraph(comment='QRAM Circuit Module Dependencies Diagram', format=fmt)
    dot.attr(
        # rankdir='TB',  # Top to Bottom
        rankdir='LR',  # Left to Right
        # rankdir='BT',  # Bottom to Top
        # rankdir='RL',  # Right to Left
        engine=engine,
        fontsize='13',
        splines='spline',
        bgcolor='black',
        fontcolor='white'
    )

    # Define colors for different module types
    COLOR_MODULE_CLASSES_INHERITANCE = 'dodgerblue'
    COLOR_MODULE_CLASSES_INHERITANCE_COMPOSITION = 'darkblue'
    COLOR_MODULE_CLASSES_COMPOSITION = 'darkorange'
    COLOR_MODULE_CLASSES_OPTIMIZATION = 'gold'
    COLOR_MODULE_MAIN = 'darkgreen'
    COLOR_MODULE_UTILS = 'red'

    # Define colors and styles for different relation types
    COLOR_RELATIONS = {
        'Inheritance': {'color': 'cyan', 'style': 'solid'},
        'Composition': {'color': 'orange', 'style': 'dashed'},
        'Optimization': {'color': 'yellow', 'style': 'dotted'},
        'Execution': {'color': 'lime', 'style': 'bold'},
        'Utils': {'color': 'lightcoral', 'style': 'dotted'}
    }

    # Modules with Descriptions and Colors
    modules = {
        # Class Inheritance
        'qramcircuits/qram_circuit_core.py\nQRAMCircuitCore Class': {
            'description': 'Constructs QRAM Circuits',
            'color': COLOR_MODULE_CLASSES_INHERITANCE,
            'type': 'Class Inheritance'
        },
        'qramcircuits/qram_circuit_stress.py\nQRAMCircuitStress Class': {
            'description': 'Performs stress testing on QRAM Circuits',
            'color': COLOR_MODULE_CLASSES_INHERITANCE,
            'type': 'Class Inheritance'
        },
        'qramcircuits/qram_circuit_experiments.py\nQRAMCircuitExperiments Class': {
            'description': 'Handles experiments for QRAM Circuits',
            'color': COLOR_MODULE_CLASSES_INHERITANCE,
            'type': 'Class Inheritance'
        },
        'qramcircuits/qram_circuit_bilan.py\nQRAMCircuitBilan Class': {
            'description': 'Generates bilan reports for QRAM Circuits',
            'color': COLOR_MODULE_CLASSES_INHERITANCE,
            'type': 'Class Inheritance'
        },

        # Class Inheritance Composition
        'qramcircuits/qram_simulator_base.py\nQRAMSimulatorBase Class': {
            'description': 'Base class for QRAM Simulators',
            'color': COLOR_MODULE_CLASSES_INHERITANCE_COMPOSITION,
            'type': 'Class Inheritance Composition'
        },
        'qramcircuits/qram_simulator_decomposition.py\nQRAMSimulatorDecompositions Class': {
            'description': 'Simulates Toffoli decompositions',
            'color': COLOR_MODULE_CLASSES_INHERITANCE_COMPOSITION,
            'type': 'Class Inheritance Composition'
        },
        'qramcircuits/qram_simulator_circuit_core.py\nQRAMSimulatorCircuitCore Class': {
            'description': 'Core class for QRAM Circuit Simulators',
            'color': COLOR_MODULE_CLASSES_INHERITANCE_COMPOSITION,
            'type': 'Class Inheritance Composition'
        },
        'qramcircuits/qram_simulator_circuit_hpc.py\nQRAMSimulationCircuitHPC Class': {
            'description': 'Simulates QRAM Circuit on HPC',
            'color': COLOR_MODULE_CLASSES_INHERITANCE_COMPOSITION,
            'type': 'Class Inheritance Composition'
        },
        'qramcircuits/qram_simulator_circuit_parallel.py\nQRAMSimulatorCircuitParallel Class': {
            'description': 'Simulates QRAM Circuit in parallel',
            'color': COLOR_MODULE_CLASSES_INHERITANCE_COMPOSITION,
            'type': 'Class Inheritance Composition'
        },
        'qramcircuits/qram_simulator_circuit_sequential.py\nQRAMSimulatorCircuitSequential Class': {
            'description': 'Simulates QRAM Circuit sequentially',
            'color': COLOR_MODULE_CLASSES_INHERITANCE_COMPOSITION,
            'type': 'Class Inheritance Composition'
        },

        # Class Composition
        'qramcircuits/qram_circuit_simulator.py\nQRAMCircuitSimulator Class': {
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
            "description": "Transforms (T and T) or (T^-1 and T^-1) or (S and S) or (S^-1 and S^-1)\ngates that are neighbor horizontally on series qubits",
            "color": COLOR_MODULE_CLASSES_OPTIMIZATION,
            "type": "Class Optimization"
        },
        'optimizers/cancel_ngh_clifford_t_gates.py\nCancelNGHCliffordTGates Class': {
            "description": "Cancels (H and H) or (T and T^-1) or (S and S^-1) or (Z and Z)\ngates that are neighbor horizontally on series qubits",
            "color": COLOR_MODULE_CLASSES_OPTIMIZATION,
            "type": "Class Optimization"
        },
        'optimizers/cancel_ngh_cnots.py\nCancelNghCNOTs Class': {
            "description": "Cancels two neighbouring CNOTs",
            "color": COLOR_MODULE_CLASSES_OPTIMIZATION,
            "type": "Class Optimization"
        },
        'optimizers/commute_t_to_start.py\nCommuteTGatesToStart Class': {
            "description": "Commutes T gates to the start of the circuit",
            "color": COLOR_MODULE_CLASSES_OPTIMIZATION,
            "type": "Class Optimization"
        },
        'optimizers/parallelize_cnots.py\nParallelizeCNOTs Class': {
            "description": "Parallelizes CNOTs",
            "color": COLOR_MODULE_CLASSES_OPTIMIZATION,
            "type": "Class Optimization"
        },
        'optimizers/cancel_t_gates.py\nCancelTGates Class': {
            "description": "Cancel T gates in a circuit",
            "color": COLOR_MODULE_CLASSES_OPTIMIZATION,
            "type": "Class Optimization"
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
    
    # Define subgraphs (clusters) for module types
    def add_cluster(c, cluster_name, label, color, fontcolor, module_type):
        with c.subgraph(name=f'cluster_{cluster_name}') as sub:
            sub.attr(style='filled', color=color, label=label, fontcolor=fontcolor, fontsize='14')
            for module, attrs in modules.items():
                if attrs['type'] == module_type:
                    sub.node(module, f"{module}\n{attrs['description']}",
                             style='filled',
                             fillcolor=attrs['color'],
                             fontcolor='white' if attrs['color'] not in ['red', 'gold'] else 'black',
                             shape='box',
                             fontsize='10')

    # Add clusters
    add_cluster(dot, 'classes_inheritance', 'Classes Inheritance', 'gray30', 'white', 'Class Inheritance')
    add_cluster(dot, 'classes_inheritance_composition', 'Classes Inheritance Composition', 'gray40', 'white', 'Class Inheritance Composition')
    add_cluster(dot, 'utils', 'Utils', 'gray90', 'black', 'Utils')
    add_cluster(dot, 'main_executions', 'Main Executions', 'gray10', 'white', 'Main')
    add_cluster(dot, 'classes_optimization', 'Classes Optimization', 'gray70', 'black', 'Class Optimization')
    add_cluster(dot, 'classes_composition', 'Classes Composition', 'gray50', 'white', 'Class Composition')

    # Define dependencies with relation types
    dependencies = [
        # Class Inheritance
        ("qramcircuits/qram_circuit_experiments.py\nQRAMCircuitExperiments Class",
            "qramcircuits/qram_circuit_core.py\nQRAMCircuitCore Class", 'Inheritance'),
        ("qramcircuits/qram_circuit_bilan.py\nQRAMCircuitBilan Class",
            "qramcircuits/qram_circuit_core.py\nQRAMCircuitCore Class", 'Inheritance'),
        ("qramcircuits/qram_circuit_stress.py\nQRAMCircuitStress Class",
            "qramcircuits/qram_circuit_experiments.py\nQRAMCircuitExperiments Class", 'Inheritance'),

        # Class Inheritance Composition
        ("qramcircuits/qram_simulator_decomposition.py\nQRAMSimulatorDecompositions Class",
            "qramcircuits/qram_simulator_base.py\nQRAMSimulatorBase Class", 'Inheritance'),
        ("qramcircuits/qram_simulator_circuit_core.py\nQRAMSimulatorCircuitCore Class",
            "qramcircuits/qram_simulator_base.py\nQRAMSimulatorBase Class", 'Inheritance'),
        ("qramcircuits/qram_simulator_circuit_hpc.py\nQRAMSimulationCircuitHPC Class",
            "qramcircuits/qram_simulator_circuit_core.py\nQRAMSimulatorCircuitCore Class", 'Inheritance'),
        ("qramcircuits/qram_simulator_circuit_parallel.py\nQRAMSimulatorCircuitParallel Class",
            "qramcircuits/qram_simulator_circuit_core.py\nQRAMSimulatorCircuitCore Class", 'Inheritance'),
        ("qramcircuits/qram_simulator_circuit_sequential.py\nQRAMSimulatorCircuitSequential Class",
            "qramcircuits/qram_simulator_circuit_core.py\nQRAMSimulatorCircuitCore Class", 'Inheritance'),

        # Class Composition
        ("qramcircuits/qram_simulator_decomposition.py\nQRAMSimulatorDecompositions Class",
            "qramcircuits/qram_circuit_simulator.py\nQRAMCircuitSimulator Class", 'Composition'),
        ("qramcircuits/qram_simulator_circuit_hpc.py\nQRAMSimulationCircuitHPC Class",
            "qramcircuits/qram_circuit_simulator.py\nQRAMCircuitSimulator Class", 'Composition'),
        ("qramcircuits/qram_simulator_circuit_parallel.py\nQRAMSimulatorCircuitParallel Class",
            "qramcircuits/qram_circuit_simulator.py\nQRAMCircuitSimulator Class", 'Composition'),
        ("qramcircuits/qram_simulator_circuit_sequential.py\nQRAMSimulatorCircuitSequential Class",
            "qramcircuits/qram_circuit_simulator.py\nQRAMCircuitSimulator Class", 'Composition'),
        ("qramcircuits/qram_circuit_simulator.py\nQRAMCircuitSimulator Class",
            "qramcircuits/qram_circuit_experiments.py\nQRAMCircuitExperiments Class", 'Composition'),
        ("qramcircuits/bucket_brigade.py\nBucketBrigade Class",
            "qramcircuits/qram_circuit_core.py\nQRAMCircuitCore Class", 'Composition'),

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
            "qramcircuits/qram_circuit_stress.py\nQRAMCircuitStress Class", 'Optimization'),

        # Main Executions
        ("main_experiments.py\nMainExperiments",
            "qramcircuits/qram_circuit_experiments.py\nQRAMCircuitExperiments Class", 'Execution'),
        ("main_bilan.py\nMainBilan",
            "qramcircuits/qram_circuit_bilan.py\nQRAMCircuitBilan Class", 'Execution'),
        ("main_stress.py\nMainStress",
            "qramcircuits/qram_circuit_stress.py\nQRAMCircuitStress Class", 'Execution'),

        # Utils
        ("utils/arg_parser.py",
            "qramcircuits/qram_circuit_core.py\nQRAMCircuitCore Class", 'Utils'),
        ("utils/arg_parser.py",
            "main_experiments.py\nMainExperiments", 'Utils'),
        ("utils/arg_parser.py",
            "main_bilan.py\nMainBilan", 'Utils'),
        ("utils/arg_parser.py",
            "main_stress.py\nMainStress", 'Utils'),
        ("utils/print_utils.py",
            "qramcircuits/qram_circuit_core.py\nQRAMCircuitCore Class", 'Utils'),
        ("utils/print_utils.py",
            "qramcircuits/qram_circuit_stress.py\nQRAMCircuitStress Class", 'Utils'),
        ("utils/print_utils.py",
            "qramcircuits/qram_circuit_experiments.py\nQRAMCircuitExperiments Class", 'Utils'),
        ("utils/print_utils.py",
            "qramcircuits/qram_circuit_bilan.py\nQRAMCircuitBilan Class", 'Utils')
    ]

    # Add edges with different colors and styles based on relation type
    for src, dst, relation in dependencies:
        relation_attrs = COLOR_RELATIONS.get(relation, {'color': 'white', 'style': 'solid'})
        dot.edge(src, dst,
                 label=relation,
                 color=relation_attrs['color'],
                 fontcolor='white',
                 style=relation_attrs['style'],
                 fontsize='10')

    # Position the legend at the bottom using a subgraph with rank='sink'
    with dot.subgraph() as s:
        s.attr(rank='sink')
        s.node('legend')

    # Render the diagram
    dot.render(output_name, view=True)

if __name__ == "__main__":
    # Example usage with different engines and formats
    engines = ['twopi'] # , 'dot', 'neato', 'circo', 'fdp', 'sfdp']
    formats = ['pdf'] # , 'png', 'svg', 'jpg']

    for engine in engines:
        for fmt in formats:
            create_diagram(engine=engine, fmt=fmt, output_name=f'main_diagram')