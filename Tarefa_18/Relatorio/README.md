# Relatório da Tarefa 18

[`relatorio.pdf`](relatorio.pdf) é o documento para leitura, com explicação dos
conceitos, ilustrações TikZ, tabela de resultados, gráfico e códigos completos
nos apêndices. [`overleaf.zip`](overleaf.zip) é o projeto independente.

**Situação da análise:** os logs mostram somas corretas e permitem comparar
os tempos registrados. Eles não comprovam que o modo chamado GPU executou
na GPU. O relatório explica a diferença entre presença do hardware e offload,
o mapeamento de ponteiros e as limitações dos binários e da compilação enviados.
Por isso, documenta o progresso e a pendência de confirmação; não apresenta
os tempos como uma comparação final e verificada de CPU contra GPU.

## Dados usados

- Fontes e registros do commit `e17b7d0`, presentes em `main` na revisão `9118003`.
- Sete logs: três séries CPU e quatro séries declaradas GPU.
- 35 tempos medidos, quatro aquecimentos em processos separados, todos com
  `N=10000000`, tolerância `1e-9` e zero erros registrados.
- Os nomes V100 e H200 vêm do `nvidia-smi` dos logs, não de uma confirmação
  feita dentro da região target.
- Hardware de referência transcrito pelo autor da página do NPAD; o trecho
  está em `dados/hardware_referencia.txt`. O modelo de CPU de `service3`
  não é inferido a partir dessa referência.
- Inspeção estática dos executáveis recebidos, sem executá-los e sem novas
  medições. Os hashes estão em `dados/fontes_e_registros.sha256`.

O código principal e os resultados originais, na pasta superior, foram
preservados. `codigos/diagnostico_offload.c` é um apoio novo, ainda não executado
no NPAD. Deve ser compilado com suporte à GPU e executado dentro de uma
alocação; seu sucesso confirma sua própria região target, não retrospectivamente
as execuções históricas nem o tratamento de dados do programa de soma.

## Overleaf

1. Importe `overleaf.zip` como um novo projeto.
2. Selecione `main.tex` e o compilador **pdfLaTeX**.
3. Compile normalmente. Não precisa executar Python nem habilitar shell escape.

O preâmbulo é completo e todos os caminhos são relativos a esta pasta.
Mantenha `codigos/`, `dados/`, `diagramas/`, `figuras/`, `tabelas/` e
`gerar_figuras.py`. Os fontes são incluídos por `\lstinputlisting` sem limites
de linhas. Os registros e a inspeção também estão integrais no próprio PDF.

## VS Code ou terminal no Ubuntu

```bash
sudo apt install latexmk texlive-latex-base texlive-latex-recommended \
  texlive-latex-extra texlive-pictures texlive-lang-portuguese lmodern
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex
```

Abra `Tarefa_18/Relatorio` no VS Code com LaTeX Workshop. A configuração em
`.vscode/` coloca os temporários em `build/`. Depois de editar, revise
`build/main.pdf` e copie para `relatorio.pdf` para atualizar a versão publicada.

## Gráfico e tabelas

`gerar_figuras.py` lê os sete logs, verifica parâmetros e contagens, extrai os
39 registros e calcula as médias e os desvios amostrais das 35 medições.
Não executa os programas C. Para regenerar os artefatos:

```bash
python gerar_figuras.py
```

Requer Matplotlib apenas para essa regeneração. A compilação LaTeX usa a
figura e as tabelas já incluídas. As barras representam um desvio padrão
amostral. As séries de uma thread CPU permanecem separadas, e não se calcula
um speedup entre GPUs sem confirmar o dispositivo utilizado.

## Para consolidar a comparação no NPAD

1. Registrar compilador, flags, módulos, alocação, CPU e dispositivos disponíveis.
2. Confirmar suporte às diretivas e à GPU, com o diagnóstico e a própria soma.
3. Especificar as regiões dos vetores ou documentar um modelo de memória válido.
4. Repetir aquecimento e medições no mesmo processo se a intenção for medir
   um contexto já aquecido, declarando quais custos continuam no intervalo.
5. Salvar os novos scripts e logs separadamente e então atualizar o relatório.

Reservar quatro GPUs não divide automaticamente a soma entre elas. O código
analisado possui uma região target e não implementa distribuição entre GPUs.
