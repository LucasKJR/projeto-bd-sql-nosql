# Laboratório de pedidos: PostgreSQL × MongoDB

Projeto acadêmico que compara uma modelagem relacional de pedidos e vendas com documentos que incorporam os itens do pedido. O objetivo é **medir**, não pressupor, a vantagem do NoSQL em um cenário realista.

## Estado e limites

Carga e experimentos reais concluídos em 17/11/2026, com 1.000.000 de pedidos e 5.492.836 itens nos dois bancos. Integridade validada e medições brutas incluídas em `results/`. PostgreSQL venceu as três consultas iniciais. Um experimento exploratório adicional com lotes de 100 pedidos completos encontrou MongoDB ~1,72× mais rápido. Isso é uma vantagem específica de modelagem/implementação, não uma superioridade geral de NoSQL. Veja [resultados completos](docs/RESULTADOS_REAIS.md).

O repositório não contém o JSONL de 630 MB, volumes, VM ou dependências instaladas. A massa é sintética e reproduzível; o gerador, o manifesto e as evidências de medição acompanham o código.

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
python -m lab generate --count 1000000 --seed 42 --data data-local
python -m lab load --data data-local --out results/carga-local
python -m lab serve --port 8765
```

### Telas locais

| Tela | Endereço | O que mostra |
| --- | --- | --- |
| Dashboard ao vivo | [`/`](http://127.0.0.1:8765/) | Indicadores e consultas Q1–Q4, com tempos da execução atual. |
| Explorar dados | [`/explorer`](http://127.0.0.1:8765/explorer) | Tabelas PostgreSQL e documentos MongoDB, com filtros e seleção de campos. |
| Comparar | [`/compare`](http://127.0.0.1:8765/compare) | Mesmos filtros e campos nos dois bancos; verifica IDs e valores da página e mostra tempos lado a lado. |
| Benchmark registrado | [`/benchmark`](http://127.0.0.1:8765/benchmark) | Medianas arquivadas de Q1–Q4, sem conectar aos bancos. |

Para abrir só o benchmark registrado, basta iniciar `python -m lab serve --port 8765`, sem Docker ou dependências de banco. As demais telas consultam os dois bancos locais. Não exponha o servidor ou as portas de banco à internet: as credenciais de desenvolvimento não são apropriadas para produção.

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
- [Slides da apresentação](apresentacao/Projeto_BD_Slides.pdf)
- [Explorar dados](docs/EXPLORADOR.md), [Comparar](docs/COMPARAR.md) e [benchmark registrado](docs/BENCHMARK_HISTORICO.md)

As datas de 19/11 e 24/11/2026 foram fornecidas pelo aluno. O enunciado atualizado define os requisitos; os materiais anteriores fornecem a fundamentação sobre documentos/MongoDB e o cenário de pedidos. Este código concretiza a proposta, sem converter hipóteses anteriores em resultados.

## CRUD equivalente

Com os dois bancos ativos, rode `python -m lab crud-demo`. O roteiro e a comparação dos comandos estão em [CRUD de demonstração](docs/CRUD_DEMONSTRACAO.md). O CRUD opera somente sobre um pedido criado para a demonstração, em estruturas separadas da massa.

## Testes sem os bancos

```bash
python -m unittest discover -s tests
node --test static/*.test.cjs
```

Node é necessário apenas para os testes JavaScript; não é necessário para servir o dashboard. Os relatórios em `results/` registram verificações anteriores em Chrome desktop e emulado para celular, CRUD isolado e equivalência das consultas. Testes unitários de um novo checkout não confirmam, sozinhos, a integração com bancos.

Cada benchmark recusa sobrescrever uma rodada anterior. Para repetir, use `python -m lab benchmark --out results/rodada-2`. Rodadas falhadas geram `benchmark-failure.json`; amostras parciais não são resultado concluído.

## Experimentos adicionais

`python experiment_q1.py` e `python experiment_batch.py` reproduzem os experimentos adicionais. Recusam diretórios de saída existentes: preserve/renomeie a evidência anterior antes de uma nova rodada. O benchmark padrão executa Q1–Q3; Q4 é separado e também está no dashboard.

As portas padrão do código e do Compose são PostgreSQL **55432** e MongoDB **57017**, somente localhost. `PG_DSN` e `MONGO_URI` permitem alterar os destinos. Consulte [operação local](docs/OPERACAO_SSD.txt); não recarregue bancos já preenchidos.
