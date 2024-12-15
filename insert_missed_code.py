import sys


def insert_code(file_path, code, line_number):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    lines.insert(line_number - 1, code + '\n')
    
    with open(file_path, 'w') as file:
        file.writelines(lines)


def main():
    if sys.argv[1] == 'docker':
        file_path = '/usr/local/lib/python3.7/dist-packages/cirq/contrib/svg/__init__.py'
    elif sys.argv[1] == 'local':
        file_path = './.venv/lib/python3.7/site-packages/cirq/contrib/svg/__init__.py'

    code = "    tdd_to_svg,"

    line_number = 4

    insert_code(file_path, code, line_number)


if __name__ == '__main__':
    main()