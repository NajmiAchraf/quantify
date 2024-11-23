from graphviz import Digraph

# Initialize Digraph with black background
dot = Digraph(comment='QRAM Circuit Module Dependencies Diagram', format='pdf')
dot.attr(rankdir='LR', fontsize='10', splines='ortho', bgcolor='black', fontcolor='white')

# Define synchronized bright colors for different types
COLOR_CLASSES = 'dodgerblue'
COLOR_MAIN = 'darkgreen'
COLOR_RELATIONS = {
    'Inheritance': 'orange',
    'Composition': 'cyan',
    'Execution': 'magenta'
}

# Modules with Descriptions and Colors
modules = {
    'qram_circuit_simulator.py\nQRAMCircuitSimulator Class': {
        'description': 'Simulates QRAM Circuits',
        'color': COLOR_CLASSES,
        'type': 'Class Composition'
    },
    'qram_circuit_core.py\nQRAMCircuitCore Class': {
        'description': 'Constructs QRAM Circuits',
        'color': COLOR_CLASSES,
        'type': 'Class Inheritance'
    },
    'qram_circuit_stress.py\nQRAMCircuitStress Class': {
        'description': 'Performs stress testing on QRAM Circuits',
        'color': COLOR_CLASSES,
        'type': 'Class Inheritance'
    },
    'qram_circuit_experiments.py\nQRAMCircuitExperiments Class': {
        'description': 'Handles experiments for QRAM Circuits',
        'color': COLOR_CLASSES,
        'type': 'Class Inheritance'
    },
    'qram_circuit_bilan.py\nQRAMCircuitBilan Class': {
        'description': 'Generates bilan reports for QRAM Circuits',
        'color': COLOR_CLASSES,
        'type': 'Class Inheritance'
    },
    'bucket_brigade.py\nBucketBrigade Class': {
        'description': 'Creates Bucket Brigade for QRAM Circuit',
        'color': COLOR_CLASSES,
        'type': 'Class Composition'
    },
    'main_experiments.py\nMainExperiments': {
        'description': 'Executes QRAMCircuitExperiments',
        'color': COLOR_MAIN,
        'type': 'Main'
    },
    'main_bilan.py\nMainBilan': {
        'description': 'Executes QRAMCircuitBilan',
        'color': COLOR_MAIN,
        'type': 'Main'
    },
    'main_stress.py\nMainStress': {
        'description': 'Executes QRAMCircuitStress',
        'color': COLOR_MAIN,
        'type': 'Main'
    }
}

# Define subgraphs (clusters) for layering
with dot.subgraph(name='cluster_classes_inheritance') as c:
    c.attr(style='filled', color='gray30', label='Classes Inheritance', fontcolor='white')
    for module, attrs in modules.items():
        if attrs['type'] == 'Class Inheritance':
            c.node(module, f"{module}\n{attrs['description']}",
                   style='filled', fillcolor=attrs['color'], fontcolor='white', shape='box')

with dot.subgraph(name='cluster_classes_composition') as c:
    c.attr(style='filled', color='gray50', label='Classes Composition', fontcolor='white')
    for module, attrs in modules.items():
        if attrs['type'] == 'Class Composition':
            c.node(module, f"{module}\n{attrs['description']}",
                   style='filled', fillcolor=attrs['color'], fontcolor='white', shape='box')

with dot.subgraph(name='cluster_main') as c:
    c.attr(style='filled', color='gray10', label='Main Executions', fontcolor='white')
    for module, attrs in modules.items():
        if attrs['type'] == 'Main':
            c.node(module, f"{module}\n{attrs['description']}",
                   style='filled', fillcolor=attrs['color'], fontcolor='white', shape='box')

# Dependencies with Relation Types
dependencies = [
    # Class Inheritance
    ("qram_circuit_experiments.py\nQRAMCircuitExperiments Class", "qram_circuit_core.py\nQRAMCircuitCore Class", 'Inheritance'),
    ("qram_circuit_bilan.py\nQRAMCircuitBilan Class", "qram_circuit_core.py\nQRAMCircuitCore Class", 'Inheritance'),
    ("qram_circuit_stress.py\nQRAMCircuitStress Class", "qram_circuit_experiments.py\nQRAMCircuitExperiments Class", 'Inheritance'),

    # Composition
    ("bucket_brigade.py\nBucketBrigade Class", "qram_circuit_core.py\nQRAMCircuitCore Class", 'Composition'),
    ("qram_circuit_simulator.py\nQRAMCircuitSimulator Class", "qram_circuit_experiments.py\nQRAMCircuitExperiments Class", 'Composition'),

    # Main Executions
    ("main_experiments.py\nMainExperiments", "qram_circuit_experiments.py\nQRAMCircuitExperiments Class", 'Execution'),
    ("main_bilan.py\nMainBilan", "qram_circuit_bilan.py\nQRAMCircuitBilan Class", 'Execution'),
    ("main_stress.py\nMainStress", "qram_circuit_stress.py\nQRAMCircuitStress Class", 'Execution')
]

# Add edges with different colors and styles based on relation type
for src, dst, relation in dependencies:
    color = COLOR_RELATIONS.get(relation, 'white')
    style = {
        'Inheritance': 'solid',
        'Composition': 'dashed',
        'Execution': 'dotted'
    }.get(relation, 'solid')
    dot.edge(src, dst, label=relation, color=color, fontcolor='white', style=style)

# Render the diagram
dot.render('main_diagram', view=True)