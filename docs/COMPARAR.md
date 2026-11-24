# Comparação interativa

Abra **http://127.0.0.1:8765/compare**. Selecione Pedidos, Clientes ou Produtos, acrescente filtros e marque os campos que deseja visualizar. Clique em **Comparar bancos**. A mesma seleção é enviada aos dois bancos, traduzindo somente o nome da chave do pedido (`id` e `_id`) e os operadores adequados de cada motor.

O painel mostra tabela relacional, documentos expansíveis, tempos atuais e se os IDs e valores dos campos escolhidos coincidem **na página exibida**, mesmo sem marcar o ID para exibição. A diferença em milissegundos e o vencedor são mostrados somente para resultados equivalentes e não vazios. Os tempos incluem conexão e leitura, não são a mediana do benchmark. Não há consulta livre ou alteração dos dados. O array de itens é uma diferença estrutural e continua em **Explorar dados**; comparações Q1–Q4 e amostras repetidas continuam em **Benchmark**.
