# CRUD equivalente de um pedido

Na pasta do projeto, com os dois bancos já iniciados:

```bash
.venv/bin/python -m lab crud-demo
```

A saída JSON mostra o mesmo UUID, cliente e itens nos dois bancos e falha se os resultados divergirem. As operações são **reais**. O pedido desta demonstração não pertence à massa de benchmark.

| Operação | PostgreSQL | MongoDB | Resultado conferido |
| --- | --- | --- | --- |
| Criação | Dois INSERTs lógicos no cabeçalho e nas linhas relacionadas, numa transação | `insert_one` de documento com os itens incorporados | Pedido criado, 2 linhas, R$ 104,50 |
| Leitura | SELECT pela chave com JOIN e agregação dos itens | `find_one` pela chave `_id` | Cabeçalho e todos os itens equivalentes |
| Atualização | UPDATE da situação, total e linhas, numa transação | `update_one` de situação, total e itens no mesmo documento | Situação concluído; 3 canecas em vez de 2; total R$ 136,00 |
| Exclusão | DELETE pela chave do pedido; FK remove as linhas de demonstração em cascata | `delete_one` pela chave do documento, incluindo os itens embutidos | 1 registro removido por banco; nova leitura vazia em ambos |

O PostgreSQL escreve exclusivamente nas tabelas do esquema `bd_lab_crud_demo` e o MongoDB escreve apenas em `bd_lab_crud_demo.orders`. Nenhuma operação de escrita usa o namespace da massa `bd_lab`; o comando não aceita ID, nome de tabela nem critério de exclusão informados por fora. Em caso de erro, a rotina tenta remover apenas o UUID que confirmou ter criado. A demonstração não depende de um cliente ou produto do conjunto de benchmark; IDs e nomes são exemplos próprios.

Na apresentação, a equipe pode executar o comando no terminal e usar o resultado salvo em `results/crud-demo.json` como evidência da execução real. O painel web continua de leitura e comparação; não há endpoint de escrita exposto.
