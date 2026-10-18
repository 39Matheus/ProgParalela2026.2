"""Confere campos completos das tres versoes, usando apenas Python padrao."""
import csv
import math
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent


def load(path):
    with path.open() as file:
        return [(int(row["i"]), int(row["j"]), float(row["u"]), float(row["v"]))
                for row in csv.DictReader(file)]


def initial(nx, ny, mode):
    values = []
    for i in range(nx):
        x = (i + .5) / nx
        for j in range(ny):
            y = (j + .5) / ny
            u = 1.0 if mode >= 1 else 0.0
            if mode == 2:
                u += .5 * math.exp(-((x - .5)**2 + (y - .5)**2) / (2 * .08**2))
            values.append(u)
    return values


def main():
    subprocess.run(["bash", str(ROOT / "compilar.sh")], check=True)
    cases = [(11, 7, 9), (12, 9, 10)]
    count = 0
    with tempfile.TemporaryDirectory(prefix="tarefa12_validacao_") as directory:
        folder = Path(directory)
        for nx, ny, steps in cases:
            for mode in (0, 1, 2):
                reference = None
                start = initial(nx, ny, mode)
                for version in (0, 1, 2):
                    for threads in (1, 2, 4):
                        output = folder / "final.csv"
                        env = dict(os.environ, OMP_NUM_THREADS=str(threads),
                                   OMP_DYNAMIC="FALSE", OMP_SCHEDULE="static")
                        result = subprocess.run(
                            [str(ROOT / "bin" / ("v" + str(version))), str(nx), str(ny),
                             str(steps), str(mode), str(output)], env=env,
                            check=True, capture_output=True, text=True, timeout=30)
                        assert "RESULTADO;" in result.stdout
                        field = load(output)
                        assert len(field) == nx * ny
                        assert all((i, j) == divmod(k, ny)
                                   for k, (i, j, u, v) in enumerate(field))
                        assert all(math.isfinite(u) and v == 0 for i, j, u, v in field)
                        if reference is None:
                            reference = field
                        # Nenhuma alteracao da ordem das operacoes de ponto flutuante.
                        assert field == reference, (version, threads, mode)
                        values = [u for i, j, u, v in field]
                        assert math.isclose(sum(values), sum(start), rel_tol=1e-12, abs_tol=1e-12)
                        assert min(values) >= min(start) - 1e-12
                        assert max(values) <= max(start) + 1e-12
                        if mode < 2:
                            assert values == start
                        else:
                            assert max(values) < max(start)
                        count += 1
        for args in ([], ["1", "2", "3"], ["a", "2", "3"], ["2", "2", "0"],
                     ["2", "2", "3", "4"], ["50000", "50000", "1"]):
            result = subprocess.run([str(ROOT / "bin/v0")] + args,
                                    capture_output=True, text=True)
            assert result.returncode != 0, args
    print("OK: %d execuções; campos idênticos, modos constantes, conservação e limites." % count)
    print("Verificação de correção local; não é uma medição de escalabilidade no NPAD.")


if __name__ == "__main__":
    main()
