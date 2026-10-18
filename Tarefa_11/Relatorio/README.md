# Relatório da Tarefa 11

Abra `main.tex`. Ele usa o estilo do relatório da Tarefa 10 e contém o preâmbulo
completo. `relatorio.pdf` é a versão já compilada; `overleaf.zip` é o projeto
independente para importar no Overleaf.

O conteúdo descreve os fontes e os resultados da revisão `5192499`, incluindo
os 54 tempos de execução. O hardware é o mesmo informado no apêndice da Tarefa
10, conforme confirmação do autor; o GCC informado é o 13.3.0 do Ubuntu.

O PDF agora inclui diagramas TikZ e apêndices com os fontes **completos** da
implementação e de `Old/`, incluindo os dois visualizadores, além do gerador
de figuras. Os códigos são inseridos por `\lstinputlisting`, sem limites de
linhas. Também contém as 54 medições brutas, os 101 diagnósticos e os metadados.
Assim, o professor pode consultar o material apenas pelo PDF entregue.

## Overleaf: caminho mais simples

1. Baixe `overleaf.zip` pelo botão de download do arquivo no GitHub.
2. No Overleaf, crie um projeto pela opção de enviar/importar um arquivo ZIP.
3. Selecione `main.tex` como documento principal e use **pdfLaTeX**.
4. Compile normalmente. Não é necessário instalar Python, rodar scripts ou
   habilitar `shell escape` para compilar o relatório.

Os arquivos `figuras/*.pdf` e `tabelas/*.tex` já estão prontos.
Preserve esses diretórios ao importar o projeto.

## VS Code no Ubuntu

Instale os pacotes LaTeX uma vez:

```bash
sudo apt update
sudo apt install latexmk texlive-latex-base texlive-latex-recommended \
  texlive-latex-extra texlive-pictures texlive-lang-portuguese lmodern
```

Instale a extensão **LaTeX Workshop**, de James Yu, e abra **esta pasta**
(`Tarefa_11/Relatorio`) no VS Code. A configuração em `.vscode/` compila com
pdfLaTeX/latexmk e coloca os temporários em `build/`.

Pelo terminal, dentro desta pasta:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex
```

O resultado estará em `build/main.pdf`. O `relatorio.pdf` da raiz é uma cópia
da versão revisada; depois de editar o texto, substitua-o pelo PDF recompilado
se quiser atualizar também a cópia publicada no GitHub.

A compilação LaTeX não depende do ambiente virtual Python da simulação.
Erros de `.sty` não encontrado indicam pacotes TeX ausentes, não um `.env`.

## GitHub e sincronização com Overleaf

O VS Code pode editar estes arquivos no mesmo repositório Git dos códigos.
A integração oficial **Overleaf–GitHub** é um recurso Premium (também pode
estar incluído em acesso institucional); os envios e recebimentos são manuais
na interface do Overleaf.

Essa integração conecta um projeto a um repositório, e não somente a esta
subpasta. Como o repositório da disciplina contém ambientes `.venv`, binários
e muitos frames, importar todo o repositório não é o caminho recomendado.
O ZIP desta pasta permite começar sem uma assinatura de sincronização.
Se desejar sincronização oficial depois, prefira um repositório dedicado ao
relatório. Não é necessário fazer isso para usar o projeto atual.

Evite editar simultaneamente a mesma versão no Overleaf e no VS Code sem
sincronizar: escolha uma cópia principal para cada rodada de revisão.

Documentação oficial:

- [Overleaf: GitHub synchronization](https://docs.overleaf.com/integrations-and-add-ons/git-integration-and-github-synchronization/github-synchronization)
- [LaTeX Workshop: instalação](https://github.com/James-Yu/LaTeX-Workshop/wiki/Install)

## Dados, figuras e código de referência

- `dados/tempos.csv`, `resumo.csv`, `configuracao.txt`: cópias dos resultados
  enviados pelo autor em `Tarefa_11/resultados_openmp/`.
- `dados/validacao_numerica.csv`: medidas calculadas dos 101 frames enviados
  pelo autor, com malha 80 × 80 e modo 2.
- `dados/campo_inicial.csv`, `campo_final.csv`: primeiro e último frames.
- `dados/metadata_visualizacao.txt`: parâmetros da execução visual.
- `dados/estatisticas.csv`: médias, desvios padrão amostrais, speedups sobre a
  referência comum e coeficientes de variação derivados dos tempos brutos.
- `codigos/`: cópias dos cinco fontes da revisão analisada e dos quatro arquivos
  da referência `Old/`. Não substituem os fontes principais, na pasta superior.
- `diagramas/`: ilustrações TikZ do estêncil e do particionamento dos laços.
- `gerar_figuras.py`: gera as quatro figuras e as tabelas, sem executar testes
  nem simulações. Requer NumPy e Matplotlib somente se for executado de novo.

Para regenerar as figuras após atualizar os dados, use um ambiente Python com
essas dependências e execute `python gerar_figuras.py`. Recompile o LaTeX em
seguida. As interpretações e os números escritos no texto precisam ser revistos
manualmente se forem incluídos novos experimentos.

Os gráficos mantêm todas as medições, inclusive as de maior dispersão. As
barras dos tempos mostram **um desvio padrão amostral**, não intervalos de
confiança. O speedup usa sempre `normal / 1 thread / static` como referência.
