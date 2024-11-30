from typing_extensions import Literal
import subprocess

slurm_type = Literal["bilan", "experiments", "stress"]
target_type = Literal["submit", "output", "error", "run"]

def shell(cmd: str) -> None:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)

def make_slurm(slurm: slurm_type, qubit: str="2", t_count: str="7", t_cancel: str="1", target: target_type="output") -> int:
    command = f"make SLURM={slurm} QUBITS={qubit} T_COUNT={t_count} T_CANCEL={t_cancel} {target}"
    shell(command)
