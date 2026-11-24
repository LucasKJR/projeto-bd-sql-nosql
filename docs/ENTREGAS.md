# Checklist final e evidências

Projeto 3 (NoSQL), cenário de pedidos e vendas. Este checklist registra **verificações técnicas**, não a submissão ou a nota.

## Rubrica de entregas

| Item | Verificação | Evidência |
| --- | --- | --- |
| Massa, carga e documentação (19/11; 1,0 ponto) | Concluído tecnicamente: 1.000.000 de pedidos lógicos e 5.492.836 linhas de itens; mesma massa nos dois bancos, com contagens e soma dos totais reconciliadas. | `data/manifest.json`, `results/load.json`, [metodologia](METODOLOGIA.md), [resultados](RESULTADOS_REAIS.md). |
| Experimentos válidos e vantagem NoSQL (24/11; 2,0 pontos) | Concluído tecnicamente: Q1–Q3, dez medições por banco/consulta; PostgreSQL venceu as três. Q4 exploratório (lote de 100 pedidos) apresentou MongoDB 1,72× mais rápido em mediana, com 300 amostras por banco. | `results/rodada-1`, `results/q4-lotes-100-pedidos`, `results/plans-indexes.json`; [resultados e limites](RESULTADOS_REAIS.md). |
| Dashboard (24/11; 2,5 pontos) | Implementado com consultas reais nos dois bancos, filtros de datas e ID, alternância de fonte e tempos lado a lado, inclusive Q4. O ganho é evidência experimental; uma medição ao vivo pode variar. | `results/dashboard-api-qa.json`, `results/dashboard-final-qa.json`; [como iniciar](OPERACAO_SSD.txt). |
| Modelagem e CRUD equivalente | Modelo relacional e documental, com CRUD isolado do benchmark nos dois bancos. | [Modelagem](METODOLOGIA.md), [roteiro CRUD](CRUD_DEMONSTRACAO.md), `results/crud-demo.json`. |
| Pesquisa e comparação teórica | Fundamentação e escolhas de modelagem no projeto; complementar com o material teórico do grupo. | [Metodologia](METODOLOGIA.md) e material de apresentação. |

## O que falta fora do código

- Usar os slides finais na apresentação e executar a demonstração ao vivo perante a turma/professor.
- Fazer a entrega no canal solicitado e verificar a versão do repositório. Este checklist não atesta submissão, publicação nem presença na apresentação.

## Roteiro de demonstração

1. Apresentar os dois modelos e a evidência da carga: pedido lógico = cabeçalho com itens.
2. Executar `.venv/bin/python -m lab crud-demo`, mostrar o antes/depois e a releitura vazia.
3. Abrir `http://127.0.0.1:8765/`, alterar o período e ID, clicar **Consultar bancos**, e trocar a fonte para mostrar as respostas equivalentes.
4. Mostrar Q4 na comparação ao vivo e abrir as medianas de 300 amostras por banco para explicar a vantagem e a variabilidade.
5. Explicar por que o PostgreSQL venceu Q1–Q3, sem generalizar Q4 como superioridade de todo NoSQL.

## Pacote portátil

Código, README, modelos, scripts, consultas, índices, manifesto, amostras e evidências reais. O arquivo JSONL de 630 MB e o ambiente instalado não acompanham o ZIP: a mesma massa é reproduzível com o gerador e a semente 42, conforme o README. A massa real permanece no SSD.
