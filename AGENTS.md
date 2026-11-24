# Guia do projeto para agentes de IA

## Objetivo e ordem de leitura

Este é um laboratório acadêmico local de PostgreSQL × MongoDB, não um sistema de produção nem um projeto de agentes de IA. Compare modelos de pedidos/vendas sobre a mesma massa sintética e meça as diferenças sem escolher artificialmente um vencedor.

Antes de alterar código, leia `README.md`, `docs/METODOLOGIA.md` e `docs/RESULTADOS_REAIS.md`. Consulte `docs/ENTREGAS.md` para requisitos, `docs/QA.txt` para verificações anteriores e os arquivos em `results/` para evidências. Distinga sempre resultados históricos, comportamento do código atual e testes que você próprio executou.

## Arquitetura e mapa do código

```text
CLI: python -m lab
  ├─ generate → JSONL + manifesto SHA-256
  ├─ load → PostgreSQL (tabelas) + MongoDB (documentos)
  ├─ benchmark → consultas equivalentes → CSV bruto + JSON de resumo
  ├─ crud-demo → pedido sintético em namespaces isolados
  └─ serve → dashboard estático → GET /api/query → lab.db.run
                                               ├─ PostgreSQL
                                               └─ MongoDB
```

| Local | Responsabilidade |
| --- | --- |
| `lab/__main__.py` | CLI e opções de geração, carga, benchmark, CRUD de demonstração e servidor. |
| `lab/core.py` | Geração sintética determinística, validação de filtros e estatísticas. |
| `lab/db.py` | Schema SQL, consultas/pipelines, conexões, normalização e cronômetro. |
| `lab/workflow.py` | JSONL/manifesto, carga com validação e benchmark Q1–Q3. |
| `lab/server.py` | `ThreadingHTTPServer` local, arquivos estáticos e API real. |
| `static/` | Dashboard, Explorar, Comparar e Benchmark histórico HTML/CSS/JS sem etapa de build; testes Node. |
| `tests/` | Testes Python de lógica, consultas, regressões e servidor. |
| `experiment_q1.py`, `experiment_batch.py` | Experimentos adicionais Q1 direta e Q4 em lotes. |
| `compose.yaml` | PostgreSQL e MongoDB, volumes persistentes e healthchecks. |
| `data/manifest.json`, `results/`, `docs/` | Manifesto, medições e documentação da entrega. |

PostgreSQL usa `customers`, `products`, `orders` e `items` com chaves/constraints; MongoDB usa coleções de clientes, produtos e pedidos com itens incorporados. Os nomes são sintéticos. Valores monetários são inteiros em centavos e datas são UTC. Não troque essas convenções silenciosamente.

### Consultas e API

- Q1 `order`: pedido completo por ID.
- Q2 `daily`: pedidos concluídos e receita diária no período `[start, end)`.
- Q3 `top`: dez produtos por quantidade, com desempate por receita e ID, no mesmo período/status.
- Q4 `batch`: até 100 pedidos a partir do ID, sem filtro temporal/status. É exportação administrativa, não expedição.

Exemplo com bancos carregados e servidor ativo:

```bash
curl 'http://127.0.0.1:8000/api/query?source=postgres&query=order&order_id=1'
```

A API aceita `source=postgres|mongo`, `query=order|daily|top|batch`, `start`, `end` e `order_id`. Retorna `rows`, `elapsed_ms`, `source` e `query`; parâmetros inválidos geram HTTP 400 e indisponibilidade/falha do banco gera HTTP 503. Não substitua falhas por números simulados. O tempo da API é de uma execução, não o benchmark estatístico.

## Ambiente, execução e testes

Python 3.11+, Docker com Compose e espaço para massa/volumes. Node é necessário somente aos testes JavaScript. `requirements.txt` define faixas; `requirements-lock.txt` registra versões da execução documentada. Tags Docker do Compose são mutáveis: consulte `results/images.txt` e `results/environment.json` ao investigar reprodução histórica.

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux; PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m unittest discover -s tests
node --test static/*.test.cjs
python -m lab --help
```

Esses testes não exigem bancos ativos e não comprovam integração. Consulte os registros de QA em `results/` e relate separadamente o que passou na sua execução. Não declare QA visual/mobile sem realizá-lo.

Para uma verificação pequena sem alterar os bancos:

```bash
python -m lab generate --count 100 --seed 42 --data data-amostra-nova
```

Para reprodução completa, **somente com bancos vazios e diretórios de saída novos**:

```bash
docker compose up -d --wait
python -m lab generate --count 1000000 --seed 42 --data data-reproducao
python -m lab load --data data-reproducao --out results/nova-carga
python -m lab benchmark --repetitions 10 --out results/nova-rodada
python -m lab serve --port 8000
```

Escolha outro nome se o diretório já contiver evidências. O JSONL completo não está no Git: são aproximadamente 630 MB, além do espaço dos bancos. O manifesto histórico registra 1.000.000 de pedidos e 5.492.836 itens. Compare hash, contagens e soma em centavos ao reproduzir; tempos de geração não são determinísticos.

`PG_DSN` e `MONGO_URI` alteram os destinos das conexões; confira-os antes de carregar. Portas padrão: PostgreSQL 55432, MongoDB 57017, dashboard 8000, sempre em localhost. O nome Mongo `bd_lab` é fixo no código; mudar só a URI não muda essa seleção. O Compose é destinado a um ambiente local isolado. Veja `docs/OPERACAO_SSD.txt` para operação local; a configuração do SSD original não está no repositório.

## Integridade, reprodução e limites

1. Não edite medições históricas para fazê-las coincidir com código alterado. Preserve `results/rodada-1`, `results/q1-direto-100-ids`, `results/q4-lotes-100-pedidos`, manifesto e relatórios. Registre novas rodadas separadamente com commit, versões, hardware, filtros e método.
2. A geração recusa sobrescrever `orders.jsonl`. A carga valida SHA-256 e contagens/somas, e recusa as estruturas de destino existentes; suas etapas nos dois bancos não são uma transação conjunta. Após falha, inspecione `load.json` e ambos os bancos. A carga escreve `load.json` no destino escolhido: use uma pasta nova para não substituir o relatório anterior.
3. O benchmark padrão exige pelo menos dez repetições, compara resultados completos, faz dois aquecimentos e alterna os bancos. Cronometra execução, materialização, normalização e serialização JSON, excluindo abertura de conexão. Mantém conexões persistentes e cache aquecido. Amostras parciais ou `benchmark-failure.json` não são uma rodada concluída.
4. A baseline Q1–Q3 favoreceu PostgreSQL. A Q1 Mongo histórica usava `aggregate`; o código atual usa `find`, portanto uma nova execução não replica exatamente aquela implementação. Não apague essa ressalva.
5. Q4 foi escolhida depois da baseline e é exploratória. Mongo foi aproximadamente 1,72× mais rápido nesse cenário específico. Isso não prova superioridade geral do NoSQL, nem separa efeito do motor, modelagem e implementação.
6. Preservar equivalência: mesmos pedidos, filtros, ordenação, campos, centavos e datas. Não remova índices de um lado para favorecer o outro. Tempos de carga e métricas de armazenamento também têm diferenças metodológicas documentadas.
7. Os scripts adicionais possuem saídas fixas já presentes no clone e recusam executá-las novamente. Para repetir, trabalhe numa cópia isolada ou altere explicitamente o destino para uma pasta nova; não apague as evidências para contornar a proteção. Eles pressupõem a massa completa, não a amostra de 100 pedidos.
8. `results/` é ignorado por padrão no Git, mas a evidência histórica já está versionada. Se novas evidências devem ser publicadas, revise-as e adicione somente os arquivos necessários explicitamente. Não use `git add -f` indiscriminadamente.

## Segurança e conservação

- Não publique `.env`, credenciais reais, dados pessoais, dumps privados, tokens, logs sensíveis, VM ou dependências instaladas. Revise também URLs de conexão e relatórios antes de commit.
- `local-lab-only` é apenas uma senha de demonstração do PostgreSQL. Mongo não está configurado com autenticação no Compose. Não exponha essas portas nem o servidor Python à internet; não trate a aplicação como pronta para produção.
- Não execute `docker compose down -v`, exclusões de tabelas/coleções ou limpeza de arquivos para resolver uma falha sem autorização específica. Para parar preservando volumes: `docker compose stop`.
- Faça alterações pequenas, preserve o conteúdo acadêmico e execute os testes relevantes. Mudanças de consultas exigem validação real de equivalência e uma nova rodada antes de alegar melhoria de desempenho.
- Ao entregar, informe arquivos alterados, comandos realmente executados, resultados e bloqueios. Nunca invente medições, vantagens, screenshots ou confirmações de funcionamento.
