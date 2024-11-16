import sys

def insert_code(file_path, code, line_number):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    lines.insert(line_number - 1, code + '\n')
    
    with open(file_path, 'w') as file:
        file.writelines(lines)
    
if sys.argv[1] == 'docker':
    file_path = '/usr/local/lib/python3.7/dist-packages/cirq/contrib/svg/__init__.py'
elif sys.argv[1] == 'local':
    file_path = './.venv/lib/python3.7/site-packages/cirq/contrib/svg/__init__.py'

code = "    tdd_to_svg,"

line_number = 4

insert_code(file_path, code, line_number)


if sys.argv[1] == 'docker':
    file_path = '/usr/local/lib/python3.7/dist-packages/qsimcirq/qsim_circuit.py'
elif sys.argv[1] == 'local':
    file_path = '.venv/lib/python3.7/site-packages/qsimcirq/qsim_circuit.py'

code = """  if isinstance(gate, cirq.ops.ControlledGate):
    # Handle ControlledGate by returning the kind of the sub-gate
    sub_gate_kind = _cirq_gate_kind(gate.sub_gate)
    if sub_gate_kind is not None:
      return sub_gate_kind
    raise ValueError(f'Unrecognized controlled gate: {gate}')"""

line_number = 103

insert_code(file_path, code, line_number)