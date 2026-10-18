"""Gera gráficos e tabelas dos CSVs incluídos, sem executar simulações."""
from pathlib import Path
import csv
from collections import defaultdict
from statistics import mean, stdev

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
DATA, FIG, TABLE = (ROOT / name for name in ("dados", "figuras", "tabelas"))
FIG.mkdir(exist_ok=True)
TABLE.mkdir(exist_ok=True)
plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "pdf.fonttype": 42})
VERSIONS = ("v0", "v1", "v2")
SIZES, THREADS = (200, 400, 800), (1, 2, 4, 8, 16)
COLORS = ("#2366a8", "#d4791f", "#258563")


def read(name):
    with (DATA / name).open(encoding="utf-8") as file:
        return list(csv.DictReader(file, delimiter=";"))


def pt(number, digits=3):
    return f"{float(number):.{digits}f}".replace(".", ",")


raw, summary, weak = read("tempos.csv"), read("resumo.csv"), read("fraca.csv")
assert len(raw) == 225 and len(summary) == 45 and len(weak) == 9
groups = defaultdict(list)
diagnostics = defaultdict(set)
for row in raw:
    version, n, p = row["versao"], int(row["nx"]), int(row["threads_reais"])
    assert int(row["threads_solicitadas"]) == p
    assert int(row["ny"]) == n and int(row["passos"]) == 2000
    groups[version, n, p].append(float(row["tempo_segundos"]))
    diagnostics[n].add(tuple(float(row[k]) for k in
                             ("media_u", "media_v", "max_pert", "rms_pert")))
assert all(len(values) == 5 for values in groups.values())
assert all(len(values) == 1 for values in diagnostics.values())
stats = {(row["versao"], int(row["nx"]), int(row["threads"])): row
         for row in summary}
for key, values in groups.items():
    row = stats[key]
    assert abs(mean(values) - float(row["tempo_medio_segundos"])) < 1e-10
    assert abs(stdev(values) - float(row["desvio_amostral"])) < 1e-10


def values(version, n, field):
    return [float(stats[version, n, p][field]) for p in THREADS]


def save(fig, name):
    fig.savefig(FIG / name, bbox_inches="tight")
    plt.close(fig)


fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.8), layout="constrained")
for version, color, marker in zip(VERSIONS, COLORS, ("o", "s", "^")):
    axes[0].errorbar(THREADS, values(version, 800, "tempo_medio_segundos"),
                     yerr=values(version, 800, "desvio_amostral"),
                     color=color, marker=marker, capsize=4, label=version)
    axes[1].plot(THREADS, values(version, 800, "speedup_versao"),
                 color=color, marker=marker, label=version)
axes[1].plot(THREADS, THREADS, "--", color=".5", label="Ideal")
for ax in axes:
    ax.set(xlabel="Threads efetivas", xticks=THREADS, ylim=(0, 18))
    ax.grid(alpha=.22)
    ax.legend(fontsize=8)
axes[0].set_ylabel("Tempo de cálculo (s)")
axes[1].set_ylabel("Speedup da própria versão")
save(fig, "forte.pdf")

fig, axes = plt.subplots(1, 3, figsize=(8.6, 3.5), sharey=True,
                         layout="constrained")
for version, ax in zip(VERSIONS, axes):
    for n, color in zip(SIZES, COLORS):
        ax.plot(THREADS, np.array(values(version, n, "eficiencia_versao")) * 100,
                "o-", color=color, label=f"N = {n}")
    ax.set(title=version, xlabel="Threads efetivas", xticks=THREADS, ylim=(0, 108))
    ax.grid(alpha=.22)
    ax.legend(fontsize=8)
axes[0].set_ylabel("Eficiência forte (%)")
save(fig, "eficiencia.pdf")

fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.8), layout="constrained")
for version, color, marker in zip(VERSIONS, COLORS, ("o", "s", "^")):
    rows = [row for row in weak if row["versao"] == version]
    p = [int(row["threads"]) for row in rows]
    axes[0].errorbar(p, [float(row["tempo_medio_segundos"]) for row in rows],
                     yerr=[float(row["desvio_amostral"]) for row in rows],
                     color=color, marker=marker, capsize=4, label=version)
    axes[1].plot(p, [100 * float(row["eficiencia_fraca"]) for row in rows],
                 color=color, marker=marker, label=version)
for ax in axes:
    ax.set(xlabel="Threads / malha", xticks=(1, 4, 16),
           xticklabels=("1 / 200²", "4 / 400²", "16 / 800²"))
    ax.grid(alpha=.22)
    ax.legend(fontsize=8)
axes[0].set(ylabel="Tempo de cálculo (s)", ylim=(0, 2.9))
axes[1].set(ylabel="Eficiência fraca (%)", ylim=(0, 108))
save(fig, "fraca.pdf")

fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.4), layout="constrained")
for version, ax in zip(VERSIONS[1:], axes):
    # Percentual de redução do tempo: positivo indica execução mais rápida.
    reduction = np.array([[100 * (1 - 1 / float(stats[version, n, p]["ganho_sobre_v0"]))
                           for p in THREADS] for n in SIZES])
    image = ax.imshow(reduction, vmin=-1.5, vmax=1.5, cmap="RdYlGn", aspect="auto")
    for i in range(3):
        for j in range(5):
            ax.text(j, i, pt(reduction[i, j], 2), ha="center", va="center", fontsize=9)
    ax.set(title=f"{version} em relação a v0", xlabel="Threads efetivas", ylabel="N",
           xticks=range(5), xticklabels=THREADS, yticks=range(3), yticklabels=SIZES)
fig.colorbar(image, ax=axes, label="Redução do tempo (%)", shrink=.85)
save(fig, "ganho.pdf")


def table(filename, columns, heading, caption, rows, label):
    text = [r"\begin{longtable}{" + columns + "}", r"\caption{" + caption +
            r"}\label{" + label + r"}\\", r"\toprule " + heading + r"\\",
            r"\midrule\endfirsthead", r"\toprule " + heading + r"\\",
            r"\midrule\endhead", r"\bottomrule\endfoot"]
    text.extend(" & ".join(row) + r"\\" for row in rows)
    text.append(r"\end{longtable}")
    (TABLE / filename).write_text("\n".join(text) + "\n", encoding="utf-8")


table("forte800.tex", "rrrrrrr",
      r"$p$ & $T_0$ (s) & $S_0$ & $E_0$ (\%) & $T_1$ (s) & $T_2$ (s) & $E_2$ (\%)",
      r"Carga forte de $800\times800$, com 2.000 passos. Os índices indicam a versão.",
      [[str(p), pt(stats["v0", 800, p]["tempo_medio_segundos"], 4),
        pt(stats["v0", 800, p]["speedup_versao"]),
        pt(100 * float(stats["v0", 800, p]["eficiencia_versao"]), 2),
        pt(stats["v1", 800, p]["tempo_medio_segundos"], 4),
        pt(stats["v2", 800, p]["tempo_medio_segundos"], 4),
        pt(100 * float(stats["v2", 800, p]["eficiencia_versao"]), 2)] for p in THREADS],
      "tab:forte")
table("fraca.tex", "lrrrrr", r"Versão & $p$ & $N$ & Média (s) & $s$ (s) & $E_f$ (\%)",
      "Escalabilidade fraca: 80 milhões de atualizações de células por thread.",
      [[row["versao"], row["threads"], row["nx"],
        pt(row["tempo_medio_segundos"], 6), pt(row["desvio_amostral"], 6),
        pt(100 * float(row["eficiencia_fraca"]), 2)] for row in weak], "tab:fraca")
table("resumo_completo.tex", "lrrrrrrrr",
      r"Versão & $N$ & $p$ & Média (s) & $s$ (s) & CV (\%) & $S$ & $E$ (\%) & $G$",
      "Todas as 45 configurações, com cinco repetições cada. "
      "$S$ e $E$ usam a própria versão; $G$ usa v0 com a mesma carga e equipe.",
      [[row["versao"], row["nx"], row["threads"],
        pt(row["tempo_medio_segundos"], 6), pt(row["desvio_amostral"], 6),
        pt(row["cv_percentual"], 2), pt(row["speedup_versao"]),
        pt(100 * float(row["eficiencia_versao"]), 2), pt(row["ganho_sobre_v0"], 4)]
       for row in summary], "tab:completo")
table("diagnosticos.tex", "rrrrr", r"$N$ & $t_{final}$ & Média de $u$ & Máximo & RMS",
      "Diagnósticos finais: para cada malha, idênticos em todas as versões e equipes.",
      [[str(n), pt(40000 / n**2, 5), pt(next(iter(diagnostics[n]))[0], 12),
        pt(next(iter(diagnostics[n]))[2], 8), pt(next(iter(diagnostics[n]))[3], 8)]
       for n in SIZES], "tab:diagnosticos")
print("Figuras e tabelas atualizadas; 225 amostras e 45 resumos conferidos.")
