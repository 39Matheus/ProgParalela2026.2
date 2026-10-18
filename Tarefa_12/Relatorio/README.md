# Relatório da Tarefa 12

O documento de entrega é [`relatorio.pdf`](relatorio.pdf). Ele contém a
explicação, quatro figuras de análise com múltiplos painéis, três ilustrações
TikZ e os apêndices com todos os programas e scripts,
45 resumos estatísticos e 270 saídas integrais das simulações. O professor não
precisa abrir o GitHub para consultar os códigos ou as medições.

O estilo segue a Tarefa 11 e os relatórios anteriores do autor. A análise usa
exclusivamente a campanha `execucao_20261018T180336Z_38920`, enviada na revisão
`99d6166`: 225 medições e 45 aquecimentos no NPAD. Nenhuma nova simulação foi
executada para preparar este documento. Os diagnósticos são comparados como
registrados; o relatório não afirma uma comparação célula a célula sem os
respectivos campos nesta campanha.

## Overleaf

1. Baixe [`overleaf.zip`](overleaf.zip) e importe como um novo projeto.
2. Use `main.tex` como documento principal e **pdfLaTeX** como compilador.
3. Compile. As figuras e tabelas já estão prontas; não precisa executar
   Python, instalar bibliotecas Python ou habilitar shell escape.

O preâmbulo é completo e usa pacotes comuns do TeX Live, incluindo TikZ e
listings. Os caminhos são relativos a esta pasta. Os códigos dos apêndices
são incluídos por `\lstinputlisting`, sem limites de linhas e sem depender
das pastas superiores do repositório. Preserve `codigos/`, `diagramas/`,
`figuras/`, `tabelas/`, `dados/` e `gerar_figuras.py` ao importar.

Os `.log` em `dados/` são **registros dos experimentos**, não temporários do
LaTeX. Eles fazem parte do projeto e devem ser mantidos.

## VS Code ou terminal no Ubuntu

```bash
sudo apt install latexmk texlive-latex-base texlive-latex-recommended \
  texlive-latex-extra texlive-pictures texlive-lang-portuguese lmodern
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex
```

A extensão LaTeX Workshop pode usar a configuração em `.vscode/`. A pasta
de trabalho deve ser `Tarefa_12/Relatorio`. A saída é `build/main.pdf`; para
atualizar a cópia publicada, copie-a para `relatorio.pdf` após a revisão.

## Conteúdo e reprodução

- `main.tex`: preâmbulo, texto e inclusão dos apêndices completos.
- `diagramas/`: ilustrações TikZ das versões, sincronização e matriz de testes.
- `codigos/`: os nove fontes e scripts da Tarefa 12, preservados integralmente.
- `dados/`: cópias dos CSVs, configuração, hardware, hashes e compilação;
  `logs_completos.txt` concatena os 270 logs com seus nomes originais.
- `figuras/` e `tabelas/`: artefatos prontos para a compilação.
- `gerar_figuras.py`: regenera os artefatos e confere médias/desvios a partir
  das 225 medições, sem executar testes de desempenho.

Para regenerar gráficos e tabelas, execute `python gerar_figuras.py` em um
ambiente com NumPy e Matplotlib e recompile. Alterar os dados exige revisar
também os valores e interpretações escritos no texto.

As barras dos tempos representam um desvio padrão amostral. O speedup forte
usa a referência de uma thread da própria versão; o ganho entre versões usa
v0 com a mesma carga e equipe. A diagonal fraca contém apenas os pontos
`(1,200)`, `(4,400)` e `(16,800)`, com passos fixos, não tempo físico fixo.

O PDF é longo porque incorpora os códigos e os registros completos. O texto
principal permanece separado dos apêndices, navegáveis pelos marcadores do
leitor de PDF. O ZIP não contém os temporários de compilação nem uma cópia
recursiva de si mesmo.
