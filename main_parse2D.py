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
    plt.plot(x, data["T Count 7"], marker="o", label="T Count 7")
    plt.plot(x, data["T Count 6"], marker="o", label="T Count 6")
    plt.plot(x, data["T Count 5"], marker="o", label="T Count 5")
    plt.plot(x, data["T Count 4"], marker="o", label="T Count 4")
    plt.xlabel("QRAM Qubits")
    plt.ylabel("T Count Removed")
    plt.title("T Count Removed (Higher is Better)")
    plt.legend()
    plt.show()


plot2D(data)
