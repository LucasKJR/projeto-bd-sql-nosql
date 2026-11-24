# Explorar dados

Abra **http://127.0.0.1:8765/explorer** com o laboratório local ativo. **Benchmark** continua em outra tela, com metodologia e consultas Q1–Q4.

1. Escolha o banco e uma tabela/coleção. PostgreSQL oferece pedidos, itens, clientes e produtos; MongoDB oferece pedidos, clientes e produtos, com itens embutidos no pedido.
2. Em **Filtros**, escolha campo, operador e valor. Você pode combinar até três condições com E. Exemplo: `product_id = 229` na tabela de itens; `items.product_id = 229` na coleção de pedidos.
3. Em **Campos no resultado**, marque somente o que deseja ver. Você pode filtrar por um campo sem exibi-lo. Na coleção de pedidos, marque `items` para incluir o array.
4. Clique em **Executar consulta**. Sem filtro, a consulta começa na primeira página; escolher o banco ou o objeto não dispara consulta automaticamente. As páginas avançam pelo identificador e, na tabela de itens, pela posição da linha.

O PostgreSQL projeta as colunas selecionadas e o MongoDB projeta os campos selecionados. Chaves usadas só na paginação não aparecem no resultado. O explorador não mostra código de consulta, não aceita comandos arbitrários e não altera registros do benchmark. Datas e horas estão em UTC e campos terminados em `_cents` estão em centavos.
