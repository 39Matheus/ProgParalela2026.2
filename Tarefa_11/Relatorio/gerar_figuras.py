"""Atualiza figuras e tabela a partir dos dados incluídos, sem executar a simulação."""
from pathlib import Path
import csv
from collections import defaultdict
from statistics import mean, stdev

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "dados"
FIG = ROOT / "figuras"
TABLE = ROOT / "tabelas"
FIG.mkdir(exist_ok=True)
TABLE.mkdir(exist_ok=True)
plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "pdf.fonttype": 42})


def read_csv(name):
    with (DATA / name).open(encoding="utf-8") as file:
        return list(csv.DictReader(file, delimiter=";"))


def pt(value, digits=3):
    return f"{value:.{digits}f}".replace(".", ",")


groups = defaultdict(list)
for row in read_csv("tempos.csv"):
    groups[row["versao"], int(row["threads"]), row["schedule"]].append(
        float(row["tempo_segundos"]))
assert len(groups) == 18 and all(len(values) == 3 for values in groups.values())
baseline = mean(groups["normal", 1, "static"])
versions = ("normal", "collapse")
schedules = ("static", "dynamic,8", "guided,8")
threads = (1, 2, 4)
colors = ("#2366a8", "#d4791f", "#258563")
stats = {}
for key, values in groups.items():
    avg, sd = mean(values), stdev(values)
    stats[key] = (avg, sd, baseline / avg, 100 * sd / avg)

for name, speedup in (("tempos", False), ("speedup", True)):
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.8), sharey=True,
                             layout="constrained")
    for ax, version in zip(axes, versions):
        for schedule, color in zip(schedules, colors):
            averages = [stats[version, p, schedule][0] for p in threads]
            deviations = [stats[version, p, schedule][1] for p in threads]
            if speedup:
                values = [baseline / value for value in averages]
                ax.plot(threads, values, "o-", color=color, label=schedule)
            else:
                ax.errorbar(threads, averages, yerr=deviations, fmt="o-",
                            capsize=4, color=color, label=schedule)
                # Mostra as três medições, inclusive as que mais se afastam.
                for p in threads:
                    ax.scatter([p] * 3, groups[version, p, schedule],
                               color=color, alpha=.38, s=17, zorder=3)
        if speedup:
            ax.plot(threads, threads, "--", color="0.55", label="Referência ideal")
        ax.set_title("Sem collapse" if version == "normal" else "Com collapse(2)")
        ax.set_xlabel("Threads solicitadas")
        ax.set_xticks(threads)
        ax.grid(alpha=.22)
        ax.legend(fontsize=8)
    upper = 4.4 if speedup else 1.12 * max(max(values) for values in groups.values())
    axes[0].set_ylim(0, upper)
    axes[0].set_ylabel("Speedup sobre normal / 1 / static" if speedup
                       else "Tempo de cálculo (s)")
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)

validation = read_csv("validacao_numerica.csv")
t = np.array([float(row["tempo_fisico"]) for row in validation])
maximum = [float(row["max_pert"]) for row in validation]
rms = [float(row["rms_pert"]) for row in validation]
limit = float(validation[0]["media_u"]) - 1
fig, ax = plt.subplots(figsize=(8.4, 3.6), layout="constrained")
ax.plot(t, maximum, label="Máximo da perturbação", color=colors[1])
ax.plot(t, rms, label="RMS da perturbação", color=colors[0])
ax.axhline(limit, ls="--", color="0.45", label="Média da perturbação conservada")
ax.set(xlabel="Tempo físico simulado", ylabel="Amplitude", ylim=(0, .52))
ax.grid(alpha=.22)
ax.legend()
fig.savefig(FIG / "decaimento.pdf", bbox_inches="tight")
plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.7), layout="constrained")
for ax, filename, title in zip(axes, ("campo_inicial.csv", "campo_final.csv"),
                               ("Estado inicial (t = 0)", "Estado final (t = 3,125)")):
    array = np.loadtxt(DATA / filename, delimiter=",", skiprows=1)
    u = array[:, 2].reshape(80, 80)
    image = ax.imshow((u - 1).T, origin="lower", extent=(0, 1, 0, 1),
                      vmin=0, vmax=.5, cmap="viridis")
    ax.set(title=title, xlabel="x", ylabel="y")
fig.colorbar(image, ax=axes, label="Perturbação u − 1", shrink=.85)
fig.savefig(FIG / "campos.pdf", bbox_inches="tight")
plt.close(fig)

lines = [r"\begin{longtable}{llrrrrr}",
         r"\caption{Resultados da carga de $400\times400$ células e 5.000 passos."
         r" $s$ é o desvio padrão amostral; CV é o coeficiente de variação.}"
         r"\label{tab:resultados}\\",
         r"\toprule Versão & Schedule & Threads & Média (s) & $s$ (s) & Speedup & CV (\%) \\",
         r"\midrule\endfirsthead",
         r"\toprule Versão & Schedule & Threads & Média (s) & $s$ (s) & Speedup & CV (\%) \\",
         r"\midrule\endhead", r"\bottomrule\endfoot"]
for version in versions:
    for p in threads:
        for schedule in schedules:
            avg, sd, speed, cv = stats[version, p, schedule]
            label = "Normal" if version == "normal" else "Collapse"
            lines.append(f"{label} & \\texttt{{{schedule}}} & {p} & "
                         f"{pt(avg)} & {pt(sd)} & {pt(speed)} & {pt(cv, 2)} " + r"\\")
    if version == "normal":
        lines.append(r"\midrule")
lines.append(r"\end{longtable}")
(TABLE / "resultados.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
with (DATA / "estatisticas.csv").open("w", encoding="utf-8", newline="") as file:
    writer = csv.writer(file, delimiter=";", lineterminator="\n")
    writer.writerow(("versao", "threads", "schedule", "media", "desvio_amostral",
                     "speedup_referencia_comum", "cv_percentual"))
    for key, values in stats.items():
        writer.writerow((*key, *values))
print("Figuras, tabela e estatísticas atualizadas a partir dos CSVs incluídos.")

# Registros completos para que os apêndices possam ser lidos somente no PDF.
def longtable(filename, columns, heading, caption, rows):
    content = [r"\begin{longtable}{" + columns + "}",
               r"\caption{" + caption + r"}\\", r"\toprule " + heading + r"\\",
               r"\midrule\endfirsthead", r"\toprule " + heading + r"\\",
               r"\midrule\endhead", r"\bottomrule\endfoot"]
    content.extend(" & ".join(row) + r"\\" for row in rows)
    content.append(r"\end{longtable}")
    (TABLE / filename).write_text("\n".join(content) + "\n", encoding="utf-8")

longtable("tempos_brutos.tex", "llrrr",
          r"Versão & Schedule & Threads & Repetição & Tempo (s)",
          "Todas as 54 medições, sem exclusão de amostras.",
          [[row["versao"], row["schedule"], row["threads"], row["repeticao"],
            pt(float(row["tempo_segundos"]), 6)] for row in read_csv("tempos.csv")])
longtable("validacao_completa.tex", "rrrrr",
          r"Passo & $t$ & Máximo & RMS & Variância de $u$",
          "Série completa dos 101 estados salvos no modo 2. "
          "A média de $u$ se conserva em aproximadamente $1{,}020106192967$ "
          "e a componente $v$ é nula em todos os estados.",
          [[row["passo"], pt(float(row["tempo_fisico"]), 5),
            pt(float(row["max_pert"]), 8), pt(float(row["rms_pert"]), 8),
            pt(float(row["variancia_u"]), 10)] for row in validation])
