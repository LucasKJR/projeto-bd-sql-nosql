# Resultados reais e limites

Execução: 17/11/2026. Mesma massa sintética seed 42: 1.000.000 pedidos lógicos, 5.492.836 itens, total 108.833.431.885 centavos; JSONL 630.043.078 bytes. SHA-256: d137569dcd47d8164c972f5d25ea2ace0c09b0179111cd9fd729ad60110437f8. Datas UTC, dinheiro inteiro e snapshots iguais.

## Ambiente e validação
Mac arm64, 16 GiB RAM, 10 CPUs lógicas. Ambos os bancos na mesma VM Colima isolada no SSD externo: 2 vCPU, 3 GiB RAM. PostgreSQL 17.11 e MongoDB 8.3.17. Python e drivers em requirements-lock.txt; configuração em results/environment.json. Sem carga concorrente deliberada, mas sem isolamento completo do host. Cache aquecido; não é teste de cache frio. Não generalizar números para produção.

Carga validada: contagens e somas coincidem com manifesto (`results/load.json`). PostgreSQL levou 440,85 s; MongoDB 53,94 s. Estratégias de carga/índices/constraints diferem, portanto essa diferença NÃO isola vantagem do motor. Espaço: PG 795.072.179 bytes via pg_database_size; Mongo totalSize 213.544.960 bytes. Métricas de armazenamento não são perfeitamente equivalentes.

## Baseline preservado: Q1–Q3
Período [2025-01-01, 2026-01-01), pedido ID 1. Duas execuções de aquecimento separadas e dez medidas por consulta/banco. Ordem dos bancos alternada. Cronômetro inclui cursor completo, normalização e serialização JSON equivalente; exclui conexão. Resultados comparados integralmente.

| Consulta | PostgreSQL mediana ms | MongoDB mediana ms |
|---|---:|---:|
| Q1 pedido completo | 0,9977 | 1,0971 |
| Q2 vendas diárias | 1382,75 | 2737,60 |
| Q3 top 10 produtos | 3595,27 | 8953,05 |

PostgreSQL venceu as três consultas. Amostras e IQR em `results/rodada-1`. O IQR de Q3 PostgreSQL foi alto (~3998 ms); interpretar variabilidade. A versão inicial de Q1 Mongo usava aggregate com match/project (`mongo_pipeline('order',...)` ainda preservado em lab/db.py). O código atual usa find por ID e renomeia _id no cliente; assim uma nova execução padrão não replica exatamente a implementação original de Q1. Q2/Q3 não mudaram.

## Verificação adicional Q1
100 IDs aleatórios (seed 20261117), dez repetições cada, 1.000 amostras/banco, aquecimento por ID, conexões persistentes. Com find direto Mongo ainda não venceu: PG 1,0594 ms (IQR 0,2706), Mongo 1,1210 ms (IQR 0,2856). Diferença pequena e distribuições sobrepostas. Evidência em `results/q1-direto-100-ids`.

## Q4 exploratória: exportação administrativa de 100 pedidos
Escolhida DEPOIS da baseline negativa, explicitamente exploratória. Recupera 100 IDs consecutivos com cabeçalho e itens, sem filtrar status/data. Os IDs não representam sequência temporal, pois as datas são aleatórias. Inclui pedidos criados, concluídos e cancelados: não chamar de expedição.

30 inícios aleatórios sem reposição (seed 20261117), dez repetições por início, 300 amostras/banco. Aquecimento separado por lote e alternância dos bancos. PostgreSQL usa faixa da PK, join e jsonb_agg; Mongo find por faixa da PK em documentos incorporados. Mesmos 100 pedidos, mesma ordenação e conteúdo comparados em todas as execuções.

| Fonte | Mediana ms | IQR ms |
|---|---:|---:|
| PostgreSQL | 10,11875 | 1,435094 |
| MongoDB | 5,880854 | 0,886583 |

Mongo ~1,72× mais rápido, ou ~41,9% menor latência mediana. Venceu medianas em 30/30 lotes (razão por lote 1,564–1,946). Evidências em `results/q4-lotes-100-pedidos`; script `experiment_batch.py`. Vantagem da implementação/modelagem e caminho até JSON medidos, não prova isolada do motor nem de todo NoSQL. Não removemos índices PostgreSQL. Planos reais e índices estão em `results/plans-indexes.json` (lote ID1–100, coleta posterior separada das amostras).

## Dashboard e QA
Dashboard executa quatro consultas reais nos dois bancos, com intervalo temporal para Q2/Q3 e ID/início do lote para Q1/Q4. Tempo mostrado é da requisição atual, não substitui o benchmark repetido. Padrão UI janeiro de 2025, diferente da baseline anual. Falhas não geram números fictícios.

12 testes Python e 3 Node passaram. 24 requisições reais à API passaram, com dois intervalos e IDs diferentes, intervalo vazio/ID inexistente, resultados equivalentes e fonte inválida HTTP400. `results/dashboard-api-qa.json`. Smoke visual desktop aprovado posteriormente no Chrome nativo: layout íntegro, oito consultas concluídas, KPIs/tabelas/ranking/Q1/Q4 e comparação renderizados. Mobile e manipulação dos filtros pela UI não foram testados; teste interrompido ao detectar interação do usuário. Não foi simulado desligamento dos bancos durante essa execução.
