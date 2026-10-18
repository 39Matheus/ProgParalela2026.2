"""Analisa somente as séries CPU e Tesla V100."""
from pathlib import Path
import csv
import re
from statistics import mean, stdev

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
DATA, FIG, TABLE = (ROOT / name for name in ("dados", "figuras", "tabelas"))
FIG.mkdir(exist_ok=True)
TABLE.mkdir(exist_ok=True)
SERIES = (
    ("CPU1a.out", "CPU 1a", "CPU", 1, "service3", "CPU não registrada"),
    ("CPU1b.out", "CPU 1b", "CPU", 1, "service3", "CPU não registrada"),
    ("CPU4.out", "CPU 4", "CPU", 4, "service3", "CPU não registrada"),
    ("GPUa.out", "V100 a", "GPU", None, "gpunode1", "Tesla V100-SXM2-16GB"),
    ("GPUb.out", "V100 b", "GPU", None, "gpunode1", "Tesla V100-SXM2-16GB"),
    ("resultado_gpu_2134904.out", "V100 c", "GPU", None, "gpunode1",
     "Tesla V100-SXM2-16GB"),
)
records, summaries = [], []
for filename, label, mode, threads, host, model in SERIES:
    text = (DATA / "logs" / filename).read_text(encoding="utf-8")
    assert f"Hostname: {host}.npad.internal" in text
    if mode == "GPU":
        assert "Tesla V100-SXM2-16GB" in text
    chunks = re.split(r"----- (Warm-up|Execucao \d+) -----", text)
    times, warmup = [], None
    for i in range(1, len(chunks), 2):
        stage, block = chunks[i:i + 2]
        n = int(re.search(r"N\s*:\s*(\d+)", block)[1])
        tol = float(re.search(r"TOL\s*:\s*([\deE+.-]+)", block)[1])
        declared = re.search(r"MODO\s*:\s*(CPU|GPU)", block)[1]
        errors = int(re.search(r"Erros\s*:\s*(\d+)", block)[1])
        elapsed = float(re.search(r"Tempo\s*:\s*([\d.]+)", block)[1])
        assert n == 10000000 and tol == 1e-9 and declared == mode and errors == 0
        repetition = 0 if stage == "Warm-up" else int(stage.split()[-1])
        records.append((filename, label, mode, threads, host, repetition,
                        n, tol, errors, elapsed))
        if repetition == 0:
            warmup = elapsed
        else:
            times.append(elapsed)
    assert len(times) == 5
    avg, sd = mean(times), stdev(times)
    summaries.append(dict(file=filename, label=label, mode=mode, threads=threads,
                          host=host, model=model, warmup=warmup, times=times,
                          avg=avg, sd=sd, cv=100 * sd / avg))
assert len(records) == 33

with (DATA / "tempos_extraidos.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, delimiter=";", lineterminator="\n")
    writer.writerow(("arquivo", "serie", "modo", "threads_configuradas",
                     "hostname", "repeticao_0_aquecimento", "N", "tolerancia",
                     "erros", "tempo_segundos"))
    writer.writerows(records)
with (DATA / "resumo.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, delimiter=";", lineterminator="\n")
    writer.writerow(("arquivo", "serie", "media_segundos", "desvio_amostral",
                     "cv_percentual", "aquecimento_segundos"))
    for row in summaries:
        writer.writerow((row["file"], row["label"], row["avg"], row["sd"],
                         row["cv"], row["warmup"]))


def pt(number, digits=3):
    return f"{number:.{digits}f}".replace(".", ",")


def table(name, columns, heading, caption, rows, label):
    text = [r"\begin{longtable}{" + columns + "}", r"\caption{" + caption +
            r"}\label{" + label + r"}\\", r"\toprule " + heading + r"\\",
            r"\midrule\endfirsthead", r"\toprule " + heading + r"\\",
            r"\midrule\endhead", r"\bottomrule\endfoot"]
    text.extend(" & ".join(row) + r"\\" for row in rows)
    text.append(r"\end{longtable}")
    (TABLE / name).write_text("\n".join(text) + "\n", encoding="utf-8")


table("resumo.tex", "lrrrr",
      r"Série & Média (ms) & $s$ (ms) & CV (\%) & Aquecimento (ms)",
      "Séries CPU e Tesla V100. Cinco medições por série; "
      "aquecimentos separados e excluídos das médias.",
      [[row["label"], pt(row["avg"] * 1000, 6), pt(row["sd"] * 1000, 6),
        pt(row["cv"], 2), "---" if row["warmup"] is None else pt(row["warmup"] * 1000, 6)]
       for row in summaries], "tab:resumo")
table("brutos.tex", "lrrr",
      r"Série & Repetição & Tempo (s) & Erros",
      "Todos os 33 registros selecionados. Repetição 0 identifica o aquecimento "
      "em processo separado.",
      [[row[1], str(row[5]), pt(row[9], 9), str(row[8])] for row in records], "tab:brutos")
table("cpu.tex", "lrrr",
      r"Referência de uma thread & $T_1/T_4$ & $E_4$ (\%) & $T_4$ (ms)",
      "Comparação CPU com o mesmo N. As duas referências permanecem separadas.",
      [[row["label"], pt(row["avg"] / summaries[2]["avg"], 4),
        pt(100 * row["avg"] / summaries[2]["avg"] / 4, 2),
        pt(summaries[2]["avg"] * 1000, 6)] for row in summaries[:2]], "tab:cpu")
table("comparacao.tex", "lrrr",
      r"Série & $T_{GPU}/T_{CPU\,1a}$ & $T_{GPU}/T_{CPU\,1b}$ & $T_{GPU}/T_{CPU\,4}$",
      "Razão entre tempos médios. Valores maiores que um indicam maior tempo "
      "da chamada GPU em relação à referência CPU da coluna.",
      [[row["label"], *[pt(row["avg"] / cpu["avg"], 3) for cpu in summaries[:3]]]
       for row in summaries[3:]], "tab:comparacao")

plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "pdf.fonttype": 42})
fig, ax = plt.subplots(figsize=(8.5, 4.2), layout="constrained")
for i, row in enumerate(summaries):
    color = "#2366a8" if row["mode"] == "CPU" else "#d4791f"
    ax.barh(i, row["avg"] * 1000, color=color, alpha=.65, height=.58)
    ax.errorbar(row["avg"] * 1000, i, xerr=row["sd"] * 1000,
                 fmt="none", ecolor="black", capsize=4)
    ax.scatter([value * 1000 for value in row["times"]], [i] * 5,
                color=color, s=25, zorder=3)
ax.set(yticks=range(len(summaries)), yticklabels=[row["label"] for row in summaries],
       xlabel="Tempo da chamada medida (ms)", xlim=(0, 15))
ax.invert_yaxis()
ax.grid(axis="x", alpha=.22)
fig.savefig(FIG / "tempos.pdf", bbox_inches="tight")
plt.close(fig)
print("Seis séries: 30 medições e três aquecimentos CPU/V100 conferidos.")
