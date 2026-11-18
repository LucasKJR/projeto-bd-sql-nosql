> Atualização: execução real concluída; consulte [RESULTADOS_REAIS.md](RESULTADOS_REAIS.md) para resultados, variantes e limitações. Qualquer pendência de execução abaixo pertence ao planejamento inicial.

# Entregas e evidências

Marque os itens somente depois de executá-los e guardar evidências. Esta lista **não declara** que os bancos já foram carregados ou que existe ganho comprovado.

## Até 19/11/2026 — Massa, carga e documentação (1,0 ponto)

- [ ] Ambiente com PostgreSQL e MongoDB funcionando.
- [x] 1.000.000 de pedidos lógicos gerados e verificados em 17/11/2026.
- [ ] Mesma massa carregada nos dois bancos.
- [ ] Contagens de pedidos, itens, clientes e produtos verificadas.
- [x] Semente, distribuição, período e significado de registro documentados.
- [ ] Esquemas/modelos e índices apresentados.
- [ ] Integridade e equivalência verificadas e limites da verificação declarados.
- [ ] Tempo de carga registrado para cada banco com escopo de medição.
- [ ] Tamanho de dados e índices registrado, com método/unidade.
- [x] Scripts, arquivos de configuração e instruções de reprodução incluídos.

## Até 24/11/2026 — Experimentos válidos (2,0 pontos)

- [ ] Três consultas equivalentes implementadas e explicadas lado a lado.
- [ ] Pelo menos 10 repetições medidas por consulta e por banco.
- [ ] Aquecimento/cache, hardware, versões e índices documentados.
- [ ] Tempos brutos preservados; medianas e dispersão calculadas.
- [ ] Resultados de negócio comparados, não apenas tempos.
- [ ] Um ganho NoSQL realista demonstrado e explicado pelo paradigma.
- [ ] Resultados favoráveis ao SQL e trade-offs relatados honestamente.
- [ ] Planos/estatísticas de execução e limitações anexados.

Se o ganho não aparecer, esse item permanece pendente; investigar e registrar os resultados reais.

## Até 24/11/2026 — Dashboard (2,5 pontos)

- [ ] Backend acessa de fato os dois bancos.
- [ ] Três visualizações/indicadores respondem a consultas reais.
- [ ] Pelo menos dois filtros alteram as consultas.
- [ ] Alternância PostgreSQL/MongoDB funciona.
- [ ] Tempos em milissegundos e comparação são visíveis.
- [ ] Estados carregando, vazio e erro não são confundidos com sucesso.
- [ ] Consulta com vantagem NoSQL demonstrada ao vivo.
- [ ] Fluxos repetidos e mudanças rápidas de filtro testados.

## Roteiro de demonstração

1. Mostrar os modelos e explicar o registro lógico.
2. Mostrar contagens e evidência da carga, não só o parâmetro passado ao gerador.
3. Escolher um pedido e consultar em cada banco; conferir cabeçalho e itens.
4. Alterar o intervalo temporal e mostrar a atualização das agregações.
5. Mostrar os tempos atuais no dashboard e distinguir uma execução isolada do benchmark de dez repetições.
6. Abrir os tempos brutos e as medianas do benchmark.
7. Explicar a consulta vencedora, os resultados que não favoreceram MongoDB e as limitações.

## Pacote final

- Código-fonte e README com execução reproduzível.
- Modelos, consultas SQL/NoSQL, índices e scripts de carga.
- Documentação da geração e evidência de volume/tamanho.
- Medições brutas e resumo estatístico.
- Registro do ambiente e do estado de cache/aquecimento.
- Evidências do dashboard e roteiro de demonstração.
- Slides com problema, abordagem, resultados reais e conclusão.

O código/dashboard não substitui slides ou as evidências experimentais. Mantenha a pesquisa teórica e a proposta anteriores como base; atualize conclusões apenas após medir.

## Registro de QA

| Verificação | Resultado | Evidência |
| --- | --- | --- |
| Geração determinística | A preencher após execução | Log/teste |
| Contagens e integridade | A preencher após carga | Relatório |
| Equivalência Q1/Q2/Q3 | A preencher após consultas reais | Resultado comparado |
| Benchmark mínimo | A preencher após execução | Arquivo de tempos brutos |
| Dashboard com bancos | A preencher após teste | Registro de navegação/API |

Datas fornecidas pelo aluno em 17/11/2026. No enunciado atualizado, a ausência de um entregável implica penalidade de 1,0 ponto; o “-1” não deve ser tratado como peso da atividade.
