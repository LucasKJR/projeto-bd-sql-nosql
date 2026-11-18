# Laboratório de pedidos: PostgreSQL × MongoDB

Projeto acadêmico que compara uma modelagem relacional de pedidos e vendas com documentos que incorporam os itens do pedido. O objetivo é **medir**, não pressupor, a vantagem do NoSQL em um cenário realista.

## Estado e limites

Carga e experimentos reais concluídos em 17/11/2026, com 1.000.000 de pedidos e 5.492.836 itens nos dois bancos. Integridade validada e medições brutas incluídas em `results/`. PostgreSQL venceu as três consultas iniciais. Um experimento exploratório adicional com lotes de 100 pedidos completos encontrou MongoDB ~1,72× mais rápido. Isso é uma vantagem específica de modelagem/implementação, não uma superioridade geral de NoSQL. Veja [resultados completos](docs/RESULTADOS_REAIS.md).

Este repositório não inclui o JSONL de 630 MB, a VM nem as dependências instaladas; inclui gerador, manifesto e evidências reais.

## Executar localmente

Requisitos: Python 3.11 ou superior, Docker Engine/Desktop com Docker Compose e espaço em disco disponível para a massa e para os dois bancos. Comece com uma amostra para verificar o ambiente; a entrega exige pelo menos **1.000.000 de pedidos lógicos**.

```bash
git clone https://github.com/LucasKJR/projeto-bd-sql-nosql.git
cd projeto-bd-sql-nosql
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell, em vez da linha anterior:
# .venv\Scripts\Activate.ps1
pip install -r requirements.txt
docker compose up -d --wait
python -m lab generate --count 1000000
python -m lab load
python -m lab benchmark --repetitions 10
python -m lab serve
```

Abra **http://127.0.0.1:8000** no navegador (ou a porta informada com `serve --port`). O dashboard consulta os bancos por uma API Python; não usa números estáticos como se fossem resultados reais. A aplicação e as portas dos bancos são destinadas ao uso local, não à publicação na internet. As credenciais de desenvolvimento não são apropriadas para produção.

Para verificar a geração em uma amostra separada, use `python -m lab generate --count 100 --data data-amostra`. Não carregue essa amostra no banco final antes da massa completa, pois a carga não sobrescreve bancos existentes.

Se `docker` não existir ou os bancos não iniciarem, a carga e os testes de integração ficam bloqueados. Não interprete testes de geração ou de lógica como prova de acesso aos bancos. Não use `docker compose down -v` para encerrar o projeto: essa opção remove os volumes. Para parar preservando os dados, use `docker compose stop`.

## Arquivos de evidência

A geração grava `orders.jsonl` e `manifest.json` em `data/` por padrão, incluindo contagens, tamanho e SHA-256. A carga grava `load.json` em `results/` por padrão. O benchmark grava `samples.csv` (tempos brutos) e `benchmark.json` (resumo). Consulte `python -m lab generate --help`, `load --help` ou `benchmark --help` para as opções. `--data` troca a pasta da geração/carga; `--out` troca a pasta de resultados da carga/benchmark. Preserve esses arquivos com a versão do código usada.

A geração se recusa a sobrescrever `orders.jsonl`; a carga exige bancos vazios. Se houver falha após uma etapa da carga, os dois bancos podem ficar em estados diferentes. Leia o erro e o relatório antes de tentar novamente; não apague bancos ou volumes existentes indiscriminadamente.

## O que comparar

| Consulta | Resultado de negócio | Hipótese/pergunta |
| --- | --- | --- |
| Pedido completo por ID | Cabeçalho e itens de um pedido | A incorporação dos itens evita o custo de reconstruir o pedido por junções? |
| Vendas por dia | Quantidade de pedidos concluídos e receita por dia | Como cada banco executa filtro temporal e agregação? |
| Top 10 produtos | Quantidade e receita por produto | Qual o custo de agrupar itens em tabelas ou dentro de documentos? |

Na comparação, ambos devem responder à **mesma pergunta**, sobre os mesmos pedidos, com os mesmos filtros e regras de negócio. PostgreSQL pode vencer uma ou mais consultas; isso deve constar no relatório.

## Documentação e entregas

- [Metodologia, dados e modelos](docs/METODOLOGIA.md)
- [Checklist de entrega e evidências](docs/ENTREGAS.md)

As datas de 19/11 e 24/11/2026 foram fornecidas pelo aluno. O enunciado atualizado define os requisitos; os materiais anteriores fornecem a fundamentação sobre documentos/MongoDB e o cenário de pedidos. Este código concretiza a proposta, sem converter hipóteses anteriores em resultados.

## Testes sem os bancos

```bash
python -m unittest discover -s tests
node --test static/*.test.cjs
```

Node é necessário apenas para os testes JavaScript; não é necessário para servir o dashboard. A integração real via API foi verificada em 24 requisições, com filtros, resultados vazios e equivalência dos bancos. Smoke visual desktop aprovado no Chrome nativo; mobile e filtros pela UI permanecem não verificados.

Cada benchmark recusa sobrescrever uma rodada anterior. Para repetir, use `python -m lab benchmark --out results/rodada-2`. Rodadas falhadas geram `benchmark-failure.json`; amostras parciais não são resultado concluído.

## Experimentos adicionais

`python experiment_q1.py` e `python experiment_batch.py` reproduzem os experimentos adicionais. Recusam diretórios de saída existentes: preserve/renomeie a evidência anterior antes de uma nova rodada. O benchmark padrão executa Q1–Q3; Q4 é separado e também está no dashboard.

As portas padrão do código e do Compose são PostgreSQL **55432** e MongoDB **57017**, somente localhost. `PG_DSN` e `MONGO_URI` permitem alterar os destinos. Para o ambiente já instalado no SSD, veja `docs/OPERACAO_SSD.txt`; não recarregue bancos já preenchidos.
