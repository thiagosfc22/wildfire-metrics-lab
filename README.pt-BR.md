# Wildfire Metrics Lab

**🇧🇷 Português** · [🇬🇧 English](README.md)

"Incêndios florestais sobem 250%" é uma manchete que você provavelmente viu
neste verão. Quase sempre ela conta o **número de incêndios**, e contar
incêndios não mede quanto território ardeu. São dois números diferentes, e em 45
anos de dados oficiais europeus eles mal se movem juntos.

Este repositório prova isso na fonte, em cerca de 100 linhas de Python da
biblioteca padrão. Sem pandas, sem openpyxl, sem chave de API — um `.xlsx` é um
zip de XML, então `zipfile` e `ElementTree` bastam.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="chart-dark.png">
  <img alt="Dois painéis empilhados com eixo x compartilhado, Portugal 1980-2024. Em cima: área queimada em hectares, com pico de 539.921 ha em 2017. Embaixo: número de incêndios, em queda desde meados dos anos 1990. O trecho de 2023 para 2024 está destacado em vermelho nos dois: área +299%, incêndios -17%." src="chart-light.png">
</picture>

## O achado

Correlação entre *número de incêndios* e *área queimada*, 1980–2024:

| País | r | O que significa |
|---|---|---|
| Espanha | **0,18** | nenhuma — a contagem não diz praticamente nada |
| Grécia | 0,41 | fraca |
| Portugal | 0,42 | fraca |
| França | 0,65 | moderada |
| Itália | 0,75 | moderada |

Portugal tem o exemplo mais limpo. De 2023 para 2024 o número de incêndios
**caiu 17%** enquanto a área queimada **subiu 299%** — 34.510 → 137.651
hectares. Menos incêndios, quatro vezes mais território. E não é um caso
isolado: a mesma inversão aparece em Portugal em 2010, 2012, 2013, 2016 e 2020.

## Por que isto é um repositório de engenharia de dados

Porque nada no stack pega esse erro. O pipeline, o data warehouse, o dashboard e
o modelo calculam fielmente aquilo que você pediu. A query está certa. O número
está certo. A conclusão está errada — e o único ponto onde isso poderia ter sido
percebido foi o momento em que alguém escolheu qual coluna contar.

A mesma armadilha, com roupa menos dramática: contar pedidos em vez de receita,
contar erros em vez de usuários afetados, contar jobs em vez de horas de
compute. **A definição da métrica é a análise.** Todo o resto é aritmética.

## O que tem aqui

| Arquivo | O que faz |
|---|---|
| [`fetch_effis.py`](fetch_effis.py) | Baixa o workbook oficial do EFFIS e converte as duas planilhas em CSV. Só stdlib. |
| [`analyze.py`](analyze.py) | Correlação por país, mais todos os anos em que as duas métricas foram em direções opostas. |
| [`make_chart.py`](make_chart.py) | Gera o gráfico em HTML e exporta os PNGs via Chrome headless. |
| [`chart.html`](chart.html) | Versão interativa — hover, claro/escuro e tabela com os 45 anos. |
| [`sample_output/analysis.txt`](sample_output/analysis.txt) | Saída de uma execução real, pra ler os resultados sem rodar nada. |
| [`data/`](data/) | Os dois CSVs já processados. |

## Rodar

```bash
python3 fetch_effis.py && python3 analyze.py && python3 make_chart.py
```

Python 3.9+. Sem dependências. Chrome ou Chromium é opcional — serve só pra
exportar os PNGs, e o gráfico em HTML é escrito de qualquer forma.

## Sobre o gráfico

Área queimada e número de incêndios são grandezas de escalas diferentes, então
ficam em dois painéis empilhados com eixo x compartilhado, e não num gráfico de
eixo duplo. Isso é deliberado: dois eixos y no mesmo plot inventam uma
correlação que o dado não tem — que é exatamente o erro de que este repositório
trata.

## Os dados

Fonte: **[EFFIS](https://forest-fire.emergency.copernicus.eu/)** — European
Forest Fire Information System, parte do Copernicus Emergency Management
Service, operado pelo Joint Research Centre da Comissão Europeia. O arquivo é o
workbook anual de estatísticas (`report_2024.xlsx`), cobrindo 1980–2024 em 31
países, em duas planilhas: hectares queimados e número de incêndios.

Licença **CC BY 4.0**. Veja [`NOTICE`](NOTICE) para a atribuição e as alterações
feitas nos dados originais.

Dois limites que vale conhecer antes de citar qualquer coisa daqui:

- O mapeamento de área queimada do EFFIS **só detecta incêndios a partir de
  aproximadamente 30 hectares**. "Área queimada" aqui significa área de
  incêndios grandes, não tudo que ardeu.
- O workbook publicado **termina em 2024**. Para a temporada corrente é preciso
  o portal de estatísticas do EFFIS ou o
  [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/), que serve focos de calor
  quase em tempo real e exige uma chave gratuita.

## Licença

Código: [MIT](LICENSE). Dados: CC BY 4.0, © União Europeia, veja [`NOTICE`](NOTICE).
