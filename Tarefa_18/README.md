# Tarefa 18 — soma de vetores em CPU e V100 com OpenMP

O [relatório em PDF](Relatorio/relatorio.pdf) apresenta os conceitos, a
implementação e a comparação CPU/V100, com fontes e logs completos nos
apêndices. O [projeto Overleaf](Relatorio/overleaf.zip) pode ser importado
diretamente. Consulte as [instruções do relatório](Relatorio/README.md).

A análise utiliza os três logs CPU e os três que identificam Tesla
V100-SXM2-16GB: `GPUa.out`, `GPUb.out` e `resultado_gpu_2134904.out`.
São 30 medições e três aquecimentos. Os demais registros permanecem como
histórico e não entram nesta comparação.

A média CPU com quatro threads foi de aproximadamente 5,379 ms; na V100,
ficou entre 12,176 e 13,484 ms. O relatório discute a vantagem CPU para essa
soma simples considerando o custo da chamada completa e a baixa quantidade
de cálculo por dado movimentado. Como os logs não medem transferência e
kernel separadamente, a análise dessas parcelas é qualitativa.

O job GPU utiliza `OMP_TARGET_OFFLOAD=MANDATORY`. O relatório explica sua
função, os pressupostos de suporte a offload e a diferença entre exigir
o dispositivo, tratar os dados e distribuir o vetor entre várias GPUs.

O enunciado está em [`requisitosTarefa18.txt`](requisitosTarefa18.txt).
`jobs.sh` submete dois jobs e compila apenas `t18.c`, que já inclui
`aux18.c` e `somas.c`. O script apresentado configura uma thread CPU;
`CPU4.out` registra a variação com quatro threads.
