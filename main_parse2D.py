import sys

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

matplotlib.use("TkAgg")

if len(sys.argv) < 2:
    print("Usage: python3 main_parse2D.py <file_path>")
    sys.exit(1)

# Read the data from the file
file_path = sys.argv[1]
data = pd.read_csv(file_path, delimiter=",")  # Adjust delimiter if needed


def plot2D(data):
    plt.figure()
    x = data["Qubits"]
    plt.plot(x, data["T-gate Count 7"], marker="o", label="AN0_TD4_TC7_CX6")
    plt.plot(x, data["T-gate Count 6"], marker="o", label="AN0_TD4_TC6_CX6")
    plt.plot(x, data["T-gate Count 5"], marker="o", label="AN0_TD4_TC5_CX6")
    plt.plot(x, data["T-gate Count 4"], marker="o", label="AN0_TD3_TC4_CX6")
    plt.xlabel("Qubits QRAM")
    plt.ylabel("T-gate Reduction")
    plt.title("T-gate Reduction vs Qubits QRAM\n(higher is better)")
    plt.legend()
    plt.show()


plot2D(data)
