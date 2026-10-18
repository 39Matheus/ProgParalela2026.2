# Relatório da Tarefa 18 — CPU e V100

[`relatorio.pdf`](relatorio.pdf) contém a análise, cinco ilustrações TikZ,
gráfico, tabelas e os códigos e logs completos nos apêndices.
[`overleaf.zip`](overleaf.zip) é o projeto independente para o Overleaf.

## Conjunto de dados

Esta revisão utiliza:

- CPU: `CPU1a.out`, `CPU1b.out` e `CPU4.out`.
- V100: `GPUa.out`, `GPUb.out` e `resultado_gpu_2134904.out`.

São 30 medições e três aquecimentos. Registros de outras classes de GPU
permanecem como histórico na pasta superior e não entram neste relatório,
no ZIP ou nas estatísticas. Os fontes utilizados são `t18.c`, `aux18.c`,
`somas.c` e `jobs.sh`, incluídos integralmente nos apêndices.

## Resultados e interpretação

A média CPU com quatro threads foi de aproximadamente 5,379 ms; na V100,
de 12,176 a 13,484 ms. A CPU foi mais rápida em todas as séries selecionadas.

A análise considera o tempo da chamada completa, com os custos de offload,
e a baixa quantidade de cálculo por dado movimentado. Os logs não separam
envio, kernel e retorno, portanto não são atribuídas porcentagens de tempo
a essas parcelas nem se calcula uma largura de banda com o tempo total.

Os 120 MB apresentados são o volume de dados úteis de duas entradas e uma
saída em um modelo de transferência explícita, não uma medição de tráfego.
O fonte não contém cláusulas `map` explícitas; o modelo efetivo de acesso
depende do compilador e do runtime. O código foi preservado na análise.

O job GPU contém `OMP_TARGET_OFFLOAD=MANDATORY`. O texto explica a política
OpenMP, seus pressupostos de suporte a offload e a distinção entre exigir
o dispositivo, tratar os dados e distribuir trabalho entre várias GPUs.

CV é o coeficiente de variação: mede a dispersão relativa dos tempos e não
o erro numérico da soma. Sua definição e um exemplo aparecem no relatório.

## Overleaf

1. Importe `overleaf.zip` como um novo projeto.
2. Selecione `main.tex` e o compilador **pdfLaTeX**.
3. Compile normalmente, sem executar Python nem habilitar shell escape.

O preâmbulo é completo. Preserve `codigos/`, `dados/`, `diagramas/`, `figuras/`,
`tabelas/` e `gerar_figuras.py`. A inclusão dos códigos usa `\lstinputlisting`,
sem cortes. Os seis logs também estão integrais no PDF.

## VS Code ou terminal no Ubuntu

```bash
sudo apt install latexmk texlive-latex-base texlive-latex-recommended \
  texlive-latex-extra texlive-pictures texlive-lang-portuguese lmodern
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex
```

Abra `Tarefa_18/Relatorio` com LaTeX Workshop. Os temporários vão para `build/`.
Após uma edição, revise `build/main.pdf` e copie a versão final para
`relatorio.pdf` para atualizar a cópia publicada.

## Regeneração dos artefatos

`gerar_figuras.py` usa uma lista explícita dos seis arquivos e verifica a
identificação V100 nos logs GPU. Ele gera os CSVs, o gráfico e as tabelas sem
executar os programas C. Para regenerar:

```bash
python gerar_figuras.py
```

Matplotlib é necessário apenas nessa etapa. As barras representam um desvio
padrão amostral. Os aquecimentos ficam fora das médias; as séries são mantidas
separadas. Os hashes e a proveniência dos arquivos estão em `dados/` e no PDF.
