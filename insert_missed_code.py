import sys


def insert_code(file_path, code, line_number):
    with open(file_path, "r") as file:
        lines = file.readlines()

    # lines.insert(line_number - 1, code)
    lines.append("\n" + code)

    with open(file_path, "w") as file:
        file.writelines(lines)


def main():
    # Get python exact version 3.x from sys.version not 3.x.x
    python_version = sys.version.split(" ")[0].split(".")
    python_version = python_version[0] + "." + python_version[1]

    if sys.argv[1] == "docker":
        file_path = f"/usr/local/lib/python{python_version}/dist-packages/cirq/contrib/svg/__init__.py"
    elif sys.argv[1] == "local":
        file_path = f"./.venv/lib/python{python_version}/site-packages/cirq/contrib/svg/__init__.py"

    code = "from cirq.contrib.svg.svg import tdd_to_svg"

    line_number = 3

    insert_code(file_path, code, line_number)


if __name__ == "__main__":
    main()
